/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Lead info submitted before combined report PDF download.
 */
export type LeadCaptureRequest = {
    /**
     * Benchmark results JSON
     */
    benchmark_json?: (string | null);
    /**
     * Lead privacy consent version accepted by the submitter
     */
    consent_version?: string;
    /**
     * Estimated deal size USD
     */
    deal_size_estimate?: (number | null);
    /**
     * Contact email
     */
    email: string;
    /**
     * Expected rating
     */
    expected_rating?: (string | null);
    /**
     * Market intelligence report JSON
     */
    market_intel_json?: (string | null);
    /**
     * Full name
     */
    name: string;
    /**
     * Organization / entity name
     */
    organization: string;
    /**
     * Phone number
     */
    phone?: (string | null);
    /**
     * Affirmative consent to collect contact details and report snapshots for report delivery and pilot-fit review
     */
    privacy_consent?: boolean;
    /**
     * Readiness assessment JSON
     */
    readiness_json?: (string | null);
    /**
     * How they heard about us
     */
    referral_source?: (string | null);
    /**
     * Primary sector of interest
     */
    sector: string;
    /**
     * Client session ID for event linkage
     */
    session_id: string;
    /**
     * State abbreviation
     */
    state?: (string | null);
    /**
     * Job title / role
     */
    title?: (string | null);
};

