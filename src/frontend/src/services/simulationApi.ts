import type { StartSimulationPayload, StartSimulationResponse } from '../domain/types';
import { apiPost } from './apiClient';

export function startSimulation(payload: StartSimulationPayload): Promise<StartSimulationResponse> {
  return apiPost<StartSimulationResponse, StartSimulationPayload>('/simulations', payload, 2500);
}
