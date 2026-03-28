/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Funnel event tracking.
 */
export type EventRequest = {
    /**
     * Optional JSON payload
     */
    event_data?: (string | null);
    /**
     * Event type (page_view, benchmark_run, etc.)
     */
    event_type: string;
    sector?: (string | null);
    /**
     * Client session ID
     */
    session_id: string;
};

