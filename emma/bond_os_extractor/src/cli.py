from __future__ import annotations

import logging
import math
import sys
from pathlib import Path

import click

from .config import get_settings, setup_logging

logger = logging.getLogger("bond_os_extractor")


@click.group()
@click.option("--log-level", default=None, help="Override log level (DEBUG, INFO, WARNING, ERROR)")
def cli(log_level: str | None) -> None:
    """Bond Official Statement PDF Extractor & Learning Engine."""
    setup_logging(log_level)


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--no-ai", is_flag=True, help="Skip AI (Tier 2) extraction")
@click.option("--no-db", is_flag=True, help="Skip database storage")
def ingest(path: str, no_ai: bool, no_db: bool) -> None:
    """Ingest one PDF or all PDFs in a directory."""
    from .extraction.orchestrator import ExtractionOrchestrator
    from .classification.deal_classifier import classify_deal
    from .storage.json_export import export_deal_to_json
    from .storage.database import init_database, save_deal_record

    settings = get_settings()
    if no_ai:
        settings.tier2_enabled = False

    target = Path(path).resolve()
    pdf_files: list[Path] = []
    if target.is_file() and target.suffix.lower() == ".pdf":
        pdf_files.append(target)
    elif target.is_dir():
        pdf_files = sorted(target.glob("*.pdf"))
    else:
        click.echo(f"Error: {path} is not a PDF file or directory", err=True)
        sys.exit(1)

    if not pdf_files:
        click.echo("No PDF files found", err=True)
        sys.exit(1)

    click.echo(f"Found {len(pdf_files)} PDF(s) to process")

    orchestrator = ExtractionOrchestrator()
    engine = None
    if not no_db:
        engine = init_database()

    success = 0
    failed = 0
    for i, pdf_path in enumerate(pdf_files, 1):
        click.echo(f"\n[{i}/{len(pdf_files)}] Processing: {pdf_path.name}")
        try:
            record = orchestrator.extract_document(pdf_path)
            record = classify_deal(record)

            # Export JSON
            json_path = export_deal_to_json(record)
            click.echo(f"  JSON: {json_path.name}")

            # Save to database
            if engine is not None:
                try:
                    save_deal_record(engine, record)
                    click.echo(f"  DB: saved")
                except Exception as exc:
                    click.echo(f"  DB: failed ({exc})", err=True)

            click.echo(
                f"  Completeness: {record.completeness_score:.0%} | "
                f"Type: {record.primary_classification} | "
                f"Size: {record.size_classification}"
            )
            success += 1
        except Exception as exc:
            click.echo(f"  FAILED: {exc}", err=True)
            logger.exception("Failed to process %s", pdf_path.name)
            failed += 1

    click.echo(f"\nDone: {success} succeeded, {failed} failed")


@cli.command()
def status() -> None:
    """Show corpus statistics."""
    from .storage.database import init_database, get_corpus_stats

    engine = init_database()
    stats = get_corpus_stats(engine)

    click.echo(f"Total deals: {stats['total_deals']}")
    click.echo(f"Avg completeness: {stats['avg_completeness']:.1%}")

    if stats["by_type"]:
        click.echo("\nBy type:")
        for t, count in stats["by_type"].items():
            click.echo(f"  {t}: {count}")

    if stats["by_size"]:
        click.echo("\nBy size:")
        for s, count in stats["by_size"].items():
            click.echo(f"  {s}: {count}")


@cli.command()
@click.option("--type", "bond_type", help="Filter by bond type")
@click.option("--min-par", type=float, help="Minimum par amount")
@click.option("--max-par", type=float, help="Maximum par amount")
@click.option("--state", help="Filter by state (2-letter code)")
@click.option("--cab", is_flag=True, default=None, help="Filter CAB bonds only")
@click.option("--slb", is_flag=True, default=None, help="Filter SLB bonds only")
def search(
    bond_type: str | None,
    min_par: float | None,
    max_par: float | None,
    state: str | None,
    cab: bool | None,
    slb: bool | None,
) -> None:
    """Search the corpus with filters."""
    from .storage.database import init_database, search_deals

    engine = init_database()
    results = search_deals(
        engine,
        bond_type=bond_type,
        min_par=min_par,
        max_par=max_par,
        state=state,
        cab=cab if cab else None,
        slb=slb if slb else None,
    )

    if not results:
        click.echo("No deals found matching criteria")
        return

    click.echo(f"Found {len(results)} deal(s):\n")
    for r in results:
        par_str = f"${r['par_amount']:,.0f}" if r["par_amount"] else "N/A"
        click.echo(
            f"  {r['issuer_name'] or 'Unknown'} | {r['series'] or ''} | "
            f"{par_str} | {r['bond_type'] or 'N/A'} | {r['state'] or 'N/A'} | "
            f"{r['classification'] or 'N/A'}"
        )


@cli.command(name="export")
@click.option("--format", "fmt", type=click.Choice(["json", "csv"]), default="json")
@click.option("--output", type=click.Path(), help="Output path")
def export_cmd(fmt: str, output: str | None) -> None:
    """Export corpus data."""
    import csv
    from .storage.database import init_database, search_deals

    engine = init_database()
    results = search_deals(engine)

    if not results:
        click.echo("No deals to export")
        return

    if fmt == "csv":
        out_path = Path(output) if output else get_settings().data_dir / "export.csv"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        click.echo(f"Exported {len(results)} deals to {out_path}")
    else:
        import json
        out_path = Path(output) if output else get_settings().data_dir / "export.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str)
        click.echo(f"Exported {len(results)} deals to {out_path}")


@cli.command(name="clear-cache")
@click.option("--older-than", type=int, default=0, help="Only clear entries older than N days")
def clear_cache(older_than: int) -> None:
    """Clear AI response cache."""
    from .extraction.cache import clear_cache as _clear

    settings = get_settings()
    removed = _clear(settings.cache_dir, older_than)
    click.echo(f"Removed {removed} cache entries")


@cli.command()
@click.argument("pdf_path", type=click.Path(exists=True))
def test_ingest(pdf_path: str) -> None:
    """Test PDF ingestion only (no extraction, no AI)."""
    from .ingestion.pdf_reader import extract_pdf
    from .ingestion.section_detector import detect_sections

    result = extract_pdf(Path(pdf_path))
    click.echo(f"File: {result.source_file}")
    click.echo(f"Hash: {result.source_hash[:16]}...")
    click.echo(f"Method: {result.extraction_method}")
    click.echo(f"Pages: {result.page_count}")
    click.echo(f"Locked: {result.metadata.is_locked}")

    total_chars = sum(len(p.text) for p in result.pages)
    total_tables = sum(len(p.tables) for p in result.pages)
    click.echo(f"Total chars: {total_chars:,}")
    click.echo(f"Total tables: {total_tables}")

    # Section detection
    sections = detect_sections(result)
    click.echo(f"\nSections detected: {len(sections)}")
    for s in sections:
        click.echo(f"  [{s.start_page}-{s.end_page}] {s.section_id}: {s.heading_text[:60]}")


@cli.command(name="ingest-all")
@click.argument("path", type=click.Path(exists=True))
@click.option("--no-db", is_flag=True, help="Skip database storage")
@click.option("--dry-run", is_flag=True, help="Show what would be processed without extracting")
def ingest_all(path: str, no_db: bool, dry_run: bool) -> None:
    """Ingest all document types from a directory using module routing.

    Routes each PDF to the appropriate extraction module (rating action,
    event filing, financial report) or falls back to the OS extractor.
    """
    import time
    from .ingestion.pdf_reader import extract_pdf
    from .modules.registry import get_registry
    from .storage.database import init_database

    target = Path(path).resolve()
    if target.is_file():
        pdf_files = [target]
    elif target.is_dir():
        pdf_files = sorted(target.rglob("*.pdf"))
    else:
        click.echo(f"Error: {path} is not a PDF file or directory", err=True)
        sys.exit(1)

    if not pdf_files:
        click.echo("No PDF files found", err=True)
        sys.exit(1)

    registry = get_registry()
    click.echo(f"Found {len(pdf_files)} PDF(s) to process")
    click.echo(f"Registered modules: {', '.join(m.name for m in registry.modules)}")

    if dry_run:
        # Just show routing decisions
        for i, pdf_path in enumerate(pdf_files, 1):
            # Quick first-page peek for routing
            try:
                ingestion = extract_pdf(pdf_path)
                first_page = ingestion.pages[0].text if ingestion.pages else ""
                mod = registry.route(pdf_path.name, first_page)
                mod_name = mod.display_name if mod else "Official Statement (default)"
                click.echo(f"  {i:3d}. [{mod_name}] {pdf_path.name[:70]}")
            except Exception:
                click.echo(f"  {i:3d}. [ERROR] {pdf_path.name[:70]}")
        return

    engine = None
    if not no_db:
        engine = init_database()

    # Track per-module stats
    stats: dict[str, dict[str, int]] = {}
    total_success = 0
    total_failed = 0

    for i, pdf_path in enumerate(pdf_files, 1):
        click.echo(f"\n{'='*70}")
        click.echo(f"[{i}/{len(pdf_files)}] {pdf_path.name}")
        click.echo(f"{'='*70}")
        t0 = time.time()

        try:
            ingestion = extract_pdf(pdf_path)
            first_page = ingestion.pages[0].text if ingestion.pages else ""
            mod = registry.route(pdf_path.name, first_page)

            if mod is not None:
                # Module handles this document
                click.echo(f"  Module: {mod.display_name}")
                record = mod.extract(ingestion)

                # Export JSON
                json_path = mod.export_json(record)
                click.echo(f"  JSON: {json_path.name}")

                # Save to database
                if engine is not None:
                    try:
                        mod.save(engine, record)
                        click.echo(f"  DB: saved")
                    except Exception as exc:
                        click.echo(f"  DB: failed ({exc})", err=True)

                completeness = getattr(record, "completeness_score", 0)
                issuer = getattr(record, "issuer_name", None) or "Unknown"
                elapsed = time.time() - t0
                click.echo(f"  Completeness: {completeness:.0%} | Issuer: {issuer} | Time: {elapsed:.1f}s")

                mod_name = mod.name
            else:
                # Fall back to OS extractor
                click.echo(f"  Module: Official Statement (default)")
                from .extraction.orchestrator import ExtractionOrchestrator
                from .classification.deal_classifier import classify_deal
                from .storage.json_export import export_deal_to_json
                from .storage.database import save_deal_record

                orchestrator = ExtractionOrchestrator()
                record = orchestrator.extract_document(pdf_path)
                record = classify_deal(record)

                json_path = export_deal_to_json(record)
                click.echo(f"  JSON: {json_path.name}")

                if engine is not None:
                    try:
                        save_deal_record(engine, record)
                        click.echo(f"  DB: saved")
                    except Exception as exc:
                        click.echo(f"  DB: failed ({exc})", err=True)

                elapsed = time.time() - t0
                click.echo(
                    f"  Completeness: {record.completeness_score:.0%} | "
                    f"Type: {record.primary_classification} | Time: {elapsed:.1f}s"
                )
                mod_name = "official_statement"

            # Update stats
            if mod_name not in stats:
                stats[mod_name] = {"success": 0, "failed": 0}
            stats[mod_name]["success"] += 1
            total_success += 1

        except Exception as exc:
            elapsed = time.time() - t0
            click.echo(f"  FAILED ({elapsed:.1f}s): {exc}", err=True)
            logger.exception("Failed to process %s", pdf_path.name)
            total_failed += 1

    click.echo(f"\n{'='*70}")
    click.echo(f"BATCH COMPLETE: {total_success} succeeded, {total_failed} failed")
    if stats:
        click.echo("\nBy module:")
        for mod_name, counts in sorted(stats.items()):
            click.echo(f"  {mod_name}: {counts['success']} succeeded, {counts['failed']} failed")
    click.echo(f"{'='*70}")


