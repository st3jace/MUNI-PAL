"""
UCS CAB+SLB Playbook Configuration Data.

This module contains the structured configuration extracted from the
UCS Bond Intelligence Configuration Playbook v0.2.

Per spec: This is the source of truth for schema paths, extractors,
checklist items, and readiness scoring rules.
"""

# Schema path definitions with criticality tiers
SCHEMA_PATHS = [
    # Project Foundation
    {"path": "project.canonicaldescription", "display_name": "Project Description", "value_type": "string", "criticality": "material", "min_confidence": 0.70},
    {"path": "project.location.jurisdiction", "display_name": "Jurisdiction", "value_type": "string", "criticality": "secondary", "min_confidence": 0.70},
    {"path": "project.location.sitecontrol", "display_name": "Site Control", "value_type": "enum", "criticality": "material", "min_confidence": 0.80, "allowed_values": ["purchase", "lease", "option", "loi"]},
    {"path": "project.location.coordinates", "display_name": "Coordinates", "value_type": "string", "criticality": "secondary", "min_confidence": 0.65},
    {"path": "project.operatingstatus", "display_name": "Operating Status", "value_type": "enum", "criticality": "material", "min_confidence": 0.75, "allowed_values": ["planned", "under-construction", "operational"]},
    {"path": "project.designlife", "display_name": "Design Life", "value_type": "number", "unit": "years", "criticality": "secondary", "min_confidence": 0.70},

    # Parties & Governance
    {"path": "parties.issuer.name", "display_name": "Issuer Name", "value_type": "string", "criticality": "material", "min_confidence": 0.80},
    {"path": "parties.issuer.jurisdiction", "display_name": "Issuer Jurisdiction", "value_type": "string", "criticality": "material", "min_confidence": 0.80},
    {"path": "parties.borrower.name", "display_name": "Borrower Name", "value_type": "string", "criticality": "material", "min_confidence": 0.80},
    {"path": "parties.operator.name", "display_name": "Operator Name", "value_type": "string", "criticality": "material", "min_confidence": 0.80},
    {"path": "parties.sponsor.name", "display_name": "Sponsor Name", "value_type": "string", "criticality": "secondary", "min_confidence": 0.75},
    {"path": "governance.inducement", "display_name": "Inducement Status", "value_type": "enum", "criticality": "critical", "min_confidence": 0.90, "allowed_values": ["draft", "proposed", "adopted"]},
    {"path": "governance.publicpurpose", "display_name": "Public Purpose", "value_type": "string", "criticality": "material", "min_confidence": 0.70},

    # Technology & Operations
    {"path": "technology.type", "display_name": "Technology Type", "value_type": "enum", "criticality": "material", "min_confidence": 0.85, "allowed_values": ["ucs", "thermal", "biological", "chemical"]},
    {"path": "technology.throughput.nameplate", "display_name": "Nameplate Throughput", "value_type": "number", "unit": "tons/day", "criticality": "critical", "min_confidence": 0.85},
    {"path": "technology.throughput.annual", "display_name": "Annual Throughput", "value_type": "number", "unit": "tons/year", "criticality": "material", "min_confidence": 0.80},
    {"path": "technology.lifespan", "display_name": "Technology Lifespan", "value_type": "number", "unit": "years", "criticality": "secondary", "min_confidence": 0.75},
    {"path": "technology.warranty.supplier", "display_name": "Warranty Supplier", "value_type": "string", "criticality": "secondary", "min_confidence": 0.70},
    {"path": "technology.warranty.duration", "display_name": "Warranty Duration", "value_type": "number", "unit": "years", "criticality": "material", "min_confidence": 0.80},
    {"path": "operations.staffing.direct", "display_name": "Direct Staffing", "value_type": "number", "unit": "headcount", "criticality": "material", "min_confidence": 0.75},

    # Feedstock & Supply
    {"path": "feedstock.type", "display_name": "Feedstock Type", "value_type": "enum", "criticality": "material", "min_confidence": 0.80, "allowed_values": ["forestry", "msw", "agricultural", "mixed"]},
    {"path": "feedstock.volume.annual", "display_name": "Annual Feedstock Volume", "value_type": "number", "unit": "tons", "criticality": "material", "min_confidence": 0.80},
    {"path": "feedstock.supply.mechanism", "display_name": "Supply Mechanism", "value_type": "enum", "criticality": "critical", "min_confidence": 0.85, "allowed_values": ["contract", "mou", "letter-of-intent", "assessment"]},
    {"path": "feedstock.supply.confidence", "display_name": "Supply Confidence", "value_type": "enum", "criticality": "critical", "min_confidence": 0.85, "allowed_values": ["preliminary", "advanced", "secured"]},

    # Revenue Model
    {"path": "revenue.commodities.list", "display_name": "Commodity Revenue List", "value_type": "array", "criticality": "critical", "min_confidence": 0.85},
    {"path": "revenue.commodities.renewable-diesel", "display_name": "Renewable Diesel Revenue", "value_type": "currency", "unit": "USD/year", "criticality": "material", "min_confidence": 0.80},
    {"path": "revenue.commodities.biochar", "display_name": "Biochar Revenue", "value_type": "currency", "unit": "USD/year", "criticality": "secondary", "min_confidence": 0.75},
    {"path": "revenue.offtake.status", "display_name": "Offtake Status", "value_type": "enum", "criticality": "critical", "min_confidence": 0.90, "allowed_values": ["executed", "advanced-mou", "letter-of-intent", "negotiating"]},
    {"path": "revenue.gross.annual", "display_name": "Gross Annual Revenue", "value_type": "currency", "unit": "USD", "criticality": "critical", "min_confidence": 0.85},

    # Operating Expenses
    {"path": "opex.total.annual", "display_name": "Total Annual OpEx", "value_type": "currency", "unit": "USD", "criticality": "material", "min_confidence": 0.80},
    {"path": "opex.margin", "display_name": "Operating Margin", "value_type": "percentage", "criticality": "material", "min_confidence": 0.80},
    {"path": "ebitda", "display_name": "EBITDA", "value_type": "currency", "unit": "USD", "criticality": "critical", "min_confidence": 0.85},

    # Capital Structure
    {"path": "capital.project-cost", "display_name": "Total Project Cost", "value_type": "currency", "unit": "USD", "criticality": "critical", "min_confidence": 0.90},
    {"path": "capital.equipment-cost", "display_name": "Equipment Cost", "value_type": "currency", "unit": "USD", "criticality": "material", "min_confidence": 0.85},
    {"path": "capital.equity-contribution", "display_name": "Equity Contribution", "value_type": "currency", "unit": "USD", "criticality": "critical", "min_confidence": 0.90},
    {"path": "capital.equity-percent", "display_name": "Equity Percentage", "value_type": "percentage", "criticality": "critical", "min_confidence": 0.90},

    # CAB Terms - CRITICAL
    {"path": "cab.enabled", "display_name": "CAB Enabled", "value_type": "boolean", "criticality": "critical", "min_confidence": 0.95},
    {"path": "cab.originalprincipial", "display_name": "Original Principal", "value_type": "currency", "unit": "USD", "criticality": "critical", "min_confidence": 0.90},
    {"path": "cab.accretionrate", "display_name": "Accretion Rate", "value_type": "percentage", "criticality": "critical", "min_confidence": 0.90},
    {"path": "cab.accretion.period.years", "display_name": "Accretion Period", "value_type": "number", "unit": "years", "criticality": "critical", "min_confidence": 0.90},
    {"path": "cab.finalmaturitydate", "display_name": "Final Maturity Date", "value_type": "date", "criticality": "critical", "min_confidence": 0.90},
    {"path": "cab.turbo.enabled", "display_name": "Turbo Redemption Enabled", "value_type": "boolean", "criticality": "material", "min_confidence": 0.85},
    {"path": "cab.conversion.rate", "display_name": "Conversion Rate", "value_type": "percentage", "criticality": "critical", "min_confidence": 0.90},

    # Financial Model & DSCR - CRITICAL
    {"path": "finmodel.inputs.revenue.annual", "display_name": "Projected Annual Revenue", "value_type": "currency", "unit": "USD", "criticality": "critical", "min_confidence": 0.90},
    {"path": "finmodel.inputs.revenue.ramp", "display_name": "Revenue Ramp Schedule", "value_type": "object", "criticality": "critical", "min_confidence": 0.85},
    {"path": "finmodel.inputs.dscr.minimum", "display_name": "Minimum DSCR Covenant", "value_type": "number", "criticality": "critical", "min_confidence": 0.95},
    {"path": "finmodel.outputs.dscrbase", "display_name": "Base DSCR", "value_type": "number", "criticality": "critical", "min_confidence": 0.90},
    {"path": "finmodel.outputs.dscrstress", "display_name": "Stress DSCR", "value_type": "number", "criticality": "critical", "min_confidence": 0.85},

    # SLB KPIs - CRITICAL
    {"path": "slb.enabled", "display_name": "SLB Enabled", "value_type": "boolean", "criticality": "critical", "min_confidence": 0.95},
    {"path": "slb.kpis.shortlist", "display_name": "Selected KPIs", "value_type": "array", "criticality": "critical", "min_confidence": 0.90},
    {"path": "slb.kpi.1.name", "display_name": "KPI 1 Name", "value_type": "string", "criticality": "critical", "min_confidence": 0.90},
    {"path": "slb.kpi.1.baseline.value", "display_name": "KPI 1 Baseline", "value_type": "number", "criticality": "critical", "min_confidence": 0.90},
    {"path": "slb.kpi.1.baseline.methodology", "display_name": "KPI 1 Baseline Methodology", "value_type": "string", "criticality": "critical", "min_confidence": 0.85},
    {"path": "slb.kpi.1.verification.method", "display_name": "KPI 1 Verification Method", "value_type": "string", "criticality": "critical", "min_confidence": 0.85},
    {"path": "slb.penalty.stepup.magnitude", "display_name": "Step-Up Penalty", "value_type": "number", "unit": "bps", "criticality": "critical", "min_confidence": 0.90},

    # Security & Collateral
    {"path": "security.realproperty", "display_name": "Real Property Security", "value_type": "string", "criticality": "material", "min_confidence": 0.80},
    {"path": "security.equipment.schedule", "display_name": "Equipment Security Schedule", "value_type": "string", "criticality": "material", "min_confidence": 0.80},
    {"path": "security.revenue.pledge", "display_name": "Revenue Pledge", "value_type": "enum", "criticality": "critical", "min_confidence": 0.90, "allowed_values": ["gross", "net"]},

    # Permitting
    {"path": "permitting.air-quality.status", "display_name": "Air Quality Permit Status", "value_type": "enum", "criticality": "material", "min_confidence": 0.85, "allowed_values": ["not-started", "in-progress", "pending-approval", "approved"]},
    {"path": "permitting.solidwaste.status", "display_name": "Solid Waste Permit Status", "value_type": "enum", "criticality": "material", "min_confidence": 0.85, "allowed_values": ["not-started", "in-progress", "pending-approval", "approved"]},

    # Regulatory
    {"path": "regulatory.tax-status", "display_name": "Tax Status", "value_type": "enum", "criticality": "critical", "min_confidence": 0.90, "allowed_values": ["tax-exempt-idb", "tax-exempt-solidwaste", "taxable"]},
]

