/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DealVertical } from './DealVertical';
/**
 * Input for deal-structure-driven clause recommendations.
 */
export type ClauseRecommendationRequest = {
    deal_features?: Array<string>;
    deal_vertical?: DealVertical;
    document_type_code?: (string | null);
    jurisdiction?: (string | null);
    limit?: number;
    text_query?: (string | null);
};

