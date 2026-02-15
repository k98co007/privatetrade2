import type { ApiEnvelope } from '../domain/types';

const API_BASE = '/api';

export class ApiClientError extends Error {
  status?: number;
  code?: string;
  requestId?: string;
  details?: Record<string, unknown>;

  constructor(message: string, options?: { status?: number; code?: string; requestId?: string; details?: Record<string, unknown> }) {
    super(message);
    this.name = 'ApiClientError';
    this.status = options?.status;
    this.code = options?.code;
    this.requestId = options?.requestId;
    this.details = options?.details;
  }
}

async function request<T>(path: string, init: RequestInit, timeoutMs = 2500): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${API_BASE}${path}`, {
      ...init,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...(init.headers ?? {}),
      },
    });

    let payload: ApiEnvelope<T> | null = null;
    try {
      payload = (await response.json()) as ApiEnvelope<T>;
    } catch {
      payload = null;
    }

    if (!response.ok || !payload?.success) {
      throw new ApiClientError(payload?.error?.message ?? '요청이 실패했습니다.', {
        status: response.status,
        code: payload?.error?.code,
        requestId: payload?.meta?.request_id,
        details: payload?.error?.details,
      });
    }

    return payload.data;
  } catch (error) {
    if (error instanceof ApiClientError) {
      throw error;
    }
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiClientError('요청 시간이 초과되었습니다.', { status: 408, code: 'TIMEOUT' });
    }
    throw new ApiClientError('네트워크 오류가 발생했습니다.', { status: 0, code: 'NETWORK_ERROR' });
  } finally {
    clearTimeout(timer);
  }
}

export function apiGet<T>(path: string, timeoutMs?: number): Promise<T> {
  return request<T>(path, { method: 'GET' }, timeoutMs);
}

export function apiPost<TResponse, TBody extends object>(path: string, body: TBody, timeoutMs?: number): Promise<TResponse> {
  return request<TResponse>(path, { method: 'POST', body: JSON.stringify(body) }, timeoutMs);
}