# Extractor definitions
EXTRACTORS = [
    {
        "extractor_id": "ProjectDescriptionExtractor",
        "name": "Project Description Extractor",
        "description": "Extracts project overview, location, and technology details",
        "target_schema_paths": [
            "project.canonicaldescription",
            "project.location.jurisdiction",
            "project.location.coordinates",
            "project.operatingstatus",
            "technology.type",
            "technology.throughput.nameplate",
            "technology.throughput.annual",
        ],
        "system_prompt": """You are an expert municipal bond analyst extracting structured information from project documents.
Extract ONLY information that is explicitly stated in the document. Never infer or estimate missing values.
For each extracted fact, provide the exact quote from the document as evidence.""",
        "extraction_prompt_template": """From the following document content, extract these specific facts:
1. Canonical project description (1-2 sentences describing the system, location, and purpose)
2. Jurisdiction (state/county where project is located)
3. GPS coordinates (if stated)
4. Technology throughput nameplate (e.g., "100 tons/day")
5. Annual throughput (nameplate × 351 operating days, or as stated)
6. Current operating status (planned, under construction, or operational)

IMPORTANT: Only extract if explicitly stated. Return null for missing values.

Document content:
{content}

Return a JSON object with the extracted facts and confidence scores.""",
        "requires_full_document": False,
        "idempotent": True,
    },
    {
        "extractor_id": "PartiesExtractor",
        "name": "Parties & Governance Extractor",
        "description": "Extracts information about project parties and governance structure",
        "target_schema_paths": [
            "parties.issuer.name",
            "parties.issuer.jurisdiction",
            "parties.borrower.name",
            "parties.operator.name",
            "parties.sponsor.name",
            "governance.inducement",
            "governance.publicpurpose",
        ],
        "system_prompt": """You are an expert municipal bond analyst extracting party and governance information.
Focus on identifying the legal entities involved in the transaction structure.
Cite exact text for each party identification.""",
        "extraction_prompt_template": """Extract the following from this document:
1. Project issuer (typically IDA or municipal entity)
2. Issuer jurisdiction (state)
3. Project borrower or operator (private entity)
4. Technology provider/OEM
5. Equity sponsor or funding source
6. Inducement status (draft, proposed, or adopted)
7. Public purpose / community benefit statement

Document content:
{content}

Return a JSON object with extracted facts, confidence scores, and source quotes.""",
        "requires_full_document": False,
        "idempotent": True,
    },
    {
        "extractor_id": "FeedstockSupplyExtractor",
        "name": "Feedstock & Supply Extractor",
        "description": "Extracts feedstock type, volume, and supply agreement details",
        "target_schema_paths": [
            "feedstock.type",
            "feedstock.volume.annual",
            "feedstock.supply.mechanism",
            "feedstock.supply.confidence",
            "feedstock.characterization",
        ],
        "system_prompt": """You are extracting feedstock and supply chain information for a waste-to-energy project.
Pay attention to supply agreement status and confidence levels.""",
        "extraction_prompt_template": """Extract feedstock and supply information:
1. Feedstock type (forestry, MSW, agricultural, or mixed)
2. Annual feedstock volume (tons/year)
3. Supply mechanism (contract, MOU, letter of intent, or assessment only)
4. Supply confidence level (preliminary, advanced, or secured)
5. Feedstock characterization details

Document content:
{content}

Return JSON with facts, confidence scores, and supporting quotes.""",
        "requires_full_document": False,
        "idempotent": True,
    },
    {
        "extractor_id": "RevenueModelExtractor",
        "name": "Revenue Model Extractor",
        "description": "Extracts commodity revenues, offtake agreements, and projections",
        "target_schema_paths": [
            "revenue.commodities.list",
            "revenue.commodities.renewable-diesel",
            "revenue.commodities.biochar",
            "revenue.offtake.status",
            "revenue.gross.annual",
        ],
        "system_prompt": """You are extracting revenue model information for bond structuring.
Focus on quantifiable revenue streams and their contractual status.""",
        "extraction_prompt_template": """Extract revenue model information:
1. List of commodity revenue streams (product, volume, price, annual revenue)
2. Renewable diesel specifics (gallons/year, price/gallon)
3. Biochar specifics (tons/year, price/ton)
4. Offtake agreement status (executed, advanced MOU, LOI, or negotiating)
5. Total gross annual revenue projection

Document content:
{content}

Return JSON with structured revenue data and confidence scores.""",
        "requires_full_document": True,
        "idempotent": True,
    },
    {
        "extractor_id": "CABTermsExtractor",
        "name": "CAB Terms Extractor",
        "description": "Extracts Capital Appreciation Bond specific terms and structure",
        "target_schema_paths": [
            "cab.enabled",
            "cab.originalprincipial",
            "cab.accretionrate",
            "cab.accretion.period.years",
            "cab.finalmaturitydate",
            "cab.turbo.enabled",
            "cab.conversion.rate",
        ],
        "system_prompt": """You are extracting Capital Appreciation Bond (CAB) terms.
CABs are zero-coupon bonds that accrete value before converting to current-pay.
Extract terms with high precision - these are critical for bond structuring.""",
        "extraction_prompt_template": """Extract CAB-specific bond terms:
1. Is CAB structure enabled/proposed? (boolean)
2. Original principal amount
3. Accretion rate (annual %)
4. Accretion period (years before conversion)
5. Final maturity date
6. Turbo redemption enabled? (mandatory prepayment from excess cash)
7. Conversion rate (interest rate after conversion to current-pay)

Document content:
{content}

Return JSON with precise values and high confidence thresholds.""",
        "requires_full_document": True,
        "idempotent": True,
    },
    {
        "extractor_id": "DSCRInputsExtractor",
        "name": "DSCR & Financial Inputs Extractor",
        "description": "Extracts debt service coverage ratio inputs and covenants",
        "target_schema_paths": [
            "finmodel.inputs.revenue.annual",
            "finmodel.inputs.revenue.ramp",
            "finmodel.inputs.dscr.minimum",
            "finmodel.outputs.dscrbase",
            "finmodel.outputs.dscrstress",
            "capital.project-cost",
            "capital.equity-contribution",
        ],
        "system_prompt": """You are extracting financial model inputs for DSCR calculation.
DSCR = Net Operating Income / Annual Debt Service. Minimum covenant is typically 1.35x.
Extract with precision - these drive bond sizing and credit analysis.""",
        "extraction_prompt_template": """Extract DSCR and financial model inputs:
1. Projected annual revenue (Year 1 or steady-state)
2. Revenue ramp schedule by year
3. Minimum DSCR covenant (typically 1.35x)
4. Base case DSCR
5. Stress case DSCR (at -20% revenue)
6. Total project cost
7. Equity contribution amount

Document content:
{content}

Return JSON with financial metrics and calculation methodology.""",
        "requires_full_document": True,
        "idempotent": True,
    },
    {
        "extractor_id": "SLBMetricsExtractor",
        "name": "SLB KPI & Metrics Extractor",
        "description": "Extracts Sustainability-Linked Bond KPIs, targets, and verification",
        "target_schema_paths": [
            "slb.enabled",
            "slb.kpis.shortlist",
            "slb.kpi.1.name",
            "slb.kpi.1.baseline.value",
            "slb.kpi.1.baseline.methodology",
            "slb.kpi.1.verification.method",
            "slb.penalty.stepup.magnitude",
        ],
        "system_prompt": """You are extracting Sustainability-Linked Bond (SLB) KPI information.
SLBs have performance targets with coupon step-ups/step-downs based on achievement.
Focus on KPI definitions, baselines, targets, and verification methodology.""",
        "extraction_prompt_template": """Extract SLB KPI information:
1. Is SLB structure enabled?
2. Selected KPIs (shortlist)
3. For each KPI: name, definition, unit of measure
4. Baseline value and calculation methodology
5. Year 3/6/9 targets (SPTs)
6. Verification method and provider
7. Step-up penalty magnitude (basis points)

Document content:
{content}

Return JSON with complete KPI structure and verification plan.""",
        "requires_full_document": True,
        "idempotent": True,
    },
    {
        "extractor_id": "PermitRegulatoryExtractor",
        "name": "Permits & Regulatory Extractor",
        "description": "Extracts permitting status and regulatory compliance information",
        "target_schema_paths": [
            "permitting.air-quality.status",
            "permitting.solidwaste.status",
            "permitting.buildingzoning.status",
            "regulatory.tax-status",
            "regulatory.tax-exemption.basis",
        ],
        "system_prompt": """You are extracting permitting and regulatory information.
Permit status is critical for project timeline and bond closing.""",
        "extraction_prompt_template": """Extract permitting and regulatory status:
1. Air quality permit status and type
2. Solid waste permit status
3. Building/zoning permit status
4. Tax status (tax-exempt IDB, tax-exempt solid waste, or taxable)
5. Tax exemption legal basis (if applicable)

Document content:
{content}

Return JSON with permit statuses and regulatory classifications.""",
        "requires_full_document": False,
        "idempotent": True,
    },
]