@cli.command(name="module-status")
@click.option("--module", "module_name", help="Show stats for a specific module")
def module_status(module_name: str | None) -> None:
    """Show corpus statistics for document modules."""
    from .modules.registry import get_registry
    from .storage.database import init_database

    engine = init_database()
    registry = get_registry()

    if module_name:
        mod = registry.get_module(module_name)
        if not mod:
            click.echo(f"Unknown module: {module_name}", err=True)
            click.echo(f"Available: {', '.join(m.name for m in registry.modules)}")
            sys.exit(1)
        try:
            mod_stats = mod.get_stats(engine)
            click.echo(f"\n{mod.display_name} Statistics:")
            for key, val in mod_stats.items():
                if isinstance(val, dict):
                    click.echo(f"  {key}:")
                    for k, v in val.items():
                        click.echo(f"    {k}: {v}")
                else:
                    click.echo(f"  {key}: {val}")
        except Exception as exc:
            click.echo(f"  No data yet ({exc})")
    else:
        click.echo("Document Module Statistics:")
        for mod in registry.modules:
            try:
                mod_stats = mod.get_stats(engine)
                total = mod_stats.get("total", 0)
                avg_c = mod_stats.get("avg_completeness", 0)
                click.echo(f"  {mod.display_name}: {total} docs, {avg_c:.1%} avg completeness")
            except Exception:
                click.echo(f"  {mod.display_name}: no data yet")


@cli.command()
@click.option("--threshold", type=float, default=50.0, help="Investable threshold (0-100)")
@click.option("--ticker-dir", type=click.Path(exists=True), default=None,
              help="Path to waste_tickers directory (auto-detected if not set)")
@click.option("--output", type=click.Path(), default=None, help="Output JSON path")
def score(threshold: float, ticker_dir: str | None, output: str | None) -> None:
    """Score the obligor universe using Summers' fundamental screening.

    Loads bond corpus data (OS, financial reports, rating actions) and
    equity ticker data (price history, financials) to compute F_i scores
    across five dimensions: Financial Stability, Profitability, Credit
    Quality, Structural Quality, and Growth/Momentum.

    Outputs the investable universe (F_i >= threshold) for Phase 2.
    """
    from .storage.database import init_database
    from .analysis.scoring_engine import score_universe, export_scores

    engine = init_database()
    ticker_base = Path(ticker_dir) if ticker_dir else None

    click.echo(f"Scoring universe with threshold={threshold}...")
    universe = score_universe(engine, threshold=threshold, ticker_base_dir=ticker_base)

    # Display results
    click.echo(f"\n{'='*70}")
    click.echo(f"FUNDAMENTAL SCORING RESULTS")
    click.echo(f"{'='*70}")

    summary = universe.summary()
    click.echo(f"Total obligors scored: {summary['total_obligors']}")
    click.echo(f"Investable (F_i >= {threshold}): {summary['investable_count']}")
    click.echo(f"Average F_i: {summary['avg_f_score']}")

    if summary["top_5"]:
        click.echo(f"\nTop 5 Obligors:")
        for i, s in enumerate(summary["top_5"], 1):
            ticker_str = f" ({s['ticker']})" if s.get("ticker") else ""
            click.echo(f"  {i}. {s['obligor']}{ticker_str}: F_i = {s['f_score']}")

    # Data quality summary
    quality_counts = {"full": 0, "partial": 0, "thin": 0}
    for s in universe.scores:
        quality_counts[s.data_quality] = quality_counts.get(s.data_quality, 0) + 1
    click.echo(f"\nData quality: {quality_counts['full']} full, "
               f"{quality_counts['partial']} partial, {quality_counts['thin']} thin")

    click.echo(f"\n{'='*70}")
    click.echo("Dimension Breakdown (Investable Universe):")
    click.echo(f"{'='*70}")
    for s in universe.investable:
        ticker_str = f" ({s.ticker})" if s.ticker else ""
        quality_str = f" [{s.data_quality}]" if s.data_quality else ""
        dflt_str = f" ({s.defaulted_dimensions} defaulted)" if s.defaulted_dimensions else ""
        click.echo(f"\n  {s.obligor_name}{ticker_str} — F_i = {s.f_score}{quality_str}{dflt_str}")
        for dim_name in [
            "financial_stability", "profitability",
            "credit_quality", "structural_quality",
            "growth_momentum",
        ]:
            dim = getattr(s, dim_name)
            if dim is not None:
                dflt_flag = " *DEFAULTED*" if dim.defaulted else ""
                click.echo(
                    f"    {dim.name:25s}: {dim.raw_score:5.1f} x {dim.weight:.2f} "
                    f"= {dim.weighted_score:5.2f}  [{dim.data_source}]{dflt_flag}"
                )

    # Export
    out_path = Path(output) if output else None
    json_path = export_scores(universe, out_path)
    click.echo(f"\nScores exported to: {json_path}")


@cli.command(name="score-detail")
@click.argument("obligor_name")
@click.option("--ticker-dir", type=click.Path(exists=True), default=None)
def score_detail(obligor_name: str, ticker_dir: str | None) -> None:
    """Show detailed scoring breakdown for a specific obligor.

    OBLIGOR_NAME can be a ticker (WM, RSG) or an issuer name substring.
    """
    from .storage.database import init_database
    from .analysis.scoring_engine import score_universe

    engine = init_database()
    ticker_base = Path(ticker_dir) if ticker_dir else None
    universe = score_universe(engine, ticker_base_dir=ticker_base)

    # Find the requested obligor
    name_lower = obligor_name.lower()
    match = None
    for s in universe.scores:
        if (s.ticker and s.ticker.lower() == name_lower) or \
           name_lower in s.obligor_name.lower():
            match = s
            break

    if match is None:
        click.echo(f"No obligor found matching '{obligor_name}'")
        click.echo(f"Available: {', '.join(s.obligor_name for s in universe.scores)}")
        return

    click.echo(f"\n{'='*70}")
    click.echo(f"DETAILED SCORE: {match.obligor_name}")
    if match.ticker:
        click.echo(f"Ticker: {match.ticker}")
    if match.cusips:
        click.echo(f"CUSIPs: {', '.join(match.cusips[:5])}")
    click.echo(f"{'='*70}")
    click.echo(f"\nComposite F_i: {match.f_score}")
    click.echo(f"Investable: {'YES' if match.investable else 'NO'} (threshold={match.threshold})")

    click.echo(f"\nData Sources:")
    for k, v in match.data_sources.items():
        click.echo(f"  {k}: {v}")

    for dim_name in [
        "financial_stability", "profitability",
        "credit_quality", "structural_quality",
        "growth_momentum",
    ]:
        dim = getattr(match, dim_name)
        if dim is None:
            continue
        click.echo(f"\n  {dim.name} (weight={dim.weight}, source={dim.data_source}):")
        click.echo(f"    Raw: {dim.raw_score:.1f} | Weighted: {dim.weighted_score:.2f}")
        click.echo(f"    Components:")
        for comp_name, comp_val in dim.components.items():
            if comp_val is not None:
                if isinstance(comp_val, float) and abs(comp_val) < 1:
                    click.echo(f"      {comp_name}: {comp_val:.4f}")
                else:
                    click.echo(f"      {comp_name}: {comp_val}")


