"""
Advisory package endpoints for v2 bifurcated deliverables.

Per spec: Split handoff pack into:
- Internal Readiness Report (sponsor team use)
- External Advisory Package (municipal advisor consumption)
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from munipal.api.dependencies import AuthenticatedUserId, require_auth
from munipal.core.schemas.advisory_package import (
    DistributionValidation,
    ExternalAdvisoryPackageRead,
    ExternalAdvisoryPackageSummary,
    GenerateExternalPackageRequest,
    GenerateExternalPackageResponse,
    GenerateInternalReportRequest,
    GenerateInternalReportResponse,
    InternalReadinessReportRead,
    InternalReadinessReportSummary,
)
from munipal.db.session import get_async_session
from munipal.services.advisory_package_service import (
    ExternalPackageService,
    InternalReportService,
)
from munipal.services.audit_service import AuditService

router = APIRouter(dependencies=[Depends(require_auth)])


def get_internal_report_service(
    db: AsyncSession = Depends(get_async_session),
) -> InternalReportService:
    """Dependency to get InternalReportService instance."""
    return InternalReportService(db)


def get_external_package_service(
    db: AsyncSession = Depends(get_async_session),
) -> ExternalPackageService:
    """Dependency to get ExternalPackageService instance."""
    return ExternalPackageService(db)


# =============================================================================
# Internal Readiness Report Endpoints
# =============================================================================


@router.post("/internal/generate", response_model=GenerateInternalReportResponse)
async def generate_internal_report(
    request: GenerateInternalReportRequest,
    service: InternalReportService = Depends(get_internal_report_service),
) -> GenerateInternalReportResponse:
    """
    Generate an internal readiness report for a project.

    Per spec: Provides complete visibility into readiness state, gaps,
    information requests, evidence, and checklist progress.
    NOT for external consumption.
    """
    try:
        report = await service.generate_report(
            project_id=request.project_id,
            force_regenerate=request.force_regenerate,
        )
        return GenerateInternalReportResponse(
            report_id=UUID(report.id),
            status="completed",
            message=f"Report generated with score {report.overall_score:.1f}/10",
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/internal/", response_model=dict[str, Any])
async def list_internal_reports(
    project_id: UUID,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: InternalReportService = Depends(get_internal_report_service),
) -> dict[str, Any]:
    """List internal reports for a project."""
    reports, total = await service.list_reports(project_id, limit, offset)
    return {
        "reports": [
            InternalReadinessReportSummary(
                id=UUID(r.id),
                project_id=UUID(r.project_id),
                version=r.version,
                overall_score=r.overall_score,
                critical_gap_count=r.critical_gap_count,
                open_request_count=r.open_request_count or 0,
                is_complete=r.is_complete,
                created_at=r.created_at,
            )
            for r in reports
        ],
        "total": total,
    }


@router.get("/internal/{report_id}", response_model=InternalReadinessReportRead)
async def get_internal_report(
    report_id: UUID,
    service: InternalReportService = Depends(get_internal_report_service),
) -> InternalReadinessReportRead:
    """Get an internal readiness report by ID."""
    report = await service.get_report(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Internal report {report_id} not found",
        )
    return service.report_to_read_schema(report)


@router.get("/internal/project/{project_id}/latest", response_model=InternalReadinessReportRead | None)
async def get_latest_internal_report(
    project_id: UUID,
    service: InternalReportService = Depends(get_internal_report_service),
) -> InternalReadinessReportRead | None:
    """Get the latest internal report for a project."""
    report = await service.get_latest_report(project_id)
    if not report:
        return None
    return service.report_to_read_schema(report)


@router.get("/internal/{report_id}/export")
async def export_internal_report(
    report_id: UUID,
    user_id: AuthenticatedUserId,
    format: str = Query("md", pattern="^(md|pdf|html)$"),
    service: InternalReportService = Depends(get_internal_report_service),
) -> dict[str, Any]:
    """
    Export an internal report in the specified format.

    Supported formats: md (Markdown), pdf, html
    """
    report = await service.get_report(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Internal report {report_id} not found",
        )

    if format == "md":
        # Generate markdown content
        content = _generate_internal_report_markdown(report)
        AuditService.emit_event(
            actor_id=user_id,
            action="export_internal_report_markdown",
            target_type="internal_report",
            target_id=str(report_id),
            project_id=str(report.project_id),
        )
        return {
            "format": format,
            "filename": f"internal_report_v{report.version}.md",
            "content": content,
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"Export format '{format}' not yet implemented",
        )


# =============================================================================
# External Advisory Package Endpoints
# =============================================================================


@router.post("/external/generate", response_model=GenerateExternalPackageResponse)
async def generate_external_package(
    request: GenerateExternalPackageRequest,
    service: ExternalPackageService = Depends(get_external_package_service),
) -> GenerateExternalPackageResponse:
    """
    Generate an external advisory package for a project.

    Per spec: Professional deliverable for municipal advisors.
    Does NOT reveal internal gaps, conflicts, or operational status.
    """
    try:
        package = await service.generate_package(
            project_id=request.project_id,
            title=request.title,
            generated_for=request.generated_for,
            include_disclosure=request.include_disclosure,
            force_regenerate=request.force_regenerate,
        )
        return GenerateExternalPackageResponse(
            package_id=UUID(package.id),
            status="completed",
            message=f"Package generated. Ready for distribution: {package.ready_for_distribution}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/external/", response_model=dict[str, Any])
async def list_external_packages(
    project_id: UUID,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: ExternalPackageService = Depends(get_external_package_service),
) -> dict[str, Any]:
    """List external packages for a project."""
    packages, total = await service.list_packages(project_id, limit, offset)
    return {
        "packages": [
            ExternalAdvisoryPackageSummary(
                id=UUID(p.id),
                project_id=UUID(p.project_id),
                version=p.version,
                title=p.title,
                generated_for=p.generated_for,
                ready_for_distribution=p.ready_for_distribution,
                disclosure_completeness_score=p.disclosure_completeness_score,
                critical_tbd_count=p.critical_tbd_count or 0,
                is_complete=p.is_complete,
                created_at=p.created_at,
            )
            for p in packages
        ],
        "total": total,
    }


@router.get("/external/{package_id}", response_model=ExternalAdvisoryPackageRead)
async def get_external_package(
    package_id: UUID,
    service: ExternalPackageService = Depends(get_external_package_service),
) -> ExternalAdvisoryPackageRead:
    """Get an external advisory package by ID."""
    package = await service.get_package(package_id)
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"External package {package_id} not found",
        )
    return service.package_to_read_schema(package)


@router.get("/external/project/{project_id}/latest", response_model=ExternalAdvisoryPackageRead | None)
async def get_latest_external_package(
    project_id: UUID,
    service: ExternalPackageService = Depends(get_external_package_service),
) -> ExternalAdvisoryPackageRead | None:
    """Get the latest external package for a project."""
    package = await service.get_latest_package(project_id)
    if not package:
        return None
    return service.package_to_read_schema(package)


@router.get("/external/{package_id}/validate", response_model=DistributionValidation)
async def validate_external_package(
    package_id: UUID,
    service: ExternalPackageService = Depends(get_external_package_service),
) -> DistributionValidation:
    """
    Validate an external package for distribution readiness.

    Per spec: Package must pass quality gates before external distribution.
    """
    package = await service.get_package(package_id)
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"External package {package_id} not found",
        )

    return DistributionValidation(
        ready_for_distribution=package.ready_for_distribution,
        issues=package.distribution_issues,
        warnings=[],
        recommendations=[],
    )


@router.get("/external/{package_id}/export")
async def export_external_package(
    package_id: UUID,
    user_id: AuthenticatedUserId,
    format: str = Query("pdf", pattern="^(md|pdf|docx)$"),
    service: ExternalPackageService = Depends(get_external_package_service),
) -> dict[str, Any]:
    """
    Export an external advisory package in the specified format.

    Supported formats: pdf (primary), docx, md (Markdown)
    """
    package = await service.get_package(package_id)
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"External package {package_id} not found",
        )

    if format == "md":
        content = _generate_external_package_markdown(package)
        AuditService.emit_event(
            actor_id=user_id,
            action="export_external_package_markdown",
            target_type="external_package",
            target_id=str(package_id),
            project_id=str(package.project_id),
        )
        return {
            "format": format,
            "filename": f"advisory_package_v{package.version}.md",
            "content": content,
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"Export format '{format}' not yet implemented",
        )


# =============================================================================
# Helper Functions
# =============================================================================


def _generate_internal_report_markdown(report) -> str:
    """Generate markdown content for internal report."""
    lines = [
        "# Internal Readiness Report",
        f"\n**Version:** {report.version}",
        f"**Generated:** {report.generation_completed_at}",
        "\n---\n",
        "## Executive Summary",
        f"\n**Overall Score:** {report.overall_score:.1f}/10" if report.overall_score else "",
        f"**Critical Gaps:** {report.critical_gap_count}",
        f"**Open Information Requests:** {report.open_request_count}",
        f"**Approved Facts:** {report.facts_count}",
    ]

    # Executive Summary details
    if report.executive_summary:
        exec_summary = report.executive_summary
        if isinstance(exec_summary, dict):
            interpretation = exec_summary.get('score_interpretation', '')
            if interpretation:
                lines.append(f"\n**Status:** {interpretation}")

            # Critical Blockers
            blockers = exec_summary.get('critical_blockers', [])
            if blockers:
                lines.append("\n### Critical Blockers\n")
                for blocker in blockers:
                    lines.append(f"- **{blocker.get('title', 'Unknown')}**: {blocker.get('summary', '')}")
                    if blocker.get('consequences'):
                        lines.append(f"  - Impact: {blocker.get('consequences', '')}")

    # Gap Analysis
    if report.gap_analysis:
        gap = report.gap_analysis
        if isinstance(gap, dict):
            lines.append("\n---\n")
            lines.append("## Gap Analysis\n")
            summary = gap.get("summary", {})
            lines.append("| Severity | Count |")
            lines.append("|----------|-------|")
            lines.append(f"| Critical | {summary.get('critical_count', 0)} |")
            lines.append(f"| High | {summary.get('high_count', 0)} |")
            lines.append(f"| Medium | {summary.get('medium_count', 0)} |")
            lines.append(f"| **Risk Factors** | **{summary.get('risk_factor_gap_count', 0)}** |")

            # List critical gaps
            critical_gaps = gap.get('critical_gaps', [])
            if critical_gaps:
                lines.append("\n### Critical Gaps\n")
                for g in critical_gaps:
                    lines.append(f"- **{g.get('schema_path', '')}** ({g.get('dimension', '')})")
                    lines.append(f"  - {g.get('description', '')}")
                    if g.get('suggested_evidence'):
                        lines.append(f"  - *Suggested evidence:* {g.get('suggested_evidence', '')}")

            # List high gaps
            high_gaps = gap.get('high_gaps', [])
            if high_gaps:
                lines.append("\n### High Priority Gaps\n")
                for g in high_gaps[:10]:  # Limit to 10
                    lines.append(f"- **{g.get('schema_path', '')}**: {g.get('description', '')}")

            # Risk Factor Gaps (dedicated section)
            risk_factor_gaps = gap.get('risk_factor_gaps', [])
            if risk_factor_gaps:
                lines.append("\n### ⚠️ Risk Factor Documentation Gaps\n")
                lines.append("The following risk factors require documentation for disclosure compliance:\n")
                for g in risk_factor_gaps:
                    path = g.get('schema_path', '')
                    # Make the path more readable
                    readable_path = path.replace('risk.', '').replace('.', ' ').title()
                    lines.append(f"- **{readable_path}** (`{path}`)")
                    lines.append(f"  - {g.get('description', 'Documentation required')}")
                    if g.get('suggested_evidence'):
                        lines.append(f"  - *Suggested evidence:* {g.get('suggested_evidence', '')}")
                lines.append("\n> **Note:** These gaps block checklist item P4.3 (Risk Factor Documentation) and affect the Risk, Security & Permitting readiness dimension.")

            # Priority actions
            priority_actions = gap.get('priority_actions', [])
            if priority_actions:
                lines.append("\n### Recommended Priority Actions\n")
                for i, action in enumerate(priority_actions, 1):
                    lines.append(f"{i}. {action}")

    # Information Requests Section
    if report.information_requests_section:
        ir_section = report.information_requests_section
        if isinstance(ir_section, dict):
            lines.append("\n---\n")
            lines.append("## Information Requests\n")

            # Summary
            summary = ir_section.get('summary', {})
            if summary:
                lines.append("### Status Summary\n")
                lines.append("| Status | Count |")
                lines.append("|--------|-------|")
                for status, count in summary.items():
                    lines.append(f"| {status.replace('_', ' ').title()} | {count} |")

            # Risk Factor Requests (highlighted)
            full_requests = ir_section.get('full_requests', [])
            risk_requests = [r for r in full_requests if 'risk' in r.get('title', '').lower() or 'risk_factors' in r.get('request_code', '').lower()]
            if risk_requests:
                lines.append("\n### 📋 Risk Factor Information Requests\n")
                for req in risk_requests:
                    lines.append(f"- **{req.get('request_code', '')}**: {req.get('title', '')}")
                    lines.append(f"  - Priority: {req.get('priority', 'N/A').upper()}")
                    lines.append(f"  - Status: {req.get('status', 'N/A').replace('_', ' ').title()}")
                    lines.append(f"  - Owner: {req.get('owner', 'Unassigned')}")

            # Overdue requests
            overdue = ir_section.get('overdue_requests', [])
            if overdue:
                lines.append("\n### ⚠️ Overdue Requests\n")
                for req in overdue:
                    lines.append(f"- **{req.get('request_code', '')}**: {req.get('title', '')}")
                    lines.append(f"  - Target date: {req.get('target_date', 'N/A')}")
                    lines.append(f"  - Owner: {req.get('owner', 'Unassigned')}")

            # Requests by owner
            by_owner = ir_section.get('by_owner', [])
            if by_owner:
                lines.append("\n### Requests by Owner\n")
                for owner_data in by_owner:
                    owner = owner_data.get('owner', 'Unassigned')
                    open_count = owner_data.get('open_count', 0)
                    lines.append(f"\n#### {owner} ({open_count} open)\n")

                    requests = owner_data.get('requests', [])
                    for req in requests:
                        status = req.get('status', 'unknown').replace('_', ' ').title()
                        priority = req.get('priority', 'medium').upper()
                        lines.append(f"- [{status}] **{req.get('request_code', '')}**: {req.get('title', '')} [{priority}]")

            # Full request details
            full_requests = ir_section.get('full_requests', [])
            if full_requests:
                lines.append("\n### All Information Requests (Details)\n")
                for req in full_requests:
                    lines.append(f"\n#### {req.get('request_code', '')}: {req.get('title', '')}\n")
                    lines.append(f"- **Priority:** {req.get('priority', 'N/A').upper()}")
                    lines.append(f"- **Status:** {req.get('status', 'N/A').replace('_', ' ').title()}")
                    lines.append(f"- **Owner:** {req.get('owner', 'Unassigned')}")
                    if req.get('why_it_matters'):
                        lines.append(f"\n**Why it matters:** {req.get('why_it_matters', '')[:500]}...")
                    if req.get('specific_questions'):
                        lines.append("\n**Questions to answer:**")
                        for q in req.get('specific_questions', [])[:5]:
                            lines.append(f"- {q}")

    # Checklist Status
    if report.checklist_status:
        checklist = report.checklist_status
        if isinstance(checklist, dict):
            lines.append("\n---\n")
            lines.append("## Checklist Progress\n")

            phase_summary = checklist.get('phase_summary', [])
            if phase_summary:
                lines.append("| Phase | Ready | In Progress | Blocked | Not Started | Can Proceed |")
                lines.append("|-------|-------|-------------|---------|-------------|-------------|")
                for phase in phase_summary:
                    can_proceed = "✓" if phase.get('can_proceed') else "✗"
                    lines.append(
                        f"| {phase.get('phase', '')} | {phase.get('ready', 0)} | "
                        f"{phase.get('in_progress', 0)} | {phase.get('blocked', 0)} | "
                        f"{phase.get('not_started', 0)} | {can_proceed} |"
                    )

    # Evidence Index Summary
    if report.evidence_index:
        evidence = report.evidence_index
        if isinstance(evidence, dict):
            lines.append("\n---\n")
            lines.append("## Evidence Summary\n")
            summary = evidence.get('summary', {})
            lines.append(f"- **Total Facts:** {summary.get('total', 0)}")
            lines.append(f"- **Approved:** {summary.get('approved', 0)}")
            lines.append(f"- **Pending Review:** {summary.get('pending', 0)}")
            lines.append(f"- **Rejected:** {summary.get('rejected', 0)}")

            by_domain = evidence.get('by_domain', {})
            if by_domain:
                lines.append("\n### Facts by Domain\n")
                lines.append("| Domain | Count |")
                lines.append("|--------|-------|")
                for domain, facts in sorted(by_domain.items()):
                    lines.append(f"| {domain} | {len(facts)} |")

    # Footer
    lines.append("\n---\n")
    lines.append("*This report is for internal use only. Do not distribute externally.*")
    lines.append(f"\n*Generated by Muni-Pal BFMS v{report.bfms_version or '2.0'}*")

    return "\n".join(lines)


def _generate_external_package_markdown(package) -> str:
    """Generate markdown content for external advisory package."""
    lines = [
        "# Advisory Information Package",
        f"\n## {package.title}",
        f"\n**Prepared for:** {package.generated_for}",
        f"**Version:** {package.version}",
        f"**Generated:** {package.generation_completed_at}",
    ]

    # Cover page
    if package.cover_page:
        cover = package.cover_page
        if isinstance(cover, dict):
            lines.append("\n---\n")
            lines.append(f"**{cover.get('project_name', 'Project')}**")
            lines.append(f"\n{cover.get('structure_description', '')}")
            lines.append(f"\n*{cover.get('disclaimer_text', '')}*")

    # Executive Summary
    if package.executive_summary:
        exec_sum = package.executive_summary
        if isinstance(exec_sum, dict):
            lines.append("\n---\n## Executive Summary")
            lines.append(f"\n{exec_sum.get('transaction_overview', '')}")

            metrics = exec_sum.get("key_metrics", {})
            if metrics:
                lines.append("\n### Key Metrics\n")
                for metric, value in metrics.items():
                    lines.append(f"- **{metric}:** {value}")

    # Deal Overview
    if package.deal_overview:
        deal = package.deal_overview
        if isinstance(deal, dict):
            lines.append("\n---\n## Deal Overview")
            lines.append(f"\n{deal.get('project_summary', '')}")

    # Disclaimer
    if package.disclaimer:
        lines.append(f"\n---\n{package.disclaimer}")

    return "\n".join(lines)
