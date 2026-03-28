/**
 * OpenAPI-generated frontend client entrypoint.
 *
 * This is intentionally separate from the legacy hand-authored API layer to
 * support incremental migration to contract-generated clients.
 */

import {
  ApiError,
  OpenAPI,
  AdvisoryPackagesService,
  ArtifactsService,
  ChecklistService,
  DeliverablesService,
  DisclosureService,
  ExtractionService,
  FactsService,
  HealthService,
  InformationRequestsService,
  PlaybooksService,
  ProjectsService,
  ReadinessService,
  RiskService,
} from '../generated/api-client';

const DEV_USER_ID = '00000000-0000-0000-0000-000000000001';
const DEV_USER_ROLE = 'admin';
const TOKEN_STORAGE_KEY = 'munipal_api_bearer_token';

const configuredBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? '').trim();
const configuredBearerToken = (import.meta.env.VITE_API_BEARER_TOKEN ?? '').trim();
const configuredDevUserId = (import.meta.env.VITE_DEV_USER_ID ?? DEV_USER_ID).trim();
const configuredDevUserRole = (import.meta.env.VITE_DEV_USER_ROLE ?? DEV_USER_ROLE).trim();

const getStoredToken = (): string => {
  if (typeof window === 'undefined') {
    return '';
  }
  const stored = window.localStorage.getItem(TOKEN_STORAGE_KEY);
  return (stored ?? '').trim();
};

OpenAPI.BASE = configuredBaseUrl;
OpenAPI.TOKEN = async () => {
  const stored = getStoredToken();
  if (stored) {
    return stored;
  }
  return configuredBearerToken;
};
OpenAPI.HEADERS = async () => {
  const headers: Record<string, string> = {};
  const token = getStoredToken() || configuredBearerToken;
  if (!token) {
    headers['x-user-id'] = configuredDevUserId;
    headers['x-user-role'] = configuredDevUserRole;
  }
  return headers;
};

export {
  ApiError,
  OpenAPI,
  AdvisoryPackagesService,
  ArtifactsService,
  ChecklistService,
  DeliverablesService,
  DisclosureService,
  ExtractionService,
  FactsService,
  HealthService,
  InformationRequestsService,
  PlaybooksService,
  ProjectsService,
  ReadinessService,
  RiskService,
};