@cli.command(name="s-omega")
@click.option("--threshold", type=float, default=50.0, help="F_i investable threshold")
@click.option("--rf", type=float, default=0.045, help="Annual risk-free rate (default 4.5%)")
@click.option("--start-date", default="2020-01-01", help="Start date for return series (YYYY-MM-DD)")
@click.option("--ticker-dir", type=click.Path(exists=True), default=None)
@click.option("--output", type=click.Path(), default=None)
def s_omega_cmd(
    threshold: float,
    rf: float,
    start_date: str,
    ticker_dir: str | None,
    output: str | None,
) -> None:
    """Compute S_Omega for the investable universe (Phase 2).

    Builds on Phase 1's fundamental scores: takes the investable set,
    constructs return series from equity price history, builds a waste
    sector market benchmark, and computes Summers' S_Omega, Omega ratio,
    and SIC matrix for each obligor.
    """
    from .storage.database import init_database
    from .analysis.scoring_engine import score_universe
    from .analysis.omega import analyze_universe, export_s_omega

    ticker_base = Path(ticker_dir) if ticker_dir else None

    # Phase 1: Get investable universe
    click.echo("Phase 1: Scoring fundamental universe...")
    engine = init_database()
    universe = score_universe(engine, threshold=threshold, ticker_base_dir=ticker_base)

    investable = [
        {
            "obligor_name": s.obligor_name,
            "ticker": s.ticker,
            "f_score": s.f_score,
            "aliases": getattr(s, "aliases", []),
        }
        for s in universe.investable
    ]
    click.echo(f"  {len(investable)} investable obligors from Phase 1\n")

    # Phase 2: S_Omega analysis
    click.echo("Phase 2: Computing S_Omega...")
    results = analyze_universe(
        investable,
        ticker_base_dir=ticker_base,
        rf_annual=rf,
        start_date=start_date,
        engine=engine,
    )

    if not results:
        click.echo("No assets with sufficient return data for S_Omega analysis.")
        return

    # Display results
    click.echo(f"\n{'='*70}")
    click.echo(f"S_OMEGA ANALYSIS RESULTS")
    click.echo(f"Risk-free rate: {rf*100:.1f}% annual | Start: {start_date}")
    click.echo(f"{'='*70}")

    click.echo(f"\n{'Ticker':<8} {'S_Omega':>9} {'Omega':>7} {'R_A':>8} {'E_A':>8} "
               f"{'MDDD_S':>7} {'MaxDD':>7} {'n':>6} {'Years':>6} {'F_i':>5}")
    click.echo("-" * 80)

    for r in results:
        sic = r.sic
        click.echo(
            f"{r.asset_id:<8} {r.s_omega*100:>8.2f}% "
            f"{r.omega_at_rf:>7.3f} "
            f"{sic.annualized_risk*100 if sic else 0:>7.2f}% "
            f"{sic.annualized_return*100 if sic else 0:>7.2f}% "
            f"{sic.max_drawdown_duration_years if sic else 0:>6.1f}y "
            f"{sic.max_drawdown_pct*100 if sic else 0:>6.1f}% "
            f"{r.n_observations:>6} "
            f"{r.n_years:>5.1f}y "
            f"{r.f_score or 0:>5.1f}"
        )

    click.echo(f"\n{'='*70}")
    click.echo("SIC Matrix (Summers Intuitive Characteristics):")
    click.echo(f"{'='*70}")
    for r in results:
        sic = r.sic
        if sic is None:
            continue
        click.echo(f"\n  {r.asset_id} ({r.asset_name}):")
        click.echo(f"    Annualized Risk (R_A):       {sic.annualized_risk*100:>8.2f}%")
        click.echo(f"    Annualized Return (E_A):      {sic.annualized_return*100:>8.2f}%")
        click.echo(f"    Max DD Duration (MDDD_S):     {sic.max_drawdown_duration_years:>7.1f} years")
        click.echo(f"      Drawdown (MDDD_A):          {sic.mddd_a:>7.0f} periods")
        click.echo(f"      Recovery (t_R):             {sic.recovery_time:>7.0f} periods")
        click.echo(f"    Max Drawdown Depth:           {sic.max_drawdown_pct*100:>7.1f}%")
        click.echo(f"    Accuracy A(S_Omega):          {r.accuracy*100:>7.2f}%")
        click.echo(f"    P(Black Swan):                {r.p_bse*100:>7.4f}%")

    # Export
    out_path = Path(output) if output else None
    json_path = export_s_omega(results, out_path)
    click.echo(f"\nResults exported to: {json_path}")


@cli.command(name="s-omega-detail")
@click.argument("ticker")
@click.option("--rf", type=float, default=0.045, help="Annual risk-free rate")
@click.option("--start-date", default="2020-01-01")
@click.option("--ticker-dir", type=click.Path(exists=True), default=None)
def s_omega_detail(ticker: str, rf: float, start_date: str, ticker_dir: str | None) -> None:
    """Show detailed S_Omega analysis for a single ticker."""
    from .analysis.return_series import build_equity_returns, build_market_benchmark
    from .analysis.omega import compute_s_omega

    ticker_base = Path(ticker_dir) if ticker_dir else None
    ticker = ticker.upper()

    click.echo(f"Building return series for {ticker}...")
    series = build_equity_returns(ticker, ticker_base, start_date)
    if series.n < 60:
        click.echo(f"Insufficient data for {ticker} ({series.n} observations)")
        return

    click.echo(f"Building market benchmark...")
    market = build_market_benchmark(base_dir=ticker_base, start_date=start_date)

    result = compute_s_omega(series, market, rf)

    click.echo(f"\n{'='*70}")
    click.echo(f"S_OMEGA DETAIL: {ticker}")
    click.echo(f"{'='*70}")

    click.echo(f"\n  S_Omega (annualized):    {result.s_omega*100:.4f}%")
    click.echo(f"  Omega at r_f:            {result.omega_at_rf:.4f}")
    click.echo(f"  Geometric mean (daily):  {result.geometric_mean*100:.6f}%")
    click.echo(f"  Risk-free (daily):       {result.risk_free_rate*100:.6f}%")
    click.echo(f"  Asset downside:          {result.downside_risk*100:.6f}%")
    click.echo(f"  Market downside:         {result.market_downside*100:.6f}%")
    click.echo(f"  Observations:            {result.n_observations}")
    click.echo(f"  Years of data:           {result.n_years:.1f}")
    click.echo(f"  Accuracy:                {result.accuracy*100:.2f}%")
    click.echo(f"  P(BSE):                  {result.p_bse*100:.4f}%")

    if result.sic:
        click.echo(f"\n  SIC Matrix:")
        click.echo(f"    R_A (annualized risk):  {result.sic.annualized_risk*100:.2f}%")
        click.echo(f"    E_A (annualized ret):   {result.sic.annualized_return*100:.2f}%")
        click.echo(f"    MDDD_S:                 {result.sic.max_drawdown_duration_years:.1f} years")
        click.echo(f"    Max drawdown:           {result.sic.max_drawdown_pct*100:.1f}%")

    if result.omega_curve:
        click.echo(f"\n  Omega Curve (21 thresholds):")
        for o in result.omega_curve:
            omega_str = f"{o.omega:.4f}" if not math.isinf(o.omega) else "inf"
            click.echo(f"    Theta={o.threshold*100:>8.4f}% -> Omega={omega_str}")


# ---------------------------------------------------------------------------
# Phase 3: Benchmark & Index Development
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--threshold", type=float, default=50.0, help="F_i investable threshold")
@click.option("--rf", type=float, default=0.045, help="Annual risk-free rate (default 4.5%)")
@click.option("--start-date", default="2020-01-01", help="Start date for return series")
@click.option("--ticker-dir", type=click.Path(exists=True), default=None)
@click.option("--output", type=click.Path(), default=None)
def benchmark(
    threshold: float,
    rf: float,
    start_date: str,
    ticker_dir: str | None,
    output: str | None,
) -> None:
    """Construct sector benchmark and composite ranking index (Phase 3).

    Runs Phase 1 (scoring) → Phase 2 (S_Omega) → Phase 3 (benchmark):
      - S_Omega-weighted sector benchmark
      - SIC efficiency frontier
      - Composite Ranking Index (CRI)
      - Relative value signals (overweight/equal/underweight)
    """
    from .storage.database import init_database
    from .analysis.scoring_engine import score_universe
    from .analysis.omega import analyze_universe
    from .analysis.benchmark import build_benchmark, export_benchmark

    ticker_base = Path(ticker_dir) if ticker_dir else None

    # Phase 1
    click.echo("Phase 1: Scoring fundamental universe...")
    engine = init_database()
    universe = score_universe(engine, threshold=threshold, ticker_base_dir=ticker_base)
    investable = [
        {"obligor_name": s.obligor_name, "ticker": s.ticker, "f_score": s.f_score,
         "aliases": getattr(s, "aliases", [])}
        for s in universe.investable
    ]
    click.echo(f"  {len(investable)} investable obligors\n")

    # Phase 2
    click.echo("Phase 2: Computing S_Omega...")
    s_omega_results = analyze_universe(
        investable, ticker_base_dir=ticker_base, rf_annual=rf, start_date=start_date,
        engine=engine,
    )
    if not s_omega_results:
        click.echo("No assets with sufficient data for benchmark construction.")
        return
    click.echo(f"  {len(s_omega_results)} assets with S_Omega results\n")

    # Phase 3
    click.echo("Phase 3: Building benchmark & composite index...")
    analysis = build_benchmark(s_omega_results)
    bm = analysis.benchmark

    # Display benchmark summary
    click.echo(f"\n{'='*75}")
    click.echo("SECTOR BENCHMARK")
    click.echo(f"{'='*75}")
    click.echo(f"  Constituents:        {bm.n_constituents}")
    click.echo(f"  Benchmark S_Omega:   {bm.benchmark_s_omega*100:.4f}%")
    click.echo(f"  Benchmark E_A:       {bm.benchmark_return*100:.2f}%")
    click.echo(f"  Benchmark R_A:       {bm.benchmark_risk*100:.2f}%")
    click.echo(f"  Benchmark Efficiency:{bm.benchmark_efficiency:.4f}")
    click.echo(f"  Benchmark MDDD_S:    {bm.benchmark_mddd_s:.1f} years")
    click.echo(f"  Benchmark F_i:       {bm.benchmark_f_score:.1f}")
    click.echo(f"  Concentration (HHI): {bm.herfindahl:.4f} (eff. N={bm.effective_n:.1f})")

    click.echo(f"\n  Sector Envelope:")
    click.echo(f"    S_Omega:  {bm.min_s_omega*100:.2f}% — {bm.max_s_omega*100:.2f}% "
               f"(spread: {bm.s_omega_spread*100:.2f}%)")
    click.echo(f"    E_A:      {bm.min_return*100:.2f}% — {bm.max_return*100:.2f}% "
               f"(spread: {bm.return_spread*100:.2f}%)")
    click.echo(f"    R_A:      {bm.min_risk*100:.2f}% — {bm.max_risk*100:.2f}% "
               f"(spread: {bm.risk_spread*100:.2f}%)")
    click.echo(f"    MDDD_S:   {bm.min_mddd_s:.1f}y — {bm.max_mddd_s:.1f}y")

    # Display CRI ranking table
    from .analysis.benchmark import CRI_WEIGHTS

    click.echo(f"\n{'='*75}")
    click.echo("COMPOSITE RANKING INDEX (CRI)")
    click.echo(f"  Weights: S_Omega={CRI_WEIGHTS['s_omega']:.0%}, "
               f"Efficiency={CRI_WEIGHTS['sic_efficiency']:.0%}, "
               f"Drawdown={CRI_WEIGHTS['drawdown_resilience']:.0%}, "
               f"Fundamental={CRI_WEIGHTS['fundamental_quality']:.0%}")
    click.echo(f"{'='*75}")

    click.echo(f"\n{'Rank':<5} {'Ticker':<8} {'CRI':>6} {'Signal':<12} "
               f"{'S_Omega':>9} {'Eff':>7} {'E_A':>8} {'R_A':>8} "
               f"{'MDDD_S':>7} {'F_i':>5} {'Wgt':>6}")
    click.echo("-" * 90)

    for c in analysis.ranked:
        click.echo(
            f"  {c.cri_rank:<3} {c.asset_id:<8} {c.cri_score:>5.1f} "
            f"{c.signal:<12} "
            f"{c.s_omega*100:>8.2f}% "
            f"{c.sic_efficiency:>7.4f} "
            f"{c.annualized_return*100:>7.2f}% "
            f"{c.annualized_risk*100:>7.2f}% "
            f"{c.mddd_s_years:>6.1f}y "
            f"{c.f_score:>5.1f} "
            f"{c.benchmark_weight*100:>5.1f}%"
        )

    # Relative value summary
    click.echo(f"\n{'='*75}")
    click.echo("RELATIVE VALUE vs BENCHMARK")
    click.echo(f"{'='*75}")

    for c in analysis.ranked:
        s_dir = "+" if c.s_omega_spread >= 0 else ""
        e_dir = "+" if c.efficiency_spread >= 0 else ""
        click.echo(
            f"\n  {c.asset_id} (CRI #{c.cri_rank}, {c.signal}):"
            f"\n    S_Omega spread:    {s_dir}{c.s_omega_spread*100:.2f}% vs benchmark"
            f"\n    Efficiency spread: {e_dir}{c.efficiency_spread:.4f} vs benchmark"
            f"\n    Percentiles:  S_Omega={c.s_omega_percentile:.0f}th, "
            f"Eff={c.efficiency_percentile:.0f}th, "
            f"DD={c.drawdown_percentile:.0f}th, "
            f"F_i={c.fundamental_percentile:.0f}th"
        )

    # Export
    out_path = Path(output) if output else None
    json_path = export_benchmark(analysis, out_path)
    click.echo(f"\nResults exported to: {json_path}")


