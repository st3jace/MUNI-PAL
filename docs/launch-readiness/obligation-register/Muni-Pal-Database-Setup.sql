BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> a1b2c3d4e5f6

CREATE TABLE users (
    id UUID NOT NULL, 
    email VARCHAR(255) NOT NULL, 
    hashed_password VARCHAR(255) NOT NULL, 
    full_name VARCHAR(255), 
    organization VARCHAR(255), 
    is_active BOOLEAN DEFAULT 'true' NOT NULL, 
    is_superuser BOOLEAN DEFAULT 'false' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE TABLE playbooks (
    id UUID NOT NULL, 
    name VARCHAR(100) NOT NULL, 
    version VARCHAR(20) NOT NULL, 
    description TEXT NOT NULL, 
    bond_archetype VARCHAR(255) NOT NULL, 
    is_active BOOLEAN DEFAULT 'true' NOT NULL, 
    is_default BOOLEAN DEFAULT 'false' NOT NULL, 
    schema_paths JSON DEFAULT '[]' NOT NULL, 
    extractors JSON DEFAULT '[]' NOT NULL, 
    checklist_items JSON DEFAULT '[]' NOT NULL, 
    readiness_config JSON DEFAULT '{}' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id)
);

CREATE TABLE projects (
    id UUID NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    description TEXT, 
    issuer_name VARCHAR(255), 
    project_location VARCHAR(500), 
    target_bond_amount FLOAT, 
    owner_id UUID NOT NULL, 
    playbook_id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(owner_id) REFERENCES users (id), 
    FOREIGN KEY(playbook_id) REFERENCES playbooks (id)
);

CREATE TABLE artifacts (
    id UUID NOT NULL, 
    filename VARCHAR(255) NOT NULL, 
    display_name VARCHAR(255), 
    artifact_type VARCHAR(20) NOT NULL, 
    mime_type VARCHAR(100) NOT NULL, 
    file_size_bytes INTEGER NOT NULL, 
    storage_path VARCHAR(500) NOT NULL, 
    is_processed BOOLEAN DEFAULT 'false' NOT NULL, 
    processing_error TEXT, 
    project_id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id)
);

CREATE INDEX ix_artifacts_project_id ON artifacts (project_id);

CREATE TABLE chunks (
    id UUID NOT NULL, 
    chunk_type VARCHAR(20) NOT NULL, 
    sequence_number INTEGER NOT NULL, 
    page_number INTEGER, 
    sheet_name VARCHAR(100), 
    section_title VARCHAR(255), 
    text_content TEXT, 
    content_hash VARCHAR(64) NOT NULL, 
    has_image BOOLEAN DEFAULT 'false' NOT NULL, 
    artifact_id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(artifact_id) REFERENCES artifacts (id)
);

CREATE INDEX ix_chunks_artifact_id ON chunks (artifact_id);

CREATE TABLE extraction_jobs (
    id UUID NOT NULL, 
    job_type VARCHAR(100) NOT NULL, 
    target_schema_paths JSON DEFAULT '[]' NOT NULL, 
    artifact_ids JSON NOT NULL, 
    chunk_ids JSON, 
    status VARCHAR(20) DEFAULT 'queued' NOT NULL, 
    started_at TIMESTAMP WITH TIME ZONE, 
    completed_at TIMESTAMP WITH TIME ZONE, 
    total_chunks INTEGER DEFAULT '0' NOT NULL, 
    processed_chunks INTEGER DEFAULT '0' NOT NULL, 
    facts_extracted INTEGER DEFAULT '0' NOT NULL, 
    error_message TEXT, 
    retry_count INTEGER DEFAULT '0' NOT NULL, 
    celery_task_id VARCHAR(255), 
    project_id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id)
);

CREATE INDEX ix_extraction_jobs_project_id ON extraction_jobs (project_id);

CREATE INDEX ix_extraction_jobs_status ON extraction_jobs (status);

CREATE TABLE extracted_facts (
    id UUID NOT NULL, 
    schema_path VARCHAR(255) NOT NULL, 
    criticality VARCHAR(20) DEFAULT 'secondary' NOT NULL, 
    value JSON NOT NULL, 
    value_type VARCHAR(50) DEFAULT 'string' NOT NULL, 
    unit VARCHAR(50), 
    confidence_score FLOAT NOT NULL, 
    confidence_rationale TEXT, 
    review_status VARCHAR(20) DEFAULT 'pending' NOT NULL, 
    reviewed_by UUID, 
    reviewed_at TIMESTAMP WITH TIME ZONE, 
    review_note TEXT, 
    original_value JSON, 
    project_id UUID NOT NULL, 
    extraction_job_id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(extraction_job_id) REFERENCES extraction_jobs (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    FOREIGN KEY(reviewed_by) REFERENCES users (id)
);

CREATE INDEX ix_extracted_facts_project_id ON extracted_facts (project_id);

CREATE INDEX ix_extracted_facts_schema_path ON extracted_facts (schema_path);

CREATE INDEX ix_extracted_facts_review_status ON extracted_facts (review_status);

CREATE TABLE fact_chunks (
    fact_id UUID NOT NULL, 
    chunk_id UUID NOT NULL, 
    excerpt TEXT, 
    PRIMARY KEY (fact_id, chunk_id), 
    FOREIGN KEY(chunk_id) REFERENCES chunks (id), 
    FOREIGN KEY(fact_id) REFERENCES extracted_facts (id)
);

CREATE TABLE fact_revisions (
    id UUID NOT NULL, 
    revision_number INTEGER NOT NULL, 
    previous_value JSON, 
    new_value JSON NOT NULL, 
    previous_status VARCHAR(20), 
    new_status VARCHAR(20) NOT NULL, 
    changed_by_id UUID NOT NULL, 
    change_reason TEXT, 
    fact_id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(changed_by_id) REFERENCES users (id), 
    FOREIGN KEY(fact_id) REFERENCES extracted_facts (id)
);

CREATE INDEX ix_fact_revisions_fact_id ON fact_revisions (fact_id);

CREATE TABLE evidence_links (
    id UUID NOT NULL, 
    link_type VARCHAR(50) NOT NULL, 
    target_id VARCHAR(100) NOT NULL, 
    contribution_weight FLOAT DEFAULT '1.0' NOT NULL, 
    fact_id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(fact_id) REFERENCES extracted_facts (id)
);

CREATE INDEX ix_evidence_links_fact_id ON evidence_links (fact_id);

CREATE TABLE deliverable_packs (
    id UUID NOT NULL, 
    title VARCHAR(255) NOT NULL, 
    generated_for VARCHAR(255) NOT NULL, 
    is_complete BOOLEAN DEFAULT 'false' NOT NULL, 
    generation_started_at TIMESTAMP WITH TIME ZONE, 
    generation_completed_at TIMESTAMP WITH TIME ZONE, 
    include_sections JSON DEFAULT '[1,2,3,4,5,6,7,8,9]' NOT NULL, 
    include_appendices BOOLEAN DEFAULT 'true' NOT NULL, 
    sections JSON DEFAULT '[]' NOT NULL, 
    facts_included_count INTEGER DEFAULT '0' NOT NULL, 
    readiness_score_at_generation FLOAT, 
    warnings JSON DEFAULT '[]' NOT NULL, 
    pdf_storage_path VARCHAR(500), 
    celery_task_id VARCHAR(255), 
    project_id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id)
);

CREATE INDEX ix_deliverable_packs_project_id ON deliverable_packs (project_id);

INSERT INTO alembic_version (version_num) VALUES ('a1b2c3d4e5f6') RETURNING alembic_version.version_num;

-- Running upgrade a1b2c3d4e5f6 -> b2c3d4e5f6a7

