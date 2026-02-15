import type { ApiReportResponse } from '../domain/types';
import { apiGet } from './apiClient';

export type ReportQuery = {
  schemaVersion?: string;
};

export function getReport(simulationId: string, query: ReportQuery = {}): Promise<ApiReportResponse> {
  const schemaVersion = query.schemaVersion ?? '1.0';
  const encodedId = encodeURIComponent(simulationId);
  return apiGet<ApiReportResponse>(`/simulations/${encodedId}/report?schema_version=${encodeURIComponent(schemaVersion)}`, 3000);
}
