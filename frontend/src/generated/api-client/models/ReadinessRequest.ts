/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type ReadinessRequest = {
    /**
     * Minimum coverage ratio
     */
    coverage_ratio?: (number | null);
    /**
     * Debt Service Coverage Ratio
     */
    dscr?: (number | null);
    /**
     * Evidence item IDs present (e.g., risk.technology.evidence.1)
     */
    evidence_ids?: Array<string>;
    /**
     * Project name
     */
    project_name?: string;
    /**
     * Dimension responses (e.g., risk.technology.description: true)
     */
    responses?: Record<string, boolean>;
    /**
     * Annual revenue in USD
     */
    revenue?: (number | null);
    /**
     * Sector (waste, healthcare)
     */
    sector: string;
};

