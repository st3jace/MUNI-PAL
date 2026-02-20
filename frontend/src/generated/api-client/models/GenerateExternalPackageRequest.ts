/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Request to generate an external advisory package.
 */
export type GenerateExternalPackageRequest = {
    force_regenerate?: boolean;
    generated_for: string;
    include_disclosure?: boolean;
    project_id: string;
    title: string;
};