INSERT INTO playbooks (
                id, name, version, description, bond_archetype,
                is_active, is_default,
                schema_paths, extractors, checklist_items, readiness_config,
                created_at, updated_at
            ) VALUES (
                '00000000-0000-0000-0000-000000000001', 'UCS CAB+SLB Revenue Bond', '0.3.0', 'Bond Intelligence Configuration Playbook for UCS Waste-to-Energy Capital Appreciation + Sustainability-Linked Bond structures. Defines extraction schema, checklist phases P1-P6, readiness scoring, disclosure synthesis templates (WP7), and information request templates (WP8) for El Dorado, California IDA-style revenue bond facilities.', 'UCS Waste-to-Energy CAB+SLB Revenue Bond',
                true, true,
                '[{"path": "project.canonicaldescription", "display_name": "Project Description", "value_type": "string", "criticality": "material", "min_confidence": 0.7}, {"path": "project.location.jurisdiction", "display_name": "Jurisdiction", "value_type": "string", "criticality": "secondary", "min_confidence": 0.7}, {"path": "project.location.sitecontrol", "display_name": "Site Control", "value_type": "enum", "criticality": "material", "min_confidence": 0.8, "allowed_values": ["purchase", "lease", "option", "loi"]}, {"path": "project.location.coordinates", "display_name": "Coordinates", "value_type": "string", "criticality": "secondary", "min_confidence": 0.65}, {"path": "project.operatingstatus", "display_name": "Operating Status", "value_type": "enum", "criticality": "material", "min_confidence": 0.75, "allowed_values": ["planned", "under-construction", "operational"]}, {"path": "project.designlife", "display_name": "Design Life", "value_type": "number", "unit": "years", "criticality": "secondary", "min_confidence": 0.7}, {"path": "parties.issuer.name", "display_name": "Issuer Name", "value_type": "string", "criticality": "material", "min_confidence": 0.8}, {"path": "parties.issuer.jurisdiction", "display_name": "Issuer Jurisdiction", "value_type": "string", "criticality": "material", "min_confidence": 0.8}, {"path": "parties.borrower.name", "display_name": "Borrower Name", "value_type": "string", "criticality": "material", "min_confidence": 0.8}, {"path": "parties.operator.name", "display_name": "Operator Name", "value_type": "string", "criticality": "material", "min_confidence": 0.8}, {"path": "parties.sponsor.name", "display_name": "Sponsor Name", "value_type": "string", "criticality": "secondary", "min_confidence": 0.75}, {"path": "governance.inducement", "display_name": "Inducement Status", "value_type": "enum", "criticality": "critical", "min_confidence": 0.9, "allowed_values": ["draft", "proposed", "adopted"]}, {"path": "governance.publicpurpose", "display_name": "Public Purpose", "value_type": "string", "criticality": "material", "min_confidence": 0.7}, {"path": "technology.type", "display_name": "Technology Type", "value_type": "enum", "criticality": "material", "min_confidence": 0.85, "allowed_values": ["ucs", "thermal", "biological", "chemical"]}, {"path": "technology.throughput.nameplate", "display_name": "Nameplate Throughput", "value_type": "number", "unit": "tons/day", "criticality": "critical", "min_confidence": 0.85}, {"path": "technology.throughput.annual", "display_name": "Annual Throughput", "value_type": "number", "unit": "tons/year", "criticality": "material", "min_confidence": 0.8}, {"path": "technology.lifespan", "display_name": "Technology Lifespan", "value_type": "number", "unit": "years", "criticality": "secondary", "min_confidence": 0.75}, {"path": "technology.warranty.supplier", "display_name": "Warranty Supplier", "value_type": "string", "criticality": "secondary", "min_confidence": 0.7}, {"path": "technology.warranty.duration", "display_name": "Warranty Duration", "value_type": "number", "unit": "years", "criticality": "material", "min_confidence": 0.8}, {"path": "operations.staffing.direct", "display_name": "Direct Staffing", "value_type": "number", "unit": "headcount", "criticality": "material", "min_confidence": 0.75}, {"path": "feedstock.type", "display_name": "Feedstock Type", "value_type": "enum", "criticality": "material", "min_confidence": 0.8, "allowed_values": ["forestry", "msw", "agricultural", "mixed"]}, {"path": "feedstock.volume.annual", "display_name": "Annual Feedstock Volume", "value_type": "number", "unit": "tons", "criticality": "material", "min_confidence": 0.8}, {"path": "feedstock.supply.mechanism", "display_name": "Supply Mechanism", "value_type": "enum", "criticality": "critical", "min_confidence": 0.85, "allowed_values": ["contract", "mou", "letter-of-intent", "assessment"]}, {"path": "feedstock.supply.confidence", "display_name": "Supply Confidence", "value_type": "enum", "criticality": "critical", "min_confidence": 0.85, "allowed_values": ["preliminary", "advanced", "secured"]}, {"path": "feedstock.characterization", "display_name": "Feedstock Characterization", "value_type": "string", "criticality": "secondary", "min_confidence": 0.7}, {"path": "revenue.commodities.list", "display_name": "Commodity Revenue List", "value_type": "array", "criticality": "critical", "min_confidence": 0.85}, {"path": "revenue.commodities.renewable-diesel", "display_name": "Renewable Diesel Revenue", "value_type": "currency", "unit": "USD/year", "criticality": "material", "min_confidence": 0.8}, {"path": "revenue.commodities.biochar", "display_name": "Biochar Revenue", "value_type": "currency", "unit": "USD/year", "criticality": "secondary", "min_confidence": 0.75}, {"path": "revenue.offtake.status", "display_name": "Offtake Status", "value_type": "enum", "criticality": "critical", "min_confidence": 0.9, "allowed_values": ["executed", "advanced-mou", "letter-of-intent", "negotiating"]}, {"path": "revenue.gross.annual", "display_name": "Gross Annual Revenue", "value_type": "currency", "unit": "USD", "criticality": "critical", "min_confidence": 0.85}, {"path": "opex.total.annual", "display_name": "Total Annual OpEx", "value_type": "currency", "unit": "USD", "criticality": "material", "min_confidence": 0.8}, {"path": "opex.margin", "display_name": "Operating Margin", "value_type": "percentage", "criticality": "material", "min_confidence": 0.8}, {"path": "ebitda", "display_name": "EBITDA", "value_type": "currency", "unit": "USD", "criticality": "critical", "min_confidence": 0.85}, {"path": "capital.project-cost", "display_name": "Total Project Cost", "value_type": "currency", "unit": "USD", "criticality": "critical", "min_confidence": 0.9}, {"path": "capital.equipment-cost", "display_name": "Equipment Cost", "value_type": "currency", "unit": "USD", "criticality": "material", "min_confidence": 0.85}, {"path": "capital.equity-contribution", "display_name": "Equity Contribution", "value_type": "currency", "unit": "USD", "criticality": "critical", "min_confidence": 0.9}, {"path": "capital.equity-percent", "display_name": "Equity Percentage", "value_type": "percentage", "criticality": "critical", "min_confidence": 0.9}, {"path": "cab.enabled", "display_name": "CAB Enabled", "value_type": "boolean", "criticality": "critical", "min_confidence": 0.95}, {"path": "cab.originalprincipial", "display_name": "Original Principal", "value_type": "currency", "unit": "USD", "criticality": "critical", "min_confidence": 0.9}, {"path": "cab.accretionrate", "display_name": "Accretion Rate", "value_type": "percentage", "criticality": "critical", "min_confidence": 0.9}, {"path": "cab.accretion.period.years", "display_name": "Accretion Period", "value_type": "number", "unit": "years", "criticality": "critical", "min_confidence": 0.9}, {"path": "cab.finalmaturitydate", "display_name": "Final Maturity Date", "value_type": "date", "criticality": "critical", "min_confidence": 0.9}, {"path": "cab.turbo.enabled", "display_name": "Turbo Redemption Enabled", "value_type": "boolean", "criticality": "material", "min_confidence": 0.85}, {"path": "cab.conversion.rate", "display_name": "Conversion Rate", "value_type": "percentage", "criticality": "critical", "min_confidence": 0.9}, {"path": "finmodel.inputs.revenue.annual", "display_name": "Projected Annual Revenue", "value_type": "currency", "unit": "USD", "criticality": "critical", "min_confidence": 0.9}, {"path": "finmodel.inputs.revenue.ramp", "display_name": "Revenue Ramp Schedule", "value_type": "object", "criticality": "critical", "min_confidence": 0.85}, {"path": "finmodel.inputs.dscr.minimum", "display_name": "Minimum DSCR Covenant", "value_type": "number", "criticality": "critical", "min_confidence": 0.95}, {"path": "finmodel.outputs.dscrbase", "display_name": "Base DSCR", "value_type": "number", "criticality": "critical", "min_confidence": 0.9}, {"path": "finmodel.outputs.dscrstress", "display_name": "Stress DSCR", "value_type": "number", "criticality": "critical", "min_confidence": 0.85}, {"path": "slb.enabled", "display_name": "SLB Enabled", "value_type": "boolean", "criticality": "critical", "min_confidence": 0.95}, {"path": "slb.kpis.shortlist", "display_name": "Selected KPIs", "value_type": "array", "criticality": "critical", "min_confidence": 0.9}, {"path": "slb.kpi.1.name", "display_name": "KPI 1 Name", "value_type": "string", "criticality": "critical", "min_confidence": 0.9}, {"path": "slb.kpi.1.baseline.value", "display_name": "KPI 1 Baseline", "value_type": "number", "criticality": "critical", "min_confidence": 0.9}, {"path": "slb.kpi.1.baseline.methodology", "display_name": "KPI 1 Baseline Methodology", "value_type": "string", "criticality": "critical", "min_confidence": 0.85}, {"path": "slb.kpi.1.verification.method", "display_name": "KPI 1 Verification Method", "value_type": "string", "criticality": "critical", "min_confidence": 0.85}, {"path": "slb.penalty.stepup.magnitude", "display_name": "Step-Up Penalty", "value_type": "number", "unit": "bps", "criticality": "critical", "min_confidence": 0.9}, {"path": "security.realproperty", "display_name": "Real Property Security", "value_type": "string", "criticality": "material", "min_confidence": 0.8}, {"path": "security.equipment.schedule", "display_name": "Equipment Security Schedule", "value_type": "string", "criticality": "material", "min_confidence": 0.8}, {"path": "security.revenue.pledge", "display_name": "Revenue Pledge", "value_type": "enum", "criticality": "critical", "min_confidence": 0.9, "allowed_values": ["gross", "net"]}, {"path": "permitting.air-quality.status", "display_name": "Air Quality Permit Status", "value_type": "enum", "criticality": "material", "min_confidence": 0.85, "allowed_values": ["not-started", "in-progress", "pending-approval", "approved"]}, {"path": "permitting.solidwaste.status", "display_name": "Solid Waste Permit Status", "value_type": "enum", "criticality": "material", "min_confidence": 0.85, "allowed_values": ["not-started", "in-progress", "pending-approval", "approved"]}, {"path": "permitting.buildingzoning.status", "display_name": "Building/Zoning Status", "value_type": "enum", "criticality": "secondary", "min_confidence": 0.8, "allowed_values": ["not-started", "in-progress", "pending-approval", "approved"]}, {"path": "regulatory.tax-status", "display_name": "Tax Status", "value_type": "enum", "criticality": "critical", "min_confidence": 0.9, "allowed_values": ["tax-exempt-idb", "tax-exempt-solidwaste", "taxable"]}, {"path": "regulatory.tax-exemption.basis", "display_name": "Tax Exemption Basis", "value_type": "string", "criticality": "material", "min_confidence": 0.85}, {"path": "risk.technology.description", "display_name": "Technology Risk Description", "value_type": "string", "criticality": "material", "min_confidence": 0.75}, {"path": "risk.technology.mitigants", "display_name": "Technology Risk Mitigants", "value_type": "string", "criticality": "material", "min_confidence": 0.75}, {"path": "risk.construction.description", "display_name": "Construction Risk Description", "value_type": "string", "criticality": "material", "min_confidence": 0.75}, {"path": "risk.construction.mitigants", "display_name": "Construction Risk Mitigants", "value_type": "string", "criticality": "material", "min_confidence": 0.75}, {"path": "risk.market.description", "display_name": "Market Risk Description", "value_type": "string", "criticality": "material", "min_confidence": 0.75}, {"path": "risk.market.mitigants", "display_name": "Market Risk Mitigants", "value_type": "string", "criticality": "material", "min_confidence": 0.75}, {"path": "risk.regulatory.description", "display_name": "Regulatory Risk Description", "value_type": "string", "criticality": "material", "min_confidence": 0.75}, {"path": "risk.regulatory.mitigants", "display_name": "Regulatory Risk Mitigants", "value_type": "string", "criticality": "material", "min_confidence": 0.75}, {"path": "risk.feedstock.description", "display_name": "Feedstock Risk Description", "value_type": "string", "criticality": "material", "min_confidence": 0.75}, {"path": "risk.feedstock.mitigants", "display_name": "Feedstock Risk Mitigants", "value_type": "string", "criticality": "material", "min_confidence": 0.75}, {"path": "project.name", "display_name": "Project Name", "value_type": "string", "criticality": "critical", "min_confidence": 0.7}, {"path": "project.location", "display_name": "Project Location", "value_type": "string", "criticality": "critical", "min_confidence": 0.7}, {"path": "healthcare.facility_type", "display_name": "Facility Type", "value_type": "string", "criticality": "critical", "min_confidence": 0.7}, {"path": "healthcare.licensure", "display_name": "Healthcare Licensure", "value_type": "string", "criticality": "critical", "min_confidence": 0.7}, {"path": "healthcare.cms_certification", "display_name": "CMS Certification", "value_type": "string", "criticality": "critical", "min_confidence": 0.7}, {"path": "healthcare.accreditation", "display_name": "Accreditation", "value_type": "string", "criticality": "material", "min_confidence": 0.7}, {"path": "healthcare.utilization.trend", "display_name": "Utilization Trend", "value_type": "string", "criticality": "material", "min_confidence": 0.7}, {"path": "healthcare.service_area", "display_name": "Healthcare Service Area", "value_type": "string", "criticality": "material", "min_confidence": 0.7}, {"path": "healthcare.physician_alignment", "display_name": "Physician Alignment", "value_type": "string", "criticality": "material", "min_confidence": 0.7}, {"path": "healthcare.ehr_platform", "display_name": "EHR Platform", "value_type": "string", "criticality": "secondary", "min_confidence": 0.7}, {"path": "healthcare.payor_mix", "display_name": "Payor Mix", "value_type": "string", "criticality": "material", "min_confidence": 0.7}, {"path": "healthcare.net_patient_revenue", "display_name": "Net Patient Revenue", "value_type": "currency", "unit": "USD", "criticality": "critical", "min_confidence": 0.7}, {"path": "liquidity.days_cash_on_hand", "display_name": "Days Cash on Hand", "value_type": "number", "unit": "days", "criticality": "critical", "min_confidence": 0.7}, {"path": "market.demand", "display_name": "Market Demand", "value_type": "string", "criticality": "material", "min_confidence": 0.7}, {"path": "environmental.phase_one", "display_name": "Phase I Environmental Review", "value_type": "string", "criticality": "material", "min_confidence": 0.7}, {"path": "financials.audited-statements", "display_name": "Audited Financial Statements", "value_type": "string", "criticality": "critical", "min_confidence": 0.7}]', '[{"extractor_id": "ProjectDescriptionExtractor", "name": "Project Description Extractor", "description": "Extracts project overview, location, and technology details", "target_schema_paths": ["project.canonicaldescription", "project.location.jurisdiction", "project.location.coordinates", "project.operatingstatus", "technology.type", "technology.throughput.nameplate", "technology.throughput.annual"], "system_prompt": "You are an expert municipal bond analyst extracting structured information from project documents.\nExtract ONLY information that is explicitly stated in the document. Never infer or estimate missing values.\nFor each extracted fact, provide the exact quote from the document as evidence.", "extraction_prompt_template": "From the following document content, extract these specific facts:\n1. Canonical project description (1-2 sentences describing the system, location, and purpose)\n2. Jurisdiction (state/county where project is located)\n3. GPS coordinates (if stated)\n4. Technology throughput nameplate (e.g., \"100 tons/day\")\n5. Annual throughput (nameplate \u00d7 351 operating days, or as stated)\n6. Current operating status (planned, under construction, or operational)\n\nIMPORTANT: Only extract if explicitly stated. Return null for missing values.\n\nDocument content:\n{content}\n\nReturn a JSON object with the extracted facts and confidence scores.", "requires_full_document": false, "idempotent": true}, {"extractor_id": "PartiesExtractor", "name": "Parties & Governance Extractor", "description": "Extracts information about project parties and governance structure", "target_schema_paths": ["parties.issuer.name", "parties.issuer.jurisdiction", "parties.borrower.name", "parties.operator.name", "parties.sponsor.name", "governance.inducement", "governance.publicpurpose"], "system_prompt": "You are an expert municipal bond analyst extracting party and governance information.\nFocus on identifying the legal entities involved in the transaction structure.\nCite exact text for each party identification.", "extraction_prompt_template": "Extract the following from this document:\n1. Project issuer (typically IDA or municipal entity)\n2. Issuer jurisdiction (state)\n3. Project borrower or operator (private entity)\n4. Technology provider/OEM\n5. Equity sponsor or funding source\n6. Inducement status (draft, proposed, or adopted)\n7. Public purpose / community benefit statement\n\nDocument content:\n{content}\n\nReturn a JSON object with extracted facts, confidence scores, and source quotes.", "requires_full_document": false, "idempotent": true}, {"extractor_id": "FeedstockSupplyExtractor", "name": "Feedstock & Supply Extractor", "description": "Extracts feedstock type, volume, and supply agreement details", "target_schema_paths": ["feedstock.type", "feedstock.volume.annual", "feedstock.supply.mechanism", "feedstock.supply.confidence", "feedstock.characterization"], "system_prompt": "You are extracting feedstock and supply chain information for a waste-to-energy project.\nPay attention to supply agreement status and confidence levels.", "extraction_prompt_template": "Extract feedstock and supply information:\n1. Feedstock type (forestry, MSW, agricultural, or mixed)\n2. Annual feedstock volume (tons/year)\n3. Supply mechanism (contract, MOU, letter of intent, or assessment only)\n4. Supply confidence level (preliminary, advanced, or secured)\n5. Feedstock characterization details\n\nDocument content:\n{content}\n\nReturn JSON with facts, confidence scores, and supporting quotes.", "requires_full_document": false, "idempotent": true}, {"extractor_id": "RevenueModelExtractor", "name": "Revenue Model Extractor", "description": "Extracts commodity revenues, offtake agreements, and projections", "target_schema_paths": ["revenue.commodities.list", "revenue.commodities.renewable-diesel", "revenue.commodities.biochar", "revenue.offtake.status", "revenue.gross.annual"], "system_prompt": "You are extracting revenue model information for bond structuring.\nFocus on quantifiable revenue streams and their contractual status.", "extraction_prompt_template": "Extract revenue model information:\n1. List of commodity revenue streams (product, volume, price, annual revenue)\n2. Renewable diesel specifics (gallons/year, price/gallon)\n3. Biochar specifics (tons/year, price/ton)\n4. Offtake agreement status (executed, advanced MOU, LOI, or negotiating)\n5. Total gross annual revenue projection\n\nDocument content:\n{content}\n\nReturn JSON with structured revenue data and confidence scores.", "requires_full_document": true, "idempotent": true}, {"extractor_id": "CABTermsExtractor", "name": "CAB Terms Extractor", "description": "Extracts Capital Appreciation Bond specific terms and structure", "target_schema_paths": ["cab.enabled", "cab.originalprincipial", "cab.accretionrate", "cab.accretion.period.years", "cab.finalmaturitydate", "cab.turbo.enabled", "cab.conversion.rate"], "system_prompt": "You are extracting Capital Appreciation Bond (CAB) terms.\nCABs are zero-coupon bonds that accrete value before converting to current-pay.\nExtract terms with high precision - these are critical for bond structuring.", "extraction_prompt_template": "Extract CAB-specific bond terms:\n1. Is CAB structure enabled/proposed? (boolean)\n2. Original principal amount\n3. Accretion rate (annual %)\n4. Accretion period (years before conversion)\n5. Final maturity date\n6. Turbo redemption enabled? (mandatory prepayment from excess cash)\n7. Conversion rate (interest rate after conversion to current-pay)\n\nDocument content:\n{content}\n\nReturn JSON with precise values and high confidence thresholds.", "requires_full_document": true, "idempotent": true}, {"extractor_id": "DSCRInputsExtractor", "name": "DSCR & Financial Inputs Extractor", "description": "Extracts debt service coverage ratio inputs, operating expenses, EBITDA, and covenants", "target_schema_paths": ["finmodel.inputs.revenue.annual", "finmodel.inputs.revenue.ramp", "finmodel.inputs.dscr.minimum", "finmodel.outputs.dscrbase", "finmodel.outputs.dscrstress", "capital.project-cost", "capital.equity-contribution", "capital.equity-percent", "opex.total.annual", "opex.margin", "ebitda"], "system_prompt": "You are extracting financial model inputs for DSCR calculation and operating performance metrics.\nDSCR = Net Operating Income / Annual Debt Service. Minimum covenant is typically 1.35x.\nEBITDA = Earnings Before Interest, Taxes, Depreciation, and Amortization.\nOperating Margin = (Revenue - Operating Expenses) / Revenue.\n\nWhen extracting from Excel/spreadsheet data:\n- Look for labeled rows/columns containing financial metrics\n- Common labels: \"EBITDA\", \"Operating Income\", \"OpEx\", \"Operating Expenses\", \"Net Operating Income\"\n- Values may be annual totals or broken down by year/period\n- Extract the steady-state or Year 1 values when multiple periods shown\n\nExtract with precision - these drive bond sizing and credit analysis.", "extraction_prompt_template": "Extract DSCR, operating expenses, and financial model inputs:\n1. Projected annual revenue (Year 1 or steady-state)\n2. Revenue ramp schedule by year (if available)\n3. Total annual operating expenses (OpEx)\n4. Operating margin percentage (if stated or calculable)\n5. EBITDA (Earnings Before Interest, Taxes, Depreciation & Amortization)\n6. Minimum DSCR covenant (typically 1.35x)\n7. Base case DSCR\n8. Stress case DSCR (at -20% revenue, if available)\n9. Total project cost\n10. Equity contribution amount\n11. Equity percentage of total project cost\n\nIMPORTANT: For spreadsheet/Excel data, look for:\n- Row labels like \"EBITDA\", \"Operating Expenses\", \"OpEx\", \"Net Operating Income\"\n- Column headers indicating years or periods\n- Summary totals or annual figures\n- Financial model output sections\n\nDocument content:\n{content}\n\nReturn JSON with financial metrics, values, units, and source quotes from the document.", "requires_full_document": true, "idempotent": true}, {"extractor_id": "SLBMetricsExtractor", "name": "SLB KPI & Metrics Extractor", "description": "Extracts Sustainability-Linked Bond KPIs, targets, and verification", "target_schema_paths": ["slb.enabled", "slb.kpis.shortlist", "slb.kpi.1.name", "slb.kpi.1.baseline.value", "slb.kpi.1.baseline.methodology", "slb.kpi.1.verification.method", "slb.penalty.stepup.magnitude"], "system_prompt": "You are extracting Sustainability-Linked Bond (SLB) KPI information.\nSLBs have performance targets with coupon step-ups/step-downs based on achievement.\nFocus on KPI definitions, baselines, targets, and verification methodology.", "extraction_prompt_template": "Extract SLB KPI information:\n1. Is SLB structure enabled?\n2. Selected KPIs (shortlist)\n3. For each KPI: name, definition, unit of measure\n4. Baseline value and calculation methodology\n5. Year 3/6/9 targets (SPTs)\n6. Verification method and provider\n7. Step-up penalty magnitude (basis points)\n\nDocument content:\n{content}\n\nReturn JSON with complete KPI structure and verification plan.", "requires_full_document": true, "idempotent": true}, {"extractor_id": "PermitRegulatoryExtractor", "name": "Permits & Regulatory Extractor", "description": "Extracts permitting status and regulatory compliance information", "target_schema_paths": ["permitting.air-quality.status", "permitting.solidwaste.status", "permitting.buildingzoning.status", "regulatory.tax-status", "regulatory.tax-exemption.basis"], "system_prompt": "You are extracting permitting and regulatory information.\nPermit status is critical for project timeline and bond closing.", "extraction_prompt_template": "Extract permitting and regulatory status:\n1. Air quality permit status and type\n2. Solid waste permit status\n3. Building/zoning permit status\n4. Tax status (tax-exempt IDB, tax-exempt solid waste, or taxable)\n5. Tax exemption legal basis (if applicable)\n\nDocument content:\n{content}\n\nReturn JSON with permit statuses and regulatory classifications.", "requires_full_document": false, "idempotent": true}]', '[{"item_code": "P1.1", "phase": "P1", "title": "Inducement Resolution", "description": "IDA has adopted or proposed inducement resolution authorizing bond issuance consideration", "required_schema_paths": ["governance.inducement", "parties.issuer.name", "parties.issuer.jurisdiction"], "optional_schema_paths": ["governance.publicpurpose"], "criticality": "critical", "blocks_phase_completion": true}, {"item_code": "P1.2", "phase": "P1", "title": "Tax Status Determination", "description": "Preliminary determination of tax-exempt eligibility or taxable bond structure", "required_schema_paths": ["regulatory.tax-status"], "optional_schema_paths": ["regulatory.tax-exemption.basis"], "criticality": "critical", "blocks_phase_completion": true}, {"item_code": "P1.3", "phase": "P1", "title": "Project Entity Formation", "description": "Borrower/project entity identified with proper legal structure", "required_schema_paths": ["parties.borrower.name", "parties.operator.name"], "optional_schema_paths": ["parties.sponsor.name"], "criticality": "material", "blocks_phase_completion": true}, {"item_code": "P2.1", "phase": "P2", "title": "Technology Specification", "description": "UCS technology type and throughput capacity documented", "required_schema_paths": ["technology.type", "technology.throughput.nameplate", "technology.throughput.annual"], "optional_schema_paths": ["technology.lifespan", "technology.warranty.duration"], "criticality": "critical", "blocks_phase_completion": true}, {"item_code": "P2.2", "phase": "P2", "title": "Site Control Evidence", "description": "Site control mechanism documented (purchase, lease, option, or LOI)", "required_schema_paths": ["project.location.sitecontrol", "project.location.jurisdiction"], "optional_schema_paths": ["project.location.coordinates"], "criticality": "material", "blocks_phase_completion": true}, {"item_code": "P2.3", "phase": "P2", "title": "Feedstock Supply Mechanism", "description": "Feedstock type and supply mechanism identified", "required_schema_paths": ["feedstock.type", "feedstock.volume.annual", "feedstock.supply.mechanism"], "optional_schema_paths": ["feedstock.characterization"], "criticality": "critical", "blocks_phase_completion": true}, {"item_code": "P2.4", "phase": "P2", "title": "Permitting Pathway", "description": "Key permits identified with status tracking", "required_schema_paths": ["permitting.air-quality.status", "permitting.solidwaste.status"], "optional_schema_paths": ["permitting.buildingzoning.status"], "criticality": "material", "blocks_phase_completion": false}, {"item_code": "P3.1", "phase": "P3", "title": "Revenue Model Documentation", "description": "Commodity revenue streams quantified with pricing assumptions", "required_schema_paths": ["revenue.commodities.list", "revenue.gross.annual"], "optional_schema_paths": ["revenue.commodities.renewable-diesel", "revenue.commodities.biochar"], "criticality": "critical", "blocks_phase_completion": true}, {"item_code": "P3.2", "phase": "P3", "title": "Offtake Agreement Status", "description": "Status of commodity offtake agreements (executed, MOU, LOI, negotiating)", "required_schema_paths": ["revenue.offtake.status"], "optional_schema_paths": [], "criticality": "critical", "blocks_phase_completion": true}, {"item_code": "P3.3", "phase": "P3", "title": "Capital Structure", "description": "Total project cost, equity contribution, and debt requirement documented", "required_schema_paths": ["capital.project-cost", "capital.equity-contribution", "capital.equity-percent"], "optional_schema_paths": ["capital.equipment-cost"], "criticality": "critical", "blocks_phase_completion": true}, {"item_code": "P3.4", "phase": "P3", "title": "Feedstock Supply Confidence", "description": "Feedstock supply confidence level advanced beyond preliminary", "required_schema_paths": ["feedstock.supply.confidence"], "optional_schema_paths": [], "criticality": "material", "blocks_phase_completion": true}, {"item_code": "P4.1", "phase": "P4", "title": "Security Package Definition", "description": "Collateral package defined (real property, equipment, revenue pledge)", "required_schema_paths": ["security.revenue.pledge"], "optional_schema_paths": ["security.realproperty", "security.equipment.schedule"], "criticality": "critical", "blocks_phase_completion": true}, {"item_code": "P4.2", "phase": "P4", "title": "Operating Expense Model", "description": "OpEx budget documented with margin analysis", "required_schema_paths": ["opex.total.annual", "ebitda"], "optional_schema_paths": ["opex.margin"], "criticality": "material", "blocks_phase_completion": true}, {"item_code": "P4.3", "phase": "P4", "title": "Risk Factor Documentation", "description": "Key risk factors documented with mitigation measures for disclosure", "required_schema_paths": ["risk.technology.description", "risk.construction.description", "risk.market.description"], "optional_schema_paths": ["risk.technology.mitigants", "risk.construction.mitigants", "risk.market.mitigants", "risk.regulatory.description", "risk.regulatory.mitigants", "risk.feedstock.description", "risk.feedstock.mitigants"], "criticality": "material", "blocks_phase_completion": true}, {"item_code": "P5.1", "phase": "P5", "title": "CAB Structure Confirmation", "description": "CAB terms defined (principal, accretion rate, period, maturity)", "required_schema_paths": ["cab.enabled", "cab.originalprincipial", "cab.accretionrate", "cab.accretion.period.years"], "optional_schema_paths": ["cab.finalmaturitydate", "cab.turbo.enabled", "cab.conversion.rate"], "criticality": "critical", "blocks_phase_completion": true}, {"item_code": "P5.2", "phase": "P5", "title": "DSCR Covenant & Coverage", "description": "DSCR covenant defined with base and stress case coverage documented", "required_schema_paths": ["finmodel.inputs.dscr.minimum", "finmodel.outputs.dscrbase"], "optional_schema_paths": ["finmodel.outputs.dscrstress", "finmodel.inputs.revenue.ramp"], "criticality": "critical", "blocks_phase_completion": true}, {"item_code": "P5.3", "phase": "P5", "title": "SLB KPI Selection & Baselines", "description": "SLB KPIs selected with baselines, targets, and verification methodology", "required_schema_paths": ["slb.enabled", "slb.kpis.shortlist", "slb.kpi.1.baseline.methodology"], "optional_schema_paths": ["slb.kpi.1.name", "slb.kpi.1.baseline.value", "slb.kpi.1.verification.method"], "criticality": "critical", "blocks_phase_completion": true}, {"item_code": "P5.4", "phase": "P5", "title": "SLB Penalty Structure", "description": "Step-up/step-down penalty structure defined", "required_schema_paths": ["slb.penalty.stepup.magnitude"], "optional_schema_paths": [], "criticality": "material", "blocks_phase_completion": true}, {"item_code": "P6.1", "phase": "P6", "title": "Warm Handoff Pack Complete", "description": "All sections of advisor handoff pack generated and reviewed", "required_schema_paths": [], "optional_schema_paths": [], "criticality": "material", "blocks_phase_completion": false}]', '{"dimensions": {"issuer_authority": {"name": "Issuer Authority", "weight": 0.2, "contributing_paths": ["governance.inducement", "parties.issuer.name", "parties.issuer.jurisdiction", "regulatory.tax-status", "regulatory.tax-exemption.basis", "parties.borrower.name", "parties.operator.name", "parties.sponsor.name", "governance.publicpurpose"], "critical_paths": ["governance.inducement", "regulatory.tax-status"]}, "project_tech": {"name": "Project & Technology", "weight": 0.2, "contributing_paths": ["project.canonicaldescription", "project.operatingstatus", "project.location.jurisdiction", "project.location.sitecontrol", "project.location.coordinates", "project.designlife", "technology.type", "technology.throughput.nameplate", "technology.throughput.annual", "technology.lifespan", "technology.warranty.supplier", "technology.warranty.duration", "operations.staffing.direct"], "critical_paths": ["technology.type", "technology.throughput.nameplate"]}, "revenue_feedstock": {"name": "Revenue & Feedstock", "weight": 0.15, "contributing_paths": ["feedstock.type", "feedstock.volume.annual", "feedstock.supply.mechanism", "feedstock.supply.confidence", "feedstock.characterization", "revenue.commodities.list", "revenue.commodities.renewable-diesel", "revenue.commodities.biochar", "revenue.gross.annual", "revenue.offtake.status"], "critical_paths": ["feedstock.supply.mechanism", "revenue.offtake.status", "revenue.gross.annual"]}, "cab_financial": {"name": "CAB Financial Structure", "weight": 0.2, "contributing_paths": ["cab.enabled", "cab.originalprincipial", "cab.accretionrate", "cab.accretion.period.years", "cab.finalmaturitydate", "cab.turbo.enabled", "cab.conversion.rate", "finmodel.inputs.revenue.annual", "finmodel.inputs.revenue.ramp", "finmodel.inputs.dscr.minimum", "finmodel.outputs.dscrbase", "finmodel.outputs.dscrstress", "capital.project-cost", "capital.equipment-cost", "capital.equity-contribution", "capital.equity-percent"], "critical_paths": ["cab.accretionrate", "finmodel.outputs.dscrbase", "capital.equity-contribution"]}, "risk_security_slb": {"name": "Risk, Security & Permitting", "weight": 0.15, "contributing_paths": ["security.revenue.pledge", "security.realproperty", "security.equipment.schedule", "permitting.air-quality.status", "permitting.solidwaste.status", "permitting.buildingzoning.status", "opex.total.annual", "opex.margin", "ebitda", "risk.technology.description", "risk.technology.mitigants", "risk.construction.description", "risk.construction.mitigants", "risk.market.description", "risk.market.mitigants", "risk.regulatory.description", "risk.regulatory.mitigants", "risk.feedstock.description", "risk.feedstock.mitigants"], "critical_paths": ["security.revenue.pledge", "risk.technology.description", "risk.construction.description"]}, "slb_verification": {"name": "SLB Verification", "weight": 0.1, "contributing_paths": ["slb.enabled", "slb.kpis.shortlist", "slb.kpi.1.name", "slb.kpi.1.baseline.value", "slb.kpi.1.baseline.methodology", "slb.kpi.1.verification.method", "slb.penalty.stepup.magnitude"], "critical_paths": ["slb.kpis.shortlist", "slb.kpi.1.baseline.methodology"]}}, "score_thresholds": {"not_yet_viable": {"min": 0.0, "max": 3.0}, "structurally_viable": {"min": 3.0, "max": 5.5}, "ready_for_selective_engagement": {"min": 5.5, "max": 7.5}, "ready_for_broad_market": {"min": 7.5, "max": 10.0}}}',
                NOW(), NOW()
            );

