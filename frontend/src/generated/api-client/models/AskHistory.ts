/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AskMessageRead } from './AskMessageRead';
export type AskHistory = {
    artifact_id: (string | null);
    created_at: string;
    id: string;
    messages: Array<AskMessageRead>;
    project_id: string;
    title: string;
    updated_at: string;
};

