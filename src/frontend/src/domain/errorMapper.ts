import { ApiClientError } from '../services/apiClient';
import type { UiError } from './types';

const CODE_MESSAGE_MAP: Record<string, string> = {
  REPORT_NOT_READY: '시뮬레이션이 아직 완료되지 않았습니다.',
  SIMULATION_NOT_FOUND: '시뮬레이션을 찾을 수 없습니다.',
  REPORT_SCHEMA_NOT_SUPPORTED: '지원하지 않는 스키마 버전입니다.',
  SIMULATION_FAILED: '시뮬레이션 실행 중 오류가 발생했습니다.',
};

export function toUiError(error: unknown): UiError {
  if (error instanceof ApiClientError) {
    const messageKo = CODE_MESSAGE_MAP[error.code ?? ''] ?? error.message ?? '요청 처리 중 오류가 발생했습니다.';
    return {
      code: error.code ?? `HTTP_${error.status ?? 0}`,
      messageKo,
      requestId: error.requestId,
      recoverable: (error.status ?? 500) < 500,
    };
  }

  return {
    code: 'UNKNOWN_ERROR',
    messageKo: '알 수 없는 오류가 발생했습니다.',
    recoverable: false,
  };
}