UPDATE alembic_version SET version_num='b2c3d4e5f6a7' WHERE alembic_version.version_num = 'a1b2c3d4e5f6';

-- Running upgrade b2c3d4e5f6a7 -> c3d4e5f6a7b8

ALTER TABLE artifacts ADD COLUMN is_extracted BOOLEAN DEFAULT 'false' NOT NULL;

ALTER TABLE artifacts ADD COLUMN last_extraction_job_id UUID;

UPDATE alembic_version SET version_num='c3d4e5f6a7b8' WHERE alembic_version.version_num = 'b2c3d4e5f6a7';

-- Running upgrade c3d4e5f6a7b8 -> d4e5f6a7b8c9

ALTER TABLE extracted_facts ADD COLUMN source_type VARCHAR(20) DEFAULT 'extracted' NOT NULL;

CREATE INDEX IF NOT EXISTS ix_extracted_facts_source_type
        ON extracted_facts (source_type);

ALTER TABLE extracted_facts ALTER COLUMN extraction_job_id DROP NOT NULL;

UPDATE alembic_version SET version_num='d4e5f6a7b8c9' WHERE alembic_version.version_num = 'c3d4e5f6a7b8';

-- Running upgrade d4e5f6a7b8c9 -> f6a7b8c9d0e1

CREATE TABLE disclosure_documents (
    id UUID NOT NULL, 
    version INTEGER DEFAULT '1' NOT NULL, 
    completeness_score FLOAT DEFAULT '0.0' NOT NULL, 
    is_complete BOOLEAN DEFAULT 'false' NOT NULL, 
    generation_started_at TIMESTAMP WITH TIME ZONE, 
    generation_completed_at TIMESTAMP WITH TIME ZONE, 
    playbook_version VARCHAR(50), 
    project_id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id)
);

