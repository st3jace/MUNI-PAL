/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AskCitation } from './AskCitation';
export type AskMessageRead = {
    citations: Array<AskCitation>;
    content: string;
    created_at: string;
    id: string;
    kind: AskMessageRead.kind;
    role: AskMessageRead.role;
    sequence: number;
    updated_at: string;
};
export namespace AskMessageRead {
    export enum kind {
        QUESTION = 'question',
        EVIDENCE = 'evidence',
        REFUSAL = 'refusal',
        NO_HITS = 'no_hits',
    }
    export enum role {
        USER = 'user',
        ASSISTANT = 'assistant',
    }
}

