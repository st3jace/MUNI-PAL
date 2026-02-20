"""
Disclosure Synthesis Service for WP7.

Per spec: WP7 transforms the skeletal "Disclosure Outline" into a substantive
disclosure document by synthesizing extracted facts into coherent, disclosure-ready prose.

Core principles (NON-NEGOTIABLE):
- Every sentence must trace to ExtractedFact(s) or be a templated qualifier
- [TBD] markers are mandatory when evidence is insufficient
- No promotional language; no forward-looking claims without qualification
- Confidence thresholds must be respected
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from munipal.core.models.disclosure import (
    DisclosureDocument,
    DisclosureSection,
    TBDMarker,
)
from munipal.core.models.fact import ExtractedFact
from munipal.core.schemas.base import ReviewStatus
from munipal.core.schemas.disclosure import (
    DisclosureDocumentCreate,
    DisclosureDocumentRead,
    DisclosureSectionRead,
    DisclosureSectionPreview,
    TBDMarkerRead,
    TBDSeverity,
)
from munipal.services.playbook_data import (
    DISCLOSURE_SECTION_TEMPLATES,
    TBD_REASONS,
    SCHEMA_PATHS,
)

logger = logging.getLogger(__name__)


class DisclosureSynthesisService:
    """
    Service for synthesizing disclosure documents from extracted facts.

    Per WP7 spec: Template-driven prose synthesis, NOT generative AI.
    All content derives from templates + facts.
    """

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session

    # -------------------------------------------------------------------------
    # Document Management
    # -------------------------------------------------------------------------

    async def create_document(
        self, project_id: UUID, playbook_version: str | None = None
    ) -> DisclosureDocument:
        """Create a new disclosure document for a project."""
        # Check for existing document and get next version
        result = await self.session.execute(
            select(func.max(DisclosureDocument.version)).where(
                DisclosureDocument.project_id == str(project_id)
            )
        )
        max_version = result.scalar() or 0

        document = DisclosureDocument(
            id=str(uuid4()),
            project_id=str(project_id),
            version=max_version + 1,
            playbook_version=playbook_version,
            completeness_score=0.0,
            is_complete=False,
        )
        self.session.add(document)
        await self.session.flush()
        return document

    async def get_document(self, document_id: UUID) -> DisclosureDocument | None:
        """Get a disclosure document by ID with all relationships."""
        result = await self.session.execute(
            select(DisclosureDocument)
            .options(
                selectinload(DisclosureDocument.sections).selectinload(
                    DisclosureSection.tbd_markers
                ),
                selectinload(DisclosureDocument.tbd_items),
            )
            .where(DisclosureDocument.id == str(document_id))
        )
        return result.scalar_one_or_none()

    async def get_latest_document(self, project_id: UUID) -> DisclosureDocument | None:
        """Get the latest disclosure document for a project."""
        result = await self.session.execute(
            select(DisclosureDocument)
            .options(
                selectinload(DisclosureDocument.sections).selectinload(
                    DisclosureSection.tbd_markers
                ),
                selectinload(DisclosureDocument.tbd_items),
            )
            .where(DisclosureDocument.project_id == str(project_id))
            .order_by(DisclosureDocument.version.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_documents(
        self, project_id: UUID, limit: int = 10, offset: int = 0
    ) -> tuple[list[DisclosureDocument], int]:
        """List disclosure documents for a project."""
        count_result = await self.session.execute(
            select(func.count()).where(
                DisclosureDocument.project_id == str(project_id)
            )
        )
        total = count_result.scalar() or 0

        result = await self.session.execute(
            select(DisclosureDocument)
            .where(DisclosureDocument.project_id == str(project_id))
            .order_by(DisclosureDocument.version.desc())
            .limit(limit)
            .offset(offset)
        )
        documents = list(result.scalars().all())
        return documents, total

    # -------------------------------------------------------------------------
    # Section Synthesis
    # -------------------------------------------------------------------------

    async def generate_document(
        self,
        project_id: UUID,
        section_ids: list[str] | None = None,
        force_regenerate: bool = False,
    ) -> DisclosureDocument:
        """
        Generate a disclosure document from extracted facts.

        Args:
            project_id: Project UUID
            section_ids: Specific sections to generate (None = all)
            force_regenerate: Regenerate even if document exists

        Returns:
            Generated DisclosureDocument
        """
        logger.info(f"Generating disclosure document for project {project_id}")

        # Get or create document
        if not force_regenerate:
            document = await self.get_latest_document(project_id)
            if document and document.is_complete:
                return document

        # Create new document
        document = await self.create_document(project_id)
        document.generation_started_at = datetime.now(timezone.utc)

        # Get all approved facts for the project
        facts = await self._get_approved_facts(project_id)
        facts_by_path = self._index_facts_by_path(facts)

        # Get templates to process
        templates = DISCLOSURE_SECTION_TEMPLATES
        if section_ids:
            templates = [t for t in templates if t["section_id"] in section_ids]

        # Generate each section
        total_required = 0
        total_present = 0
        total_tbd = 0

        for template in templates:
            section, stats = await self._generate_section(
                document=document,
                template=template,
                facts_by_path=facts_by_path,
                parent_section_id=None,
            )
            if section:
                self.session.add(section)
                total_required += stats["required"]
                total_present += stats["present"]
                total_tbd += stats["tbd_count"]

        # Calculate completeness score
        if total_required > 0:
            document.completeness_score = total_present / total_required
        else:
            document.completeness_score = 1.0

        document.is_complete = True
        document.generation_completed_at = datetime.now(timezone.utc)

        await self.session.flush()
        logger.info(
            f"Generated disclosure document {document.id} with "
            f"completeness {document.completeness_score:.2%}"
        )

        return document

    async def _generate_section(
        self,
        document: DisclosureDocument,
        template: dict,
        facts_by_path: dict[str, ExtractedFact],
        parent_section_id: str | None,
    ) -> tuple[DisclosureSection | None, dict]:
        """
        Generate a single disclosure section from template.

        Returns:
            Tuple of (section, stats_dict)
        """
        section_id = template["section_id"]
        required_paths = template.get("required_fact_paths", [])
        optional_paths = template.get("optional_fact_paths", [])
        min_confidence = template.get("minimum_confidence", 0.70)
        conditional_on = template.get("conditional_on")

        # Check conditional rendering
        is_rendered = True
        if conditional_on:
            is_rendered = self._evaluate_condition(conditional_on, facts_by_path)
            if not is_rendered:
                return None, {"required": 0, "present": 0, "tbd_count": 0}

        # Calculate coverage
        present_required = [p for p in required_paths if p in facts_by_path]
        present_optional = [p for p in optional_paths if p in facts_by_path]
        all_present_paths = present_required + present_optional

        # Calculate confidence
        if all_present_paths:
            avg_confidence = sum(
                facts_by_path[p].confidence_score for p in all_present_paths
            ) / len(all_present_paths)
        else:
            avg_confidence = 0.0

        # Synthesize content
        content_md, tbd_markers, supporting_fact_ids = self._synthesize_content(
            template=template,
            facts_by_path=facts_by_path,
            document_id=document.id,
        )

        # Create section
        section = DisclosureSection(
            id=str(uuid4()),
            disclosure_document_id=document.id,
            section_id=section_id,
            title=template["title"],
            section_order=template.get("section_order", 0),
            parent_section_id=parent_section_id,
            content_md=content_md,
            confidence=avg_confidence,
            required_fact_count=len(required_paths),
            present_fact_count=len(present_required),
            tbd_count=len(tbd_markers),
            supporting_fact_ids=[str(fid) for fid in supporting_fact_ids],
            conditional_on=conditional_on,
            is_rendered=is_rendered,
        )

        # Add TBD markers
        for marker in tbd_markers:
            marker.section_id = section.id
            self.session.add(marker)

        # Process subsections
        subsection_stats = {"required": 0, "present": 0, "tbd_count": 0}
        for sub_template in template.get("subsection_templates", []):
            sub_section, sub_stats = await self._generate_section(
                document=document,
                template=sub_template,
                facts_by_path=facts_by_path,
                parent_section_id=section.id,
            )
            if sub_section:
                self.session.add(sub_section)
                subsection_stats["required"] += sub_stats["required"]
                subsection_stats["present"] += sub_stats["present"]
                subsection_stats["tbd_count"] += sub_stats["tbd_count"]

        stats = {
            "required": len(required_paths) + subsection_stats["required"],
            "present": len(present_required) + subsection_stats["present"],
            "tbd_count": len(tbd_markers) + subsection_stats["tbd_count"],
        }

        return section, stats

    def _synthesize_content(
        self,
        template: dict,
        facts_by_path: dict[str, ExtractedFact],
        document_id: str,
    ) -> tuple[str, list[TBDMarker], list[UUID]]:
        """
        Synthesize content from template and facts.

        Returns:
            Tuple of (content_md, tbd_markers, supporting_fact_ids)
        """
        template_content = template.get("template", "")
        tbd_markers = []
        supporting_fact_ids = []

        # Process fact slots: {schema_path:format:TBD: reason}
        def replace_fact_slot(match):
            slot = match.group(1)

            # Skip conditional markers - they'll be processed later by _process_conditionals
            if (slot.startswith("IF ") or slot.startswith("ELSEIF ") or
                slot == "ELSE" or slot == "ENDIF"):
                return match.group(0)  # Keep as-is for later processing

            parts = slot.split(":")
            schema_path = parts[0]

            # Get format and TBD options
            format_type = None
            tbd_reason = None
            for part in parts[1:]:
                if part == "formatted":
                    format_type = "formatted"
                elif part == "percent":
                    format_type = "percent"
                elif part.startswith("TBD"):
                    if len(part) > 3:
                        tbd_reason = part[4:].strip()
                    else:
                        tbd_reason = TBD_REASONS.get(
                            schema_path, f"Information for {schema_path} not yet available"
                        )

            # Look up fact
            if schema_path in facts_by_path:
                fact = facts_by_path[schema_path]
                supporting_fact_ids.append(UUID(fact.id))
                value = fact.value
                if isinstance(value, dict):
                    value = value.get("value", str(value))

                # Format value
                if format_type == "formatted":
                    try:
                        value = f"{float(value):,.2f}"
                    except (ValueError, TypeError):
                        pass
                elif format_type == "percent":
                    try:
                        value = f"{float(value):.1f}"
                    except (ValueError, TypeError):
                        pass

                return str(value)
            else:
                # Insert TBD marker
                if tbd_reason:
                    marker = TBDMarker(
                        id=str(uuid4()),
                        disclosure_document_id=document_id,
                        location=schema_path,
                        missing_fact_paths=[schema_path],
                        reason=tbd_reason,
                        severity=self._get_tbd_severity(schema_path),
                    )
                    tbd_markers.append(marker)
                    return f"[TBD: {tbd_reason}]"
                else:
                    return f"[{schema_path}]"

        # Replace fact slots
        content = re.sub(r"\{([^}]+)\}", replace_fact_slot, template_content)

        # Process conditional blocks: {IF condition}...{ENDIF}
        content = self._process_conditionals(content, facts_by_path)

        return content, tbd_markers, supporting_fact_ids

    def _process_conditionals(
        self, content: str, facts_by_path: dict[str, ExtractedFact]
    ) -> str:
        """Process conditional blocks in content."""
        # Process IF/ELSEIF/ELSE/ENDIF chains
        # We need to handle nested conditions and multiple branches

        def process_conditional_chain(match):
            """Process a complete IF/ELSEIF/ELSE/ENDIF chain."""
            full_block = match.group(0)

            # Parse the chain into branches
            # Pattern to extract the initial IF
            if_pattern = r"\{IF\s+([^}]+)\}"
            if_match = re.match(if_pattern, full_block)
            if not if_match:
                return full_block

            current_pos = if_match.end()
            branches = []

            # Extract the first condition
            first_condition = if_match.group(1).strip()

            # Find content until next ELSEIF, ELSE, or ENDIF
            remaining = full_block[current_pos:]

            # Split by ELSEIF, ELSE, ENDIF markers
            # This pattern captures the content between markers
            branch_pattern = r"(.*?)(?:\{ELSEIF\s+([^}]+)\}|\{ELSE\}|\{ENDIF\})"

            conditions = [first_condition]
            contents = []
            else_content = ""

            while remaining:
                branch_match = re.match(branch_pattern, remaining, flags=re.DOTALL)
                if not branch_match:
                    break

                content_part = branch_match.group(1)
                contents.append(content_part)

                # Check what we matched
                match_end = branch_match.end()
                matched_text = remaining[branch_match.start():match_end]

                if "{ELSEIF" in matched_text:
                    elseif_cond = branch_match.group(2)
                    if elseif_cond:
                        conditions.append(elseif_cond.strip())
                    remaining = remaining[match_end:]
                elif "{ELSE}" in matched_text:
                    # Find content until ENDIF
                    remaining = remaining[match_end:]
                    endif_match = re.search(r"(.*?)\{ENDIF\}", remaining, flags=re.DOTALL)
                    if endif_match:
                        else_content = endif_match.group(1)
                    break
                elif "{ENDIF}" in matched_text:
                    break
                else:
                    remaining = remaining[match_end:]

            # Evaluate conditions in order
            for i, condition in enumerate(conditions):
                if self._evaluate_condition(condition, facts_by_path):
                    if i < len(contents):
                        return contents[i]
                    return ""

            # If no condition matched, return else content
            return else_content

        # First, process simple IF/ELSE/ENDIF without ELSEIF
        # Pattern for IF with optional ELSE
        simple_pattern = r"\{IF\s+([^}]+)\}((?:(?!\{IF\s)(?!\{ELSEIF\s)(?!\{ELSE\})(?!\{ENDIF\}).)*?)(?:\{ELSE\}((?:(?!\{IF\s)(?!\{ELSEIF\s)(?!\{ELSE\})(?!\{ENDIF\}).)*?))?\{ENDIF\}"

        def process_simple_if(match):
            condition = match.group(1).strip()
            if_content = match.group(2) or ""
            else_content = match.group(3) or ""

            if self._evaluate_condition(condition, facts_by_path):
                return if_content
            else:
                return else_content

        # Iteratively process until no more matches (handles nested structures)
        max_iterations = 10
        for _ in range(max_iterations):
            new_content = re.sub(simple_pattern, process_simple_if, content, flags=re.DOTALL)
            if new_content == content:
                break
            content = new_content

        # Process IF/ELSEIF/ELSE/ENDIF chains
        # This more complex pattern handles ELSEIF branches
        elseif_pattern = r"\{IF\s+([^}]+)\}(.*?)(?:\{ELSEIF\s+[^}]+\}.*?)*(?:\{ELSE\}(.*?))?\{ENDIF\}"

        def process_elseif_chain(match):
            full_match = match.group(0)
            first_condition = match.group(1).strip()

            # Extract all conditions and their content
            parts = re.split(r"\{ELSEIF\s+([^}]+)\}|\{ELSE\}|\{ENDIF\}", full_match)

            # First part after {IF condition} is the if-content
            # Find content after the opening {IF...}
            first_content_match = re.match(r"\{IF\s+[^}]+\}(.*)", full_match, flags=re.DOTALL)
            if not first_content_match:
                return ""

            remaining = first_content_match.group(1)

            # Check first condition
            if self._evaluate_condition(first_condition, facts_by_path):
                # Return content up to first ELSEIF, ELSE, or ENDIF
                content_match = re.match(r"(.*?)(?=\{ELSEIF|\{ELSE\}|\{ENDIF\})", remaining, flags=re.DOTALL)
                if content_match:
                    return content_match.group(1)
                return ""

            # Check ELSEIF conditions
            elseif_matches = list(re.finditer(r"\{ELSEIF\s+([^}]+)\}(.*?)(?=\{ELSEIF|\{ELSE\}|\{ENDIF\})", full_match, flags=re.DOTALL))
            for elseif_match in elseif_matches:
                elseif_cond = elseif_match.group(1).strip()
                elseif_content = elseif_match.group(2)
                if self._evaluate_condition(elseif_cond, facts_by_path):
                    return elseif_content

            # Check for ELSE content
            else_match = re.search(r"\{ELSE\}(.*?)\{ENDIF\}", full_match, flags=re.DOTALL)
            if else_match:
                return else_match.group(1)

            return ""

        content = re.sub(elseif_pattern, process_elseif_chain, content, flags=re.DOTALL)

        # Clean up extra whitespace
        content = re.sub(r"\n{3,}", "\n\n", content)

        # Remove any remaining unprocessed template tags (failsafe)
        # Handle both {IF ...} curly brace syntax and [IF ...] square bracket syntax
        # (Square brackets can appear if the curly brace version wasn't caught before fact replacement)
        content = re.sub(r"[\[{]IF\s+[^\]}]+[\]}]", "", content, flags=re.IGNORECASE)
        content = re.sub(r"[\[{]ELSEIF\s+[^\]}]+[\]}]", "", content, flags=re.IGNORECASE)
        content = re.sub(r"[\[{]ELSE[\]}]", "", content, flags=re.IGNORECASE)
        content = re.sub(r"[\[{]ENDIF[\]}]", "", content, flags=re.IGNORECASE)

        # Also clean up any malformed tags that might have unbalanced braces/brackets
        content = re.sub(r"[\[{]IF[^\]}]*$", "", content, flags=re.MULTILINE | re.IGNORECASE)
        content = re.sub(r"^[^\[{]*ENDIF[\]}]", "", content, flags=re.MULTILINE | re.IGNORECASE)

        # Remove empty lines that may have been left behind
        content = re.sub(r"^\s*$\n", "", content, flags=re.MULTILINE)
        content = re.sub(r"\n{3,}", "\n\n", content)

        return content

    def _evaluate_condition(
        self, condition: str, facts_by_path: dict[str, ExtractedFact]
    ) -> bool:
        """Evaluate a condition expression."""
        # Support: path == 'value', path != 'value', path (existence check)
        # Also supports OR and AND operators
        condition = condition.strip()

        # Handle OR operator (split and evaluate each part)
        if " OR " in condition:
            parts = condition.split(" OR ")
            return any(self._evaluate_condition(part.strip(), facts_by_path) for part in parts)

        # Handle AND operator (split and evaluate each part)
        if " AND " in condition:
            parts = condition.split(" AND ")
            return all(self._evaluate_condition(part.strip(), facts_by_path) for part in parts)

        # Equality check
        if "==" in condition:
            parts = condition.split("==", 1)  # Split only on first ==
            path = parts[0].strip()
            expected = parts[1].strip().strip("'\"")

            if path in facts_by_path:
                fact = facts_by_path[path]
                value = fact.value
                if isinstance(value, dict):
                    value = value.get("value", str(value))
                return str(value).lower() == expected.lower()
            return False

        # Inequality check
        if "!=" in condition:
            parts = condition.split("!=", 1)  # Split only on first !=
            path = parts[0].strip()
            expected = parts[1].strip().strip("'\"")

            if path in facts_by_path:
                fact = facts_by_path[path]
                value = fact.value
                if isinstance(value, dict):
                    value = value.get("value", str(value))
                return str(value).lower() != expected.lower()
            return True

        # Existence check
        return condition in facts_by_path

    def _get_tbd_severity(self, schema_path: str) -> str:
        """Get TBD severity based on schema path criticality."""
        for path_def in SCHEMA_PATHS:
            if path_def["path"] == schema_path:
                criticality = path_def.get("criticality", "secondary")
                if criticality == "critical":
                    return TBDSeverity.CRITICAL.value
                elif criticality == "material":
                    return TBDSeverity.HIGH.value
                else:
                    return TBDSeverity.MEDIUM.value
        return TBDSeverity.MEDIUM.value

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    async def _get_approved_facts(self, project_id: UUID) -> list[ExtractedFact]:
        """Get all approved facts for a project."""
        result = await self.session.execute(
            select(ExtractedFact).where(
                ExtractedFact.project_id == str(project_id),
                ExtractedFact.review_status == ReviewStatus.APPROVED.value,
                ExtractedFact.lifecycle_state != "archived",
            )
        )
        return list(result.scalars().all())

    def _index_facts_by_path(
        self, facts: list[ExtractedFact]
    ) -> dict[str, ExtractedFact]:
        """Index facts by schema path, preferring highest confidence."""
        facts_by_path = {}
        for fact in facts:
            path = fact.schema_path
            if path not in facts_by_path:
                facts_by_path[path] = fact
            elif fact.confidence_score > facts_by_path[path].confidence_score:
                facts_by_path[path] = fact
        return facts_by_path

    # -------------------------------------------------------------------------
    # Preview Methods
    # -------------------------------------------------------------------------

    async def get_section_preview(
        self, project_id: UUID, section_id: str
    ) -> DisclosureSectionPreview | None:
        """Get a preview of what a section would contain."""
        # Find template
        template = None
        for t in DISCLOSURE_SECTION_TEMPLATES:
            if t["section_id"] == section_id:
                template = t
                break
            for sub in t.get("subsection_templates", []):
                if sub["section_id"] == section_id:
                    template = sub
                    break

        if not template:
            return None

        # Get facts
        facts = await self._get_approved_facts(project_id)
        facts_by_path = self._index_facts_by_path(facts)

        required_paths = template.get("required_fact_paths", [])
        optional_paths = template.get("optional_fact_paths", [])
        all_paths = required_paths + optional_paths

        available_paths = [p for p in all_paths if p in facts_by_path]
        missing_paths = [p for p in required_paths if p not in facts_by_path]

        # Calculate estimated confidence
        if available_paths:
            avg_confidence = sum(
                facts_by_path[p].confidence_score for p in available_paths
            ) / len(available_paths)
        else:
            avg_confidence = 0.0

        can_generate = len(missing_paths) == 0 or len(available_paths) > 0

        return DisclosureSectionPreview(
            section_id=section_id,
            title=template["title"],
            can_generate=can_generate,
            required_facts=required_paths,
            available_facts=available_paths,
            missing_facts=missing_paths,
            estimated_confidence=avg_confidence,
        )

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def document_to_read_schema(
        self, document: DisclosureDocument
    ) -> DisclosureDocumentRead:
        """Convert document model to read schema."""
        # Build TBD summary
        tbd_summary = {}
        for severity in TBDSeverity:
            tbd_summary[severity] = sum(
                1 for m in document.tbd_items if m.severity == severity.value
            )

        return DisclosureDocumentRead(
            id=UUID(document.id),
            project_id=UUID(document.project_id),
            version=document.version,
            playbook_version=document.playbook_version,
            completeness_score=document.completeness_score,
            is_complete=document.is_complete,
            generation_started_at=document.generation_started_at,
            generation_completed_at=document.generation_completed_at,
            sections=[self.section_to_read_schema(s) for s in document.sections],
            tbd_items=[self.tbd_to_read_schema(m) for m in document.tbd_items],
            tbd_summary=tbd_summary,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    def section_to_read_schema(
        self, section: DisclosureSection
    ) -> DisclosureSectionRead:
        """Convert section model to read schema."""
        return DisclosureSectionRead(
            id=UUID(section.id),
            disclosure_document_id=UUID(section.disclosure_document_id),
            section_id=section.section_id,
            title=section.title,
            section_order=section.section_order,
            parent_section_id=UUID(section.parent_section_id) if section.parent_section_id else None,
            content_md=section.content_md,
            confidence=section.confidence,
            required_fact_count=section.required_fact_count,
            present_fact_count=section.present_fact_count,
            tbd_count=section.tbd_count,
            supporting_fact_ids=[UUID(fid) for fid in section.supporting_fact_ids],
            conditional_on=section.conditional_on,
            is_rendered=section.is_rendered,
            tbd_markers=[self.tbd_to_read_schema(m) for m in section.tbd_markers],
            subsections=[],  # Would need recursive loading
            created_at=section.created_at,
            updated_at=section.updated_at,
        )

    def tbd_to_read_schema(self, marker: TBDMarker) -> TBDMarkerRead:
        """Convert TBD marker model to read schema."""
        return TBDMarkerRead(
            id=UUID(marker.id),
            disclosure_document_id=UUID(marker.disclosure_document_id),
            section_id=UUID(marker.section_id) if marker.section_id else None,
            location=marker.location,
            missing_fact_paths=marker.missing_fact_paths,
            reason=marker.reason,
            severity=TBDSeverity(marker.severity),
            is_resolved=marker.is_resolved,
            resolved_at=marker.resolved_at,
            resolved_by_fact_id=UUID(marker.resolved_by_fact_id) if marker.resolved_by_fact_id else None,
            created_at=marker.created_at,
            updated_at=marker.updated_at,
        )