CREATE INDEX ix_disclosure_documents_project_id ON disclosure_documents (project_id);

CREATE TABLE disclosure_sections (
    id UUID NOT NULL, 
    section_id VARCHAR(100) NOT NULL, 
    section_order INTEGER DEFAULT '0' NOT NULL, 
    title VARCHAR(255) NOT NULL, 
    parent_section_id UUID, 
    content_md TEXT DEFAULT '' NOT NULL, 
    confidence FLOAT DEFAULT '0.0' NOT NULL, 
    required_fact_count INTEGER DEFAULT '0' NOT NULL, 
    present_fact_count INTEGER DEFAULT '0' NOT NULL, 
    tbd_count INTEGER DEFAULT '0' NOT NULL, 
    supporting_fact_ids JSON DEFAULT '[]' NOT NULL, 
    conditional_on VARCHAR(255), 
    is_rendered BOOLEAN DEFAULT 'true' NOT NULL, 
    disclosure_document_id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(disclosure_document_id) REFERENCES disclosure_documents (id), 
    FOREIGN KEY(parent_section_id) REFERENCES disclosure_sections (id)
);

CREATE INDEX ix_disclosure_sections_disclosure_document_id ON disclosure_sections (disclosure_document_id);

CREATE TABLE tbd_markers (
    id UUID NOT NULL, 
    location VARCHAR(255) NOT NULL, 
    missing_fact_paths JSON DEFAULT '[]' NOT NULL, 
    reason TEXT NOT NULL, 
    severity VARCHAR(20) DEFAULT '''medium''' NOT NULL, 
    is_resolved BOOLEAN DEFAULT 'false' NOT NULL, 
    resolved_at TIMESTAMP WITH TIME ZONE, 
    resolved_by_fact_id UUID, 
    disclosure_document_id UUID NOT NULL, 
    section_id UUID, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(disclosure_document_id) REFERENCES disclosure_documents (id), 
    FOREIGN KEY(resolved_by_fact_id) REFERENCES extracted_facts (id), 
    FOREIGN KEY(section_id) REFERENCES disclosure_sections (id)
);