@cli.command(name="benchmark-detail")
@click.argument("ticker")
@click.option("--threshold", type=float, default=50.0)
@click.option("--rf", type=float, default=0.045)
@click.option("--start-date", default="2020-01-01")
@click.option("--ticker-dir", type=click.Path(exists=True), default=None)
def benchmark_detail(
    ticker: str,
    threshold: float,
    rf: float,
    start_date: str,
    ticker_dir: str | None,
) -> None:
    """Show detailed benchmark analysis for a single constituent."""
    from .storage.database import init_database
    from .analysis.scoring_engine import score_universe
    from .analysis.omega import analyze_universe
    from .analysis.benchmark import build_benchmark, CRI_WEIGHTS

    ticker = ticker.upper()
    ticker_base = Path(ticker_dir) if ticker_dir else None

    # Run full pipeline
    click.echo(f"Running Phase 1 > 2 > 3 pipeline for {ticker}...")
    engine = init_database()
    universe = score_universe(engine, threshold=threshold, ticker_base_dir=ticker_base)
    investable = [
        {"obligor_name": s.obligor_name, "ticker": s.ticker, "f_score": s.f_score,
         "aliases": getattr(s, "aliases", [])}
        for s in universe.investable
    ]

    s_omega_results = analyze_universe(
        investable, ticker_base_dir=ticker_base, rf_annual=rf, start_date=start_date,
        engine=engine,
    )
    if not s_omega_results:
        click.echo("No S_Omega results available.")
        return

    analysis = build_benchmark(s_omega_results)
    bm = analysis.benchmark

    # Find the target constituent
    target = None
    for c in analysis.constituents:
        if c.asset_id == ticker:
            target = c
            break

    if target is None:
        click.echo(f"{ticker} not found in benchmark constituents.")
        click.echo(f"Available: {', '.join(c.asset_id for c in analysis.constituents)}")
        return

    c = target

    click.echo(f"\n{'='*70}")
    click.echo(f"BENCHMARK DETAIL: {c.asset_id} ({c.asset_name})")
    click.echo(f"{'='*70}")

    click.echo(f"\n  Composite Ranking Index:")
    click.echo(f"    CRI Score:             {c.cri_score:.1f} / 100")
    click.echo(f"    CRI Rank:              #{c.cri_rank} of {bm.n_constituents}")
    click.echo(f"    Signal:                {c.signal.upper()}")
    click.echo(f"    Benchmark Weight:      {c.benchmark_weight*100:.1f}%")

    click.echo(f"\n  Dimension Ranks (1 = best):")
    click.echo(f"    S_Omega:               #{c.s_omega_rank}  "
               f"({c.s_omega_percentile:.0f}th percentile)")
    click.echo(f"    SIC Efficiency:        #{c.efficiency_rank}  "
               f"({c.efficiency_percentile:.0f}th percentile)")
    click.echo(f"    Drawdown Resilience:   #{c.drawdown_rank}  "
               f"({c.drawdown_percentile:.0f}th percentile)")
    click.echo(f"    Fundamental Quality:   #{c.fundamental_rank}  "
               f"({c.fundamental_percentile:.0f}th percentile)")

    click.echo(f"\n  Absolute Measures:")
    click.echo(f"    S_Omega:               {c.s_omega*100:.4f}%")
    click.echo(f"    Omega at r_f:          {c.omega_at_rf:.4f}")
    click.echo(f"    SIC Efficiency (E_A/R_A): {c.sic_efficiency:.4f}")
    click.echo(f"    Annualized Return:     {c.annualized_return*100:.2f}%")
    click.echo(f"    Annualized Risk:       {c.annualized_risk*100:.2f}%")
    click.echo(f"    MDDD_S:                {c.mddd_s_years:.1f} years")
    click.echo(f"    Max Drawdown:          {c.max_drawdown_pct*100:.1f}%")
    click.echo(f"    F_i (Fundamental):     {c.f_score:.1f}")
    click.echo(f"    Observations:          {c.n_observations}")
    click.echo(f"    Years of data:         {c.n_years:.1f}")

    s_dir = "+" if c.s_omega_spread >= 0 else ""
    e_dir = "+" if c.efficiency_spread >= 0 else ""
    r_dir = "+" if c.return_spread >= 0 else ""
    rk_dir = "+" if c.risk_spread >= 0 else ""

    click.echo(f"\n  Relative Value vs Benchmark:")
    click.echo(f"    S_Omega spread:        {s_dir}{c.s_omega_spread*100:.4f}%  "
               f"(benchmark: {bm.benchmark_s_omega*100:.4f}%)")
    click.echo(f"    Efficiency spread:     {e_dir}{c.efficiency_spread:.4f}  "
               f"(benchmark: {bm.benchmark_efficiency:.4f})")
    click.echo(f"    Return spread:         {r_dir}{c.return_spread*100:.2f}%  "
               f"(benchmark: {bm.benchmark_return*100:.2f}%)")
    click.echo(f"    Risk spread:           {rk_dir}{c.risk_spread*100:.2f}%  "
               f"(benchmark: {bm.benchmark_risk*100:.2f}%)")

    click.echo(f"\n  Sector Position:")
    click.echo(f"    S_Omega range:         {bm.min_s_omega*100:.2f}% — "
               f"{bm.max_s_omega*100:.2f}% (this: {c.s_omega*100:.2f}%)")
    click.echo(f"    Return range:          {bm.min_return*100:.2f}% — "
               f"{bm.max_return*100:.2f}% (this: {c.annualized_return*100:.2f}%)")
    click.echo(f"    Risk range:            {bm.min_risk*100:.2f}% — "
               f"{bm.max_risk*100:.2f}% (this: {c.annualized_risk*100:.2f}%)")