# Checklist items organized by phase
CHECKLIST_ITEMS = [
    # P1: Issuer Authority & Deal Formation (Months 0-1)
    {
        "item_code": "P1.1",
        "phase": "P1",
        "title": "Inducement Resolution",
        "description": "IDA has adopted or proposed inducement resolution authorizing bond issuance consideration",
        "required_schema_paths": ["governance.inducement", "parties.issuer.name", "parties.issuer.jurisdiction"],
        "optional_schema_paths": ["governance.publicpurpose"],
        "criticality": "critical",
        "blocks_phase_completion": True,
    },
    {
        "item_code": "P1.2",
        "phase": "P1",
        "title": "Tax Status Determination",
        "description": "Preliminary determination of tax-exempt eligibility or taxable bond structure",
        "required_schema_paths": ["regulatory.tax-status"],
        "optional_schema_paths": ["regulatory.tax-exemption.basis"],
        "criticality": "critical",
        "blocks_phase_completion": True,
    },
    {
        "item_code": "P1.3",
        "phase": "P1",
        "title": "Project Entity Formation",
        "description": "Borrower/project entity identified with proper legal structure",
        "required_schema_paths": ["parties.borrower.name", "parties.operator.name"],
        "optional_schema_paths": ["parties.sponsor.name"],
        "criticality": "material",
        "blocks_phase_completion": True,
    },

    # P2: Project & Technology Definition (Months 1-4)
    {
        "item_code": "P2.1",
        "phase": "P2",
        "title": "Technology Specification",
        "description": "UCS technology type and throughput capacity documented",
        "required_schema_paths": ["technology.type", "technology.throughput.nameplate", "technology.throughput.annual"],
        "optional_schema_paths": ["technology.lifespan", "technology.warranty.duration"],
        "criticality": "critical",
        "blocks_phase_completion": True,
    },
    {
        "item_code": "P2.2",
        "phase": "P2",
        "title": "Site Control Evidence",
        "description": "Site control mechanism documented (purchase, lease, option, or LOI)",
        "required_schema_paths": ["project.location.sitecontrol", "project.location.jurisdiction"],
        "optional_schema_paths": ["project.location.coordinates"],
        "criticality": "material",
        "blocks_phase_completion": True,
    },
    {
        "item_code": "P2.3",
        "phase": "P2",
        "title": "Feedstock Supply Mechanism",
        "description": "Feedstock type and supply mechanism identified",
        "required_schema_paths": ["feedstock.type", "feedstock.volume.annual", "feedstock.supply.mechanism"],
        "optional_schema_paths": ["feedstock.characterization"],
        "criticality": "critical",
        "blocks_phase_completion": True,
    },
    {
        "item_code": "P2.4",
        "phase": "P2",
        "title": "Permitting Pathway",
        "description": "Key permits identified with status tracking",
        "required_schema_paths": ["permitting.air-quality.status", "permitting.solidwaste.status"],
        "optional_schema_paths": ["permitting.buildingzoning.status"],
        "criticality": "material",
        "blocks_phase_completion": False,
    },

    # P3: Financial Structure & Revenue Model (Months 2-6)
    {
        "item_code": "P3.1",
        "phase": "P3",
        "title": "Revenue Model Documentation",
        "description": "Commodity revenue streams quantified with pricing assumptions",
        "required_schema_paths": ["revenue.commodities.list", "revenue.gross.annual"],
        "optional_schema_paths": ["revenue.commodities.renewable-diesel", "revenue.commodities.biochar"],
        "criticality": "critical",
        "blocks_phase_completion": True,
    },
    {
        "item_code": "P3.2",
        "phase": "P3",
        "title": "Offtake Agreement Status",
        "description": "Status of commodity offtake agreements (executed, MOU, LOI, negotiating)",
        "required_schema_paths": ["revenue.offtake.status"],
        "optional_schema_paths": [],
        "criticality": "critical",
        "blocks_phase_completion": True,
    },
    {
        "item_code": "P3.3",
        "phase": "P3",
        "title": "Capital Structure",
        "description": "Total project cost, equity contribution, and debt requirement documented",
        "required_schema_paths": ["capital.project-cost", "capital.equity-contribution", "capital.equity-percent"],
        "optional_schema_paths": ["capital.equipment-cost"],
        "criticality": "critical",
        "blocks_phase_completion": True,
    },
    {
        "item_code": "P3.4",
        "phase": "P3",
        "title": "Feedstock Supply Confidence",
        "description": "Feedstock supply confidence level advanced beyond preliminary",
        "required_schema_paths": ["feedstock.supply.confidence"],
        "optional_schema_paths": [],
        "criticality": "material",
        "blocks_phase_completion": True,
    },

    # P4: Risk, Security & Disclosure (Months 4-8)
    {
        "item_code": "P4.1",
        "phase": "P4",
        "title": "Security Package Definition",
        "description": "Collateral package defined (real property, equipment, revenue pledge)",
        "required_schema_paths": ["security.revenue.pledge"],
        "optional_schema_paths": ["security.realproperty", "security.equipment.schedule"],
        "criticality": "critical",
        "blocks_phase_completion": True,
    },
    {
        "item_code": "P4.2",
        "phase": "P4",
        "title": "Operating Expense Model",
        "description": "OpEx budget documented with margin analysis",
        "required_schema_paths": ["opex.total.annual", "ebitda"],
        "optional_schema_paths": ["opex.margin"],
        "criticality": "material",
        "blocks_phase_completion": True,
    },

    # P5: SLB Architecture & Final Modeling (Months 6-8)
    {
        "item_code": "P5.1",
        "phase": "P5",
        "title": "CAB Structure Confirmation",
        "description": "CAB terms defined (principal, accretion rate, period, maturity)",
        "required_schema_paths": ["cab.enabled", "cab.originalprincipial", "cab.accretionrate", "cab.accretion.period.years"],
        "optional_schema_paths": ["cab.finalmaturitydate", "cab.turbo.enabled", "cab.conversion.rate"],
        "criticality": "critical",
        "blocks_phase_completion": True,
    },
    {
        "item_code": "P5.2",
        "phase": "P5",
        "title": "DSCR Covenant & Coverage",
        "description": "DSCR covenant defined with base and stress case coverage documented",
        "required_schema_paths": ["finmodel.inputs.dscr.minimum", "finmodel.outputs.dscrbase"],
        "optional_schema_paths": ["finmodel.outputs.dscrstress", "finmodel.inputs.revenue.ramp"],
        "criticality": "critical",
        "blocks_phase_completion": True,
    },
    {
        "item_code": "P5.3",
        "phase": "P5",
        "title": "SLB KPI Selection & Baselines",
        "description": "SLB KPIs selected with baselines, targets, and verification methodology",
        "required_schema_paths": ["slb.enabled", "slb.kpis.shortlist", "slb.kpi.1.baseline.methodology"],
        "optional_schema_paths": ["slb.kpi.1.name", "slb.kpi.1.baseline.value", "slb.kpi.1.verification.method"],
        "criticality": "critical",
        "blocks_phase_completion": True,
    },
    {
        "item_code": "P5.4",
        "phase": "P5",
        "title": "SLB Penalty Structure",
        "description": "Step-up/step-down penalty structure defined",
        "required_schema_paths": ["slb.penalty.stepup.magnitude"],
        "optional_schema_paths": [],
        "criticality": "material",
        "blocks_phase_completion": True,
    },

    # P6: Advisor Engagement & Execution (Months 8-12+)
    {
        "item_code": "P6.1",
        "phase": "P6",
        "title": "Warm Handoff Pack Complete",
        "description": "All sections of advisor handoff pack generated and reviewed",
        "required_schema_paths": [],
        "optional_schema_paths": [],
        "criticality": "material",
        "blocks_phase_completion": False,
    },
]