CREATE INDEX ix_tbd_markers_disclosure_document_id ON tbd_markers (disclosure_document_id);

CREATE INDEX ix_tbd_markers_section_id ON tbd_markers (section_id);

CREATE TABLE information_requests (
    id UUID NOT NULL, 
    request_code VARCHAR(50) NOT NULL, 
    title VARCHAR(255) NOT NULL, 
    missing_fact_paths JSON DEFAULT '[]' NOT NULL, 
    current_evidence_state VARCHAR(20) DEFAULT '''none''' NOT NULL, 
    gap_id VARCHAR(100), 
    why_it_matters TEXT NOT NULL, 
    who_needs_it JSON DEFAULT '[]' NOT NULL, 
    when_needed VARCHAR(255), 
    consequences TEXT NOT NULL, 
    related_requirements JSON DEFAULT '[]' NOT NULL, 
    regulatory_reference VARCHAR(255), 
    affected_checklist_items JSON DEFAULT '[]' NOT NULL, 
    affected_dimensions JSON DEFAULT '[]' NOT NULL, 
    guidance_overview TEXT NOT NULL, 
    specific_questions JSON DEFAULT '[]' NOT NULL, 
    data_points_needed JSON DEFAULT '[]' NOT NULL, 
    suggested_approach TEXT, 
    common_pitfalls JSON DEFAULT '[]' NOT NULL, 
    time_estimate VARCHAR(100), 
    examples JSON DEFAULT '[]' NOT NULL, 
    acceptable_sources JSON DEFAULT '[]' NOT NULL, 
    minimum_confidence FLOAT DEFAULT '0.80' NOT NULL, 
    expected_format VARCHAR(255), 
    priority VARCHAR(20) DEFAULT '''medium''' NOT NULL, 
    suggested_owner VARCHAR(255), 
    target_date DATE, 
    status VARCHAR(20) DEFAULT '''open''' NOT NULL, 
    acknowledged_at TIMESTAMP WITH TIME ZONE, 
    acknowledged_by UUID, 
    submitted_at TIMESTAMP WITH TIME ZONE, 
    resolved_at TIMESTAMP WITH TIME ZONE, 
    deferred_at TIMESTAMP WITH TIME ZONE, 
    deferred_reason TEXT, 
    deferred_review_date DATE, 
    resolution_notes TEXT, 
    resolved_by_fact_ids JSON DEFAULT '[]' NOT NULL, 
    linked_artifact_id UUID, 
    escalation_level INTEGER DEFAULT '0' NOT NULL, 
    last_escalated_at TIMESTAMP WITH TIME ZONE, 
    project_id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(acknowledged_by) REFERENCES users (id), 
    FOREIGN KEY(linked_artifact_id) REFERENCES artifacts (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    UNIQUE (request_code)
);

CREATE INDEX ix_information_requests_project_id ON information_requests (project_id);

CREATE INDEX ix_information_requests_status ON information_requests (status);

CREATE UNIQUE INDEX ix_information_requests_request_code ON information_requests (request_code);

CREATE TABLE information_request_notes (
    id UUID NOT NULL, 
    content TEXT NOT NULL, 
    note_type VARCHAR(50) DEFAULT '''update''' NOT NULL, 
    request_id UUID NOT NULL, 
    created_by_id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(created_by_id) REFERENCES users (id), 
    FOREIGN KEY(request_id) REFERENCES information_requests (id)
);

CREATE INDEX ix_information_request_notes_request_id ON information_request_notes (request_id);

CREATE TABLE internal_readiness_reports (
    id UUID NOT NULL, 
    version INTEGER DEFAULT '1' NOT NULL, 
    is_complete BOOLEAN DEFAULT 'false' NOT NULL, 
    generation_started_at TIMESTAMP WITH TIME ZONE, 
    generation_completed_at TIMESTAMP WITH TIME ZONE, 
    executive_summary JSON DEFAULT '{}' NOT NULL, 
    readiness_dashboard JSON DEFAULT '{}' NOT NULL, 
    gap_analysis JSON DEFAULT '{}' NOT NULL, 
    information_requests_section JSON DEFAULT '{}' NOT NULL, 
    checklist_status JSON DEFAULT '{}' NOT NULL, 
    evidence_index JSON DEFAULT '{}' NOT NULL, 
    assumption_register JSON DEFAULT '{}' NOT NULL, 
    overall_score FLOAT, 
    dimension_scores JSON DEFAULT '[]' NOT NULL, 
    critical_gap_count INTEGER DEFAULT '0' NOT NULL, 
    high_gap_count INTEGER DEFAULT '0' NOT NULL, 
    open_request_count INTEGER DEFAULT '0' NOT NULL, 
    overdue_request_count INTEGER DEFAULT '0' NOT NULL, 
    facts_count INTEGER DEFAULT '0' NOT NULL, 
    playbook_version VARCHAR(50), 
    bfms_version VARCHAR(50), 
    pdf_storage_path VARCHAR(500), 
    md_storage_path VARCHAR(500), 
    celery_task_id VARCHAR(255), 
    project_id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id)
);

CREATE INDEX ix_internal_readiness_reports_project_id ON internal_readiness_reports (project_id);

CREATE TABLE external_advisory_packages (
    id UUID NOT NULL, 
    version INTEGER DEFAULT '1' NOT NULL, 
    title VARCHAR(255) NOT NULL, 
    generated_for VARCHAR(255) NOT NULL, 
    is_complete BOOLEAN DEFAULT 'false' NOT NULL, 
    generation_started_at TIMESTAMP WITH TIME ZONE, 
    generation_completed_at TIMESTAMP WITH TIME ZONE, 
    cover_page JSON DEFAULT '{}' NOT NULL, 
    executive_summary JSON DEFAULT '{}' NOT NULL, 
    deal_overview JSON DEFAULT '{}' NOT NULL, 
    financial_tables JSON DEFAULT '{}' NOT NULL, 
    slb_brief JSON DEFAULT '{}' NOT NULL, 
    key_assumptions JSON DEFAULT '[]' NOT NULL, 
    disclaimer TEXT DEFAULT '''''' NOT NULL, 
    disclosure_completeness_score FLOAT, 
    critical_tbd_count INTEGER DEFAULT '0' NOT NULL, 
    high_tbd_count INTEGER DEFAULT '0' NOT NULL, 
    readiness_score_at_generation FLOAT, 
    ready_for_distribution BOOLEAN DEFAULT 'false' NOT NULL, 
    distribution_issues JSON DEFAULT '[]' NOT NULL, 
    playbook_version VARCHAR(50), 
    bfms_version VARCHAR(50), 
    pdf_storage_path VARCHAR(500), 
    docx_storage_path VARCHAR(500), 
    md_storage_path VARCHAR(500), 
    celery_task_id VARCHAR(255), 
    project_id UUID NOT NULL, 
    disclosure_document_id UUID, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(disclosure_document_id) REFERENCES disclosure_documents (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id)
);

CREATE INDEX ix_external_advisory_packages_project_id ON external_advisory_packages (project_id);

UPDATE alembic_version SET version_num='f6a7b8c9d0e1' WHERE alembic_version.version_num = 'd4e5f6a7b8c9';

-- Running upgrade f6a7b8c9d0e1 -> g7h8i9j0k1l2

