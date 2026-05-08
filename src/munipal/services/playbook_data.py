"""
UCS CAB+SLB Playbook Configuration Data.

This module contains the structured configuration extracted from the
UCS Bond Intelligence Configuration Playbook v0.2.

Per spec: This is the source of truth for schema paths, extractors,
checklist items, and readiness scoring rules.
"""

# =============================================================================
# SCHEMA PATH METADATA
# =============================================================================
# Comprehensive descriptions, guidance, and examples for each schema path.
# This enables non-technical users to understand what information is needed.

SCHEMA_PATH_METADATA = {
    # -------------------------------------------------------------------------
    # Project Foundation
    # -------------------------------------------------------------------------
    "project.canonicaldescription": {
        "description": "A concise 1-2 sentence description of the project that captures its purpose, location, and key features. This appears prominently in disclosure documents and advisor materials.",
        "short_description": "Project summary for disclosure documents",
        "guidance": "Provide a factual, neutral description of the project. Include the technology type, location, and primary outputs. Avoid promotional language or forward-looking statements.",
        "example": "A 100 TPD Ultimate Conversion System facility in El Dorado County, California that converts forest biomass into renewable diesel, biochar, and electricity.",
        "who_needs_it": ["Bond Counsel", "Underwriter", "Rating Agency"],
    },
    "project.location.jurisdiction": {
        "description": "The state, county, or municipality where the project is physically located. This determines regulatory requirements and the applicable IDA.",
        "short_description": "Project location for regulatory compliance",
        "guidance": "Enter the full jurisdiction name (e.g., 'El Dorado County, California'). This must match the IDA's service territory.",
        "example": "El Dorado County, California",
        "who_needs_it": ["Bond Counsel", "Permitting Consultant"],
    },
    "project.location.sitecontrol": {
        "description": "The legal mechanism by which the project has rights to use the land. Site control is a prerequisite for permitting and financing.",
        "short_description": "Land rights documentation status",
        "guidance": "Select the strongest form of site control currently in place: 'purchase' (ownership), 'lease' (long-term agreement), 'option' (right to acquire), or 'loi' (letter of intent).",
        "example": "lease",
        "who_needs_it": ["Real Estate Counsel", "Lender"],
    },
    "project.location.coordinates": {
        "description": "GPS coordinates of the project site, used for permitting applications and environmental assessments.",
        "short_description": "GPS coordinates for permitting",
        "guidance": "Provide coordinates in decimal degrees format (latitude, longitude). Accuracy to 4 decimal places is sufficient.",
        "example": "38.7296, -120.7984",
        "who_needs_it": ["Environmental Consultant"],
    },
    "project.operatingstatus": {
        "description": "Current development phase of the project. This affects risk assessment, insurance requirements, and disclosure language.",
        "short_description": "Current development phase",
        "guidance": "Select 'planned' if in development/permitting, 'under-construction' if construction has begun, or 'operational' if generating revenue.",
        "example": "planned",
        "who_needs_it": ["Independent Engineer", "Insurance Broker"],
    },
    "project.designlife": {
        "description": "The expected useful life of the facility in years. This affects depreciation, bond term, and long-term financial projections.",
        "short_description": "Expected facility lifespan",
        "guidance": "Enter the design life from engineering studies. Typical range for industrial facilities is 20-30 years.",
        "example": "25",
        "who_needs_it": ["Independent Engineer", "Financial Advisor"],
    },

    # -------------------------------------------------------------------------
    # Parties & Governance
    # -------------------------------------------------------------------------
    "parties.issuer.name": {
        "description": "The Industrial Development Authority (IDA) or municipal entity that will issue the bonds. The issuer provides the tax-exempt status but typically has no obligation to repay.",
        "short_description": "Bond-issuing municipal authority",
        "guidance": "Enter the full legal name of the IDA or issuing authority (e.g., 'El Dorado County Industrial Development Authority').",
        "example": "El Dorado County Industrial Development Authority",
        "who_needs_it": ["Bond Counsel", "Municipal Advisor", "Underwriter"],
    },
    "parties.issuer.jurisdiction": {
        "description": "The state where the issuing authority is organized. This determines applicable bond law and procedures.",
        "short_description": "Issuer's state of organization",
        "guidance": "Enter the state name where the IDA is organized (typically matches project location).",
        "example": "California",
        "who_needs_it": ["Bond Counsel"],
    },
    "parties.borrower.name": {
        "description": "The private entity that will borrow the bond proceeds and be obligated to repay. This is typically a special purpose entity (SPE) created for the project.",
        "short_description": "Entity receiving bond proceeds",
        "guidance": "Enter the full legal name of the borrowing entity. If not yet formed, note the anticipated name and formation status.",
        "example": "El Dorado BioEnergy LLC",
        "who_needs_it": ["Bond Counsel", "Underwriter", "Rating Agency"],
    },
    "parties.operator.name": {
        "description": "The entity responsible for day-to-day operations of the facility. May be the same as borrower or a contracted O&M provider.",
        "short_description": "Facility operator",
        "guidance": "Enter the entity that will operate the facility. Include any O&M agreement status if different from borrower.",
        "example": "El Dorado Operations Inc.",
        "who_needs_it": ["Independent Engineer", "Insurance Broker"],
    },
    "parties.sponsor.name": {
        "description": "The equity investor or parent company providing financial backing. Sponsor creditworthiness affects investor confidence.",
        "short_description": "Equity sponsor providing backing",
        "guidance": "Enter the name of the primary equity sponsor. Note ownership percentage if multiple sponsors.",
        "example": "Sierra Clean Energy Partners",
        "who_needs_it": ["Underwriter", "Rating Agency"],
    },
    "governance.inducement": {
        "description": "The status of the IDA's inducement resolution, which formally authorizes the issuer to proceed with bond financing. This is a legal prerequisite for engagement.",
        "short_description": "IDA authorization status",
        "guidance": "Select 'draft' if resolution is being prepared, 'proposed' if submitted for board consideration, or 'adopted' if approved by the IDA board.",
        "example": "adopted",
        "who_needs_it": ["Bond Counsel", "Municipal Advisor"],
    },
    "governance.publicpurpose": {
        "description": "The community benefit statement explaining how the project serves public interests. Required for tax-exempt bond qualification.",
        "short_description": "Community benefit justification",
        "guidance": "Describe specific public benefits: job creation, environmental remediation, tax revenue, energy independence, etc.",
        "example": "The project will create 35 permanent jobs, reduce wildfire fuel load on 50,000 acres annually, and generate local tax revenue of $1.2M per year.",
        "who_needs_it": ["Bond Counsel", "IDA Board"],
    },

    # -------------------------------------------------------------------------
    # Technology & Operations
    # -------------------------------------------------------------------------
    "technology.type": {
        "description": "The core conversion technology used by the project. This determines technical risk profile, regulatory requirements, and comparable transactions.",
        "short_description": "Core conversion technology",
        "guidance": "Select the primary technology: 'ucs' (Ultimate Conversion System), 'thermal' (gasification/pyrolysis), 'biological' (anaerobic digestion), or 'chemical' (other processes).",
        "example": "ucs",
        "who_needs_it": ["Independent Engineer", "Technical Advisor"],
    },
    "technology.throughput.nameplate": {
        "description": "The maximum daily processing capacity of the facility in tons per day (TPD). This is the design capacity at full operation.",
        "short_description": "Design capacity (tons/day)",
        "guidance": "Enter the nameplate capacity from engineering specifications. This should match equipment warranties.",
        "example": "100",
        "who_needs_it": ["Independent Engineer", "Rating Agency"],
    },
    "technology.throughput.annual": {
        "description": "The expected annual feedstock throughput in tons per year. Typically calculated as nameplate × operating days × capacity factor.",
        "short_description": "Annual throughput (tons/year)",
        "guidance": "Enter annual throughput. Standard calculation: nameplate TPD × 351 operating days × 95% availability = annual tons.",
        "example": "33,345",
        "who_needs_it": ["Independent Engineer", "Financial Advisor"],
    },
    "technology.lifespan": {
        "description": "The expected useful life of the technology/equipment in years before major refurbishment or replacement.",
        "short_description": "Equipment useful life",
        "guidance": "Enter equipment lifespan from manufacturer specifications. Should align with or exceed bond term.",
        "example": "20",
        "who_needs_it": ["Independent Engineer"],
    },
    "technology.warranty.supplier": {
        "description": "The entity providing equipment performance warranties. Warranty provider creditworthiness affects risk assessment.",
        "short_description": "Equipment warranty provider",
        "guidance": "Enter the name of the OEM or technology provider offering performance guarantees.",
        "example": "Sierra Energy Corporation",
        "who_needs_it": ["Independent Engineer", "Insurance Broker"],
    },
    "technology.warranty.duration": {
        "description": "The duration of equipment performance warranties in years. Longer warranties reduce technology risk during the critical early operating period.",
        "short_description": "Warranty coverage duration",
        "guidance": "Enter warranty term in years. Market standard is 3-5 years for core equipment.",
        "example": "5",
        "who_needs_it": ["Independent Engineer", "Underwriter"],
    },
    "operations.staffing.direct": {
        "description": "The number of direct employees required to operate the facility. This affects operating expenses and community benefit calculations.",
        "short_description": "Permanent facility employees",
        "guidance": "Enter the total headcount of permanent, direct employees (not including contractors or construction workers).",
        "example": "35",
        "who_needs_it": ["Financial Advisor", "IDA Board"],
    },

    # -------------------------------------------------------------------------
    # Feedstock & Supply
    # -------------------------------------------------------------------------
    "feedstock.type": {
        "description": "The primary type of input material processed by the facility. Feedstock type affects permits, revenue streams, and supply risk.",
        "short_description": "Primary input material category",
        "guidance": "Select: 'forestry' (wood waste/biomass), 'msw' (municipal solid waste), 'agricultural' (crop residues), or 'mixed' (multiple sources).",
        "example": "forestry",
        "who_needs_it": ["Independent Engineer", "Permitting Consultant"],
    },
    "feedstock.volume.annual": {
        "description": "The annual volume of feedstock required to operate the facility at design capacity, measured in tons per year.",
        "short_description": "Annual feedstock requirement",
        "guidance": "Enter annual tonnage needed. Must be supported by supply agreements or availability studies.",
        "example": "35,000",
        "who_needs_it": ["Independent Engineer", "Rating Agency"],
    },
    "feedstock.supply.mechanism": {
        "description": "The contractual status of feedstock supply arrangements. Binding contracts reduce supply risk compared to preliminary discussions.",
        "short_description": "Supply agreement status",
        "guidance": "Select the strongest current status: 'contract' (binding agreement), 'mou' (memorandum of understanding), 'letter-of-intent' (LOI), or 'assessment' (feasibility study only).",
        "example": "mou",
        "who_needs_it": ["Rating Agency", "Underwriter"],
    },
    "feedstock.supply.confidence": {
        "description": "The overall confidence level in securing adequate feedstock supply. Affects risk assessment and disclosure language.",
        "short_description": "Supply security confidence level",
        "guidance": "Select: 'preliminary' (early discussions), 'advanced' (term sheets/MOUs in place), or 'secured' (binding contracts executed).",
        "example": "advanced",
        "who_needs_it": ["Rating Agency", "Independent Engineer"],
    },
    "feedstock.characterization": {
        "description": "Technical analysis of feedstock properties including moisture content, energy content, and contaminant levels. Required for technology sizing and permits.",
        "short_description": "Feedstock quality analysis",
        "guidance": "Describe feedstock composition: moisture %, BTU content, ash content, and any contaminants. Attach lab analysis if available.",
        "example": "Forest biomass at 25% moisture, 8,500 BTU/lb, <2% ash content, no heavy metals.",
        "who_needs_it": ["Independent Engineer", "Permitting Consultant"],
    },

    # -------------------------------------------------------------------------
    # Revenue Model
    # -------------------------------------------------------------------------
    "revenue.commodities.list": {
        "description": "List of all commodity products that will generate revenue. Each commodity represents a distinct revenue stream with its own pricing and offtake arrangements.",
        "short_description": "Revenue-generating product list",
        "guidance": "List all output products: renewable diesel, biochar, electricity, carbon credits, tipping fees, etc.",
        "example": ["Renewable Diesel", "Biochar", "Renewable Electricity"],
        "who_needs_it": ["Financial Advisor", "Underwriter"],
    },
    "revenue.commodities.renewable-diesel": {
        "description": "Projected annual revenue from renewable diesel sales in USD. This is typically the primary revenue stream for UCS projects.",
        "short_description": "Annual renewable diesel revenue",
        "guidance": "Enter projected annual revenue in USD. Calculate as: gallons/year × price/gallon. Include LCFS credit value if applicable.",
        "example": "15000000",
        "who_needs_it": ["Financial Advisor", "Rating Agency"],
    },
    "revenue.commodities.biochar": {
        "description": "Projected annual revenue from biochar sales in USD. Biochar can be sold for agricultural, environmental, or industrial applications.",
        "short_description": "Annual biochar revenue",
        "guidance": "Enter projected annual revenue in USD. Calculate as: tons/year × price/ton.",
        "example": "2500000",
        "who_needs_it": ["Financial Advisor"],
    },
    "revenue.offtake.status": {
        "description": "The contractual status of commodity sales agreements. Executed offtake agreements significantly reduce revenue risk.",
        "short_description": "Commodity sales contract status",
        "guidance": "Select: 'executed' (binding contracts signed), 'advanced-mou' (detailed terms agreed), 'letter-of-intent' (preliminary agreement), or 'negotiating' (discussions ongoing).",
        "example": "advanced-mou",
        "who_needs_it": ["Rating Agency", "Underwriter"],
    },
    "revenue.gross.annual": {
        "description": "Total projected annual revenue from all sources at stabilized operations. This is the top-line revenue figure used in DSCR calculations.",
        "short_description": "Total annual gross revenue",
        "guidance": "Enter total projected annual revenue in USD, including all commodity sales, tipping fees, and credits.",
        "example": "22000000",
        "who_needs_it": ["Financial Advisor", "Rating Agency", "Underwriter"],
    },

    # -------------------------------------------------------------------------
    # Operating Expenses
    # -------------------------------------------------------------------------
    "opex.total.annual": {
        "description": "Total projected annual operating expenses excluding debt service. Includes labor, feedstock handling, maintenance, utilities, insurance, and administration.",
        "short_description": "Total annual operating costs",
        "guidance": "Enter total annual OpEx in USD from the financial model. Should be detailed by category in supporting documentation.",
        "example": "8500000",
        "who_needs_it": ["Financial Advisor", "Independent Engineer"],
    },
    "opex.margin": {
        "description": "Operating margin expressed as a percentage: (Revenue - OpEx) / Revenue. Indicates operating efficiency and cushion for debt service.",
        "short_description": "Operating margin percentage",
        "guidance": "Enter as a percentage. Typical target is 40-60% for project finance deals.",
        "example": "61.4",
        "who_needs_it": ["Financial Advisor", "Rating Agency"],
    },
    "ebitda": {
        "description": "Earnings Before Interest, Taxes, Depreciation, and Amortization. The primary cash flow metric for debt capacity analysis.",
        "short_description": "EBITDA cash flow metric",
        "guidance": "Enter annual EBITDA in USD. Calculate as: Revenue - Operating Expenses (before debt service, depreciation, taxes).",
        "example": "13500000",
        "who_needs_it": ["Financial Advisor", "Rating Agency", "Underwriter"],
    },

    # -------------------------------------------------------------------------
    # Capital Structure
    # -------------------------------------------------------------------------
    "capital.project-cost": {
        "description": "Total project cost including equipment, construction, development costs, financing fees, and reserves. This is the capital requirement to be funded.",
        "short_description": "Total project capital requirement",
        "guidance": "Enter total project cost in USD from the development budget. Should include contingency (typically 10-15%).",
        "example": "85000000",
        "who_needs_it": ["Financial Advisor", "Underwriter", "Rating Agency"],
    },
    "capital.equipment-cost": {
        "description": "Cost of core technology and equipment. Equipment cost as a percentage of total project cost indicates technology concentration risk.",
        "short_description": "Core equipment cost",
        "guidance": "Enter equipment cost in USD from vendor quotes or EPC contract.",
        "example": "45000000",
        "who_needs_it": ["Independent Engineer", "Insurance Broker"],
    },
    "capital.equity-contribution": {
        "description": "Amount of equity being contributed by sponsors. Equity cushion protects bondholders and demonstrates sponsor commitment.",
        "short_description": "Sponsor equity investment",
        "guidance": "Enter equity contribution amount in USD. Market standard for project finance is 20-35% equity.",
        "example": "25500000",
        "who_needs_it": ["Underwriter", "Rating Agency"],
    },
    "capital.equity-percent": {
        "description": "Equity contribution as a percentage of total project cost. Higher equity percentages indicate stronger sponsor commitment and lower bondholder risk.",
        "short_description": "Equity percentage of project",
        "guidance": "Enter as a percentage. Calculate as: Equity Contribution / Total Project Cost × 100.",
        "example": "30",
        "who_needs_it": ["Rating Agency", "Underwriter"],
    },

    # -------------------------------------------------------------------------
    # CAB Terms
    # -------------------------------------------------------------------------
    "cab.enabled": {
        "description": "Indicates whether the bond structure includes Capital Appreciation Bond (CAB) features. CABs defer interest payments during construction/ramp-up.",
        "short_description": "CAB structure enabled",
        "guidance": "Enter 'true' if using CAB structure, 'false' if current-pay bonds from issuance.",
        "example": "true",
        "who_needs_it": ["Financial Advisor", "Bond Counsel"],
    },
    "cab.originalprincipial": {
        "description": "The original principal amount of the CAB at issuance, before accretion. This is the bond amount investors will pay at closing.",
        "short_description": "Initial bond principal",
        "guidance": "Enter original principal in USD. This accretes to maturity value over the accretion period.",
        "example": "59500000",
        "who_needs_it": ["Financial Advisor", "Underwriter"],
    },
    "cab.accretionrate": {
        "description": "The annual interest rate at which the CAB accretes value during the deferral period, expressed as a percentage.",
        "short_description": "Annual accretion rate",
        "guidance": "Enter as a percentage. Market range is typically 5-7% for project finance CABs.",
        "example": "5.75",
        "who_needs_it": ["Financial Advisor", "Underwriter", "Bond Counsel"],
    },
    "cab.accretion.period.years": {
        "description": "The number of years during which the CAB accretes (defers interest) before converting to current-pay. Should align with construction and ramp-up timeline.",
        "short_description": "Years before conversion",
        "guidance": "Enter number of years. Typically 3-6 years to cover construction plus stabilization period.",
        "example": "5",
        "who_needs_it": ["Financial Advisor", "Independent Engineer"],
    },
    "cab.finalmaturitydate": {
        "description": "The date when all bond principal and accreted interest becomes due. Typically 20-30 years from issuance.",
        "short_description": "Bond maturity date",
        "guidance": "Enter date in YYYY-MM-DD format. Should align with equipment useful life and project cash flows.",
        "example": "2049-01-01",
        "who_needs_it": ["Financial Advisor", "Bond Counsel"],
    },
    "cab.turbo.enabled": {
        "description": "Indicates whether turbo redemption provisions apply, requiring mandatory principal prepayment from excess cash flows.",
        "short_description": "Turbo prepayment enabled",
        "guidance": "Enter 'true' if turbo provisions apply, 'false' otherwise. Turbo provisions accelerate bondholder payback but reduce sponsor cash distributions.",
        "example": "true",
        "who_needs_it": ["Financial Advisor", "Underwriter"],
    },
    "cab.conversion.rate": {
        "description": "The interest rate that applies after the CAB converts from accretion to current-pay status, expressed as a percentage.",
        "short_description": "Post-conversion interest rate",
        "guidance": "Enter as a percentage. May be fixed or floating. Often the same as accretion rate.",
        "example": "5.75",
        "who_needs_it": ["Financial Advisor", "Underwriter"],
    },

    # -------------------------------------------------------------------------
    # Financial Model & DSCR
    # -------------------------------------------------------------------------
    "finmodel.inputs.revenue.annual": {
        "description": "The annual revenue assumption used in the financial model at stabilized operations. May differ from revenue.gross.annual due to ramp assumptions.",
        "short_description": "Model revenue assumption",
        "guidance": "Enter the Year 1 stabilized revenue assumption from the financial model in USD.",
        "example": "22000000",
        "who_needs_it": ["Financial Advisor", "Rating Agency"],
    },
    "finmodel.inputs.revenue.ramp": {
        "description": "The revenue ramp schedule showing how revenue builds from COD to stabilization. Affects DSCR during early operating years.",
        "short_description": "Revenue ramp-up schedule",
        "guidance": "Provide year-by-year revenue as percentage of stabilized revenue (e.g., Y1: 60%, Y2: 85%, Y3: 100%).",
        "example": {"Year1": "60%", "Year2": "85%", "Year3": "100%"},
        "who_needs_it": ["Financial Advisor", "Independent Engineer"],
    },
    "finmodel.inputs.dscr.minimum": {
        "description": "The minimum Debt Service Coverage Ratio covenant in the bond indenture. Breach triggers remedial actions.",
        "short_description": "Minimum DSCR covenant",
        "guidance": "Enter as a decimal (e.g., 1.35 for 1.35x coverage). Market standard for project finance is 1.25-1.50x.",
        "example": "1.35",
        "who_needs_it": ["Bond Counsel", "Underwriter", "Rating Agency"],
    },
    "finmodel.outputs.dscrbase": {
        "description": "The projected Debt Service Coverage Ratio under base case assumptions at stabilization. DSCR = Net Operating Income / Annual Debt Service.",
        "short_description": "Base case DSCR projection",
        "guidance": "Enter as a decimal from the financial model. Typical target is 1.4-1.7x for project finance.",
        "example": "1.65",
        "who_needs_it": ["Rating Agency", "Underwriter"],
    },
    "finmodel.outputs.dscrstress": {
        "description": "The projected DSCR under stress case assumptions (typically -20% revenue). Shows cushion above minimum covenant.",
        "short_description": "Stress case DSCR",
        "guidance": "Enter as a decimal. Should remain above minimum covenant (1.35x) even under stress.",
        "example": "1.32",
        "who_needs_it": ["Rating Agency", "Underwriter"],
    },

    # -------------------------------------------------------------------------
    # SLB KPIs
    # -------------------------------------------------------------------------
    "slb.enabled": {
        "description": "Indicates whether Sustainability-Linked Bond (SLB) features are included. SLBs tie bond terms to achievement of sustainability performance targets.",
        "short_description": "SLB features enabled",
        "guidance": "Enter 'true' if using SLB structure with KPIs and step-up provisions, 'false' otherwise.",
        "example": "true",
        "who_needs_it": ["ESG Advisor", "Underwriter"],
    },
    "slb.kpis.shortlist": {
        "description": "The list of Key Performance Indicators selected for SLB tracking. KPIs must be measurable, material, and independently verifiable.",
        "short_description": "Selected sustainability KPIs",
        "guidance": "List 2-4 KPIs such as: waste diversion rate, GHG reduction, renewable fuel production volume, etc.",
        "example": ["Waste Diversion Rate (%)", "Scope 1 GHG Emissions (tCO2e)", "Renewable Diesel Production (gallons)"],
        "who_needs_it": ["ESG Advisor", "Second-Party Opinion Provider"],
    },
    "slb.kpi.1.name": {
        "description": "The name of the primary SLB KPI. This should be specific, measurable, and aligned with ICMA SLB Principles.",
        "short_description": "Primary KPI name",
        "guidance": "Enter a clear, specific KPI name (e.g., 'Annual Waste Diversion Rate').",
        "example": "Annual Waste Diversion Rate",
        "who_needs_it": ["ESG Advisor", "Second-Party Opinion Provider"],
    },
    "slb.kpi.1.baseline.value": {
        "description": "The baseline value for KPI 1 from which improvement will be measured. Must be established using consistent methodology.",
        "short_description": "KPI baseline value",
        "guidance": "Enter the baseline value with units. This is the starting point for measuring improvement.",
        "example": "85",
        "who_needs_it": ["ESG Advisor", "Verifier"],
    },
    "slb.kpi.1.baseline.methodology": {
        "description": "The methodology used to calculate the KPI 1 baseline. Must be documented and replicable for ongoing verification.",
        "short_description": "Baseline calculation method",
        "guidance": "Describe the calculation methodology, data sources, and measurement period for the baseline.",
        "example": "Waste diversion rate calculated as (tons processed - residual waste) / tons processed, based on facility scale ticket records, measured annually.",
        "who_needs_it": ["Verifier", "Second-Party Opinion Provider"],
    },
    "slb.kpi.1.verification.method": {
        "description": "The independent verification process for KPI 1 measurements. Must involve a qualified third-party verifier.",
        "short_description": "Third-party verification approach",
        "guidance": "Describe the verifier type (accounting firm, specialized ESG firm), verification standard (ISAE 3000), and frequency.",
        "example": "Annual limited assurance engagement under ISAE 3000 by a Big 4 accounting firm, with verification report published within 120 days of fiscal year end.",
        "who_needs_it": ["Verifier", "ESG Advisor", "Bond Counsel"],
    },
    "slb.penalty.stepup.magnitude": {
        "description": "The coupon step-up penalty in basis points if Sustainability Performance Targets are not met.",
        "short_description": "Coupon step-up penalty (bps)",
        "guidance": "Enter in basis points (e.g., 25 = 0.25%). Market range is 12.5-50 bps.",
        "example": "25",
        "who_needs_it": ["ESG Advisor", "Underwriter"],
    },

    # -------------------------------------------------------------------------
    # Security & Collateral
    # -------------------------------------------------------------------------
    "security.realproperty": {
        "description": "Description of real property (land, buildings) pledged as security. First mortgage liens provide strongest protection.",
        "short_description": "Real property pledged as collateral",
        "guidance": "Describe the real property: acreage, improvements, lien position (first/second), and recording status.",
        "example": "First deed of trust on 45-acre project site with all improvements, to be recorded at closing.",
        "who_needs_it": ["Bond Counsel", "Title Company"],
    },
    "security.equipment.schedule": {
        "description": "Description of equipment pledged under UCC-1 security agreement. Equipment schedule should itemize major components.",
        "short_description": "Equipment collateral schedule",
        "guidance": "List major equipment categories or reference an attached equipment schedule with values.",
        "example": "All UCS conversion equipment, feedstock handling systems, and balance of plant per Equipment Schedule A, with perfected UCC-1 filing.",
        "who_needs_it": ["Bond Counsel", "Lender's Counsel"],
    },
    "security.revenue.pledge": {
        "description": "The type of revenue pledge securing the bonds. 'Gross' pledges all revenue before expenses; 'net' pledges revenue after operating expenses.",
        "short_description": "Revenue pledge structure",
        "guidance": "Select 'gross' (bondholders paid before OpEx) or 'net' (bondholders paid after OpEx). Gross is stronger security.",
        "example": "gross",
        "who_needs_it": ["Bond Counsel", "Underwriter"],
    },

    # -------------------------------------------------------------------------
    # Permitting
    # -------------------------------------------------------------------------
    "permitting.air-quality.status": {
        "description": "Status of air quality/emissions permits required for facility operation. Air permits are often the longest-lead regulatory requirement.",
        "short_description": "Air quality permit status",
        "guidance": "Select: 'not-started', 'in-progress' (application filed), 'pending-approval' (under agency review), or 'approved' (permit issued).",
        "example": "in-progress",
        "who_needs_it": ["Environmental Consultant", "Independent Engineer"],
    },
    "permitting.solidwaste.status": {
        "description": "Status of solid waste handling permits. Required for facilities receiving waste materials as feedstock.",
        "short_description": "Solid waste permit status",
        "guidance": "Select: 'not-started', 'in-progress', 'pending-approval', or 'approved'. N/A if facility doesn't process waste.",
        "example": "pending-approval",
        "who_needs_it": ["Environmental Consultant", "Permitting Consultant"],
    },
    "permitting.buildingzoning.status": {
        "description": "Status of building permits and zoning approvals for facility construction. Includes conditional use permits if required.",
        "short_description": "Building/zoning approval status",
        "guidance": "Select: 'not-started', 'in-progress', 'pending-approval', or 'approved'. Include conditional use permit status if applicable.",
        "example": "approved",
        "who_needs_it": ["Developer", "Construction Manager"],
    },

    # -------------------------------------------------------------------------
    # Regulatory
    # -------------------------------------------------------------------------
    "regulatory.tax-status": {
        "description": "The anticipated tax status of the bonds. Tax-exempt bonds have lower interest rates but more restrictions.",
        "short_description": "Bond tax status determination",
        "guidance": "Select: 'tax-exempt-idb' (industrial development), 'tax-exempt-solidwaste' (solid waste facility), or 'taxable'.",
        "example": "tax-exempt-solidwaste",
        "who_needs_it": ["Bond Counsel", "Underwriter"],
    },
    "regulatory.tax-exemption.basis": {
        "description": "The legal basis for tax-exempt status under IRC Section 103 and applicable Treasury regulations.",
        "short_description": "Tax exemption legal basis",
        "guidance": "Cite applicable IRC sections and/or Treasury regulations supporting tax-exempt treatment.",
        "example": "IRC Section 142(a)(6) - solid waste disposal facility; Rev. Proc. 97-13 private activity bond volume cap exemption.",
        "who_needs_it": ["Bond Counsel"],
    },
    # -------------------------------------------------------------------------
    # Risk Factors
    # -------------------------------------------------------------------------
    "risk.technology.description": {
        "description": "Assessment of technology risk including commercial readiness, performance track record, and execution uncertainties.",
        "short_description": "Technology risk assessment",
        "guidance": "Describe the technology's commercial maturity, any pilot/demonstration results, and key execution risks.",
        "example": "The Ultimate Conversion System technology has been demonstrated at pilot scale (10 TPD) over 24 months. Commercial scale-up to 100 TPD introduces execution risk typical of first-of-kind deployments.",
        "who_needs_it": ["Independent Engineer", "Rating Agency", "Investors"],
    },
    "risk.technology.mitigants": {
        "description": "Measures taken to mitigate technology risks including warranties, performance guarantees, and insurance.",
        "short_description": "Technology risk mitigation",
        "guidance": "List specific mitigants: warranties, performance bonds, insurance coverage, technology guarantees.",
        "example": "5-year performance warranty from OEM; $10M performance bond; Technology Performance Insurance covering throughput shortfalls up to 20%.",
        "who_needs_it": ["Independent Engineer", "Rating Agency", "Insurance Broker"],
    },
    "risk.construction.description": {
        "description": "Assessment of construction risks including schedule, budget, contractor experience, and force majeure exposure.",
        "short_description": "Construction risk assessment",
        "guidance": "Describe construction timeline risks, contractor qualifications, and potential cost overrun scenarios.",
        "example": "24-month construction period with EPC contractor experienced in similar facilities. Primary risks: permitting delays (3-6 month impact), supply chain disruptions, weather-related delays.",
        "who_needs_it": ["Independent Engineer", "Rating Agency", "Construction Lender"],
    },
    "risk.construction.mitigants": {
        "description": "Measures taken to mitigate construction risks including bonding, liquidated damages, and contingency.",
        "short_description": "Construction risk mitigation",
        "guidance": "List specific mitigants: performance bonds, completion guarantees, liquidated damages, contingency reserves.",
        "example": "EPC fixed-price contract with $5M performance bond; Liquidated damages of $50K/day for delays beyond 30 days; 15% construction contingency reserve.",
        "who_needs_it": ["Independent Engineer", "Rating Agency", "Bond Counsel"],
    },
    "risk.market.description": {
        "description": "Assessment of market and offtake risks including commodity price volatility, counterparty credit, and demand uncertainty.",
        "short_description": "Market/offtake risk assessment",
        "guidance": "Describe commodity pricing risks, offtake counterparty credit quality, and market demand factors.",
        "example": "Renewable diesel pricing indexed to OPIS diesel; Biochar market emerging with limited price history; Offtake counterparty is investment-grade fuel distributor.",
        "who_needs_it": ["Financial Advisor", "Rating Agency", "Investors"],
    },
    "risk.market.mitigants": {
        "description": "Measures taken to mitigate market risks including offtake agreements, hedging, and pricing floors.",
        "short_description": "Market risk mitigation",
        "guidance": "List specific mitigants: long-term offtake contracts, price floors, credit support, diversification.",
        "example": "7-year renewable diesel offtake with floor price at 85% of OPIS index; Biochar offtake LOI with industrial buyer; Revenue diversification across 3 product streams.",
        "who_needs_it": ["Financial Advisor", "Rating Agency", "Underwriter"],
    },
    "risk.regulatory.description": {
        "description": "Assessment of regulatory risks including permit conditions, environmental compliance, and policy changes.",
        "short_description": "Regulatory risk assessment",
        "guidance": "Describe key regulatory exposures: permit conditions, compliance requirements, policy change scenarios.",
        "example": "Facility subject to air quality permits with emission limits. Changes to LCFS program could affect renewable fuel pricing. No federal solid waste regulatory changes anticipated.",
        "who_needs_it": ["Environmental Consultant", "Bond Counsel", "Rating Agency"],
    },
    "risk.regulatory.mitigants": {
        "description": "Measures taken to mitigate regulatory risks including compliance systems, legal opinions, and regulatory engagement.",
        "short_description": "Regulatory risk mitigation",
        "guidance": "List specific mitigants: compliance monitoring, legal opinions, regulatory relationships, contingency plans.",
        "example": "Continuous emissions monitoring system (CEMS) installed; Bond counsel opinion on tax-exempt eligibility; Quarterly regulatory compliance reporting to trustee.",
        "who_needs_it": ["Environmental Consultant", "Bond Counsel", "Investors"],
    },
    "risk.feedstock.description": {
        "description": "Assessment of feedstock supply risks including availability, quality, pricing, and supply chain reliability.",
        "short_description": "Feedstock supply risk assessment",
        "guidance": "Describe feedstock availability risks, quality variability, supplier concentration, and pricing mechanisms.",
        "example": "Forest biomass supply dependent on timber harvest activity and fire prevention budgets. Multiple suppliers within 50-mile radius. Quality varies by season and source.",
        "who_needs_it": ["Independent Engineer", "Rating Agency", "Operations"],
    },
    "risk.feedstock.mitigants": {
        "description": "Measures taken to mitigate feedstock supply risks including contracts, diversification, and storage.",
        "short_description": "Feedstock risk mitigation",
        "guidance": "List specific mitigants: supply contracts, supplier diversification, storage capacity, alternative feedstock provisions.",
        "example": "10-year supply agreement with primary supplier; Secondary agreements covering 40% of capacity; 30-day feedstock storage on-site; Technology accepts alternative biomass types.",
        "who_needs_it": ["Independent Engineer", "Rating Agency", "Operations"],
    },
}


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
    {"path": "feedstock.characterization", "display_name": "Feedstock Characterization", "value_type": "string", "criticality": "secondary", "min_confidence": 0.70},

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
    {"path": "permitting.buildingzoning.status", "display_name": "Building/Zoning Status", "value_type": "enum", "criticality": "secondary", "min_confidence": 0.80, "allowed_values": ["not-started", "in-progress", "pending-approval", "approved"]},

    # Regulatory
    {"path": "regulatory.tax-status", "display_name": "Tax Status", "value_type": "enum", "criticality": "critical", "min_confidence": 0.90, "allowed_values": ["tax-exempt-idb", "tax-exempt-solidwaste", "taxable"]},
    {"path": "regulatory.tax-exemption.basis", "display_name": "Tax Exemption Basis", "value_type": "string", "criticality": "material", "min_confidence": 0.85},

    # Risk Factors
    {"path": "risk.technology.description", "display_name": "Technology Risk Description", "value_type": "string", "criticality": "material", "min_confidence": 0.75},
    {"path": "risk.technology.mitigants", "display_name": "Technology Risk Mitigants", "value_type": "string", "criticality": "material", "min_confidence": 0.75},
    {"path": "risk.construction.description", "display_name": "Construction Risk Description", "value_type": "string", "criticality": "material", "min_confidence": 0.75},
    {"path": "risk.construction.mitigants", "display_name": "Construction Risk Mitigants", "value_type": "string", "criticality": "material", "min_confidence": 0.75},
    {"path": "risk.market.description", "display_name": "Market Risk Description", "value_type": "string", "criticality": "material", "min_confidence": 0.75},
    {"path": "risk.market.mitigants", "display_name": "Market Risk Mitigants", "value_type": "string", "criticality": "material", "min_confidence": 0.75},
    {"path": "risk.regulatory.description", "display_name": "Regulatory Risk Description", "value_type": "string", "criticality": "material", "min_confidence": 0.75},
    {"path": "risk.regulatory.mitigants", "display_name": "Regulatory Risk Mitigants", "value_type": "string", "criticality": "material", "min_confidence": 0.75},
    {"path": "risk.feedstock.description", "display_name": "Feedstock Risk Description", "value_type": "string", "criticality": "material", "min_confidence": 0.75},
    {"path": "risk.feedstock.mitigants", "display_name": "Feedstock Risk Mitigants", "value_type": "string", "criticality": "material", "min_confidence": 0.75},
]