# Readiness dimension configuration
READINESS_CONFIG = {
    "dimensions": {
        "issuer_authority": {
            "name": "Issuer Authority",
            "weight": 0.20,
            "contributing_paths": [
                "governance.inducement",
                "parties.issuer.name",
                "parties.issuer.jurisdiction",
                "regulatory.tax-status",
                "parties.borrower.name",
            ],
            "critical_paths": ["governance.inducement", "regulatory.tax-status"],
        },
        "project_tech": {
            "name": "Project & Technology",
            "weight": 0.20,
            "contributing_paths": [
                "project.canonicaldescription",
                "technology.type",
                "technology.throughput.nameplate",
                "project.location.sitecontrol",
                "technology.warranty.duration",
            ],
            "critical_paths": ["technology.type", "technology.throughput.nameplate"],
        },
        "revenue_feedstock": {
            "name": "Revenue & Feedstock",
            "weight": 0.15,
            "contributing_paths": [
                "feedstock.type",
                "feedstock.volume.annual",
                "feedstock.supply.mechanism",
                "feedstock.supply.confidence",
                "revenue.commodities.list",
                "revenue.gross.annual",
                "revenue.offtake.status",
            ],
            "critical_paths": ["feedstock.supply.mechanism", "revenue.offtake.status", "revenue.gross.annual"],
        },
        "cab_financial": {
            "name": "CAB Financial Structure",
            "weight": 0.20,
            "contributing_paths": [
                "cab.enabled",
                "cab.originalprincipial",
                "cab.accretionrate",
                "cab.accretion.period.years",
                "finmodel.inputs.dscr.minimum",
                "finmodel.outputs.dscrbase",
                "capital.project-cost",
                "capital.equity-contribution",
            ],
            "critical_paths": ["cab.accretionrate", "finmodel.outputs.dscrbase", "capital.equity-contribution"],
        },
        "risk_security_slb": {
            "name": "Risk, Security & SLB",
            "weight": 0.15,
            "contributing_paths": [
                "security.revenue.pledge",
                "security.realproperty",
                "permitting.air-quality.status",
                "permitting.solidwaste.status",
                "opex.total.annual",
                "ebitda",
            ],
            "critical_paths": ["security.revenue.pledge"],
        },
        "slb_verification": {
            "name": "SLB Verification",
            "weight": 0.10,
            "contributing_paths": [
                "slb.enabled",
                "slb.kpis.shortlist",
                "slb.kpi.1.baseline.methodology",
                "slb.kpi.1.verification.method",
                "slb.penalty.stepup.magnitude",
            ],
            "critical_paths": ["slb.kpis.shortlist", "slb.kpi.1.baseline.methodology"],
        },
    },
    "score_thresholds": {
        "not_yet_viable": {"min": 0.0, "max": 3.0},
        "structurally_viable": {"min": 3.0, "max": 5.5},
        "ready_for_selective_engagement": {"min": 5.5, "max": 7.5},
        "ready_for_broad_market": {"min": 7.5, "max": 10.0},
    },
}

# Complete playbook configuration
UCS_PLAYBOOK_CONFIG = {
    "name": "UCS CAB+SLB Revenue Bond",
    "version": "0.2.0",
    "description": "Bond Intelligence Configuration Playbook for UCS Waste-to-Energy Capital Appreciation + Sustainability-Linked Bond structures. Defines extraction schema, checklist phases P1-P6, and readiness scoring for Sierra Vista IDA-style revenue bond facilities.",
    "bond_archetype": "UCS Waste-to-Energy CAB+SLB Revenue Bond",
    "schema_paths": SCHEMA_PATHS,
    "extractors": EXTRACTORS,
    "checklist_items": CHECKLIST_ITEMS,
    "readiness_config": READINESS_CONFIG,
}