# ---------------------------------------------------------------------------
# Phase 4: Hilbert Space Signal Extraction
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--threshold", type=float, default=50.0, help="F_i investable threshold")
@click.option("--rf", type=float, default=0.045, help="Annual risk-free rate")
@click.option("--start-date", default="2020-01-01")
@click.option("--ticker-dir", type=click.Path(exists=True), default=None)
@click.option("--output", type=click.Path(), default=None)
def signals(
    threshold: float,
    rf: float,
    start_date: str,
    ticker_dir: str | None,
    output: str | None,
) -> None:
    """Extract Hilbert space signals from investable universe (Phase 4).

    Runs Phase 1 > 2 > 4 pipeline:
      - FFT spectral analysis (dominant cycles, entropy, SNR)
      - DWT/MRA wavelet decomposition (trend vs noise energy)
      - DMD/Koopman mode extraction (cross-asset dynamics)
    """
    from .storage.database import init_database
    from .analysis.scoring_engine import score_universe
    from .analysis.return_series import build_equity_returns, build_market_benchmark
    from .analysis.hilbert import analyze_signals, export_hilbert

    ticker_base = Path(ticker_dir) if ticker_dir else None

    # Phase 1
    click.echo("Phase 1: Scoring fundamental universe...")
    engine = init_database()
    universe = score_universe(engine, threshold=threshold, ticker_base_dir=ticker_base)
    investable = [
        {"obligor_name": s.obligor_name, "ticker": s.ticker, "f_score": s.f_score,
         "aliases": getattr(s, "aliases", [])}
        for s in universe.investable
    ]
    click.echo(f"  {len(investable)} investable obligors\n")

    # Phase 2: Build return series
    click.echo("Phase 2: Building return series...")
    market = build_market_benchmark(base_dir=ticker_base, start_date=start_date)

    series_list = []
    for score_data in investable:
        ticker = score_data.get("ticker")
        if ticker:
            series = build_equity_returns(ticker, ticker_base, start_date)
            if series.n >= 60:
                series_list.append(series)
        else:
            from .analysis.synthetic_returns import build_synthetic_returns
            aliases = score_data.get("aliases", [])
            series = build_synthetic_returns(
                score_data["obligor_name"], aliases, engine, start_date=start_date,
            )
            if series and series.n >= 8:
                series_list.append(series)

    if not series_list:
        click.echo("No assets with sufficient return data for signal extraction.")
        return

    click.echo(f"  {len(series_list)} return series built\n")

    # Phase 4: Signal extraction
    click.echo("Phase 4: Extracting Hilbert space signals...")
    analysis = analyze_signals(series_list, market)

    # Display spectral results
    click.echo(f"\n{'='*75}")
    click.echo("FFT SPECTRAL ANALYSIS")
    click.echo(f"{'='*75}")
    click.echo(f"\n{'Asset':<10} {'Entropy':>8} {'SNR(dB)':>8} {'Dominant':>14} {'Top 3 Cycles'}")
    click.echo("-" * 75)

    for aid, sa in analysis.spectral.items():
        top_cycles = ", ".join(
            p.period_label for p in sa.peaks[:3]
        ) if sa.peaks else "N/A"
        click.echo(
            f"{aid:<10} {sa.spectral_entropy:>7.4f} "
            f"{sa.snr_db:>7.1f} "
            f"{sa.peaks[0].period_label if sa.peaks else 'N/A':>14} "
            f"{top_cycles}"
        )

    # Display wavelet results
    click.echo(f"\n{'='*75}")
    click.echo("WAVELET DECOMPOSITION (MRA)")
    click.echo(f"{'='*75}")

    for aid, wa in analysis.wavelet.items():
        click.echo(f"\n  {aid} ({wa.wavelet}, {wa.n_levels} levels):")
        click.echo(f"    Trend energy:  {wa.trend_energy_fraction*100:.1f}%")
        click.echo(f"    Noise energy:  {wa.noise_energy_fraction*100:.1f}%")
        t2n = wa.trend_to_noise
        t2n_str = f"{t2n:.2f}" if t2n < 1000 else "inf"
        click.echo(f"    Trend/Noise:   {t2n_str}")

        click.echo(f"    {'Level':<6} {'Scale':<22} {'Energy%':>8}")
        click.echo(f"    {'-'*40}")
        for lv in wa.levels:
            bar = "#" * int(lv.energy_fraction * 40)
            click.echo(
                f"    {lv.name:<6} {lv.scale_label:<22} "
                f"{lv.energy_fraction*100:>7.1f}% {bar}"
            )

    # Display DMD results
    if analysis.dmd and analysis.dmd.n_modes > 0:
        dmd = analysis.dmd
        click.echo(f"\n{'='*75}")
        click.echo("DMD / KOOPMAN MODE DECOMPOSITION")
        click.echo(f"{'='*75}")
        click.echo(f"  Assets: {', '.join(dmd.asset_ids)}")
        click.echo(f"  Modes extracted: {dmd.n_modes} "
                    f"({dmd.n_stable_modes} stable, {dmd.n_growing_modes} growing)")
        click.echo(f"  Reconstruction error: {dmd.reconstruction_error*100:.1f}%")

        click.echo(f"\n  {'#':<4} {'Period':<16} {'Growth':>8} {'Energy%':>8} "
                    f"{'Stable':>7}  Spatial Weights")
        click.echo(f"  {'-'*75}")

        for m in dmd.modes[:8]:
            period_str = _cli_period_label(m.period_days)
            spatial = ", ".join(
                f"{k}:{v:.3f}" for k, v in sorted(
                    m.spatial_weights.items(), key=lambda x: x[1], reverse=True,
                )
            )
            click.echo(
                f"  {m.mode_index:<4} {period_str:<16} "
                f"{m.growth_rate:>+7.4f} "
                f"{m.energy_fraction*100:>7.1f}% "
                f"{'yes' if m.is_stable else 'NO':>7}  "
                f"{spatial}"
            )

    # Export
    out_path = Path(output) if output else None
    json_path = export_hilbert(analysis, out_path)
    click.echo(f"\nResults exported to: {json_path}")


@cli.command(name="signal-detail")
@click.argument("ticker")
@click.option("--start-date", default="2020-01-01")
@click.option("--ticker-dir", type=click.Path(exists=True), default=None)
def signal_detail(ticker: str, start_date: str, ticker_dir: str | None) -> None:
    """Show detailed signal extraction for a single ticker."""
    from .analysis.return_series import build_equity_returns
    from .analysis.hilbert import compute_spectral_analysis, compute_wavelet_analysis

    ticker_base = Path(ticker_dir) if ticker_dir else None
    ticker = ticker.upper()

    click.echo(f"Building return series for {ticker}...")
    series = build_equity_returns(ticker, ticker_base, start_date)
    if series.n < 60:
        click.echo(f"Insufficient data for {ticker} ({series.n} observations)")
        return

    click.echo(f"Analyzing {series.n} observations ({series.n_years:.1f} years)...\n")

    # Spectral
    sa = compute_spectral_analysis(series, n_peaks=15)

    click.echo(f"{'='*70}")
    click.echo(f"SPECTRAL ANALYSIS: {ticker}")
    click.echo(f"{'='*70}")
    click.echo(f"  Spectral Entropy:    {sa.spectral_entropy:.4f} "
               f"({'noisy' if sa.spectral_entropy > 0.8 else 'structured' if sa.spectral_entropy < 0.6 else 'moderate'})")
    click.echo(f"  SNR:                 {sa.snr_db:.1f} dB")
    click.echo(f"  Dominant Period:     {sa.dominant_period_days:.1f} days "
               f"({sa.peaks[0].period_label if sa.peaks else 'N/A'})")

    if sa.peaks:
        click.echo(f"\n  Top Spectral Peaks:")
        click.echo(f"  {'#':<4} {'Period':<18} {'Power%':>8} {'Frequency':>12}")
        click.echo(f"  {'-'*50}")
        for i, p in enumerate(sa.peaks[:10]):
            click.echo(
                f"  {i+1:<4} {p.period_label:<18} "
                f"{p.power_fraction*100:>7.2f}% "
                f"{p.frequency:>12.6f}"
            )

    # Wavelet
    wa = compute_wavelet_analysis(series)

    click.echo(f"\n{'='*70}")
    click.echo(f"WAVELET DECOMPOSITION: {ticker}")
    click.echo(f"{'='*70}")
    click.echo(f"  Wavelet:            {wa.wavelet}")
    click.echo(f"  Levels:             {wa.n_levels}")
    click.echo(f"  Trend energy:       {wa.trend_energy_fraction*100:.1f}%")
    click.echo(f"  Noise energy:       {wa.noise_energy_fraction*100:.1f}%")
    t2n = wa.trend_to_noise
    t2n_str = f"{t2n:.2f}" if t2n < 1000 else "inf"
    click.echo(f"  Trend/Noise ratio:  {t2n_str}")

    click.echo(f"\n  Energy Distribution:")
    click.echo(f"  {'Level':<6} {'Scale':<24} {'Energy%':>8} {'Variance':>12}")
    click.echo(f"  {'-'*55}")
    for lv in wa.levels:
        bar = "#" * int(lv.energy_fraction * 50)
        click.echo(
            f"  {lv.name:<6} {lv.scale_label:<24} "
            f"{lv.energy_fraction*100:>7.1f}% "
            f"{lv.variance:>11.6f}  {bar}"
        )


def _cli_period_label(period_days: float) -> str:
    """Convert period in trading days to compact label for CLI output."""
    if period_days >= 1e6:
        return "DC/trend"
    elif period_days >= 252:
        return f"{period_days / 252:.1f}y"
    elif period_days >= 21:
        return f"{period_days / 21:.1f}mo"
    elif period_days >= 5:
        return f"{period_days / 5:.1f}wk"
    else:
        return f"{period_days:.0f}d"


# ---------------------------------------------------------------------------
# Phase 5: Extended Risk Measures — Full Pipeline
# ---------------------------------------------------------------------------

