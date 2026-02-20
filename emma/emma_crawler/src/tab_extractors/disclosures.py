from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from urllib.parse import urljoin

from .common import click_tab
from ..utils import logger


async def extract_disclosures(page: Any, pdf_dir: Path, cusip: str) -> list[dict[str, Any]]:
    disclosures: list[dict[str, Any]] = []
    pdf_dir.mkdir(parents=True, exist_ok=True)
    try:
        clicked = await click_tab(page, "Disclosure")
        if not clicked:
            return []
        rows: list[dict[str, str]] = []
        seen_urls: dict[str, int] = {}  # full_url -> index in rows list
        links = page.locator("a")
        link_count = await links.count()
        for i in range(link_count):
            link = links.nth(i)
            text = (await link.inner_text() or "").strip()
            href = await link.get_attribute("href")
            if not href:
                continue
            full_url = urljoin(page.url, href)
            lower_text = text.lower()
            # Keep only security disclosure documents (EMMA PDF docs + continuing-disclosure detail links).
            is_doc_pdf = re.search(r"/P\d+(?:-[A-Z0-9]+)*\.pdf$", full_url, flags=re.IGNORECASE) is not None
            is_continuing_detail = "/MarketActivity/ContinuingDisclosureDetails/" in full_url
            if is_doc_pdf or is_continuing_detail:
                row_loc = link.locator("xpath=ancestor::tr[1]")
                row_text = (await row_loc.inner_text()) if await row_loc.count() else text
                date_match = re.search(r"\b\d{1,2}/\d{1,2}/\d{4}\b", row_text)
                filing_date = date_match.group(0) if date_match else ""
                # Deduplicate by URL; prefer the entry with a filing date.
                if full_url in seen_urls:
                    existing_idx = seen_urls[full_url]
                    if not rows[existing_idx]["filing_date"] and filing_date:
                        rows[existing_idx]["filing_date"] = filing_date
                    continue
                seen_urls[full_url] = len(rows)
                rows.append(
                    {
                        "document_type": "Official Statement" if "official statement" in lower_text else "Disclosure",
                        "doc_type": text or "Disclosure",
                        "_href": href,
                        "filing_date": filing_date,
                    }
                )
        for idx, row in enumerate(rows, start=1):
            href = row.get("_href", "")
            pdf_url = urljoin(page.url, href) if href else ""
            local_pdf_path = ""
            download_success = False
            # Some EMMA links are not direct .pdf; keep URL when available and download only direct PDFs.
            if pdf_url.lower().endswith(".pdf"):
                try:
                    response = await page.context.request.get(pdf_url, timeout=60000)
                    if response.ok:
                        raw = await response.body()
                        doc_label = re.sub(r"[^A-Za-z0-9]+", "_", (row.get("doc_type") or "disclosure")).strip("_")[:50]
                        filename = f"{cusip}_{idx:04d}_{doc_label}.pdf"
                        output_path = pdf_dir / filename
                        output_path.write_bytes(raw)
                        local_pdf_path = str(output_path)
                        download_success = True
                except Exception as download_exc:
                    logger.warning("Disclosure PDF download failed for %s: %s", pdf_url, download_exc)
            disclosures.append(
                {
                    "doc_type": row.get("document_type") or row.get("doc_type") or row.get("col_1", ""),
                    "filing_date": row.get("filing_date") or row.get("date") or row.get("col_2", ""),
                    "pdf_url": pdf_url,
                    "local_pdf_path": local_pdf_path,
                    "download_success": download_success,
                }
            )
    except Exception as exc:
        logger.warning("Disclosures tab click failed for %s: %s", cusip, exc)
    return disclosures
