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

OpenAPI.BASE = '';
OpenAPI.HEADERS = {
  'x-user-id': '00000000-0000-0000-0000-000000000001',
  'x-user-role': 'admin',
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