@cli.command(name="full-analysis")
@click.option("--threshold", type=float, default=50.0, help="F_i investable threshold")
@click.option("--rf", type=float, default=0.045, help="Annual risk-free rate")
@click.option("--start-date", default="2020-01-01")
@click.option("--ticker-dir", type=click.Path(exists=True), default=None)
@click.option("--output", type=click.Path(), default=None)
def full_analysis(
    threshold: float,
    rf: float,
    start_date: str,
    ticker_dir: str | None,
    output: str | None,
) -> None:
    """Run complete Summers methodology: Phase 1-5 pipeline.

    Phase 1: Fundamental scoring (F_i, investable universe)
    Phase 2: S_Omega, Omega ratio, SIC matrix
    Phase 3: Sector benchmark, CRI ranking
    Phase 4: Hilbert space signal extraction (FFT, wavelet, DMD)
    Phase 5: Extended Omega measures and Integrated Risk Score
    """
    from .storage.database import init_database
    from .analysis.scoring_engine import score_universe
    from .analysis.omega import analyze_universe
    from .analysis.benchmark import build_benchmark
    from .analysis.return_series import build_equity_returns, build_market_benchmark
    from .analysis.hilbert import analyze_signals
    from .analysis.extended_risk import (
        analyze_extended_risk, export_extended_risk, IRS_WEIGHTS,
    )

    ticker_base = Path(ticker_dir) if ticker_dir else None

    # Phase 1: Fundamental scoring
    click.echo("Phase 1: Fundamental scoring...")
    engine = init_database()
    universe = score_universe(engine, threshold=threshold, ticker_base_dir=ticker_base)
    investable = [
        {"obligor_name": s.obligor_name, "ticker": s.ticker, "f_score": s.f_score,
         "aliases": getattr(s, "aliases", [])}
        for s in universe.investable
    ]
    click.echo(f"  {len(universe.scores)} scored, {len(investable)} investable\n")

    # Phase 2: S_Omega
    click.echo("Phase 2: S_Omega analysis...")
    s_omega_results = analyze_universe(
        investable, ticker_base_dir=ticker_base, rf_annual=rf, start_date=start_date,
        engine=engine,
    )
    if not s_omega_results:
        click.echo("No assets with sufficient data. Pipeline stopped.")
        return
    click.echo(f"  {len(s_omega_results)} assets analyzed\n")

    # Phase 3: Benchmark & CRI
    click.echo("Phase 3: Benchmark & composite ranking...")
    benchmark_analysis = build_benchmark(s_omega_results)
    click.echo(f"  Benchmark S_Omega: {benchmark_analysis.benchmark.benchmark_s_omega*100:.2f}%\n")

    # Phase 4: Hilbert space signals
    click.echo("Phase 4: Hilbert space signal extraction...")
    market = build_market_benchmark(base_dir=ticker_base, start_date=start_date)
    series_list = []
    for score_data in investable:
        ticker = score_data.get("ticker")
        if ticker:
            series = build_equity_returns(ticker, ticker_base, start_date)
            if series.n >= 60:
                series_list.append(series)

    hilbert = analyze_signals(series_list, market)
    click.echo(f"  {len(hilbert.spectral)} spectral, {len(hilbert.wavelet)} wavelet analyses\n")

    # Phase 5: Extended risk measures
    click.echo("Phase 5: Extended Omega & Integrated Risk Score...")
    ext_risk = analyze_extended_risk(
        s_omega_results, hilbert, benchmark_analysis.constituents,
    )

    # Display results
    click.echo(f"\n{'='*80}")
    click.echo("SUMMERS METHODOLOGY - COMPLETE ANALYSIS")
    click.echo(f"{'='*80}")

    n_equity = sum(1 for r in s_omega_results if r.asset_type == "equity")
    n_bond = sum(1 for r in s_omega_results if r.asset_type == "bond")
    click.echo(f"\n  Universe: {len(universe.scores)} obligors scored, "
               f"{len(investable)} investable, "
               f"{len(s_omega_results)} with S_Omega "
               f"({n_equity} equity [E], {n_bond} bond [B])")
    click.echo(f"  Risk-free rate: {rf*100:.1f}% | Start: {start_date}")

    # Summary table
    click.echo(f"\n{'='*80}")
    click.echo("INTEGRATED RISK SCORE (IRS) RANKING")
    click.echo(f"  Weights: Spectral={IRS_WEIGHTS['spectral_omega']:.0%}, "
               f"Wavelet={IRS_WEIGHTS['wavelet_omega']:.0%}, "
               f"Dynamic={IRS_WEIGHTS['dynamic_omega']:.0%}")
    click.echo(f"{'='*80}")

    click.echo(f"\n{'Rank':<5} {'Asset':<12} {'IRS':>7} {'Signal':>8} "
               f"{'Omega':>7} {'Om_S':>7} {'Om_W':>7} {'Om_D':>7} "
               f"{'S_Omega':>9} {'F_i':>5} {'CRI':>5}")
    click.echo("-" * 94)

    for a in ext_risk.ranked:
        type_tag = "[B]" if a.asset_type == "bond" else "[E]"
        click.echo(
            f"  {a.irs_rank:<3} {a.asset_id:<8}{type_tag} "
            f"{a.irs:>6.4f} {a.signal_quality:>8} "
            f"{a.base_omega:>7.4f} "
            f"{a.spectral_omega:>7.4f} "
            f"{a.wavelet_omega:>7.4f} "
            f"{a.dynamic_omega:>7.4f} "
            f"{a.base_s_omega*100:>8.2f}% "
            f"{a.f_score:>5.1f} "
            f"{a.cri_score:>5.1f}"
        )

    # Detailed breakdown per asset
    click.echo(f"\n{'='*80}")
    click.echo("EXTENDED OMEGA DECOMPOSITION")
    click.echo(f"{'='*80}")

    for a in ext_risk.ranked:
        type_tag = "bond" if a.asset_type == "bond" else "equity"
        click.echo(f"\n  {a.asset_id} (IRS #{a.irs_rank}, {a.signal_quality} signal, {type_tag}):")
        click.echo(f"    Base Omega (at r_f):    {a.base_omega:.4f}")

        click.echo(f"    Spectral Omega:        {a.spectral_omega:.4f}  "
                    f"(x{a.spectral_adjustment:.4f})  "
                    f"H={a.spectral_entropy:.4f}, SNR={a.spectral_snr_db:.1f}dB")
        click.echo(f"    Wavelet Omega:         {a.wavelet_omega:.4f}  "
                    f"(x{a.wavelet_adjustment:.4f})  "
                    f"T/N={a.trend_to_noise:.4f}")
        click.echo(f"    Dynamic Omega:         {a.dynamic_omega:.4f}  "
                    f"(x{a.dynamic_adjustment:.4f})  "
                    f"stable={a.stable_fraction:.0%}")

        click.echo(f"    Integrated Risk Score: {a.irs:.4f}")
        click.echo(f"    Context: S_Omega={a.base_s_omega*100:.2f}%, "
                    f"F_i={a.f_score:.1f}, CRI={a.cri_score:.1f}")

    # Universe summary
    click.echo(f"\n{'='*80}")
    click.echo("UNIVERSE SUMMARY")
    click.echo(f"{'='*80}")
    click.echo(f"  Average IRS:     {ext_risk.avg_irs:.4f}")
    click.echo(f"  Best IRS:        {ext_risk.best_irs_asset}")
    click.echo(f"  Signal quality:  "
               f"{ext_risk.signal_distribution.get('strong', 0)} strong, "
               f"{ext_risk.signal_distribution.get('moderate', 0)} moderate, "
               f"{ext_risk.signal_distribution.get('weak', 0)} weak")

    # Export
    out_path = Path(output) if output else None
    json_path = export_extended_risk(ext_risk, out_path)
    click.echo(f"\nResults exported to: {json_path}")


# ---------------------------------------------------------------------------
# Phase 6: Synthetic Bond Returns
# ---------------------------------------------------------------------------

@cli.command(name="bond-returns")
@click.argument("obligor_name")
@click.option("--start-date", default="2020-01-01", help="Start date (YYYY-MM-DD)")
@click.option("--max-rows", type=int, default=50, help="Max observation rows to display")
@click.option("--output", type=click.Path(), default=None, help="Export JSON path")
def bond_returns_cmd(
    obligor_name: str,
    start_date: str,
    max_rows: int,
    output: str | None,
) -> None:
    """Build and display synthetic bond return series for an obligor.

    Searches EMMA secondary market data for matching bonds, then
    constructs a cascading return series from four priority sources:
      P1: EMMA trade returns (highest fidelity)
      P2: Rating event shocks (spread-duration model)
      P3: Fundamental drift (DSCR/revenue changes)
      P4: Coupon carry interpolation (gap filler)

    OBLIGOR_NAME is a case-insensitive search term (e.g. "Mission", "Republic").
    """
    import json
    from .storage.database import init_database
    from .analysis.data_loader import load_emma_bonds_by_issuer
    from .analysis.synthetic_returns import build_synthetic_returns, SyntheticReturnConfig

    engine = init_database()

    # Search for EMMA bonds
    click.echo(f"Searching EMMA data for '{obligor_name}'...")
    emma_bonds = load_emma_bonds_by_issuer(obligor_name)

    if emma_bonds:
        click.echo(f"  Found {len(emma_bonds)} matching EMMA bond(s)")
        for b in emma_bonds[:5]:
            snap = b.get("snapshot", {})
            name = snap.get("security_name", "?")
            cusip = snap.get("cusip", "?")
            cpn = snap.get("coupon_pct", "?")
            n_trades = len(b.get("trades", []))
            click.echo(f"    {cusip} — {name} ({cpn} cpn, {n_trades} trades)")
        if len(emma_bonds) > 5:
            click.echo(f"    ... and {len(emma_bonds) - 5} more")
    else:
        click.echo("  No EMMA bonds found.")

    # Build synthetic returns
    click.echo(f"\nBuilding synthetic return series...")
    series = build_synthetic_returns(
        obligor_name=obligor_name,
        aliases=[],
        engine=engine,
        emma_bonds=emma_bonds,
        start_date=start_date,
    )

    if series is None:
        click.echo("Insufficient data to build return series (need >= 8 observations).")
        return

    # Display summary
    click.echo(f"\n{'='*70}")
    click.echo(f"SYNTHETIC BOND RETURNS: {series.asset_name}")
    click.echo(f"{'='*70}")
    click.echo(f"  Asset ID:          {series.asset_id}")
    click.echo(f"  Asset type:        {series.asset_type}")
    click.echo(f"  Frequency:         {series.frequency}")
    click.echo(f"  Observations:      {series.n}")
    click.echo(f"  Date range:        {series.dates[0]} to {series.dates[-1]}")
    click.echo(f"  Years of data:     {series.n_years:.2f}")
    click.echo(f"  Periods/year:      {series.periods_per_year:.1f}")

    # Return statistics
    import numpy as np
    rets = np.array(series.returns)
    click.echo(f"\n  Return Statistics:")
    click.echo(f"    Mean:            {rets.mean()*100:>8.4f}%")
    click.echo(f"    Std Dev:         {rets.std()*100:>8.4f}%")
    click.echo(f"    Min:             {rets.min()*100:>8.4f}%")
    click.echo(f"    Max:             {rets.max()*100:>8.4f}%")
    click.echo(f"    Positive:        {(rets > 0).sum()}/{len(rets)} ({(rets > 0).mean()*100:.0f}%)")
    cum = (1 + rets).prod()
    click.echo(f"    Cumulative:      {(cum - 1)*100:>8.2f}%")

    # Observation table
    click.echo(f"\n  {'Date':<12} {'Return':>10} {'Price':>10}")
    click.echo(f"  {'-'*34}")
    display_n = min(max_rows, series.n)
    for i in range(display_n):
        click.echo(
            f"  {series.dates[i]:<12} "
            f"{series.returns[i]*100:>9.4f}% "
            f"{series.prices[i]:>9.2f}"
        )
    if series.n > display_n:
        click.echo(f"  ... ({series.n - display_n} more rows, use --max-rows to show more)")

    # Export
    if output:
        out_data = {
            "obligor": series.asset_name,
            "asset_id": series.asset_id,
            "asset_type": series.asset_type,
            "frequency": series.frequency,
            "n_observations": series.n,
            "n_years": round(series.n_years, 2),
            "date_range": [series.dates[0], series.dates[-1]],
            "statistics": {
                "mean_return": round(float(rets.mean()), 6),
                "std_return": round(float(rets.std()), 6),
                "min_return": round(float(rets.min()), 6),
                "max_return": round(float(rets.max()), 6),
                "cumulative_return": round(float(cum - 1), 4),
            },
            "observations": [
                {"date": d, "return": round(r, 6), "price": round(p, 2)}
                for d, r, p in zip(series.dates, series.returns, series.prices)
            ],
        }
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(out_data, indent=2))
        click.echo(f"\nExported to: {out_path}")


