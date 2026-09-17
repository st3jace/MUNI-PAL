/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Intake form behind /obligation-register. Facts and contacts only. No judgment fields.
 */
export type ObligationRegisterIntake = {
    bond_counsel_contact?: (string | null);
    /**
     * Have the bonds already closed?
     */
    bonds_already_closed: boolean;
    cda_present?: ('yes' | 'no' | 'not_sure' | null);
    /**
     * Asking us to work a new or contemplated issuance at the same time?
     */
    concurrent_preissuance: boolean;
    consent_version?: string;
    contact_email: string;
    contact_name: string;
    contact_phone?: (string | null);
    contact_title?: (string | null);
    dissemination_agent_contact?: (string | null);
    documents_on_hand?: (string | null);
    entity_type: ObligationRegisterIntake.entity_type;
    instrument_count?: (number | null);
    instrument_list: string;
    legal_name: string;
    municipal_advisor_contact?: (string | null);
    privacy_consent?: boolean;
    session_id?: (string | null);
    state?: (string | null);
    /**
     * Which live session you attended, if any (date and time)
     */
    workshop_session?: (string | null);
};
export namespace ObligationRegisterIntake {
    export enum entity_type {
        PRIVATE_OBLIGATED_PERSON = 'private_obligated_person',
        MUNICIPAL_ENTITY = 'municipal_entity',
        UNCLEAR = 'unclear',
    }
}