def get_schema_path_metadata(schema_path: str) -> dict | None:
    """Get metadata for a schema path including description, guidance, and examples."""
    return SCHEMA_PATH_METADATA.get(schema_path)


def get_all_schema_paths_with_metadata() -> list[dict]:
    """Get all schema paths enriched with their metadata."""
    result = []
    for path_def in SCHEMA_PATHS:
        enriched = path_def.copy()
        metadata = SCHEMA_PATH_METADATA.get(path_def["path"], {})
        enriched.update({
            "description": metadata.get("description", ""),
            "short_description": metadata.get("short_description", ""),
            "guidance": metadata.get("guidance", ""),
            "example": metadata.get("example", ""),
            "who_needs_it": metadata.get("who_needs_it", []),
        })
        result.append(enriched)
    return result

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
        "description": "Extracts debt service coverage ratio inputs, operating expenses, EBITDA, and covenants",
        "target_schema_paths": [
            "finmodel.inputs.revenue.annual",
            "finmodel.inputs.revenue.ramp",
            "finmodel.inputs.dscr.minimum",
            "finmodel.outputs.dscrbase",
            "finmodel.outputs.dscrstress",
            "capital.project-cost",
            "capital.equity-contribution",
            "capital.equity-percent",
            "opex.total.annual",
            "opex.margin",
            "ebitda",
        ],
        "system_prompt": """You are extracting financial model inputs for DSCR calculation and operating performance metrics.
DSCR = Net Operating Income / Annual Debt Service. Minimum covenant is typically 1.35x.
EBITDA = Earnings Before Interest, Taxes, Depreciation, and Amortization.
Operating Margin = (Revenue - Operating Expenses) / Revenue.

When extracting from Excel/spreadsheet data:
- Look for labeled rows/columns containing financial metrics
- Common labels: "EBITDA", "Operating Income", "OpEx", "Operating Expenses", "Net Operating Income"
- Values may be annual totals or broken down by year/period
- Extract the steady-state or Year 1 values when multiple periods shown

Extract with precision - these drive bond sizing and credit analysis.""",
        "extraction_prompt_template": """Extract DSCR, operating expenses, and financial model inputs:
1. Projected annual revenue (Year 1 or steady-state)
2. Revenue ramp schedule by year (if available)
3. Total annual operating expenses (OpEx)
4. Operating margin percentage (if stated or calculable)
5. EBITDA (Earnings Before Interest, Taxes, Depreciation & Amortization)
6. Minimum DSCR covenant (typically 1.35x)
7. Base case DSCR
8. Stress case DSCR (at -20% revenue, if available)
9. Total project cost
10. Equity contribution amount
11. Equity percentage of total project cost

IMPORTANT: For spreadsheet/Excel data, look for:
- Row labels like "EBITDA", "Operating Expenses", "OpEx", "Net Operating Income"
- Column headers indicating years or periods
- Summary totals or annual figures
- Financial model output sections

Document content:
{content}

Return JSON with financial metrics, values, units, and source quotes from the document.""",
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
    {
        "item_code": "P4.3",
        "phase": "P4",
        "title": "Risk Factor Documentation",
        "description": "Key risk factors documented with mitigation measures for disclosure",
        "required_schema_paths": [
            "risk.technology.description",
            "risk.construction.description",
            "risk.market.description",
        ],
        "optional_schema_paths": [
            "risk.technology.mitigants",
            "risk.construction.mitigants",
            "risk.market.mitigants",
            "risk.regulatory.description",
            "risk.regulatory.mitigants",
            "risk.feedstock.description",
            "risk.feedstock.mitigants",
        ],
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
# Updated to include all schema paths that appear in disclosure/checklist for consistency
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
                "regulatory.tax-exemption.basis",  # Added for consistency with checklist
                "parties.borrower.name",
                "parties.operator.name",  # Added - appears in disclosure
                "parties.sponsor.name",  # Added - appears in disclosure
                "governance.publicpurpose",  # Added - appears in disclosure/checklist
            ],
            "critical_paths": ["governance.inducement", "regulatory.tax-status"],
        },
        "project_tech": {
            "name": "Project & Technology",
            "weight": 0.20,
            "contributing_paths": [
                "project.canonicaldescription",
                "project.operatingstatus",  # Added - appears in disclosure
                "project.location.jurisdiction",  # Added for completeness
                "project.location.sitecontrol",
                "project.location.coordinates",  # Added for completeness
                "project.designlife",  # Added - was orphaned
                "technology.type",
                "technology.throughput.nameplate",
                "technology.throughput.annual",  # Added - appears in disclosure
                "technology.lifespan",  # Added - appears in disclosure
                "technology.warranty.supplier",  # Added - was orphaned
                "technology.warranty.duration",
                "operations.staffing.direct",  # Added - appears in disclosure
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
                "feedstock.characterization",  # Added - appears in checklist/extractor
                "revenue.commodities.list",
                "revenue.commodities.renewable-diesel",  # Added - appears in disclosure
                "revenue.commodities.biochar",  # Added - appears in disclosure
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
                "cab.finalmaturitydate",  # Added for completeness
                "cab.turbo.enabled",  # Added for completeness
                "cab.conversion.rate",  # Added for completeness
                "finmodel.inputs.revenue.annual",  # Added for completeness
                "finmodel.inputs.revenue.ramp",  # Added for completeness
                "finmodel.inputs.dscr.minimum",
                "finmodel.outputs.dscrbase",
                "finmodel.outputs.dscrstress",  # Added - appears in disclosure
                "capital.project-cost",
                "capital.equipment-cost",  # Added - appears in checklist
                "capital.equity-contribution",
                "capital.equity-percent",  # Added - appears in disclosure
            ],
            "critical_paths": ["cab.accretionrate", "finmodel.outputs.dscrbase", "capital.equity-contribution"],
        },
        "risk_security_slb": {
            "name": "Risk, Security & Permitting",
            "weight": 0.15,
            "contributing_paths": [
                "security.revenue.pledge",
                "security.realproperty",
                "security.equipment.schedule",  # Added for completeness
                "permitting.air-quality.status",
                "permitting.solidwaste.status",
                "permitting.buildingzoning.status",  # Added - appears in checklist/extractor
                "opex.total.annual",
                "opex.margin",  # Added - appears in checklist
                "ebitda",
                # Risk Factor documentation paths
                "risk.technology.description",
                "risk.technology.mitigants",
                "risk.construction.description",
                "risk.construction.mitigants",
                "risk.market.description",
                "risk.market.mitigants",
                "risk.regulatory.description",
                "risk.regulatory.mitigants",
                "risk.feedstock.description",
                "risk.feedstock.mitigants",
            ],
            "critical_paths": ["security.revenue.pledge", "risk.technology.description", "risk.construction.description"],
        },
        "slb_verification": {
            "name": "SLB Verification",
            "weight": 0.10,
            "contributing_paths": [
                "slb.enabled",
                "slb.kpis.shortlist",
                "slb.kpi.1.name",  # Added for completeness
                "slb.kpi.1.baseline.value",  # Added for completeness
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


# =============================================================================
# WP7: DISCLOSURE SECTION TEMPLATES
# =============================================================================
# Per WP7 spec: Template-driven prose synthesis from accepted ExtractedFacts.
# Every sentence traces to fact(s) or is a templated qualifier.

DISCLOSURE_SECTION_TEMPLATES = [
    {
        "section_id": "introduction",
        "title": "Introduction and Summary",
        "section_order": 1,
        "required_fact_paths": [
            "project.canonicaldescription",
            "parties.issuer.name",
            "capital.project-cost",
        ],
        "optional_fact_paths": [
            "parties.borrower.name",
            "cab.enabled",
            "slb.enabled",
            "cab.originalprincipial",
            "security.revenue.pledge",
            "capital.equity-contribution",
            "capital.equity-percent",
        ],
        "minimum_confidence": 0.70,
        "template": """## Introduction and Summary

This document provides preliminary disclosure information for a proposed revenue bond issuance by {parties.issuer.name:TBD: Issuer not specified}.

**Project Overview**

{project.canonicaldescription:TBD: Project description pending}

**Transaction Summary**

The proposed financing contemplates {IF cab.enabled}Capital Appreciation Bonds with an accretion rate of {cab.accretionrate}%{ENDIF}{IF slb.enabled} incorporating Sustainability-Linked Bond features{ENDIF}.

- **Total Project Cost:** ${capital.project-cost:formatted:TBD}
- **Target Financing Amount for Advisor Review:** ${cab.originalprincipial:formatted:TBD}
- **Security:** {IF security.revenue.pledge}Gross revenue pledge of ${security.revenue.pledge:formatted}{ELSE}[TBD: Security structure to be determined]{ENDIF}

{IF capital.equity-percent}
Equity contribution of {capital.equity-percent:percent}% (${capital.equity-contribution:formatted}) has been identified.
{ENDIF}""",
        "conditional_on": None,
        "subsection_templates": [],
    },
    {
        "section_id": "issuer",
        "title": "The Issuer",
        "section_order": 2,
        "required_fact_paths": [
            "parties.issuer.name",
            "parties.issuer.jurisdiction",
            "governance.inducement",
        ],
        "optional_fact_paths": [
            "regulatory.tax-status",
            "governance.publicpurpose",
        ],
        "minimum_confidence": 0.80,
        "template": """## The Issuer

The bonds are expected to be issued by {parties.issuer.name}, an industrial development authority organized under the laws of {parties.issuer.jurisdiction:TBD: Jurisdiction pending}.

**Legal Authority**

{IF governance.inducement == 'adopted'}
An inducement resolution has been adopted by the issuer's governing body.
{ELSEIF governance.inducement == 'proposed'}
An inducement resolution has been proposed and is pending adoption.
{ELSE}
[TBD: Inducement resolution status to be confirmed]
{ENDIF}

**Tax Status**

{IF regulatory.tax-status}
The bonds are expected to be {regulatory.tax-status}. {IF regulatory.tax-status == 'tax-exempt-idb' OR regulatory.tax-status == 'tax-exempt-solidwaste'}Tax exemption is subject to receipt of an unqualified opinion from bond counsel.{ENDIF}
{ELSE}
[TBD: Tax status determination pending bond counsel analysis]
{ENDIF}

{IF governance.publicpurpose}
**Public Purpose**

{governance.publicpurpose}
{ENDIF}""",
        "conditional_on": None,
        "subsection_templates": [],
    },
    {
        "section_id": "project",
        "title": "The Project",
        "section_order": 3,
        "required_fact_paths": ["project.canonicaldescription"],
        "optional_fact_paths": ["project.location.jurisdiction", "project.operatingstatus"],
        "minimum_confidence": 0.70,
        "template": """## The Project

{project.canonicaldescription:TBD: Project description pending}

{IF project.location.jurisdiction}The project is located in {project.location.jurisdiction}.{ENDIF}

{IF project.operatingstatus}Current status: {project.operatingstatus}.{ENDIF}""",
        "conditional_on": None,
        "subsection_templates": [
            {
                "section_id": "project.technology",
                "title": "Technology Description",
                "section_order": 1,
                "required_fact_paths": [
                    "technology.type",
                    "technology.throughput.nameplate",
                ],
                "optional_fact_paths": [
                    "technology.throughput.annual",
                    "technology.lifespan",
                    "technology.warranty.duration",
                ],
                "minimum_confidence": 0.80,
                "template": """### Technology Description

The project utilizes {technology.type:TBD: Technology type not specified} technology with a nameplate capacity of {technology.throughput.nameplate:TBD} tons per day, translating to an annual throughput of approximately {technology.throughput.annual:TBD} tons per year.

The technology has an expected useful life of {technology.lifespan:20} years, supported by manufacturer warranty coverage of {technology.warranty.duration:TBD} years.

{IF technology.type == 'ucs'}
The Ultimate Conversion System employs electromagnetic arc decomposition to convert organic feedstock into multiple commodity outputs including renewable diesel, biochar, and renewable electricity. The system is designed as modular, containerized units enabling deployment flexibility and scalability.
{ENDIF}""",
                "conditional_on": None,
                "subsection_templates": [],
            },
            {
                "section_id": "project.operating",
                "title": "Operating Plan",
                "section_order": 2,
                "required_fact_paths": ["feedstock.type", "feedstock.volume.annual"],
                "optional_fact_paths": [
                    "project.operatingstatus",
                    "operations.staffing.direct",
                ],
                "minimum_confidence": 0.75,
                "template": """### Operating Plan

**Feedstock Supply**

The project is designed to process {feedstock.type:TBD: Feedstock type not specified} feedstock at an annual volume of {feedstock.volume.annual:TBD} tons.

{IF operations.staffing.direct}
**Staffing**

The facility will employ approximately {operations.staffing.direct} direct staff.
{ENDIF}""",
                "conditional_on": None,
                "subsection_templates": [],
            },
            {
                "section_id": "project.permitting",
                "title": "Permitting Status",
                "section_order": 3,
                "required_fact_paths": ["permitting.air-quality.status"],
                "optional_fact_paths": ["permitting.solidwaste.status"],
                "minimum_confidence": 0.75,
                "template": """### Permitting Status

**Air Quality Permit:** {permitting.air-quality.status:TBD: Status pending}

{IF permitting.solidwaste.status}
**Solid Waste Permit:** {permitting.solidwaste.status}
{ENDIF}""",
                "conditional_on": None,
                "subsection_templates": [],
            },
        ],
    },
    {
        "section_id": "security",
        "title": "Security and Sources of Payment",
        "section_order": 4,
        "required_fact_paths": ["security.revenue.pledge"],
        "optional_fact_paths": [
            "security.equipment.schedule",
            "security.realproperty",
            "revenue.gross.annual",
        ],
        "minimum_confidence": 0.80,
        "template": """## Security and Sources of Payment

### Revenue Pledge

The bonds are secured by a {security.revenue.pledge:TBD: Pledge type pending} revenue pledge. {IF revenue.gross.annual}Based on current projections, pledged revenues are estimated at ${revenue.gross.annual:formatted} annually.{ENDIF}

### Collateral Package

{IF security.equipment.schedule}
The bonds are further secured by a first-priority security interest in all project equipment pursuant to a UCC-1 financing statement.
{ELSE}
[TBD: Equipment security arrangements to be documented]
{ENDIF}

{IF security.realproperty}
{security.realproperty}
{ENDIF}

### Reserve Requirements

[TBD: Debt service reserve fund requirements to be determined in consultation with bond counsel and underwriter]""",
        "conditional_on": None,
        "subsection_templates": [],
    },
    {
        "section_id": "financial",
        "title": "Financial Information",
        "section_order": 5,
        "required_fact_paths": ["revenue.gross.annual", "finmodel.outputs.dscrbase"],
        "optional_fact_paths": [
            "opex.total.annual",
            "finmodel.outputs.dscrstress",
            "finmodel.inputs.dscr.minimum",
            "ebitda",
        ],
        "minimum_confidence": 0.80,
        "template": """## Financial Information

### Revenue Projections

Based on the financial model, gross annual revenue is projected at ${revenue.gross.annual:formatted:TBD}.

{IF opex.total.annual}
### Operating Expenses

Annual operating expenses are projected at ${opex.total.annual:formatted}.
{IF ebitda}EBITDA is projected at ${ebitda:formatted}.{ENDIF}
{ENDIF}

### Debt Service Coverage Ratio Analysis

| Scenario | DSCR |
|----------|------|
| Base Case | {finmodel.outputs.dscrbase:TBD}x |
{IF finmodel.outputs.dscrstress}| Stress Case (-20% Revenue) | {finmodel.outputs.dscrstress}x |{ENDIF}
{IF finmodel.inputs.dscr.minimum}| Minimum Covenant | {finmodel.inputs.dscr.minimum}x |{ENDIF}

*Note: All financial figures are projections subject to independent verification.*""",
        "conditional_on": None,
        "subsection_templates": [],
    },
    {
        "section_id": "risk_factors",
        "title": "Risk Factors",
        "section_order": 6,
        "required_fact_paths": [
            "risk.technology.description",
            "risk.construction.description",
            "risk.market.description",
        ],
        "optional_fact_paths": [
            "risk.technology.mitigants",
            "risk.construction.mitigants",
            "risk.market.mitigants",
            "risk.regulatory.description",
            "risk.regulatory.mitigants",
            "risk.feedstock.description",
            "risk.feedstock.mitigants",
            "technology.type",
            "feedstock.supply.mechanism",
            "revenue.offtake.status",
            "permitting.air-quality.status",
        ],
        "minimum_confidence": 0.60,
        "template": """## Risk Factors

Prospective investors should carefully consider the following risk factors in evaluating the bonds:

### Technology Risk

{IF risk.technology.description}
{risk.technology.description}

{IF risk.technology.mitigants}**Mitigants:** {risk.technology.mitigants}{ENDIF}
{ELSEIF technology.type == 'ucs'}
The Ultimate Conversion System technology, while demonstrated at pilot scale, represents an emerging technology. Commercial scale deployment carries execution risk.

[TBD: Technology risk mitigants to be documented]
{ELSE}
[TBD: Technology risk assessment pending]
{ENDIF}

### Construction Risk

{IF risk.construction.description}
{risk.construction.description}

{IF risk.construction.mitigants}**Mitigants:** {risk.construction.mitigants}{ENDIF}
{ELSE}
[TBD: Construction risk assessment pending]

Construction delays or cost overruns could affect project economics and debt service coverage.

[TBD: Construction risk mitigants to be documented]
{ENDIF}

### Market/Offtake Risk

{IF risk.market.description}
{risk.market.description}

{IF risk.market.mitigants}**Mitigants:** {risk.market.mitigants}{ENDIF}
{ELSEIF revenue.offtake.status == 'executed'}
Offtake agreements have been executed, providing contractual certainty for commodity revenues.

[TBD: Market risk details and mitigants to be documented]
{ELSEIF revenue.offtake.status == 'advanced-mou'}
Offtake arrangements are at advanced MOU stage but not yet executed.

[TBD: Market risk details and mitigants to be documented]
{ELSE}
[TBD: Market/offtake risk assessment pending]

Revenue projections assume market pricing for commodity outputs. Actual prices may vary from projections.
{ENDIF}

### Regulatory Risk

{IF risk.regulatory.description}
{risk.regulatory.description}

{IF risk.regulatory.mitigants}**Mitigants:** {risk.regulatory.mitigants}{ENDIF}
{ELSE}
[TBD: Regulatory risk assessment pending]

The project is subject to federal, state, and local regulations. Changes in environmental regulations could affect project operations and economics.
{ENDIF}

### Feedstock Supply Risk

{IF risk.feedstock.description}
{risk.feedstock.description}

{IF risk.feedstock.mitigants}**Mitigants:** {risk.feedstock.mitigants}{ENDIF}
{ELSEIF feedstock.supply.mechanism == 'contract'}
Feedstock supply is secured under binding contract.

[TBD: Feedstock risk details and mitigants to be documented]
{ELSEIF feedstock.supply.mechanism == 'mou'}
Feedstock supply arrangements are documented under MOU.

[TBD: Feedstock risk details and mitigants to be documented]
{ELSE}
[TBD: Feedstock supply risk assessment pending]

Feedstock supply arrangements are in development.
{ENDIF}""",
        "conditional_on": None,
        "subsection_templates": [],
    },
    {
        "section_id": "slb_features",
        "title": "Sustainability-Linked Features",
        "section_order": 7,
        "required_fact_paths": [
            "slb.enabled",
            "slb.kpis.shortlist",
        ],
        "optional_fact_paths": [
            "slb.kpi.1.name",
            "slb.kpi.1.baseline.value",
            "slb.kpi.1.baseline.methodology",
            "slb.kpi.1.verification.method",
            "slb.penalty.stepup.magnitude",
        ],
        "minimum_confidence": 0.80,
        "template": """## Sustainability-Linked Features

This bond issuance incorporates Sustainability-Linked Bond (SLB) features aligned with the International Capital Market Association (ICMA) Sustainability-Linked Bond Principles (2023).

### Key Performance Indicators

The following KPIs have been selected to measure sustainability performance:

{slb.kpis.shortlist:TBD: KPIs pending selection}

{IF slb.kpi.1.name}
**{slb.kpi.1.name}**
- Baseline Value: {slb.kpi.1.baseline.value:TBD}
- Measurement Methodology: {slb.kpi.1.baseline.methodology:TBD: Methodology pending}
- Verification: {slb.kpi.1.verification.method:TBD: Verification method to be established}
{ENDIF}

### Economic Linkage

{IF slb.penalty.stepup.magnitude}
Failure to meet Sustainability Performance Targets will result in a coupon step-up of {slb.penalty.stepup.magnitude} basis points, effective following each observation date.
{ELSE}
[TBD: Step-up magnitude to be determined]
{ENDIF}

### Observation Schedule

Observation dates are scheduled for [TBD: Years 3, 6, and 9 (subject to confirmation)].""",
        "conditional_on": "slb.enabled == True",
        "subsection_templates": [],
    },
]


# =============================================================================
# WP8: INFORMATION REQUEST TEMPLATES
# =============================================================================
# Per WP8 spec: Structured prompts guiding teams to fill gaps with bond-domain context.

INFORMATION_REQUEST_TEMPLATES = [
    {
        "template_id": "issuer_authority_001",
        "title_template": "Inducement Resolution and Tax Status Confirmation",
        "trigger_fact_paths": ["governance.inducement", "regulatory.tax-status"],
        "trigger_phase": "P1",
        "why_it_matters": """Municipal bond issuance requires explicit legal authority from the issuing entity. The inducement resolution formally authorizes the issuer to proceed with bond financing for this specific project. Tax status determination (tax-exempt vs. taxable) affects investor base, pricing, and disclosure requirements. Without these, bond counsel cannot issue required opinions.""",
        "who_needs_it": ["Bond Counsel", "Municipal Advisor", "Underwriter"],
        "when_needed": "Before Phase 1 close; required for advisor engagement",
        "consequences": """Without inducement and tax status determination:
- Cannot engage bond counsel for formal opinion
- Cannot size or price the transaction
- Advisor engagement limited to preliminary discussions only
- Checklist items P1.1-P1.2 remain blocked""",
        "regulatory_reference": "IRC Section 103 (tax exemption); State enabling statutes",
        "guidance_overview": """Obtain formal documentation of the issuer's authorization to proceed with this bond financing and determination of tax status.""",
        "specific_questions": [
            "Has the IDA governing body adopted an inducement resolution for this project?",
            "If not adopted, what is the expected timeline for board consideration?",
            "Has bond counsel provided preliminary guidance on tax-exempt eligibility?",
            "What is the expected tax status (tax-exempt, taxable, or hybrid)?",
        ],
        "data_points_needed": [
            "Inducement resolution date and reference number",
            "IDA board vote record",
            "Bond counsel preliminary tax opinion or memo",
            "Applicable statutory authority cited",
        ],
        "suggested_approach": """1. Request IDA staff to circulate draft inducement resolution
2. Schedule board meeting for formal adoption
3. Engage bond counsel for preliminary tax analysis
4. Document governing body approval in meeting minutes""",
        "common_pitfalls": [
            "Informal board discussion does not constitute inducement",
            "Tax status cannot be assumed based on project type; counsel analysis required",
            "IDA authority may be limited by volume cap allocation",
        ],
        "time_estimate": "2-4 weeks for resolution adoption; 1-2 weeks for tax memo",
        "examples": [
            {
                "description": "Sample inducement resolution language",
                "content_preview": """WHEREAS, [Borrower] has requested assistance from the Authority in financing a [project type] facility... NOW THEREFORE BE IT RESOLVED that the Authority expresses its intent to issue revenue bonds...""",
                "why_acceptable": "Formal resolution with specific project identification and board approval",
                "source_type": "Board Resolution",
            }
        ],
        "acceptable_sources": [
            "Executed board resolution with meeting minutes",
            "Bond counsel preliminary opinion letter",
            "IDA staff confirmation with resolution reference",
        ],
        "minimum_confidence": 0.90,
        "expected_format": "PDF of executed resolution; attorney memo",
        "default_priority": "critical",
        "default_owner": "Sponsor / Legal",
    },
    {
        "template_id": "feedstock_supply_002",
        "title_template": "Feedstock Supply Documentation and Confidence Assessment",
        "trigger_fact_paths": ["feedstock.supply.mechanism", "feedstock.supply.confidence"],
        "trigger_phase": "P2",
        "why_it_matters": """Revenue bonds are repaid from project cash flows. If feedstock supply is uncertain, revenue projections become speculative and bondholders face elevated risk. Rating agencies and investors scrutinize feedstock arrangements as a primary credit driver. For waste-to-energy projects, feedstock is the equivalent of "fuel supply" for a power plant.""",
        "who_needs_it": ["Independent Engineer", "Rating Agency", "Underwriter", "Bond Counsel"],
        "when_needed": "Before Phase 2 close; material for financial model inputs",
        "consequences": """Without documented feedstock supply:
- Financial model revenue assumptions are unsupported
- Independent Engineer cannot certify feasibility
- Rating agencies will apply significant haircuts or decline to rate
- DSCR projections lack credibility
- Dimension 3 (Revenue & Operational Readiness) capped at 2.0/5.0""",
        "regulatory_reference": None,
        "guidance_overview": """Document the arrangements by which the project will obtain sufficient feedstock to operate at projected capacity, including volume commitments, pricing (if applicable), and term.""",
        "specific_questions": [
            "What entities will supply feedstock to the facility?",
            "What is the committed annual volume (tons/year)?",
            "What is the term of supply arrangements (years)?",
            "Is feedstock provided at cost, free, or revenue-generating (tipping fees)?",
            "What is the confidence level of supply (preliminary, advanced, secured)?",
        ],
        "data_points_needed": [
            "Supplier name(s)",
            "Annual volume commitment (tons)",
            "Contract term (years)",
            "Pricing mechanism (tipping fee, cost pass-through, etc.)",
            "Current status (LOI, MOU, executed agreement)",
        ],
        "suggested_approach": """1. Identify all potential feedstock sources (forestry, municipal, commercial)
2. Obtain letters of intent (LOI) or memoranda of understanding (MOU)
3. Progress LOIs to binding agreements where possible
4. Document feedstock characterization (type, moisture content, contamination)
5. Calculate annual availability vs. project requirements""",
        "common_pitfalls": [
            "Verbal commitments without documentation are insufficient",
            "LOIs must specify volume and term, not just 'willingness to discuss'",
            "Feedstock availability studies are not supply commitments",
            "Municipal waste streams may require procurement processes",
        ],
        "time_estimate": "4-8 weeks for LOI execution; 3-6 months for binding agreements",
        "examples": [
            {
                "description": "Acceptable LOI language",
                "content_preview": """[Supplier] hereby confirms its intent to supply up to 25,000 tons per year of forest biomass to [Project] for a minimum term of 10 years, subject to execution of a definitive supply agreement...""",
                "why_acceptable": "Specifies volume, term, and path to binding commitment",
                "source_type": "Letter of Intent",
            }
        ],
        "acceptable_sources": [
            "Executed feedstock supply agreement",
            "Letter of Intent with specific terms",
            "Memorandum of Understanding with volume commitments",
            "Feasibility study feedstock assessment section",
            "Stewardship agreement with land manager",
        ],
        "minimum_confidence": 0.80,
        "expected_format": "Executed LOI/MOU (PDF); supply assessment narrative",
        "default_priority": "high",
        "default_owner": "Operations / Sponsor",
    },
    {
        "template_id": "offtake_revenue_003",
        "title_template": "Commodity Offtake Arrangements and Revenue Validation",
        "trigger_fact_paths": ["revenue.offtake.status", "revenue.commodities.list"],
        "trigger_phase": "P3",
        "why_it_matters": """Bond repayment depends on the project's ability to convert commodities into cash. Offtake agreements represent contracted revenue - the more certain the offtake, the more reliable the debt service coverage. Without documented offtake, revenue projections are market assumptions, not contractual commitments.""",
        "who_needs_it": ["Financial Advisor", "Independent Engineer", "Rating Agency", "Investors"],
        "when_needed": "Before Phase 3 close; required for financial model finalization",
        "consequences": """Without documented offtake:
- Revenue model relies entirely on market assumptions
- DSCR coverage is speculative
- Rating agencies will apply 20-40% revenue haircuts
- Investor appetite limited to higher-risk buyers
- Checklist item P3.2 remains blocked""",
        "regulatory_reference": None,
        "guidance_overview": """Document the arrangements for selling each commodity product, including counterparty, volume, pricing, and term. Focus on the top 2-3 revenue drivers (typically renewable diesel and biochar for UCS projects).""",
        "specific_questions": [
            "Who are the expected purchasers of each commodity output?",
            "What volume commitments exist (gallons, tons, MWh per year)?",
            "What pricing mechanisms apply (fixed, indexed, market)?",
            "What is the term of offtake arrangements?",
            "What is the current status (negotiating, LOI, executed)?",
        ],
        "data_points_needed": [
            "Counterparty name per commodity",
            "Annual volume commitment",
            "Pricing mechanism and illustrative pricing",
            "Contract term (years)",
            "Status (LOI, MOU, executed agreement)",
            "Creditworthiness of counterparty",
        ],
        "suggested_approach": """1. Identify target offtakers by commodity type
2. Execute LOIs with minimum 2 creditworthy counterparties
3. Document pricing basis (index, negotiated, regulatory)
4. Progress LOIs toward binding agreements during P3-P4
5. Obtain counterparty credit information""",
        "common_pitfalls": [
            "Market studies are not offtake commitments",
            "LOIs without pricing mechanisms have limited value",
            "Small or non-creditworthy counterparties require credit support",
            "Volume must align with production projections",
        ],
        "time_estimate": "6-12 weeks for LOI execution; 3-6 months for binding agreements",
        "examples": [
            {
                "description": "Renewable diesel offtake LOI",
                "content_preview": """[Fuel distributor] agrees to purchase up to 2.0 million gallons per year of renewable diesel at OPIS-indexed pricing less $0.15/gallon for logistics, for a term of 7 years...""",
                "why_acceptable": "Specific volume, pricing mechanism, and term",
                "source_type": "Letter of Intent",
            }
        ],
        "acceptable_sources": [
            "Executed offtake agreement",
            "Letter of Intent with volume and pricing terms",
            "MOU with creditworthy counterparty",
            "Regulated rate schedule (for power sales)",
        ],
        "minimum_confidence": 0.80,
        "expected_format": "Executed LOI (PDF); counterparty credit summary",
        "default_priority": "high",
        "default_owner": "Sponsor / Business Development",
    },
    {
        "template_id": "cab_structure_004",
        "title_template": "CAB Terms and Structure Documentation",
        "trigger_fact_paths": [
            "cab.originalprincipial",
            "cab.accretionrate",
            "cab.accretion.period.years",
        ],
        "trigger_phase": "P5",
        "why_it_matters": """Capital Appreciation Bonds are the core debt structure for project finance revenue bonds with construction-period cash flow constraints. The accretion rate, period, and conversion mechanics directly determine bond economics and investor returns. Without defined CAB terms, bond sizing and pricing cannot proceed.""",
        "who_needs_it": ["Municipal Advisor", "Underwriter", "Bond Counsel", "Financial Advisor"],
        "when_needed": "Before Phase 5 close; required for bond structuring",
        "consequences": """Without documented CAB terms:
- Cannot size the bond issuance
- Cannot calculate accreted value at conversion
- Underwriter cannot price or market the bonds
- Checklist item P5.1 remains blocked""",
        "regulatory_reference": "SEC Rule 15c2-12 (disclosure requirements)",
        "guidance_overview": """Document the proposed Capital Appreciation Bond structure including original principal, accretion rate, accretion period, and conversion mechanics.""",
        "specific_questions": [
            "What is the original principal amount proposed?",
            "What accretion rate is contemplated?",
            "How long is the accretion period before conversion to current-pay?",
            "What is the proposed final maturity date?",
            "Is turbo redemption from excess cash flow contemplated?",
        ],
        "data_points_needed": [
            "Original principal amount",
            "Annual accretion rate (%)",
            "Accretion period (years)",
            "Final maturity date",
            "Conversion rate (post-conversion interest rate)",
            "Turbo redemption provisions",
        ],
        "suggested_approach": """1. Work with financial advisor to model CAB scenarios
2. Align accretion period with project construction/ramp
3. Validate accretion rate against market comparables
4. Document in term sheet format
5. Review with bond counsel for tax implications""",
        "common_pitfalls": [
            "Accretion rate must be reasonable for tax-exempt treatment",
            "Accretion period should align with project cash flow development",
            "Turbo redemption provisions affect investor appetite",
        ],
        "time_estimate": "2-4 weeks for financial modeling; 1-2 weeks for documentation",
        "examples": [
            {
                "description": "CAB term sheet excerpt",
                "content_preview": """Original Principal: $25,000,000; Accretion Rate: 5.5% per annum; Accretion Period: 5 years; Maturity Accreted Value: $32,665,000; Final Maturity: 2044...""",
                "why_acceptable": "Complete CAB structure with all key terms",
                "source_type": "Term Sheet",
            }
        ],
        "acceptable_sources": [
            "Financial advisor term sheet",
            "Bond sizing memorandum",
            "Financial model CAB schedule",
            "Preliminary official statement draft",
        ],
        "minimum_confidence": 0.90,
        "expected_format": "Term sheet (PDF); financial model output",
        "default_priority": "critical",
        "default_owner": "Finance / Advisor",
    },
    {
        "template_id": "slb_verification_005",
        "title_template": "SLB KPI Verification Methodology and Third-Party Verifier",
        "trigger_fact_paths": ["slb.kpi.1.verification.method"],
        "trigger_phase": "P5",
        "why_it_matters": """Sustainability-linked bonds lose credibility without independent verification. The 2024 World Bank study found 77% of SLBs have weak verification, enabling issuers to claim greenium without accountability. Credible SLB structures require: (1) measurable KPIs, (2) conservative baselines, (3) external verification, and (4) meaningful penalties. Without verification methodology, SLB features are marketing - not structure.""",
        "who_needs_it": [
            "Second-Party Opinion Provider",
            "ESG Investors",
            "Rating Agency",
            "Bond Counsel",
        ],
        "when_needed": "Before Phase 5 close; required for SLB framework finalization",
        "consequences": """Without verification methodology:
- Second-party opinion provider cannot opine on framework credibility
- ESG-focused investors will decline or discount
- SLB greenium (25-40 bps) is lost
- Reputational risk if targets later disputed
- Checklist item P5.3 remains blocked""",
        "regulatory_reference": "ICMA Sustainability-Linked Bond Principles (2023)",
        "guidance_overview": """Define how each selected KPI will be measured, reported, and independently verified. Identify the third-party verifier and establish verification protocol.""",
        "specific_questions": [
            "What data sources will measure each KPI?",
            "How frequently will data be collected and reported?",
            "Who will serve as the independent third-party verifier?",
            "What verification standard will apply (ISAE 3000, ISO 14064, etc.)?",
            "What is the timeline for annual verification reports?",
        ],
        "data_points_needed": [
            "KPI measurement methodology (data sources, calculation)",
            "Reporting frequency and responsible party",
            "Third-party verifier name and qualifications",
            "Verification standard reference",
            "Verification report timeline",
            "Cost estimate for verification services",
        ],
        "suggested_approach": """1. Document data collection procedures for each KPI
2. Identify qualified third-party verifiers (ESG firms, accounting firms)
3. Request proposals from 2-3 verifiers
4. Select verifier and execute engagement letter
5. Document verification protocol in SLB framework""",
        "common_pitfalls": [
            "Self-reported data without third-party review is insufficient",
            "Verifier must be independent of project sponsor",
            "Verification must occur BEFORE step-up trigger dates",
            "Verification costs must be budgeted in O&M",
        ],
        "time_estimate": "4-6 weeks for verifier selection; 2-3 weeks for protocol documentation",
        "examples": [
            {
                "description": "Verification methodology for waste diversion KPI",
                "content_preview": """Waste diversion rate calculated as: (scale ticket weight IN - residual waste OUT) / scale ticket weight IN. Data source: facility scale tickets with IoT integration. Verification: Annual ISAE 3000 limited assurance engagement by [Verifier Name]...""",
                "why_acceptable": "Specific calculation, data source, and verification standard",
                "source_type": "SLB Framework",
            }
        ],
        "acceptable_sources": [
            "SLB Framework document with verification section",
            "Third-party verifier engagement letter",
            "Verification protocol specification",
            "Data management system documentation",
        ],
        "minimum_confidence": 0.85,
        "expected_format": "SLB Framework section (PDF); verifier engagement letter",
        "default_priority": "high",
        "default_owner": "Sustainability / ESG Advisor",
    },
    {
        "template_id": "financial_model_006",
        "title_template": "Financial Model Outputs and DSCR Coverage",
        "trigger_fact_paths": ["finmodel.outputs.dscrbase", "finmodel.outputs.dscrstress"],
        "trigger_phase": "P5",
        "why_it_matters": """Debt Service Coverage Ratio (DSCR) is the primary credit metric for revenue bonds. It demonstrates whether project cash flows are sufficient to service debt. Minimum DSCR covenants protect bondholders. Without documented DSCR projections, credit analysis cannot proceed and bonds cannot be sized or priced.""",
        "who_needs_it": ["Rating Agency", "Underwriter", "Bond Counsel", "Independent Engineer"],
        "when_needed": "Before Phase 5 close; required for credit analysis",
        "consequences": """Without documented DSCR:
- Rating agencies cannot assign credit rating
- Underwriter cannot price the bonds
- Bond sizing cannot be finalized
- Checklist item P5.2 remains blocked""",
        "regulatory_reference": None,
        "guidance_overview": """Provide financial model outputs demonstrating debt service coverage under base case and stress scenarios. Include DSCR covenant specification.""",
        "specific_questions": [
            "What is the base case DSCR at stabilization?",
            "What is the stress case DSCR (typically -20% revenue)?",
            "What minimum DSCR covenant is proposed?",
            "What is the DSCR trajectory over the bond life?",
        ],
        "data_points_needed": [
            "Base case DSCR by year",
            "Stress case DSCR by year",
            "Minimum DSCR covenant",
            "DSCR calculation methodology",
            "Financial model version and date",
        ],
        "suggested_approach": """1. Complete financial model with revenue and expense assumptions
2. Calculate DSCR for base and stress scenarios
3. Validate DSCR meets market standards (typically 1.35x minimum)
4. Document in financial model output summary""",
        "common_pitfalls": [
            "DSCR below 1.35x may limit investor appetite",
            "Stress case should use reasonable downside scenarios",
            "DSCR must be calculated consistently with bond documents",
        ],
        "time_estimate": "2-4 weeks for financial modeling",
        "examples": [
            {
                "description": "DSCR summary table",
                "content_preview": """Base Case DSCR: Year 6: 1.65x, Year 10: 1.78x, Year 15: 1.92x. Stress Case (-20% Revenue): Year 6: 1.32x, Year 10: 1.42x, Year 15: 1.54x. Minimum Covenant: 1.35x...""",
                "why_acceptable": "Complete DSCR analysis with multiple scenarios",
                "source_type": "Financial Model Output",
            }
        ],
        "acceptable_sources": [
            "Financial model output report",
            "Financial advisor sizing memo",
            "Independent Engineer feasibility study",
        ],
        "minimum_confidence": 0.90,
        "expected_format": "Financial model output (PDF/Excel)",
        "default_priority": "critical",
        "default_owner": "Finance",
    },
    {
        "template_id": "technology_specification_007",
        "title_template": "Technology Specification and Performance Documentation",
        "trigger_fact_paths": ["technology.type", "technology.throughput.nameplate", "technology.throughput.annual"],
        "trigger_phase": "P2",
        "why_it_matters": """Technology specification is fundamental to project feasibility assessment. The conversion technology type determines regulatory requirements, comparable transactions, and risk profile. Throughput capacity directly drives revenue projections and bond sizing. Without documented technology specs, the Independent Engineer cannot certify project feasibility.""",
        "who_needs_it": ["Independent Engineer", "Rating Agency", "Underwriter", "Insurance Broker"],
        "when_needed": "Before Phase 2 close; required for feasibility certification",
        "consequences": """Without documented technology specification:
- Independent Engineer cannot certify project feasibility
- Risk assessment cannot be completed
- Insurance coverage cannot be quoted accurately
- Disclosure document Risk Factors section incomplete
- Checklist item P2.1 remains blocked""",
        "regulatory_reference": None,
        "guidance_overview": """Document the core conversion technology including type, capacity, performance specifications, and warranty coverage.""",
        "specific_questions": [
            "What is the primary conversion technology (UCS, thermal, biological, chemical)?",
            "What is the nameplate throughput capacity (tons per day)?",
            "What is the expected annual throughput (tons per year)?",
            "What is the expected useful life of the technology?",
            "What warranty coverage is provided by the technology supplier?",
        ],
        "data_points_needed": [
            "Technology type classification",
            "Nameplate capacity (TPD)",
            "Annual throughput projection (TPY)",
            "Operating days per year assumption",
            "Capacity factor/availability assumption",
            "Expected useful life (years)",
            "Warranty duration and scope",
        ],
        "suggested_approach": """1. Obtain technology specification sheet from OEM
2. Document nameplate capacity from equipment warranty
3. Calculate annual throughput: nameplate × operating days × availability
4. Confirm useful life from engineering studies
5. Document warranty terms and conditions""",
        "common_pitfalls": [
            "Marketing materials ≠ engineering specifications",
            "Nameplate capacity assumes ideal conditions",
            "Annual throughput must account for maintenance downtime",
            "Warranty coverage may exclude certain failure modes",
        ],
        "time_estimate": "1-2 weeks for documentation compilation",
        "examples": [
            {
                "description": "Technology specification summary",
                "content_preview": """Technology: Ultimate Conversion System (UCS) electromagnetic arc decomposition. Nameplate: 100 TPD. Annual throughput: 33,345 tons (351 days × 95% availability). Useful life: 20 years. Warranty: 5-year performance guarantee from Sierra Energy...""",
                "why_acceptable": "Complete specification with all key parameters",
                "source_type": "Engineering Specification",
            }
        ],
        "acceptable_sources": [
            "OEM technology specification sheet",
            "Equipment warranty documentation",
            "Independent Engineer feasibility report",
            "EPC contract technical schedule",
        ],
        "minimum_confidence": 0.85,
        "expected_format": "Technical specification (PDF); warranty documentation",
        "default_priority": "critical",
        "default_owner": "Technology Provider / Engineering",
    },
    {
        "template_id": "security_collateral_008",
        "title_template": "Security Package and Collateral Structure Documentation",
        "trigger_fact_paths": ["security.revenue.pledge", "security.equipment.schedule", "security.realproperty"],
        "trigger_phase": "P4",
        "why_it_matters": """The security package defines bondholder protection in the event of project underperformance or default. Revenue pledge type (gross vs. net) determines payment priority. Equipment and real property collateral provide recovery value. Without documented security structure, bond counsel cannot draft indenture terms and underwriters cannot market the bonds.""",
        "who_needs_it": ["Bond Counsel", "Underwriter", "Lender's Counsel", "Rating Agency"],
        "when_needed": "Before Phase 4 close; required for bond documentation",
        "consequences": """Without documented security package:
- Bond indenture cannot be drafted
- Rating agencies cannot assess recovery prospects
- Underwriter cannot price the bonds appropriately
- Disclosure document Security section incomplete
- Checklist item P4.1 remains blocked""",
        "regulatory_reference": "UCC Article 9 (security interests); State real property recording statutes",
        "guidance_overview": """Define the collateral package securing the bonds including revenue pledge, equipment security, and real property liens.""",
        "specific_questions": [
            "Is the revenue pledge gross (before OpEx) or net (after OpEx)?",
            "What equipment will be pledged under UCC-1 security agreement?",
            "What real property will be pledged under deed of trust/mortgage?",
            "What is the lien position (first or subordinate)?",
            "Are there any senior or pari passu liens?",
        ],
        "data_points_needed": [
            "Revenue pledge type (gross/net)",
            "Equipment schedule with estimated values",
            "Real property description and acreage",
            "Lien position for each collateral type",
            "Existing liens or encumbrances",
            "Perfection requirements (UCC filing, deed recording)",
        ],
        "suggested_approach": """1. Determine revenue waterfall with financial advisor
2. Compile equipment schedule from vendor contracts
3. Obtain preliminary title report for real property
4. Confirm no existing liens that would prime bondholders
5. Document in term sheet format for bond counsel review""",
        "common_pitfalls": [
            "Revenue pledge type significantly affects bondholder protection",
            "Equipment values depreciate; use conservative estimates",
            "Real property may have existing liens from acquisition financing",
            "UCC perfection requires ongoing maintenance (continuation statements)",
        ],
        "time_estimate": "2-4 weeks for documentation; title search adds 1-2 weeks",
        "examples": [
            {
                "description": "Security package summary",
                "content_preview": """Revenue: Gross revenue pledge (bondholders paid before operating expenses). Equipment: First-priority UCC-1 security interest in all UCS equipment per Schedule A ($45M estimated value). Real Property: First deed of trust on 45-acre site with all improvements...""",
                "why_acceptable": "Complete security package with lien positions and values",
                "source_type": "Term Sheet",
            }
        ],
        "acceptable_sources": [
            "Financial advisor term sheet",
            "Bond counsel security package summary",
            "Preliminary title report",
            "Equipment schedule with values",
        ],
        "minimum_confidence": 0.90,
        "expected_format": "Term sheet section (PDF); title report; equipment schedule",
        "default_priority": "critical",
        "default_owner": "Legal / Finance",
    },
    {
        "template_id": "permitting_status_009",
        "title_template": "Permitting Status and Regulatory Compliance Documentation",
        "trigger_fact_paths": ["permitting.air-quality.status", "permitting.solidwaste.status"],
        "trigger_phase": "P2",
        "why_it_matters": """Permits are regulatory prerequisites for project construction and operation. Air quality permits are typically the longest-lead item for waste-to-energy projects. Solid waste permits authorize feedstock handling. Without clear permitting status, project timeline cannot be established and construction risk cannot be assessed.""",
        "who_needs_it": ["Independent Engineer", "Environmental Consultant", "Rating Agency", "Insurance Broker"],
        "when_needed": "Before Phase 2 close; critical path for project timeline",
        "consequences": """Without documented permitting status:
- Project timeline cannot be reliably established
- Construction risk assessment is incomplete
- Environmental liability cannot be evaluated
- Disclosure document Risk Factors incomplete
- Checklist item P2.4 remains blocked""",
        "regulatory_reference": "Clean Air Act; RCRA; State environmental regulations",
        "guidance_overview": """Document the status of all required environmental and construction permits including application dates, expected approval dates, and any conditions or variances.""",
        "specific_questions": [
            "What is the status of air quality/emissions permits?",
            "What is the status of solid waste handling permits?",
            "Are there any conditional use permits or zoning variances required?",
            "What is the expected timeline for permit approvals?",
            "Are there any permit conditions that affect project design or operations?",
        ],
        "data_points_needed": [
            "Air quality permit type and status",
            "Air quality permit application/approval dates",
            "Solid waste permit type and status",
            "Building/zoning permit status",
            "Any special conditions or variances",
            "Estimated timeline to full permit issuance",
        ],
        "suggested_approach": """1. Engage environmental consultant for permit inventory
2. File applications for longest-lead permits early
3. Track status with regulatory agencies monthly
4. Document any pre-application meetings or guidance
5. Identify and address any permit conditions""",
        "common_pitfalls": [
            "Air permits can take 12-18 months for new facilities",
            "Public comment periods may extend timelines",
            "Permit conditions may require design changes",
            "Solid waste permits may require waste characterization studies",
        ],
        "time_estimate": "Varies: 6-18 months for full permit issuance",
        "examples": [
            {
                "description": "Permitting status summary",
                "content_preview": """Air Quality: Authority to Construct application filed 2024-06-15; public comment period closed 2024-08-30; approval expected Q4 2024. Solid Waste: Permit application submitted to CalRecycle 2024-05-01; facility plan review in progress...""",
                "why_acceptable": "Complete status with dates and timeline",
                "source_type": "Permitting Status Report",
            }
        ],
        "acceptable_sources": [
            "Environmental consultant permitting status report",
            "Permit application receipts",
            "Regulatory agency correspondence",
            "Pre-application meeting notes",
        ],
        "minimum_confidence": 0.85,
        "expected_format": "Permitting status report (PDF); agency correspondence",
        "default_priority": "high",
        "default_owner": "Environmental Consultant / Operations",
    },
    {
        "template_id": "operating_expenses_010",
        "title_template": "Operating Expense Budget and EBITDA Projections",
        "trigger_fact_paths": ["opex.total.annual", "ebitda"],
        "trigger_phase": "P4",
        "why_it_matters": """Operating expenses directly affect cash available for debt service. EBITDA (Earnings Before Interest, Taxes, Depreciation & Amortization) is the primary metric for debt capacity analysis. Without documented OpEx and EBITDA, DSCR calculations are incomplete and bond sizing cannot be finalized.""",
        "who_needs_it": ["Financial Advisor", "Independent Engineer", "Rating Agency", "Underwriter"],
        "when_needed": "Before Phase 4 close; required for DSCR analysis",
        "consequences": """Without documented operating expenses:
- DSCR calculations cannot be completed
- Bond sizing is speculative
- Operating margin analysis incomplete
- Disclosure document Financial section incomplete
- Checklist item P4.2 remains blocked""",
        "regulatory_reference": None,
        "guidance_overview": """Document projected operating expenses by category and calculate EBITDA based on revenue projections less operating costs.""",
        "specific_questions": [
            "What is the projected total annual operating expense?",
            "How are expenses broken down by category (labor, maintenance, utilities, insurance, admin)?",
            "What is the operating margin (Revenue - OpEx) / Revenue?",
            "What is the projected EBITDA?",
            "How do expenses ramp during startup vs. stabilization?",
        ],
        "data_points_needed": [
            "Total annual operating expenses (stabilized)",
            "OpEx breakdown by category",
            "Labor costs (headcount × average cost)",
            "Maintenance and repair reserves",
            "Utilities (power, water, consumables)",
            "Insurance costs",
            "G&A and overhead",
            "Operating margin percentage",
            "EBITDA calculation",
        ],
        "suggested_approach": """1. Develop detailed OpEx model with Independent Engineer
2. Benchmark against comparable facilities
3. Include appropriate contingency (typically 10-15%)
4. Calculate EBITDA: Revenue - Operating Expenses
5. Validate operating margin is sustainable (target 40-60%)""",
        "common_pitfalls": [
            "Underestimating maintenance costs in early years",
            "Insurance costs may be higher for novel technology",
            "Staffing costs should include benefits and turnover",
            "EBITDA must be calculated consistently with bond documents",
        ],
        "time_estimate": "2-4 weeks for detailed OpEx model development",
        "examples": [
            {
                "description": "OpEx and EBITDA summary",
                "content_preview": """Total Annual OpEx: $8.5M. Breakdown: Labor $3.2M, Maintenance $2.1M, Utilities $1.5M, Insurance $0.8M, G&A $0.9M. Operating Margin: 61%. EBITDA: $13.5M (Revenue $22M - OpEx $8.5M)...""",
                "why_acceptable": "Complete OpEx breakdown with EBITDA calculation",
                "source_type": "Financial Model",
            }
        ],
        "acceptable_sources": [
            "Financial model operating expense schedule",
            "Independent Engineer feasibility study",
            "Comparable facility operating data",
            "Insurance broker quotations",
        ],
        "minimum_confidence": 0.85,
        "expected_format": "Financial model output (PDF/Excel); OpEx schedule",
        "default_priority": "high",
        "default_owner": "Finance / Operations",
    },
    {
        "template_id": "slb_kpi_selection_011",
        "title_template": "SLB KPI Selection, Baselines, and Target Setting",
        "trigger_fact_paths": ["slb.kpis.shortlist", "slb.kpi.1.name", "slb.kpi.1.baseline.value"],
        "trigger_phase": "P5",
        "why_it_matters": """Sustainability-Linked Bond credibility depends on selecting material, measurable KPIs with ambitious targets. The 2024 World Bank study found 77% of SLBs have weak KPIs, enabling 'greenwashing'. Proper KPI selection with conservative baselines is essential for second-party opinion and investor confidence. Without defined KPIs and baselines, SLB framework cannot be completed.""",
        "who_needs_it": ["ESG Advisor", "Second-Party Opinion Provider", "Rating Agency", "Investors"],
        "when_needed": "Before Phase 5 close; required for SLB framework",
        "consequences": """Without defined SLB KPIs and baselines:
- Second-party opinion cannot be obtained
- SLB framework document incomplete
- ESG investors will decline or discount
- SLB greenium (25-40 bps) is forfeited
- Disclosure document SLB section incomplete
- Checklist item P5.3 remains blocked""",
        "regulatory_reference": "ICMA Sustainability-Linked Bond Principles (2023)",
        "guidance_overview": """Select 2-4 material KPIs that are measurable, verifiable, and aligned with the project's sustainability impact. Establish conservative baselines and ambitious but achievable targets.""",
        "specific_questions": [
            "What KPIs best represent the project's sustainability impact?",
            "How will each KPI be measured and calculated?",
            "What is the baseline value for each KPI?",
            "What methodology was used to establish baselines?",
            "What are the Sustainability Performance Targets (SPTs) for Years 3, 6, 9?",
        ],
        "data_points_needed": [
            "Shortlist of selected KPIs (2-4)",
            "KPI definitions and units of measure",
            "Baseline values for each KPI",
            "Baseline calculation methodology",
            "Data sources for KPI measurement",
            "SPT targets by observation year",
            "Rationale for target ambition",
        ],
        "suggested_approach": """1. Identify project's primary sustainability impacts
2. Select KPIs aligned with ICMA principles (material, measurable, verifiable)
3. Establish baselines using conservative methodology
4. Set targets that represent meaningful improvement
5. Document in SLB framework format
6. Engage second-party opinion provider for validation""",
        "common_pitfalls": [
            "KPIs must be material to the project, not generic ESG metrics",
            "Baselines must use actual or conservative estimates, not projections",
            "Targets should exceed 'business as usual' trajectory",
            "KPIs requiring complex calculations are harder to verify",
        ],
        "time_estimate": "4-6 weeks for KPI selection and baseline documentation",
        "examples": [
            {
                "description": "SLB KPI summary",
                "content_preview": """KPI 1: Annual Waste Diversion Rate (%). Baseline: 85% (based on comparable UCS facility data). Methodology: (tons processed - residual waste) / tons processed. SPTs: Year 3: 88%, Year 6: 91%, Year 9: 93%. KPI 2: Scope 1 GHG Emissions (tCO2e)...""",
                "why_acceptable": "Complete KPI specification with baseline methodology and targets",
                "source_type": "SLB Framework",
            }
        ],
        "acceptable_sources": [
            "SLB Framework document",
            "ESG advisor KPI recommendation memo",
            "Second-party opinion provider feedback",
            "Comparable facility performance data",
        ],
        "minimum_confidence": 0.90,
        "expected_format": "SLB Framework section (PDF); KPI methodology documentation",
        "default_priority": "critical",
        "default_owner": "Sustainability / ESG Advisor",
    },
    {
        "template_id": "project_description_012",
        "title_template": "Canonical Project Description and Overview",
        "trigger_fact_paths": ["project.canonicaldescription"],
        "trigger_phase": "P1",
        "why_it_matters": """The canonical project description appears in all disclosure documents, advisor materials, and rating presentations. It must accurately describe the project in 1-2 neutral sentences without promotional language. This description frames how all stakeholders understand the project. Without a finalized description, disclosure documents cannot be drafted.""",
        "who_needs_it": ["Bond Counsel", "Municipal Advisor", "Underwriter", "Rating Agency"],
        "when_needed": "Before Phase 1 close; foundational for all documents",
        "consequences": """Without canonical project description:
- Disclosure document introduction cannot be written
- Marketing materials lack consistency
- Rating presentations have no standard project overview
- Advisor handoff pack incomplete
- All disclosure sections referencing project description show [TBD]""",
        "regulatory_reference": "SEC Rule 15c2-12 (disclosure standards)",
        "guidance_overview": """Develop a concise 1-2 sentence description that captures the project type, location, technology, capacity, and primary outputs. Avoid promotional language.""",
        "specific_questions": [
            "What type of facility is being developed?",
            "Where is the project located (city, county, state)?",
            "What technology does the project employ?",
            "What is the processing capacity?",
            "What are the primary outputs/products?",
        ],
        "data_points_needed": [
            "Facility type (e.g., waste-to-energy, biomass conversion)",
            "Location (jurisdiction)",
            "Technology name",
            "Capacity (tons per day or year)",
            "Primary outputs (products generated)",
        ],
        "suggested_approach": """1. Draft description following neutral, factual tone
2. Include: facility type, location, technology, capacity, outputs
3. Review with bond counsel for appropriate disclosure language
4. Avoid promotional claims or forward-looking statements
5. Finalize as standard description for all materials""",
        "common_pitfalls": [
            "Descriptions should be factual, not promotional",
            "Avoid superlatives ('revolutionary', 'world-class', etc.)",
            "Don't include financial projections in description",
            "Description should be technology-neutral where appropriate",
        ],
        "time_estimate": "1-2 weeks for drafting and legal review",
        "examples": [
            {
                "description": "Canonical project description",
                "content_preview": """A 100 TPD Ultimate Conversion System facility in El Dorado County, California that converts forest biomass into renewable diesel, biochar, and electricity, addressing regional wildfire fuel load while generating renewable energy products.""",
                "why_acceptable": "Factual, neutral, includes all key elements",
                "source_type": "Project Summary",
            }
        ],
        "acceptable_sources": [
            "Project development summary",
            "Bond counsel-reviewed description",
            "IDA board presentation materials",
            "Feasibility study executive summary",
        ],
        "minimum_confidence": 0.85,
        "expected_format": "1-2 sentence description; bond counsel approval",
        "default_priority": "high",
        "default_owner": "Sponsor / Legal",
    },
    {
        "template_id": "risk_factors_013",
        "title_template": "Risk Factor Assessment and Mitigation Documentation",
        "trigger_fact_paths": [
            "risk.technology.description",
            "risk.construction.description",
            "risk.market.description",
            "risk.regulatory.description",
            "risk.feedstock.description",
        ],
        "trigger_phase": "P4",
        "why_it_matters": """Risk factor disclosure is required under SEC Rule 15c2-12 for municipal bond offerings. Investors and rating agencies rely on comprehensive risk identification and mitigation documentation to assess creditworthiness. Without documented risk factors, the disclosure document Risk Factors section cannot be completed, and the official statement will contain incomplete or generic TBD placeholders that undermine investor confidence.""",
        "who_needs_it": ["Bond Counsel", "Underwriter", "Rating Agency", "Investors", "Municipal Advisor"],
        "when_needed": "Before Phase 4 close; required for disclosure document completion",
        "consequences": """Without documented risk factors:
- Disclosure document Risk Factors section remains TBD
- Rating agencies cannot complete credit analysis
- Bond counsel cannot certify disclosure adequacy
- Underwriter due diligence incomplete
- Investors receive insufficient information for investment decisions
- Checklist item P4.3 remains blocked
- Overall readiness score capped in Risk dimension""",
        "regulatory_reference": "SEC Rule 15c2-12; MSRB Rule G-17 (fair dealing)",
        "guidance_overview": """Document the material risks associated with the project and bonds, including technology, construction, market/offtake, regulatory, and feedstock supply risks. For each risk category, describe both the risk exposure and the specific mitigation measures in place or planned.""",
        "specific_questions": [
            "What technology risks exist and how are they mitigated (warranties, insurance, performance guarantees)?",
            "What construction risks exist and how are they mitigated (bonding, liquidated damages, contingency)?",
            "What market/offtake risks exist and how are they mitigated (contracts, hedging, diversification)?",
            "What regulatory risks exist and how are they mitigated (compliance systems, legal opinions)?",
            "What feedstock supply risks exist and how are they mitigated (contracts, storage, alternatives)?",
        ],
        "data_points_needed": [
            "Technology risk description and commercial maturity assessment",
            "Technology risk mitigants (warranties, performance bonds, insurance)",
            "Construction risk description including timeline and budget exposure",
            "Construction risk mitigants (EPC terms, bonding, contingency reserves)",
            "Market risk description including pricing and counterparty exposure",
            "Market risk mitigants (offtake contracts, price floors, credit support)",
            "Regulatory risk description including permit conditions and policy exposure",
            "Regulatory risk mitigants (compliance monitoring, legal opinions)",
            "Feedstock risk description including availability and quality factors",
            "Feedstock risk mitigants (supply contracts, diversification, storage)",
        ],
        "suggested_approach": """1. Conduct comprehensive risk identification workshop with project team
2. Categorize risks by type (technology, construction, market, regulatory, feedstock)
3. Assess probability and impact for each identified risk
4. Document specific mitigation measures for material risks
5. Review with Independent Engineer for technical risks
6. Review with bond counsel for disclosure adequacy
7. Format for inclusion in Official Statement Risk Factors section""",
        "common_pitfalls": [
            "Generic risk language without project-specific detail is insufficient",
            "Mitigants must be concrete and verifiable, not aspirational",
            "Technology risk requires honest assessment of commercial maturity",
            "Construction risk should reflect actual EPC contract terms",
            "Market risk should address both pricing and counterparty exposure",
            "Regulatory risk should identify specific permit conditions",
            "Feedstock risk should address concentration and availability",
        ],
        "time_estimate": "2-4 weeks for comprehensive risk assessment and documentation",
        "examples": [
            {
                "description": "Technology risk documentation",
                "content_preview": """Technology Risk: The UCS technology has been demonstrated at pilot scale (10 TPD) for 24 months. Commercial scale-up to 100 TPD introduces first-of-kind execution risk. Mitigants: 5-year OEM performance warranty covering throughput of 95%; $10M performance bond; Technology Performance Insurance covering 20% throughput shortfall.""",
                "why_acceptable": "Specific risk identification with quantified mitigants",
                "source_type": "Risk Assessment Memorandum",
            },
            {
                "description": "Construction risk documentation",
                "content_preview": """Construction Risk: 24-month construction period with fixed-price EPC contract. Primary exposures: permitting delays (3-6 month potential), supply chain disruptions, weather. Mitigants: $5M performance bond; LD of $50K/day for delays >30 days; 15% contingency reserve in project budget.""",
                "why_acceptable": "Identifies specific risks with quantified mitigation measures",
                "source_type": "Risk Assessment Memorandum",
            },
        ],
        "acceptable_sources": [
            "Independent Engineer risk assessment section",
            "Bond counsel risk disclosure draft",
            "EPC contract risk allocation summary",
            "Insurance broker coverage summary",
            "Project risk register with mitigants",
            "Rating agency presentation risk section",
        ],
        "minimum_confidence": 0.75,
        "expected_format": "Risk assessment memorandum (PDF); draft Risk Factors section",
        "default_priority": "high",
        "default_owner": "Risk Manager / Sponsor",
    },
]


# Owner mapping for information request assignment
OWNER_MAP = {
    "project.*": "Sponsor / Legal",
    "parties.*": "Sponsor / Legal",
    "governance.*": "Sponsor / Legal",
    "technology.*": "Technology Provider / Engineering",
    "operations.*": "Operations / Sponsor",
    "feedstock.*": "Operations / Sponsor",
    "revenue.*": "Finance / Sponsor",
    "finmodel.*": "Finance",
    "security.*": "Legal / Finance",
    "permitting.*": "Environmental Consultant / Operations",
    "slb.*": "Sustainability / ESG Advisor",
    "risk.*": "Risk Manager / Sponsor",
    "cab.*": "Finance / Advisor",
    "capital.*": "Finance",
    "opex.*": "Finance / Operations",
    "ebitda": "Finance",
    "regulatory.*": "Legal / Bond Counsel",
}


# TBD reason mappings for disclosure synthesis
TBD_REASONS = {
    # Project Foundation
    "project.canonicaldescription": "Project description not yet finalized",
    "project.location.jurisdiction": "Project jurisdiction not yet confirmed",
    "project.location.sitecontrol": "Site control status not yet documented",
    "project.location.coordinates": "Site coordinates not yet provided",
    "project.operatingstatus": "Operating status not yet determined",
    "project.designlife": "Design life not yet specified",

    # Parties & Governance
    "governance.inducement": "Inducement resolution status not yet confirmed",
    "governance.publicpurpose": "Public purpose statement not yet documented",
    "parties.issuer.name": "Issuer entity not yet identified",
    "parties.issuer.jurisdiction": "Issuer jurisdiction not yet confirmed",
    "parties.borrower.name": "Borrower entity not yet identified",
    "parties.operator.name": "Operator entity not yet identified",
    "parties.sponsor.name": "Sponsor entity not yet identified",

    # Technology & Operations
    "technology.type": "Technology type not specified",
    "technology.throughput.nameplate": "Throughput capacity not yet confirmed",
    "technology.throughput.annual": "Annual throughput not yet calculated",
    "technology.lifespan": "Technology lifespan not yet specified",
    "technology.warranty.supplier": "Warranty supplier not yet identified",
    "technology.warranty.duration": "Warranty coverage not yet documented",
    "operations.staffing.direct": "Staffing plan not yet finalized",

    # Feedstock & Supply
    "feedstock.type": "Feedstock type not specified",
    "feedstock.volume.annual": "Annual feedstock volume not yet confirmed",
    "feedstock.supply.mechanism": "Supply mechanism not yet documented",
    "feedstock.supply.confidence": "Supply confidence level not yet assessed",
    "feedstock.characterization": "Feedstock characterization not yet completed",

    # Revenue Model
    "revenue.commodities.list": "Commodity revenue streams not yet documented",
    "revenue.commodities.renewable-diesel": "Renewable diesel revenue not yet projected",
    "revenue.commodities.biochar": "Biochar revenue not yet projected",
    "revenue.gross.annual": "Annual revenue not yet projected",
    "revenue.offtake.status": "Offtake status not yet confirmed",

    # Operating Expenses
    "opex.total.annual": "Operating expenses not yet projected",
    "opex.margin": "Operating margin not yet calculated",
    "ebitda": "EBITDA not yet calculated",

    # Capital Structure
    "capital.project-cost": "Total project cost not yet finalized",
    "capital.equipment-cost": "Equipment cost not yet finalized",
    "capital.equity-contribution": "Equity contribution not yet confirmed",
    "capital.equity-percent": "Equity percentage not yet calculated",

    # CAB Terms
    "cab.enabled": "CAB structure decision not yet finalized",
    "cab.originalprincipial": "Bond principal not yet sized",
    "cab.accretionrate": "Accretion rate not yet determined",
    "cab.accretion.period.years": "Accretion period not yet defined",
    "cab.finalmaturitydate": "Final maturity date not yet determined",
    "cab.turbo.enabled": "Turbo redemption decision not yet made",
    "cab.conversion.rate": "Conversion rate not yet determined",

    # Financial Model & DSCR
    "finmodel.inputs.revenue.annual": "Projected annual revenue not yet modeled",
    "finmodel.inputs.revenue.ramp": "Revenue ramp schedule not yet defined",
    "finmodel.inputs.dscr.minimum": "DSCR covenant not yet specified",
    "finmodel.outputs.dscrbase": "Base DSCR not yet calculated",
    "finmodel.outputs.dscrstress": "Stress DSCR not yet calculated",

    # SLB KPIs
    "slb.enabled": "SLB structure decision not yet finalized",
    "slb.kpis.shortlist": "KPIs not yet selected",
    "slb.kpi.1.name": "KPI 1 name not yet defined",
    "slb.kpi.1.baseline.value": "KPI 1 baseline not yet established",
    "slb.kpi.1.baseline.methodology": "KPI 1 methodology not yet documented",
    "slb.kpi.1.verification.method": "Verification method not yet established",
    "slb.penalty.stepup.magnitude": "Step-up magnitude not yet determined",

    # Security & Collateral
    "security.realproperty": "Real property security not yet documented",
    "security.equipment.schedule": "Equipment security not yet documented",
    "security.revenue.pledge": "Revenue pledge structure not yet defined",

    # Permitting
    "permitting.air-quality.status": "Air permit status not yet confirmed",
    "permitting.solidwaste.status": "Solid waste permit status not yet confirmed",
    "permitting.buildingzoning.status": "Building/zoning permit status not yet confirmed",

    # Regulatory
    "regulatory.tax-status": "Tax status determination pending bond counsel analysis",
    "regulatory.tax-exemption.basis": "Tax exemption basis not yet documented",

    # Risk Factors
    "risk.technology.description": "Technology risk assessment not yet documented",
    "risk.technology.mitigants": "Technology risk mitigants not yet documented",
    "risk.construction.description": "Construction risk assessment not yet documented",
    "risk.construction.mitigants": "Construction risk mitigants not yet documented",
    "risk.market.description": "Market/offtake risk assessment not yet documented",
    "risk.market.mitigants": "Market risk mitigants not yet documented",
    "risk.regulatory.description": "Regulatory risk assessment not yet documented",
    "risk.regulatory.mitigants": "Regulatory risk mitigants not yet documented",
    "risk.feedstock.description": "Feedstock supply risk assessment not yet documented",
    "risk.feedstock.mitigants": "Feedstock risk mitigants not yet documented",
}


# Complete playbook configuration
UCS_PLAYBOOK_CONFIG = {
    "name": "UCS CAB+SLB Revenue Bond",
    "version": "0.3.0",  # Incremented for WP7/WP8 templates
    "description": "Bond Intelligence Configuration Playbook for UCS Waste-to-Energy Capital Appreciation + Sustainability-Linked Bond structures. Defines extraction schema, checklist phases P1-P6, readiness scoring, disclosure synthesis templates (WP7), and information request templates (WP8) for El Dorado, California IDA-style revenue bond facilities.",
    "bond_archetype": "UCS Waste-to-Energy CAB+SLB Revenue Bond",
    "schema_paths": SCHEMA_PATHS,
    "extractors": EXTRACTORS,
    "checklist_items": CHECKLIST_ITEMS,
    "readiness_config": READINESS_CONFIG,
    # WP7: Disclosure Synthesis Engine
    "disclosure_templates": DISCLOSURE_SECTION_TEMPLATES,
    "tbd_reasons": TBD_REASONS,
    # WP8: Information Request System
    "information_request_templates": INFORMATION_REQUEST_TEMPLATES,
    "owner_map": OWNER_MAP,
}