@cli.command(name="risk-benchmark")
@click.option("--output", "-o", type=click.Path(), default=None, help="Output JSON path")
def risk_benchmark(output: str | None) -> None:
    """Build risk benchmarks from EMMA corpus for readiness assessment.

    Aggregates risk factors, rating agency perspectives, and financial
    metrics from the EMMA bond corpus into benchmarks aligned with the
    5 Muni-Pal readiness risk paths.

    Each benchmark includes methodology narratives explaining how it was
    derived from the corpus and what factors drive it.
    """
    import json
    from .storage.database import init_database
    from .analysis.risk_benchmark import (
        build_risk_benchmarks,
        export_risk_benchmark,
    )

    engine = init_database()
    click.echo("Building risk benchmarks from EMMA corpus...")
    report = build_risk_benchmarks(engine)

    # Corpus summary
    cs = report.corpus_summary
    click.echo(f"\n{'=' * 72}")
    click.echo("  EMMA Corpus Risk Benchmarks for Readiness Assessment")
    click.echo(f"{'=' * 72}")
    click.echo(f"\nCorpus: {cs.get('sector', 'N/A')}")
    click.echo(
        f"  Official Statements: {cs.get('n_official_statements', 0)}  |  "
        f"Risk Factors: {cs.get('n_risk_factors', 0)}  |  "
        f"Rating Factors: {cs.get('n_rating_factors', 0)}"
    )
    click.echo(
        f"  Security Packages: {cs.get('n_security_packages', 0)}  |  "
        f"Financial Reports: {cs.get('n_financial_reports', 0)}  |  "
        f"Risk Categories: {cs.get('risk_categories_observed', 0)}"
    )

    # Per-path benchmarks
    for path, bm in report.benchmarks.items():
        click.echo(f"\n{'-' * 72}")
        click.echo(f"  {bm.display_name}  ({path})")
        click.echo(f"{'-' * 72}")

        sev = bm.severity_distribution
        total_sev = sum(sev.values()) or 1
        click.echo(
            f"  Risk factors: {bm.n_risk_factors} across {bm.n_issuances} issuances"
        )
        click.echo(
            f"  Severity: "
            f"{sev.get('boilerplate', 0)} boilerplate ({sev.get('boilerplate', 0)/total_sev*100:.0f}%), "
            f"{sev.get('material', 0)} material ({sev.get('material', 0)/total_sev*100:.0f}%), "
            f"{sev.get('significant', 0)} significant ({sev.get('significant', 0)/total_sev*100:.0f}%)"
        )
        click.echo(f"  Mitigation rate: {bm.mitigation_rate * 100:.0f}%")

        # Rating agency perspective
        click.echo(
            f"  Rating agency factors: {bm.n_rating_factors} "
            f"({bm.strength_count} strengths, {bm.challenge_count} challenges, "
            f"{bm.key_factor_count} key factors)"
        )

        # Methodology narrative
        click.echo(f"\n  Methodology:")
        _wrap_echo(bm.methodology_narrative, indent=4, width=68)

        # Benchmark standard
        click.echo(f"\n  Benchmark Standard:")
        _wrap_echo(bm.benchmark_standard, indent=4, width=68)

        # Sample titles
        if bm.sample_titles:
            click.echo(f"\n  Sample risk factor titles:")
            for t in bm.sample_titles[:5]:
                click.echo(f"    - {t[:80]}")

        # Sample rating agency factors
        if bm.sample_strengths:
            click.echo(f"\n  Rating agency strengths (sample):")
            for s in bm.sample_strengths[:3]:
                click.echo(f"    + {s[:100]}")
        if bm.sample_challenges:
            click.echo(f"  Rating agency challenges (sample):")
            for c in bm.sample_challenges[:3]:
                click.echo(f"    - {c[:100]}")

    # Financial benchmarks
    fb = report.financial_benchmarks
    click.echo(f"\n{'-' * 72}")
    click.echo("  Financial Benchmarks")
    click.echo(f"{'-' * 72}")

    if fb.dscr:
        click.echo(
            f"  DSCR: median {fb.dscr.median:.2f}x  "
            f"(p25={fb.dscr.p25:.2f}x, p75={fb.dscr.p75:.2f}x, "
            f"n={fb.dscr.n_observations})"
        )
    if fb.coverage_ratio:
        click.echo(
            f"  Coverage Ratio: median {fb.coverage_ratio.median:.2f}x  "
            f"(p25={fb.coverage_ratio.p25:.2f}x, p75={fb.coverage_ratio.p75:.2f}x, "
            f"n={fb.coverage_ratio.n_observations})"
        )
    if fb.revenue:
        click.echo(
            f"  Revenue: median ${fb.revenue.median:,.0f}  "
            f"(p25=${fb.revenue.p25:,.0f}, p75=${fb.revenue.p75:,.0f}, "
            f"n={fb.revenue.n_observations})"
        )
    if fb.pledge_type_distribution:
        click.echo(f"  Pledge types: {dict(fb.pledge_type_distribution)}")

    # Export
    out_path = Path(output) if output else None
    exported = export_risk_benchmark(report, out_path)
    click.echo(f"\nExported to: {exported}")


@cli.command(name="risk-compare")
@click.option("--project-name", "-p", default="Project", help="Project name")
@click.option("--dscr", type=float, default=None, help="Project DSCR (e.g., 1.34)")
@click.option("--revenue", type=float, default=None, help="Annual revenue in USD")
@click.option("--coverage-ratio", type=float, default=None, help="Minimum coverage ratio")
@click.option("--has-technology-risk", is_flag=True, help="Project has technology risk disclosure")
@click.option("--has-construction-risk", is_flag=True, help="Project has construction risk disclosure")
@click.option("--has-market-risk", is_flag=True, help="Project has market risk disclosure")
@click.option("--has-regulatory-risk", is_flag=True, help="Project has regulatory risk disclosure")
@click.option("--has-feedstock-risk", is_flag=True, help="Project has feedstock risk disclosure")
@click.option("--has-technology-mitigants", is_flag=True, help="Project has technology mitigants")
@click.option("--has-construction-mitigants", is_flag=True, help="Project has construction mitigants")
@click.option("--has-market-mitigants", is_flag=True, help="Project has market mitigants")
@click.option("--has-regulatory-mitigants", is_flag=True, help="Project has regulatory mitigants")
@click.option("--has-feedstock-mitigants", is_flag=True, help="Project has feedstock mitigants")
@click.option("--output", "-o", type=click.Path(), default=None, help="Output JSON path")
def risk_compare(
    project_name: str,
    dscr: float | None,
    revenue: float | None,
    coverage_ratio: float | None,
    has_technology_risk: bool,
    has_construction_risk: bool,
    has_market_risk: bool,
    has_regulatory_risk: bool,
    has_feedstock_risk: bool,
    has_technology_mitigants: bool,
    has_construction_mitigants: bool,
    has_market_mitigants: bool,
    has_regulatory_mitigants: bool,
    has_feedstock_mitigants: bool,
    output: str | None,
) -> None:
    """Compare a project's risk profile against EMMA corpus benchmarks.

    Builds benchmarks from the EMMA corpus, then compares the project's
    risk disclosures and financial metrics against them. Produces gap
    assessments with severity ratings and priority actions.

    Example:
        python -m src.cli risk-compare -p "GSI Caldor" --dscr 1.34 \\
            --revenue 10000000 --has-technology-risk --has-market-risk
    """
    import json
    from .storage.database import init_database
    from .analysis.risk_benchmark import (
        build_risk_benchmarks,
        compare_project_to_benchmarks,
        export_project_comparison,
    )

    engine = init_database()
    click.echo(f"Building corpus benchmarks and comparing {project_name}...")
    report = build_risk_benchmarks(engine)

    # Build project facts from flags
    project_facts: dict[str, str | None] = {
        "risk.technology.description": "provided" if has_technology_risk else None,
        "risk.technology.mitigants": "provided" if has_technology_mitigants else None,
        "risk.construction.description": "provided" if has_construction_risk else None,
        "risk.construction.mitigants": "provided" if has_construction_mitigants else None,
        "risk.market.description": "provided" if has_market_risk else None,
        "risk.market.mitigants": "provided" if has_market_mitigants else None,
        "risk.regulatory.description": "provided" if has_regulatory_risk else None,
        "risk.regulatory.mitigants": "provided" if has_regulatory_mitigants else None,
        "risk.feedstock.description": "provided" if has_feedstock_risk else None,
        "risk.feedstock.mitigants": "provided" if has_feedstock_mitigants else None,
    }

    project_financials: dict[str, float | None] = {
        "dscr": dscr,
        "revenue": revenue,
        "coverage_ratio": coverage_ratio,
    }

    comparison = compare_project_to_benchmarks(
        report, project_facts, project_financials, project_name,
    )

    # Display results
    click.echo(f"\n{'=' * 72}")
    click.echo(f"  Risk Comparison: {project_name} vs EMMA Corpus")
    click.echo(f"{'=' * 72}")
    click.echo(
        f"\n  Overall Risk Position: {comparison.overall_risk_position.replace('_', ' ').upper()}"
    )

    # Dimension comparisons
    for dc in comparison.dimension_comparisons:
        sev_marker = {
            "critical": "!!",
            "material": "! ",
            "acceptable": "  ",
        }.get(dc.severity, "  ")
        status_marker = {
            "missing": "[ ]",
            "partial": "[~]",
            "addressed": "[x]",
        }.get(dc.project_status, "[ ]")

        click.echo(f"\n{sev_marker} {status_marker} {dc.display_name} ({dc.readiness_path})")
        click.echo(f"      Status: {dc.project_status}  |  Severity: {dc.severity}")

        # Corpus benchmark (abbreviated)
        click.echo(f"      Corpus: ", nl=False)
        _wrap_echo(dc.corpus_benchmark, indent=14, width=58)

        # Gap assessment
        click.echo(f"      Gap: ", nl=False)
        _wrap_echo(dc.gap_assessment, indent=14, width=58)

        # Recommendation
        click.echo(f"      Action: ", nl=False)
        _wrap_echo(dc.recommendation, indent=14, width=58)

    # Financial comparison
    if comparison.financial_comparison:
        click.echo(f"\n{'-' * 72}")
        click.echo("  Financial Comparison")
        click.echo(f"{'-' * 72}")
        for metric, details in comparison.financial_comparison.items():
            if isinstance(details, dict) and "assessment" in details:
                click.echo(f"  {metric}: {details['assessment']}")

    # Priority actions
    if comparison.priority_actions:
        click.echo(f"\n{'-' * 72}")
        click.echo("  Priority Actions")
        click.echo(f"{'-' * 72}")
        for i, action in enumerate(comparison.priority_actions, 1):
            click.echo(f"  {i}. {action}")

    # Export
    if output:
        out_path = Path(output)
    else:
        out_path = None
    exported = export_project_comparison(comparison, out_path)
    click.echo(f"\nExported to: {exported}")