CREATE TABLE deal_document_types (
    id UUID NOT NULL, 
    code VARCHAR(100) NOT NULL, 
    display_name VARCHAR(255) NOT NULL, 
    category VARCHAR(50) NOT NULL, 
    deal_vertical VARCHAR(50) DEFAULT 'muni' NOT NULL, 
    description TEXT, 
    default_workflow VARCHAR(50) DEFAULT 'standard' NOT NULL, 
    retention_policy VARCHAR(50) DEFAULT 'standard_6yr' NOT NULL, 
    requires_signature BOOLEAN DEFAULT 'false' NOT NULL, 
    is_active BOOLEAN DEFAULT 'true' NOT NULL, 
    sort_order INTEGER DEFAULT '0' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_deal_document_types_code ON deal_document_types (code);

CREATE TABLE document_templates (
    id UUID NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    document_type_id UUID NOT NULL, 
    jurisdiction VARCHAR(100), 
    version INTEGER DEFAULT '1' NOT NULL, 
    template_body TEXT NOT NULL, 
    variable_schema JSON, 
    is_active BOOLEAN DEFAULT 'true' NOT NULL, 
    is_system BOOLEAN DEFAULT 'false' NOT NULL, 
    tenant_id VARCHAR(100) DEFAULT 'default' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(document_type_id) REFERENCES deal_document_types (id)
);

CREATE INDEX ix_document_templates_type ON document_templates (document_type_id);

CREATE INDEX ix_document_templates_tenant ON document_templates (tenant_id);

CREATE TABLE template_clauses (
    id UUID NOT NULL, 
    template_id UUID, 
    name VARCHAR(255) NOT NULL, 
    category VARCHAR(100) NOT NULL, 
    content_json JSON NOT NULL, 
    description TEXT, 
    jurisdiction VARCHAR(100), 
    is_active BOOLEAN DEFAULT 'true' NOT NULL, 
    tenant_id VARCHAR(100) DEFAULT 'default' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(template_id) REFERENCES document_templates (id)
);

CREATE INDEX ix_template_clauses_tenant ON template_clauses (tenant_id);

CREATE TABLE deal_documents (
    id UUID NOT NULL, 
    title VARCHAR(500) NOT NULL, 
    document_number VARCHAR(50), 
    document_type_id UUID NOT NULL, 
    status VARCHAR(30) DEFAULT 'draft' NOT NULL, 
    content_json JSON, 
    content_html TEXT, 
    content_plaintext TEXT, 
    template_id UUID, 
    template_version INTEGER, 
    signature_request_id VARCHAR(255), 
    signature_status VARCHAR(30), 
    filed_to VARCHAR(100), 
    filed_at TIMESTAMP WITH TIME ZONE, 
    filing_reference VARCHAR(255), 
    retention_policy VARCHAR(50) DEFAULT 'standard_6yr' NOT NULL, 
    legal_hold BOOLEAN DEFAULT 'false' NOT NULL, 
    retention_expires_at TIMESTAMP WITH TIME ZONE, 
    artifact_id UUID, 
    project_id UUID NOT NULL, 
    created_by_id UUID NOT NULL, 
    assigned_to_id UUID, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(document_type_id) REFERENCES deal_document_types (id), 
    FOREIGN KEY(template_id) REFERENCES document_templates (id), 
    FOREIGN KEY(artifact_id) REFERENCES artifacts (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    FOREIGN KEY(created_by_id) REFERENCES users (id), 
    FOREIGN KEY(assigned_to_id) REFERENCES users (id)
);

CREATE INDEX ix_deal_documents_project ON deal_documents (project_id);

CREATE INDEX ix_deal_documents_type ON deal_documents (document_type_id);

CREATE TABLE deal_document_versions (
    id UUID NOT NULL, 
    document_id UUID NOT NULL, 
    version_number INTEGER NOT NULL, 
    content_json JSON NOT NULL, 
    content_hash VARCHAR(64) NOT NULL, 
    change_summary TEXT, 
    snapshot_reason VARCHAR(50) DEFAULT 'auto_save' NOT NULL, 
    created_by_id UUID NOT NULL, 
    storage_path VARCHAR(500), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(document_id) REFERENCES deal_documents (id), 
    FOREIGN KEY(created_by_id) REFERENCES users (id), 
    CONSTRAINT uq_doc_version UNIQUE (document_id, version_number)
);

CREATE INDEX ix_deal_document_versions_doc ON deal_document_versions (document_id);

CREATE TABLE document_reviews (
    id UUID NOT NULL, 
    document_id UUID NOT NULL, 
    reviewer_id UUID NOT NULL, 
    status VARCHAR(30) DEFAULT 'pending' NOT NULL, 
    comments TEXT, 
    review_version INTEGER, 
    completed_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(document_id) REFERENCES deal_documents (id), 
    FOREIGN KEY(reviewer_id) REFERENCES users (id)
);

CREATE INDEX ix_document_reviews_doc ON document_reviews (document_id);

CREATE TABLE document_signers (
    id UUID NOT NULL, 
    document_id UUID NOT NULL, 
    signer_name VARCHAR(255) NOT NULL, 
    signer_email VARCHAR(255) NOT NULL, 
    signer_role VARCHAR(100) NOT NULL, 
    signing_order INTEGER DEFAULT '0' NOT NULL, 
    status VARCHAR(30) DEFAULT 'pending' NOT NULL, 
    dropbox_sign_signer_id VARCHAR(255), 
    signed_at TIMESTAMP WITH TIME ZONE, 
    ip_address VARCHAR(45), 
    device_info VARCHAR(500), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(document_id) REFERENCES deal_documents (id)
);

CREATE INDEX ix_document_signers_doc ON document_signers (document_id);

CREATE TABLE document_audit_log (
    id UUID NOT NULL, 
    document_id UUID NOT NULL, 
    actor_id UUID NOT NULL, 
    actor_email VARCHAR(255), 
    action VARCHAR(50) NOT NULL, 
    details JSON, 
    ip_address VARCHAR(45), 
    user_agent VARCHAR(500), 
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(document_id) REFERENCES deal_documents (id)
);

CREATE INDEX ix_document_audit_log_doc ON document_audit_log (document_id);

CREATE INDEX ix_document_audit_log_ts ON document_audit_log (timestamp);

CREATE TABLE virtual_data_rooms (
    id UUID NOT NULL, 
    project_id UUID NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    is_active BOOLEAN DEFAULT 'true' NOT NULL, 
    require_nda BOOLEAN DEFAULT 'true' NOT NULL, 
    nda_template_id UUID, 
    watermark_enabled BOOLEAN DEFAULT 'true' NOT NULL, 
    default_access_expiry_days INTEGER DEFAULT '30' NOT NULL, 
    settings JSON, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    FOREIGN KEY(nda_template_id) REFERENCES document_templates (id), 
    CONSTRAINT uq_vdr_project UNIQUE (project_id)
);

CREATE TABLE vdr_participants (
    id UUID NOT NULL, 
    data_room_id UUID NOT NULL, 
    email VARCHAR(255) NOT NULL, 
    full_name VARCHAR(255) NOT NULL, 
    organization VARCHAR(255), 
    role VARCHAR(30) DEFAULT 'viewer' NOT NULL, 
    access_token VARCHAR(255) NOT NULL, 
    nda_accepted BOOLEAN DEFAULT 'false' NOT NULL, 
    nda_accepted_at TIMESTAMP WITH TIME ZONE, 
    access_expires_at TIMESTAMP WITH TIME ZONE, 
    is_active BOOLEAN DEFAULT 'true' NOT NULL, 
    last_accessed_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(data_room_id) REFERENCES virtual_data_rooms (id), 
    CONSTRAINT uq_vdr_access_token UNIQUE (access_token), 
    CONSTRAINT uq_vdr_participant_email UNIQUE (data_room_id, email)
);

CREATE INDEX ix_vdr_participants_room ON vdr_participants (data_room_id);

CREATE TABLE vdr_document_permissions (
    id UUID NOT NULL, 
    data_room_id UUID NOT NULL, 
    document_id UUID NOT NULL, 
    participant_id UUID, 
    can_view BOOLEAN DEFAULT 'true' NOT NULL, 
    can_download BOOLEAN DEFAULT 'false' NOT NULL, 
    can_print BOOLEAN DEFAULT 'false' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(data_room_id) REFERENCES virtual_data_rooms (id), 
    FOREIGN KEY(document_id) REFERENCES deal_documents (id), 
    FOREIGN KEY(participant_id) REFERENCES vdr_participants (id)
);

CREATE INDEX ix_vdr_doc_perms_room ON vdr_document_permissions (data_room_id);

CREATE INDEX ix_vdr_doc_perms_doc ON vdr_document_permissions (document_id);

CREATE TABLE vdr_activity_log (
    id UUID NOT NULL, 
    data_room_id UUID NOT NULL, 
    participant_id UUID NOT NULL, 
    document_id UUID NOT NULL, 
    action VARCHAR(30) NOT NULL, 
    page_number INTEGER, 
    duration_seconds INTEGER, 
    ip_address VARCHAR(45), 
    user_agent VARCHAR(500), 
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(data_room_id) REFERENCES virtual_data_rooms (id), 
    FOREIGN KEY(participant_id) REFERENCES vdr_participants (id), 
    FOREIGN KEY(document_id) REFERENCES deal_documents (id)
);

CREATE INDEX ix_vdr_activity_room ON vdr_activity_log (data_room_id);

CREATE INDEX ix_vdr_activity_participant ON vdr_activity_log (participant_id);

CREATE INDEX ix_vdr_activity_doc ON vdr_activity_log (document_id);

CREATE INDEX ix_vdr_activity_ts ON vdr_activity_log (timestamp);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('e77425fb-2582-446f-939c-9583b2bce079', 'preliminary_official_statement', 'Preliminary Official Statement (POS)', 'regulatory', 'muni', 'Preliminary disclosure document for bond offering. Filed to EMMA per MSRB G-32.', 'indefinite', false, 1);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('7ea2cca4-33e0-458a-9953-bbf449e5cb87', 'official_statement', 'Official Statement (OS)', 'regulatory', 'muni', 'Final disclosure document. Must be filed to EMMA within 1 business day of closing.', 'indefinite', false, 2);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('71d1a2fc-fb08-42e2-bd2e-4a425ffda709', 'continuing_disclosure_agreement', 'Continuing Disclosure Agreement', 'templated', 'muni', 'SEC Rule 15c2-12 annual reporting and material event notice commitment.', 'indefinite', true, 3);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('4919baec-72ac-43d6-8fc1-f52147a01219', 'trust_indenture', 'Trust Indenture / Bond Resolution', 'negotiated', 'muni', 'Core contract between issuer and trustee. Defines covenants, flow of funds, events of default.', 'bond_life_plus_3yr', true, 10);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('11eea6bd-e80f-474b-9bdb-3d1777a2c49a', 'loan_agreement', 'Loan Agreement', 'negotiated', 'muni', 'Direct placement loan agreement between issuer and lender/bank.', 'bond_life_plus_3yr', true, 11);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('999e2131-826c-4400-8cea-b42f7e43359f', 'bond_purchase_agreement', 'Bond Purchase Agreement', 'negotiated', 'muni', 'Agreement between issuer and underwriter for purchase of bonds.', 'standard_6yr', true, 12);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('d100c4f4-2ba3-49eb-ba92-3e2b1cf975b1', 'letter_of_credit', 'Letter of Credit', 'negotiated', 'muni', 'Bank LOC providing credit enhancement for bonds.', 'bond_life_plus_3yr', true, 20);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('25b0c8e4-c75e-4efb-b45f-c5335944d362', 'bond_insurance_policy', 'Bond Insurance Policy', 'templated', 'muni', 'Insurance policy providing credit enhancement (from AGM, BAM, etc.).', 'bond_life_plus_3yr', false, 21);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('c4f8b61e-d2d3-46d4-8588-289998ffe694', 'standby_bond_purchase_agreement', 'Standby Bond Purchase Agreement', 'negotiated', 'muni', 'Liquidity facility for variable rate demand bonds.', 'bond_life_plus_3yr', true, 22);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('a79cf1fe-d1ce-48a3-89f2-c4d3275ee358', 'remarketing_agreement', 'Remarketing Agreement', 'negotiated', 'muni', 'Agreement with remarketing agent for variable rate bonds.', 'standard_6yr', true, 30);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('a88751e8-76cd-400b-86a7-dd0fb58b8c00', 'isda_master_agreement', 'ISDA Master Agreement + Schedule', 'negotiated', 'muni', 'Interest rate swap documentation under ISDA standards.', 'bond_life_plus_3yr', true, 31);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('c6ed8343-f80c-474a-a637-bbfde75dfb4b', 'tax_opinion', 'Tax Opinion / Bond Counsel Opinion', 'professional_report', 'muni', 'Legal opinion on tax-exempt status. Required for tax-exempt bonds.', 'bond_life_plus_3yr', false, 40);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('1e78ee1a-60c5-412c-b75c-2627a62c2eb5', 'tax_certificate', 'Tax Compliance Certificate (IRS 8038)', 'templated', 'muni', 'IRS Form 8038 filing and post-issuance tax compliance procedures.', 'bond_life_plus_3yr', true, 41);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('e6c8f1aa-daaa-4304-abe3-dad4b59e7be6', 'tax_regulatory_agreement', 'Tax Regulatory Agreement', 'negotiated', 'muni', 'Agreement governing tax-exempt bond compliance requirements.', 'bond_life_plus_3yr', true, 42);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('4a50078e-53c0-4cc4-9b12-a6c08fc7f8c1', 'feasibility_study', 'Feasibility Study', 'professional_report', 'muni', 'Independent feasibility analysis of revenue projections and project viability.', 'standard_6yr', false, 50);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('8883b184-3b9c-48b6-b39d-e1883ead4d72', 'engineering_report', 'Engineering Report', 'professional_report', 'muni', 'Technical engineering assessment of project infrastructure.', 'standard_6yr', false, 51);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('c883f07a-0723-44d7-949c-c5a662543dd0', 'environmental_assessment', 'Environmental Assessment (Phase I/II)', 'professional_report', 'muni', 'ASTM E1527 Phase I ESA or Phase II environmental site assessment.', 'standard_6yr', false, 52);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('cefe96b7-6a2b-4e91-8d9d-e7ed0675398e', 'appraisal', 'Appraisal', 'professional_report', 'muni', 'USPAP-compliant property or asset valuation.', 'standard_6yr', false, 53);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('8758e645-d309-4bbf-8525-7af6edec68d7', 'closing_certificate', 'Closing Certificate', 'templated', 'muni', 'Officer certificate confirming closing conditions met.', 'standard_6yr', true, 60);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('2d18da01-c8f4-4cf5-b90d-d63ad7d388fd', 'board_resolution', 'Board Resolution / Authorizing Ordinance', 'templated', 'muni', 'Governing body authorization for bond issuance.', 'indefinite', true, 61);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('43df5f05-e10f-4c8f-9a79-a746e0926f84', 'closing_checklist', 'Closing Checklist', 'templated', 'muni', 'Master checklist of all closing deliverables and responsible parties.', 'standard_6yr', false, 62);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('96a7cc8d-cbc5-404f-8f8d-436c4411c83e', 'due_diligence_request_list', 'Due Diligence Request List', 'templated', 'muni', 'Information request list from underwriter or bond counsel.', 'standard_6yr', false, 63);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('a65ebc56-a63e-4004-926e-4470e6f3c99e', 'nda', 'Non-Disclosure Agreement', 'templated', 'muni', 'Confidentiality agreement between deal parties.', 'standard_6yr', true, 70);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('33dcaa29-6518-4fc3-9191-2f0261607622', 'loi_term_sheet', 'Letter of Intent / Term Sheet', 'negotiated', 'muni', 'Non-binding outline of key transaction terms.', 'standard_6yr', true, 71);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('d0844990-3ae0-4cec-bf86-cb58d645feb8', 'material_event_notice', 'Material Event Notice', 'regulatory', 'muni', 'SEC Rule 15c2-12 material event filing to EMMA.', 'indefinite', false, 80);

UPDATE alembic_version SET version_num='g7h8i9j0k1l2' WHERE alembic_version.version_num = 'f6a7b8c9d0e1';

-- Running upgrade g7h8i9j0k1l2 -> h8i9j0k1l2m3

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('cb897ce3-140b-401e-b1cd-1e7ffcce7ef6', 'limited_partnership_agreement', 'Limited Partnership Agreement (LPA)', 'negotiated', 'pe', 'Fund constitutional document covering waterfall, governance, and LP rights.', 'indefinite', true, 200);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('677ff181-5b77-4d11-a11d-7333736b4b1f', 'private_placement_memorandum', 'Private Placement Memorandum (PPM)', 'regulatory', 'pe', 'Fund offering memorandum for institutional investors.', 'indefinite', false, 201);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('7f6a80ce-06d5-4b1b-99c4-5f2ee4047692', 'side_letter', 'Investor Side Letter', 'negotiated', 'pe', 'Investor-specific rights and reporting accommodations.', 'indefinite', true, 202);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('b427abb6-5cb2-4a58-9ac3-3c5df383c5d6', 'subscription_agreement', 'Subscription Agreement', 'templated', 'pe', 'Investor subscription package with suitability reps and commitment terms.', 'standard_6yr', true, 203);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('850d718d-bf94-4aa0-9a8d-f65a6cd97f4b', 'purchase_and_sale_agreement', 'Purchase and Sale Agreement (SPA)', 'negotiated', 'pe', 'Acquisition agreement with reps, warranties, indemnities, and closing mechanics.', 'standard_6yr', true, 210);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('49352501-211f-44ab-9a2e-eef5856ba3ec', 'credit_agreement', 'Credit Agreement', 'negotiated', 'pe', 'Senior or mezzanine debt facility agreement with covenant package.', 'bond_life_plus_3yr', true, 211);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('6d025c4c-c045-4f94-8659-3a6a7e4e5133', 'operating_agreement', 'Operating Agreement', 'negotiated', 're', 'Entity governance and member economics agreement.', 'indefinite', true, 212);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('09ad4a1b-6bae-4dd4-8bc4-f5d2180a5ef3', 'tip_fee_agreement', 'Tip Fee Agreement', 'negotiated', 'project_finance', 'Waste intake contract with volume and pricing escalation mechanics.', 'bond_life_plus_3yr', true, 220);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('d9275349-181e-4944-be1c-9d3e2c0d536a', 'power_purchase_agreement', 'Power Purchase Agreement (PPA)', 'negotiated', 'project_finance', 'Electricity offtake contract with pricing and availability terms.', 'bond_life_plus_3yr', true, 221);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('3880e6ef-d573-4f36-a2f9-f8dcecc1a57a', 'interconnection_agreement', 'Interconnection Agreement', 'negotiated', 'project_finance', 'Grid interconnection terms and operational responsibilities.', 'bond_life_plus_3yr', true, 222);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('fbf698ed-c7ca-40cc-adf2-81a341f02658', 'environmental_permit', 'Environmental Permit and Compliance Pack', 'regulatory', 'project_finance', 'Environmental permits, approvals, and monitoring obligations.', 'indefinite', false, 223);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('dbe64011-7bf9-4280-bb67-b90f4f257c24', 'lease_agreement', 'Lease Agreement', 'negotiated', 're', 'Tenant lease terms governing rent, escalation, and remedies.', 'standard_6yr', true, 230);

INSERT INTO deal_document_types (id, code, display_name, category, deal_vertical, description, retention_policy, requires_signature, sort_order) VALUES ('4a905a64-126b-4ae3-920b-58abc660eaff', 'property_management_agreement', 'Property Management Agreement', 'negotiated', 're', 'Third-party property operations and service-level agreement.', 'standard_6yr', true, 231);

UPDATE alembic_version SET version_num='h8i9j0k1l2m3' WHERE alembic_version.version_num = 'g7h8i9j0k1l2';

-- Running upgrade f6a7b8c9d0e1 -> a7b8c9d0e1f2

ALTER TABLE extracted_facts
        ADD COLUMN IF NOT EXISTS fingerprint VARCHAR(128);

ALTER TABLE extracted_facts
        ADD COLUMN IF NOT EXISTS duplicate_classification VARCHAR(32) NOT NULL DEFAULT 'unique';

ALTER TABLE extracted_facts
        ADD COLUMN IF NOT EXISTS source_trust_score DOUBLE PRECISION NOT NULL DEFAULT 0.5;

ALTER TABLE extracted_facts
        ADD COLUMN IF NOT EXISTS canonical_score DOUBLE PRECISION NOT NULL DEFAULT 0.0;

ALTER TABLE extracted_facts
        ADD COLUMN IF NOT EXISTS is_canonical BOOLEAN NOT NULL DEFAULT false;

ALTER TABLE extracted_facts
        ADD COLUMN IF NOT EXISTS lifecycle_state VARCHAR(20) NOT NULL DEFAULT 'active';

ALTER TABLE extracted_facts
        ADD COLUMN IF NOT EXISTS archive_reason_code VARCHAR(64);

ALTER TABLE extracted_facts
        ADD COLUMN IF NOT EXISTS archive_note TEXT;

ALTER TABLE extracted_facts
        ADD COLUMN IF NOT EXISTS archived_by UUID;

ALTER TABLE extracted_facts
        ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ;

DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_extracted_facts_archived_by_users'
            ) THEN
                ALTER TABLE extracted_facts
                ADD CONSTRAINT fk_extracted_facts_archived_by_users
                FOREIGN KEY (archived_by) REFERENCES users(id);
            END IF;
        END$$;;

UPDATE extracted_facts
        SET lifecycle_state = CASE
            WHEN review_status = 'rejected' THEN 'rejected'
            WHEN review_status = 'pending' THEN 'pending_review'
            ELSE 'active'
        END;

UPDATE extracted_facts
        SET duplicate_classification = 'unique'
        WHERE duplicate_classification IS NULL OR duplicate_classification = '';

UPDATE extracted_facts
        SET source_trust_score = 0.5
        WHERE source_trust_score IS NULL;

UPDATE extracted_facts
        SET canonical_score = 0.0
        WHERE canonical_score IS NULL;

UPDATE extracted_facts
        SET is_canonical = false
        WHERE is_canonical IS NULL;

CREATE INDEX IF NOT EXISTS ix_extracted_facts_fingerprint
        ON extracted_facts (fingerprint);

CREATE INDEX IF NOT EXISTS ix_extracted_facts_duplicate_classification
        ON extracted_facts (duplicate_classification);

CREATE INDEX IF NOT EXISTS ix_extracted_facts_is_canonical
        ON extracted_facts (is_canonical);

CREATE INDEX IF NOT EXISTS ix_extracted_facts_lifecycle_state
        ON extracted_facts (lifecycle_state);

INSERT INTO alembic_version (version_num) VALUES ('a7b8c9d0e1f2') RETURNING alembic_version.version_num;

-- Running upgrade a7b8c9d0e1f2 -> b8c9d0e1f2a3

ALTER TABLE projects ADD COLUMN tenant_id VARCHAR(100) DEFAULT 'default' NOT NULL;

CREATE INDEX ix_projects_tenant_id ON projects (tenant_id);

UPDATE projects AS p
                SET tenant_id = COALESCE(NULLIF(TRIM(u.organization), ''), 'default')
                FROM users AS u
                WHERE p.owner_id = u.id;

ALTER TABLE projects ALTER COLUMN tenant_id DROP DEFAULT;

UPDATE alembic_version SET version_num='b8c9d0e1f2a3' WHERE alembic_version.version_num = 'a7b8c9d0e1f2';

-- Running upgrade b8c9d0e1f2a3, h8i9j0k1l2m3 -> i9j0k1l2m3n4

DELETE FROM alembic_version WHERE alembic_version.version_num = 'b8c9d0e1f2a3';

UPDATE alembic_version SET version_num='i9j0k1l2m3n4' WHERE alembic_version.version_num = 'h8i9j0k1l2m3';

-- Running upgrade i9j0k1l2m3n4 -> ffdbab55c977

CREATE TABLE sensing_leads (
    id UUID NOT NULL, 
    email VARCHAR(255) NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    organization VARCHAR(255) NOT NULL, 
    title VARCHAR(255), 
    phone VARCHAR(50), 
    sector VARCHAR(50) NOT NULL, 
    deal_size_estimate FLOAT, 
    state VARCHAR(5), 
    expected_rating VARCHAR(10), 
    referral_source VARCHAR(255), 
    funnel_stage VARCHAR(50) NOT NULL, 
    market_intel_json TEXT, 
    benchmark_json TEXT, 
    readiness_json TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_sensing_leads_email ON sensing_leads (email);

CREATE TABLE sensing_events (
    id UUID NOT NULL, 
    lead_id VARCHAR(36), 
    session_id VARCHAR(100) NOT NULL, 
    event_type VARCHAR(50) NOT NULL, 
    sector VARCHAR(50), 
    event_data TEXT, 
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_sensing_events_lead_id ON sensing_events (lead_id);

CREATE INDEX ix_sensing_events_session_id ON sensing_events (session_id);

UPDATE alembic_version SET version_num='ffdbab55c977' WHERE alembic_version.version_num = 'i9j0k1l2m3n4';

-- Running upgrade ffdbab55c977 -> a1b2c3d4e5f7

ALTER TABLE sensing_leads ADD COLUMN email_sequence_step INTEGER DEFAULT '0' NOT NULL;

ALTER TABLE sensing_leads ADD COLUMN last_email_sent_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE sensing_leads ADD COLUMN unsubscribed BOOLEAN DEFAULT '0' NOT NULL;

ALTER TABLE sensing_leads ADD COLUMN unsubscribe_token VARCHAR(36) DEFAULT '' NOT NULL;

UPDATE sensing_leads SET unsubscribe_token = gen_random_uuid()::text WHERE unsubscribe_token = '';

ALTER TABLE sensing_leads ADD CONSTRAINT uq_sensing_leads_unsubscribe_token UNIQUE (unsubscribe_token);

UPDATE alembic_version SET version_num='a1b2c3d4e5f7' WHERE alembic_version.version_num = 'ffdbab55c977';

-- Running upgrade a1b2c3d4e5f7 -> b2c3d4e5f6g8

ALTER TABLE users ADD COLUMN subscription_tier VARCHAR(50);

ALTER TABLE users ADD COLUMN stripe_customer_id VARCHAR(255);

ALTER TABLE users ADD COLUMN stripe_subscription_id VARCHAR(255);

UPDATE alembic_version SET version_num='b2c3d4e5f6g8' WHERE alembic_version.version_num = 'a1b2c3d4e5f7';

-- Running upgrade b2c3d4e5f6g8 -> c3d4e5f6g7h9

ALTER TABLE projects ADD COLUMN sector VARCHAR(100);

ALTER TABLE projects ADD COLUMN subsector VARCHAR(150);

ALTER TABLE projects ADD COLUMN archetype_id VARCHAR(150);

ALTER TABLE projects ADD COLUMN archetype_version VARCHAR(20);

CREATE INDEX ix_projects_sector ON projects (sector);

CREATE INDEX ix_projects_subsector ON projects (subsector);

CREATE INDEX ix_projects_archetype_id ON projects (archetype_id);

UPDATE alembic_version SET version_num='c3d4e5f6g7h9' WHERE alembic_version.version_num = 'b2c3d4e5f6g8';

-- Running upgrade c3d4e5f6g7h9 -> d4e5f6g7h8i0

CREATE TABLE ask_conversations (
    id UUID NOT NULL, 
    owner_id UUID NOT NULL, 
    project_id UUID NOT NULL, 
    artifact_id UUID, 
    title VARCHAR(120) NOT NULL, 
    next_sequence INTEGER DEFAULT '1' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(owner_id) REFERENCES users (id) ON DELETE CASCADE, 
    FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE CASCADE, 
    FOREIGN KEY(artifact_id) REFERENCES artifacts (id) ON DELETE CASCADE
);

CREATE INDEX ix_ask_conversations_owner_id ON ask_conversations (owner_id);

CREATE INDEX ix_ask_conversations_project_id ON ask_conversations (project_id);

CREATE TABLE ask_messages (
    id UUID NOT NULL, 
    conversation_id UUID NOT NULL, 
    sequence INTEGER NOT NULL, 
    role VARCHAR(20) NOT NULL, 
    kind VARCHAR(20) NOT NULL, 
    content TEXT NOT NULL, 
    citations JSON NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_ask_message_sequence UNIQUE (conversation_id, sequence), 
    FOREIGN KEY(conversation_id) REFERENCES ask_conversations (id) ON DELETE CASCADE
);

CREATE INDEX ix_ask_messages_conversation_id ON ask_messages (conversation_id);

UPDATE alembic_version SET version_num='d4e5f6g7h8i0' WHERE alembic_version.version_num = 'c3d4e5f6g7h9';

-- Running upgrade d4e5f6g7h8i0 -> e5f6g7h8i9j0

CREATE TABLE register_deals (
    id UUID NOT NULL, 
    owner_id UUID NOT NULL, 
    tenant_id VARCHAR(255) NOT NULL, 
    name VARCHAR(200) NOT NULL, 
    legal_name VARCHAR(255) NOT NULL, 
    professional_contact VARCHAR(1000) NOT NULL, 
    consent_version VARCHAR(50) NOT NULL, 
    payment_status VARCHAR(30) NOT NULL, 
    amount_cents INTEGER, 
    currency VARCHAR(3) NOT NULL, 
    quote_note TEXT, 
    quote_version INTEGER NOT NULL, 
    quoted_by UUID, 
    checkout_session_id VARCHAR(255), 
    checkout_url TEXT, 
    payment_intent_id VARCHAR(255), 
    report_sequence INTEGER NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(owner_id) REFERENCES users (id), 
    FOREIGN KEY(quoted_by) REFERENCES users (id), 
    UNIQUE (checkout_session_id), 
    UNIQUE (payment_intent_id)
);

CREATE INDEX ix_register_deals_owner_id ON register_deals (owner_id);

CREATE TABLE register_documents (
    id UUID NOT NULL, 
    deal_id UUID NOT NULL, 
    filename VARCHAR(200) NOT NULL, 
    sha256 VARCHAR(64) NOT NULL, 
    size INTEGER NOT NULL, 
    content BYTEA NOT NULL, 
    extracted JSON NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_register_document_hash UNIQUE (deal_id, sha256), 
    FOREIGN KEY(deal_id) REFERENCES register_deals (id) ON DELETE CASCADE
);

CREATE TABLE register_folders (
    id UUID NOT NULL, 
    deal_id UUID NOT NULL, 
    url TEXT NOT NULL, 
    status VARCHAR(30) NOT NULL, 
    note TEXT, 
    updated_by UUID, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(deal_id) REFERENCES register_deals (id) ON DELETE CASCADE, 
    FOREIGN KEY(updated_by) REFERENCES users (id)
);

CREATE TABLE register_reports (
    id UUID NOT NULL, 
    deal_id UUID NOT NULL, 
    version INTEGER NOT NULL, 
    kind VARCHAR(30) NOT NULL, 
    note TEXT, 
    published_by UUID, 
    candidate_count INTEGER NOT NULL, 
    document_count INTEGER NOT NULL, 
    content BYTEA NOT NULL, 
    sha256 VARCHAR(64) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_register_report_version UNIQUE (deal_id, version), 
    FOREIGN KEY(deal_id) REFERENCES register_deals (id) ON DELETE CASCADE, 
    FOREIGN KEY(published_by) REFERENCES users (id)
);

CREATE TABLE register_payment_reversals (
    payment_intent_id VARCHAR(255) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (payment_intent_id)
);

CREATE INDEX ix_register_documents_deal_id ON register_documents (deal_id);

CREATE INDEX ix_register_folders_deal_id ON register_folders (deal_id);

CREATE INDEX ix_register_reports_deal_id ON register_reports (deal_id);

ALTER TABLE register_deals ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE register_deals FROM PUBLIC;

ALTER TABLE register_documents ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE register_documents FROM PUBLIC;

ALTER TABLE register_folders ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE register_folders FROM PUBLIC;

ALTER TABLE register_reports ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE register_reports FROM PUBLIC;

ALTER TABLE register_payment_reversals ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE register_payment_reversals FROM PUBLIC;

UPDATE alembic_version SET version_num='e5f6g7h8i9j0' WHERE alembic_version.version_num = 'd4e5f6g7h8i0';

COMMIT;