def _wrap_echo(text: str, indent: int = 4, width: int = 68) -> None:
    """Word-wrap text and echo with indentation."""
    import textwrap
    prefix = " " * indent
    wrapped = textwrap.fill(text, width=width, initial_indent="", subsequent_indent=prefix)
    click.echo(wrapped)


@cli.command(name="risk-guide")
@click.option("--project-name", "-p", default="Project", help="Project name")
@click.option("--dscr", type=float, default=None, help="Project DSCR (e.g., 1.34)")
@click.option("--revenue", type=float, default=None, help="Annual revenue in USD")
@click.option("--coverage-ratio", type=float, default=None, help="Minimum coverage ratio")
@click.option("--has-technology-risk", is_flag=True, help="Project has technology risk disclosure")
@click.option("--has-construction-risk", is_flag=True, help="Project has construction risk disclosure")
@click.option("--has-market-risk", is_flag=True, help="Project has market risk disclosure")
@click.option("--has-regulatory-risk", is_flag=True, help="Project has regulatory risk disclosure")
@click.option("--has-feedstock-risk", is_flag=True, help="Project has feedstock risk disclosure")
@click.option("--has-technology-mitigants", is_flag=True, help="Project has technology mitigants")
@click.option("--has-construction-mitigants", is_flag=True, help="Project has construction mitigants")
@click.option("--has-market-mitigants", is_flag=True, help="Project has market mitigants")
@click.option("--has-regulatory-mitigants", is_flag=True, help="Project has regulatory mitigants")
@click.option("--has-feedstock-mitigants", is_flag=True, help="Project has feedstock mitigants")
@click.option("--output", "-o", type=click.Path(), default=None, help="Output path prefix")
@click.option("--format", "fmt", type=click.Choice(["json", "markdown", "both"]),
              default="both", help="Output format")
def risk_guide(
    project_name: str,
    dscr: float | None,
    revenue: float | None,
    coverage_ratio: float | None,
    has_technology_risk: bool,
    has_construction_risk: bool,
    has_market_risk: bool,
    has_regulatory_risk: bool,
    has_feedstock_risk: bool,
    has_technology_mitigants: bool,
    has_construction_mitigants: bool,
    has_market_mitigants: bool,
    has_regulatory_mitigants: bool,
    has_feedstock_mitigants: bool,
    output: str | None,
    fmt: str,
) -> None:
    """Generate Risk Mitigation Implementation Guide for a project.

    Combines corpus evidence, rating agency perspectives, structural
    protections, and playbook guidance into actionable recommendations.
    Shows HOW corpus issuers addressed risks and WHAT the project should
    do to close each gap.

    Example:
        python -m src.cli risk-guide -p "GSI Caldor UCS" --dscr 1.34 \\
            --revenue 10000000 --has-technology-risk --has-market-risk
    """
    from .storage.database import init_database
    from .analysis.risk_benchmark import (
        build_implementation_guide,
        export_implementation_guide,
        export_implementation_guide_markdown,
    )

    engine = init_database()

    # Build project facts from flags
    project_facts: dict[str, str | None] = {
        "risk.technology.description": "yes" if has_technology_risk else None,
        "risk.technology.mitigants": "yes" if has_technology_mitigants else None,
        "risk.construction.description": "yes" if has_construction_risk else None,
        "risk.construction.mitigants": "yes" if has_construction_mitigants else None,
        "risk.market.description": "yes" if has_market_risk else None,
        "risk.market.mitigants": "yes" if has_market_mitigants else None,
        "risk.regulatory.description": "yes" if has_regulatory_risk else None,
        "risk.regulatory.mitigants": "yes" if has_regulatory_mitigants else None,
        "risk.feedstock.description": "yes" if has_feedstock_risk else None,
        "risk.feedstock.mitigants": "yes" if has_feedstock_mitigants else None,
    }

    project_financials: dict[str, float | None] = {
        "dscr": dscr,
        "revenue": revenue,
        "coverage_ratio": coverage_ratio,
    }

    click.echo(f"\n{'=' * 72}")
    click.echo(f"  RISK MITIGATION IMPLEMENTATION GUIDE: {project_name}")
    click.echo(f"{'=' * 72}")
    click.echo("\nBuilding implementation guide from EMMA corpus...")

    guide = build_implementation_guide(
        engine, project_facts, project_financials, project_name,
    )

    # Executive summary
    click.echo(f"\n{'-' * 72}")
    click.echo("  EXECUTIVE SUMMARY")
    click.echo(f"{'-' * 72}")
    click.echo("")
    _wrap_echo(guide.executive_summary, indent=2, width=70)
    click.echo("")
    click.echo(f"  Overall Risk Posture: {guide.overall_risk_posture.replace('_', ' ').upper()}")
    click.echo(f"  Critical Gaps: {guide.critical_gap_count}  |  Material Gaps: {guide.material_gap_count}")

    # Dimension summaries
    for idx, (path, dg) in enumerate(guide.dimension_guides.items(), 1):
        click.echo(f"\n{'-' * 72}")
        click.echo(f"  {idx}. {dg.display_name}")
        click.echo(f"{'-' * 72}")
        click.echo(
            f"  Corpus: {dg.corpus_evidence.n_risk_factors} factors across "
            f"{dg.corpus_evidence.n_issuances} issuances | "
            f"Mitigation: {dg.corpus_evidence.mitigation_rate * 100:.0f}%"
        )

        # Rating agency summary
        n_str = sum(len(v) for v in dg.agency_strengths_by_issuer.values())
        n_chl = sum(len(v) for v in dg.agency_challenges_by_issuer.values())
        if n_str or n_chl:
            click.echo(
                f"  Rating agencies: {n_str} strengths, {n_chl} challenges "
                f"across {len(set(dg.agency_strengths_by_issuer) | set(dg.agency_challenges_by_issuer))} issuers"
            )

        # Key recommendations (abbreviated)
        click.echo("  Recommendations:")
        for rec in dg.recommendations[:3]:
            click.echo(f"    [{rec.priority.upper()}] {rec.action}")

    # Financial targets
    fi = guide.financial_implementation
    if fi.dscr_target or fi.coverage_ratio_target:
        click.echo(f"\n{'-' * 72}")
        click.echo("  FINANCIAL TARGETS")
        click.echo(f"{'-' * 72}")
        if fi.dscr_target:
            click.echo(f"  DSCR: {fi.dscr_target}")
        if fi.coverage_ratio_target:
            click.echo(f"  Coverage: {fi.coverage_ratio_target}")
        if fi.recommended_pledge_type:
            click.echo(f"  Pledge: {fi.recommended_pledge_type}")

    # Priority sequence
    click.echo(f"\n{'-' * 72}")
    click.echo("  PRIORITY IMPLEMENTATION SEQUENCE")
    click.echo(f"{'-' * 72}")
    for act in guide.priority_sequence[:10]:
        dim = act.dimension.replace("risk.", "").replace(".", " ").title()
        if act.dimension == "financial":
            dim = "Financial"
        click.echo(f"  {act.action_id:2d}. [{act.priority.upper():8s}] [{dim:15s}] {act.action}")

    # Export
    click.echo(f"\n{'-' * 72}")
    if fmt in ("json", "both"):
        json_path = Path(output + ".json") if output else None
        exported_json = export_implementation_guide(guide, json_path)
        click.echo(f"  JSON: {exported_json}")
    if fmt in ("markdown", "both"):
        md_path = Path(output + ".md") if output else None
        exported_md = export_implementation_guide_markdown(guide, md_path)
        click.echo(f"  Markdown: {exported_md}")
    click.echo("")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
