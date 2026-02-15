# 구현수준 설계 문서 (ILD)
# Implementation-Level Design Document - FRONTEND

| 항목 | 내용 |
|------|------|
| **문서 버전** | 1.0.0 |
| **작성일** | 2026-02-16 |
| **대상 모듈** | FRONTEND (프론트엔드 UI 모듈) |
| **기반 문서** | LLD FRONTEND v1.0.0, HLD v1.0.0 (4.7, 5.1~5.3, 6.2), SRS v1.0.0 (FR-010~FR-015, NFR-003, NFR-004), ILD WEBAPI/REPORT v1.0.0 |
| **관련 티켓** | TICKET-015-ILD-FRONTEND |

---

## 목차

1. [목적 및 범위](#1-목적-및-범위)
2. [구현 단위/파일 구조](#2-구현-단위파일-구조)
3. [도메인 타입/상태 정규화 계약](#3-도메인-타입상태-정규화-계약)
4. [페이지/컴포넌트 구현 계약 (Props/State/Events)](#4-페이지컴포넌트-구현-계약-propsstateevents)
5. [훅/스토어 구현 계약 (REST/SSE 연동)](#5-훅스토어-구현-계약-restsse-연동)
6. [REST/SSE 수명주기/재연결/오류 UI 플로우](#6-restsse-수명주기재연결오류-ui-플로우)
7. [검증/로딩/오류/완료 상태 전이 상세](#7-검증로딩오류완료-상태-전이-상세)
8. [성능/사용성 제약 반영 (NFR-003, NFR-004)](#8-성능사용성-제약-반영-nfr-003-nfr-004)
9. [실행 가능한 언어 중립 수도코드](#9-실행-가능한-언어-중립-수도코드)
10. [요구사항/설계 추적성 매트릭스 (SRS + LLD)](#10-요구사항설계-추적성-매트릭스-srs--lld)
11. [구현 체크리스트 (주니어 개발자용)](#11-구현-체크리스트-주니어-개발자용)

---

## 1. 목적 및 범위

### 1.1 목적

본 문서는 `lld-frontend-v1.0.0.md`를 실제 코드로 구현하기 위한 **구현 수준(ILD)** 명세를 제공한다. 페이지/컴포넌트 계약(Props/State/Events), Zustand 스토어 구조, REST/SSE 수명주기, 이벤트 정규화·캐시 규칙, 오류 UI 복구 플로우를 함수 단위로 고정하여 초급 개발자가 문서만으로 구현 가능하도록 한다.

### 1.2 범위 (In-Scope)

- 시작/모니터링/결과 3개 페이지의 구현 계약
- `POST /api/simulations`, `GET /api/simulations/{id}/report`, `GET /api/simulations/{id}/stream` 연동 상세
- SSE 재연결(지수 백오프), 이벤트 중복 제거, 마지막 이벤트 ID 기반 복구
- 입력 검증/로딩/오류/완료 상태 전이 및 UI 표현 규칙
- 결과 데이터 캐시 및 상태 정규화 전략
- FR-010~FR-015, NFR-003, NFR-004 추적성 확보

### 1.3 비범위 (Out-of-Scope)

- 시뮬레이션 계산 알고리즘/전략 로직
- 백엔드 REST/SSE 엔드포인트 구현
- 서버 저장소/트랜잭션 구현
- 디자인 테마 확장 및 고급 시각화(차트 추가)

---

## 2. 구현 단위/파일 구조

다음 구조를 기준으로 구현한다.

```text
src/
  frontend/
    app/
      App.tsx
      routes.tsx
      ErrorBoundary.tsx
    pages/
      SimulationStartPage.tsx
      MonitoringPage.tsx
      ResultPage.tsx
    components/
      SymbolInput.tsx
      StrategySelector.tsx
      StatusBadge.tsx
      ProgressBar.tsx
      EventLog.tsx
      ProfitSummaryCard.tsx
      TradeHistoryTable.tsx
      ComprehensiveReportCard.tsx
    store/
      simulationStore.ts
      reportStore.ts
      uiStore.ts
      selectors.ts
    hooks/
      useStartSimulation.ts
      useMonitoringSse.ts
      useReportQuery.ts
      useNetworkStatus.ts
    services/
      apiClient.ts
      simulationApi.ts
      reportApi.ts
      sseClient.ts
    domain/
      types.ts
      mappers.ts
      validators.ts
      normalizers.ts
      errorMapper.ts
    utils/
      formatters.ts
      retry.ts
      time.ts
```

### 2.1 파일별 책임

| 파일/폴더 | 주요 책임 |
|-----------|-----------|
| `app/` | 라우팅, 전역 오류 바운더리, 공통 레이아웃 |
| `pages/` | 화면 단위 오케스트레이션 (폼 제출, 모니터링 연결, 결과 조회) |
| `components/` | 프리젠테이션 컴포넌트, 접근성 속성 포함 렌더링 |
| `store/` | 단일 원천 상태(State Source of Truth), 액션/셀렉터 |
| `hooks/` | API/SSE 생명주기와 UI 이벤트 연결 |
| `services/` | REST/SSE 통신 캡슐화, 타임아웃/에러 표준화 |
| `domain/` | 타입 정의, 응답 정규화, 검증/오류 매핑 |
| `utils/` | 금액/날짜 포맷팅, 백오프 계산 |

---

## 3. 도메인 타입/상태 정규화 계약

### 3.1 핵심 타입 계약

| 타입 | 필드 | 규칙 |
|------|------|------|
| `SimulationStatus` | `idle|starting|running|completed|error` | 화면 상태 분기의 단일 기준 |
| `SimulationMeta` | `simulationId, symbol, strategy` | 시작 성공 후 고정 |
| `ProgressState` | `currentDay, totalDays, progressPct, tradingDate` | `progressPct`는 0~100 |
| `EventItem` | `eventId, eventType, eventTime, payload` | `eventId` 단조 증가 가정 |
| `ReportCacheEntry` | `simulationId, schemaVersion, fetchedAt, report` | fresh 판정용 메타 포함 |
| `UiError` | `code, messageKo, requestId?, recoverable` | 한국어 메시지 필수 |

### 3.2 상태 정규화 정책

#### 3.2.1 `simulationStore`

```text
simulationStore = {
  currentSimulationId: string | null,
  byId: {
    [simulationId]: {
      meta,
      status,
      progress,
      lastAppliedEventId,
      eventIds[]
    }
  },
  eventsById: {
    [eventId]: EventItem
  }
}
```

규칙:
1. 이벤트는 `eventsById` + `eventIds[]`로 분리 저장한다(중복 렌더링/복사 최소화).
2. `eventIds` 길이는 최대 500으로 제한한다(초과 시 앞에서 제거).
3. `lastAppliedEventId` 이하 이벤트는 적용하지 않는다(멱등 보장).
4. `currentSimulationId` 변경 시 이전 시뮬레이션 상태는 보존하되 구독은 분리한다.

#### 3.2.2 `reportStore`

```text
reportStore = {
  cacheBySimulationId: {
    [simulationId]: ReportCacheEntry
  },
  activeSimulationId: string | null,
  isLoading: boolean,
  error: UiError | null
}
```

규칙:
1. 보고서는 `simulationId` 키로 캐시한다.
2. 동일 `simulationId` 재진입 시 캐시가 30초 이내면 즉시 렌더링 후 백그라운드 재검증한다.
3. 재조회 성공 시 `summary`+`trades`+`report`를 원자적으로 교체한다(부분 깜빡임 방지).
4. 조회 실패 시 마지막 성공 캐시는 유지하고 `error`만 갱신한다.

### 3.3 입력/응답 정규화 규칙

| 항목 | 규칙 |
|------|------|
| 심볼 입력 | trim 후 대문자, 정규식 `^[0-9]{6}\.KS$` 검증 |
| 전략값 | `sell_trailing_stop`, `buy_sell_trailing_stop`, `rsi_buy_sell_trailing_stop`만 허용 |
| SSE payload | 필수 필드 누락 시 무시 + 경고 토스트 |
| 거래내역 정렬 | `buy_datetime` ASC, NULL은 마지막 |
| 금액 표기 | `#,###원`, 음수는 `-` 접두 |
| 수익률 표기 | 소수점 둘째 자리 (`0.00%`) |

---

## 4. 페이지/컴포넌트 구현 계약 (Props/State/Events)

### 4.1 페이지 계약

| 페이지 | Props | Local State | 주요 이벤트 | 구현 계약 |
|--------|-------|-------------|-------------|-----------|
| `SimulationStartPage` | 없음 | `symbolInput`, `strategy`, `fieldErrors`, `isSubmitting` | `onSubmit`, `onSymbolBlur`, `onRetry` | 검증 통과 시 `startSimulation` 호출, 202 수신 시 모니터링 이동 |
| `MonitoringPage` | `simulationId`(route) | `isSseConnected`, `reconnectCount` | `onMountAttach`, `onManualReconnect`, `onGoResult` | SSE 수신으로 상태 갱신, `completed` 시 결과 페이지 이동 |
| `ResultPage` | `simulationId`(route) | 없음 | `onMountFetch`, `onRetryFetch`, `onRefresh` | 캐시 우선 렌더 + 조건부 재검증, 실패 시 재시도 버튼 |

### 4.2 핵심 컴포넌트 계약

| 컴포넌트 | Props | Events | 상태/UI 규칙 |
|---------|-------|--------|-------------|
| `SymbolInput` | `value, error, disabled, onChange, onBlur` | `input, blur, paste` | blur 시 인라인 오류, `aria-invalid` 반영 |
| `StrategySelector` | `value, options, error, disabled, onChange` | `change` | 3개 전략 외 값 선택 불가 |
| `StatusBadge` | `status, message?` | 없음 | `running/완료/오류` 텍스트+스타일 명확 구분 |
| `ProgressBar` | `currentDay, totalDays, progressPct, tradingDate` | 없음 | 텍스트+바 동기 렌더 (`15/42일 완료`) |
| `EventLog` | `items, maxItems=500` | `onToggleAutoScroll, onClear` | 이벤트 타입 라벨(매수/매도/시스템) 표시 |
| `ProfitSummaryCard` | `initialSeed, finalSeed, totalProfit, totalProfitRate` | 없음 | FR-013 표기 규칙 준수 |
| `TradeHistoryTable` | `rows, loading, emptyText` | `onSortChange` | FR-014 14개 컬럼 표시, 시간순 정렬 기본 |
| `ComprehensiveReportCard` | `summary` | 없음 | FR-015 통계(총거래/승률/손익총액) 표시 |

### 4.3 컴포넌트 불변 조건

1. 렌더 함수는 외부 부수효과를 가지지 않는다.
2. API 호출은 페이지 또는 훅에서만 수행하고 프리젠테이션 컴포넌트에서는 수행하지 않는다.
3. 오류 메시지는 `errorMapper`를 통해 한국어로만 노출한다.
4. 로딩 상태와 버튼 비활성 상태는 항상 함께 갱신한다.

---

## 5. 훅/스토어 구현 계약 (REST/SSE 연동)

### 5.1 `useStartSimulation`

| 함수 | 입력 | 반환 | 실패 |
|------|------|------|------|
| `submitStart({symbol, strategy})` | 시작 폼 값 | `Promise<{simulationId}>` | `UiError` throw + 폼 오류 세팅 |

처리 규칙:
1. 클라이언트 검증 통과 후 `POST /api/simulations` 호출.
2. `202` 수신 시 `simulationStore.createSimulation()` + `status='running'`.
3. `400`은 필드 오류로 매핑, `5xx`는 배너 오류로 매핑.
4. 중복 클릭 방지를 위해 in-flight 동안 재호출 차단.

### 5.2 `useMonitoringSse`

| 함수 | 입력 | 반환 | 비고 |
|------|------|------|------|
| `connect(simulationId)` | string | disconnect 함수 | mount 시 자동 실행 |
| `reconnect()` | - | void | 사용자 수동 재시도 |

처리 규칙:
1. 기본 재시도: `1s, 2s, 4s, 8s, 10s`, 최대 5회.
2. `Last-Event-ID`를 저장/전달하여 이벤트 재생 간격 최소화.
3. `progress/trade/heartbeat/completed/error` 타입별 핸들러 분리.
4. `completed` 수신 즉시 연결 종료 후 결과 페이지 이동.
5. 최대 재시도 초과 시 `status='error'`, 수동 재연결 버튼 활성.

### 5.3 `useReportQuery`

| 함수 | 입력 | 반환 | 캐시 규칙 |
|------|------|------|-----------|
| `loadReport(simulationId)` | string | `Promise<ComprehensiveReport>` | fresh(30초)이면 즉시 반환 |
| `refreshReport(simulationId)` | string | `Promise<void>` | 네트워크 우선 갱신 |

처리 규칙:
1. `GET /api/simulations/{id}/report` 성공 시 `reportStore.upsertCache`.
2. `404`는 안내 메시지 + 시작 화면 이동 액션 제공.
3. `409 REPORT_NOT_READY`는 대기 안내 + 재시도 버튼 제공.
4. `schema_version` 불일치(406)는 치명 오류로 처리.

### 5.4 서비스 함수 계약

| 서비스 | 시그니처 | 응답 |
|--------|----------|------|
| `simulationApi.startSimulation` | `(payload: {symbol, strategy})` | `{simulation_id, status}` |
| `reportApi.getReport` | `(simulationId, query?)` | `ComprehensiveReport` |
| `sseClient.open` | `({simulationId, lastEventId, handlers})` | `EventSourceLike` |

---

## 6. REST/SSE 수명주기/재연결/오류 UI 플로우

### 6.1 시작 → 모니터링 연결 수명주기

1. 사용자가 시작 제출.
2. `POST /api/simulations` 성공(`202`) 시 `simulationId` 획득.
3. `/monitoring/:simulationId`로 라우팅.
4. `useMonitoringSse.connect(simulationId)` 호출.
5. 1초 이내 `progress|heartbeat` 미수신 시 연결 경고 상태 표시.

### 6.2 SSE 이벤트 처리 규칙

| 이벤트 | 검증 | 상태 반영 | UI 반영 |
|--------|------|-----------|---------|
| `progress` | day/total/pct 필수 | `progress` 갱신, `status=running` | 진행률 바/거래일 텍스트 업데이트 |
| `trade` | type/datetime/price/qty 필수 | 이벤트 로그 append | EventLog 행 추가 |
| `heartbeat` | timestamp 필수 | `lastHeartbeatAt` 갱신 | 연결 정상 표시 유지 |
| `completed` | simulation_id 일치 | `status=completed` | 결과 페이지 자동 이동 |
| `error` | code/message 필수 | `status=error`, error 세팅 | 배너 + 재연결 버튼 |

### 6.3 재연결/복구 UI 플로우

1. 연결 에러 발생 시 상태를 `degraded`로 표시.
2. 자동 재연결 중에는 `재연결 중 (n/5)` 메시지 표시.
3. 성공 시 `degraded → online` 전환, 토스트 `연결이 복구되었습니다.` 출력.
4. 5회 실패 시 `error` 고정, `다시 연결` 버튼으로 수동 재시도 제공.
5. 수동 재시도 성공 시 마지막 eventId 기준 누락 이벤트 재적용.

### 6.4 결과 조회 플로우

1. `ResultPage` 진입 시 캐시 확인.
2. fresh 캐시 존재 시 즉시 렌더링 후 백그라운드 재조회.
3. 캐시 없음 또는 stale 시 로딩 스켈레톤 노출 후 네트워크 조회.
4. 성공 시 카드/테이블/종합 리포트를 원자 교체.
5. 실패 시 오류 배너와 `재시도` 버튼 노출, 기존 캐시는 유지.

---

## 7. 검증/로딩/오류/완료 상태 전이 상세

### 7.1 시작 화면 상태 머신

| 현재 상태 | 이벤트 | 가드 | 다음 상태 | 부수효과 |
|-----------|--------|------|-----------|----------|
| `idle` | `SUBMIT` | 입력 유효 | `starting` | API 요청 시작 |
| `idle` | `SUBMIT` | 입력 무효 | `idle` | 필드 오류 표시 |
| `starting` | `START_OK` | `simulationId` 존재 | `running` | 모니터링 이동 |
| `starting` | `START_FAIL` | - | `error` | 오류 배너 표시 |
| `error` | `RETRY` | - | `starting` | 재요청 |

### 7.2 모니터링 상태 머신

| 현재 상태 | 이벤트 | 다음 상태 | UI |
|-----------|--------|-----------|----|
| `running` | `SSE_PROGRESS` | `running` | 진행률 갱신 |
| `running` | `SSE_TRADE` | `running` | 이벤트 로그 갱신 |
| `running` | `SSE_COMPLETED` | `completed` | 결과 페이지 이동 |
| `running` | `SSE_ERROR` | `error` | 배너 + 재연결 버튼 |
| `error` | `RECONNECT_OK` | `running` | 배너 해제 |
| `error` | `RECONNECT_FAIL_MAX` | `error` | 수동 재시도 유지 |

### 7.3 결과 화면 상태 머신

| 현재 상태 | 이벤트 | 다음 상태 | UI |
|-----------|--------|-----------|----|
| `idle` | `FETCH` | `loading` | 스켈레톤 |
| `loading` | `FETCH_OK` | `ready` | 요약/표/통계 노출 |
| `loading` | `FETCH_FAIL` | `error` | 오류 배너 + 재시도 |
| `error` | `RETRY` | `loading` | 재조회 |
| `ready` | `REFRESH` | `loading` | 기존 데이터 유지 + 인디케이터 |

### 7.4 검증 규칙 요약

| 항목 | 규칙 | 메시지 |
|------|------|--------|
| 심볼 | `^[0-9]{6}\.KS$` | `유효한 코스피 심볼을 입력하세요. 예: 005930.KS` |
| 전략 | 허용 3종 중 1개 | `전략 1/2/3 중 하나를 선택하세요.` |
| simulationId | URL-safe/비공백 | `시뮬레이션 ID가 올바르지 않습니다.` |

---

## 8. 성능/사용성 제약 반영 (NFR-003, NFR-004)

### 8.1 NFR-003 반영 구현 규칙

| 요구사항 | 구현 기준 |
|----------|----------|
| 웹 브라우저 사용 가능 | 라우팅 기반 SPA, 표준 `fetch`/`EventSource`만 사용 |
| 무설치 | 브라우저 기본 기능 외 의존 없음 |
| Chrome/Edge/Firefox 최신 지원 | 비표준 API 금지, 폴리필 없는 표준 범위 유지 |
| 1280×720 표시 | 최소 폭 기준 레이아웃, 표는 수평 스크롤 허용 |

### 8.2 NFR-004 반영 구현 규칙

| 요구사항 | 구현 기준 |
|----------|----------|
| 3단계 시작 조작 | 시작 화면 단일 폼에서 `종목→전략→시작` |
| 상태 시각 구분 | 상태 배지 텍스트/색상/아이콘 일관 분리 |
| 한국어 오류 메시지 | 모든 에러 `errorMapper` 경유 |
| 천 단위 구분 | `formatCurrencyKRW()` 공통 함수 강제 |

### 8.3 성능 예산 및 가드

| 지표 | 목표 | 구현 가드 |
|------|------|-----------|
| 시작 요청 확인 응답 | 2초 이내 | 요청 타임아웃 2.5초, 실패 즉시 오류 UI |
| 모니터링 갱신 반영 | 이벤트 수신 후 300ms 이내 | 이벤트 배치 반영(최대 100ms) |
| 결과 화면 표시 | 응답 수신 후 1초 이내 | 정규화/포맷 비용 최소화, memoized selector |
| EventLog 성능 | 500개 유지 | 초과 시 오래된 항목 제거 |

---

## 9. 실행 가능한 언어 중립 수도코드

### 9.1 시작 제출/검증/라우팅

```text
FUNCTION handleStartSubmit(formState):
    normalizedSymbol <- normalizeSymbol(formState.symbol)
    selectedStrategy <- formState.strategy

    fieldErrors <- validateStartForm(normalizedSymbol, selectedStrategy)
    IF fieldErrors IS NOT EMPTY:
        setStartPageFieldErrors(fieldErrors)
        setSimulationStatus("idle")
        RETURN FAILURE
    ENDIF

    setSimulationStatus("starting")
    disableStartButton(TRUE)

    TRY:
        response <- simulationApi.startSimulation({
            symbol: normalizedSymbol,
            strategy: selectedStrategy
        })

        simulationId <- response.simulation_id
        simulationStore.createSimulation(simulationId, normalizedSymbol, selectedStrategy)
        simulationStore.updateStatus(simulationId, "running")

        navigateTo("/monitoring/" + simulationId)
        RETURN SUCCESS
    CATCH error:
        mapped <- errorMapper.toUiError(error)
        applyStartError(mapped)
        setSimulationStatus("error")
        RETURN FAILURE
    FINALLY:
        disableStartButton(FALSE)
END FUNCTION
```

### 9.2 SSE 연결/재연결/중복제거

```text
FUNCTION attachMonitoringStream(simulationId):
    retrySchedule <- [1, 2, 4, 8, 10]
    retryIndex <- 0

    WHILE retryIndex <= LENGTH(retrySchedule):
        lastEventId <- simulationStore.getLastAppliedEventId(simulationId)
        stream <- sseClient.open(simulationId, lastEventId)
        markNetworkState("online")

        ON stream.progress(payload, eventId):
            IF eventId <= simulationStore.getLastAppliedEventId(simulationId):
                CONTINUE
            ENDIF

            simulationStore.applyProgress(simulationId, payload, eventId)
            uiStore.setLastHeartbeat(NOW())
        END ON

        ON stream.trade(payload, eventId):
            IF eventId <= simulationStore.getLastAppliedEventId(simulationId):
                CONTINUE
            ENDIF

            normalizedEvent <- normalizers.toEventItem(payload, eventId)
            simulationStore.appendEvent(simulationId, normalizedEvent)
        END ON

        ON stream.heartbeat(payload, eventId):
            uiStore.setLastHeartbeat(payload.timestamp)
            simulationStore.markEventApplied(simulationId, eventId)
        END ON

        ON stream.completed(payload, eventId):
            simulationStore.updateStatus(simulationId, "completed")
            simulationStore.markEventApplied(simulationId, eventId)
            stream.close()
            navigateTo("/results/" + simulationId)
            RETURN SUCCESS
        END ON

        ON stream.error(payload):
            stream.close()
            markNetworkState("degraded")

            IF retryIndex == LENGTH(retrySchedule):
                simulationStore.updateStatus(simulationId, "error")
                simulationStore.setError(simulationId, errorMapper.toUiError(payload))
                showReconnectButton(TRUE)
                RETURN FAILURE
            ENDIF

            waitSeconds(retrySchedule[retryIndex])
            retryIndex <- retryIndex + 1
        END ON
    END WHILE
END FUNCTION
```

### 9.3 결과 캐시 우선 조회 + 재검증

```text
FUNCTION loadResultPage(simulationId):
    cached <- reportStore.getCache(simulationId)
    IF cached EXISTS AND isFresh(cached.fetchedAt, 30 seconds):
        renderReport(cached.report)
        runInBackground(refreshResult(simulationId))
        RETURN SUCCESS
    ENDIF

    setResultState("loading")

    TRY:
        report <- reportApi.getReport(simulationId, {schema_version: "1.0"})
        normalized <- normalizers.normalizeReport(report)

        reportStore.upsertCache(simulationId, normalized, NOW())
        reportStore.setActive(simulationId)
        setResultState("ready")
        RETURN SUCCESS
    CATCH error:
        mapped <- errorMapper.toUiError(error)
        reportStore.setError(mapped)
        setResultState("error")
        RETURN FAILURE
END FUNCTION
```

### 9.4 테이블 렌더링/검증

```text
FUNCTION buildTradeTableRows(report):
    rows <- report.trades
    validRows <- []

    FOR EACH row IN rows:
        IF row.trade_id IS NULL:
            CONTINUE
        ENDIF

        normalized <- {
            trade_id: row.trade_id,
            trade_date: row.trade_date,
            buy_datetime: row.buy_datetime,
            buy_price: toCurrency(row.buy_price),
            buy_quantity: row.buy_quantity,
            buy_amount: toCurrency(row.buy_amount),
            sell_datetime: row.sell_datetime,
            sell_price: toCurrency(row.sell_price),
            sell_amount: toCurrency(row.sell_amount),
            sell_reason: mapSellReasonToKo(row.sell_reason),
            tax: toCurrency(row.tax),
            fee: toCurrency(row.fee),
            net_profit: toCurrency(row.net_profit),
            profit_rate: toPercent(row.profit_rate)
        }
        validRows.APPEND(normalized)
    END FOR

    RETURN sortByBuyDatetimeAscNullLast(validRows)
END FUNCTION
```

---

## 10. 요구사항/설계 추적성 매트릭스 (SRS + LLD)

### 10.1 SRS 추적성

| 추적 ID | SRS 요구사항 | 구현 반영 | ILD 위치 |
|---------|---------------|-----------|----------|
| `T-FE-001` | FR-010 시작 화면/검증/시작 실행 | `SimulationStartPage`, `useStartSimulation`, 폼 검증 | 4.1, 5.1, 7.1, 9.1 |
| `T-FE-002` | FR-011 실시간 모니터링 | `MonitoringPage`, `StatusBadge`, `ProgressBar`, `EventLog`, SSE 훅 | 4.1~4.2, 5.2, 6.2 |
| `T-FE-003` | FR-012 결과 조회/재조회 | `ResultPage`, `useReportQuery`, 캐시 정책 | 4.1, 5.3, 6.4, 9.3 |
| `T-FE-004` | FR-013 수익률/수익금 표시 | `ProfitSummaryCard`, 포맷 유틸 | 4.2, 3.3, 9.3 |
| `T-FE-005` | FR-014 거래내역 14개 항목/정렬 | `TradeHistoryTable`, 정렬/정규화 | 4.2, 3.3, 9.4 |
| `T-FE-006` | FR-015 종합 결과 보고서 | `ComprehensiveReportCard` + summary 바인딩 | 4.2, 9.3 |
| `T-FE-007` | NFR-003 브라우저 접근성 | 표준 Web API, 1280×720 대응 | 2장, 8.1 |
| `T-FE-008` | NFR-004 UI 직관성 | 3단계 조작, 상태 시각 구분, 한국어 오류, 천단위 포맷 | 7.4, 8.2 |

### 10.2 LLD 추적성

| LLD 항목 | ILD 반영 |
|----------|----------|
| 3장 상태 관리 설계 | 3장 정규화/스토어 계약, 5장 훅/스토어 액션 |
| 4장 컴포넌트 인터페이스 | 4장 페이지/컴포넌트 구현 계약 |
| 5장 REST/SSE 데이터 플로우 | 5~6장 연동 수명주기/복구 플로우 |
| 6장 검증/상태 전이 | 7장 상태 머신/오류 정책 |
| 7장 NFR 반영 설계 | 8장 성능·사용성 구현 기준 |
| 9장 수도코드 | 9장 구현 단계별 수도코드 상세화 |

---

## 11. 구현 체크리스트 (주니어 개발자용)

### 11.1 착수 전

1. `domain/types.ts`에 SRS/WEBAPI 스키마 기반 타입을 먼저 정의한다.
2. `validators.ts`에 심볼/전략/ID 검증 함수를 작성한다.
3. `errorMapper.ts`의 코드별 한국어 메시지 테이블을 완성한다.

### 11.2 구현 순서

1. `simulationStore`/`reportStore`/`uiStore`를 작성한다.
2. `simulationApi`, `reportApi`, `sseClient`를 작성한다.
3. `useStartSimulation`, `useMonitoringSse`, `useReportQuery`를 작성한다.
4. `SimulationStartPage` → `MonitoringPage` → `ResultPage` 순서로 연결한다.
5. 프리젠테이션 컴포넌트를 Props 중심으로 분리한다.

### 11.3 검증 포인트

1. 잘못된 심볼로 시작 시 API 호출이 발생하지 않아야 한다.
2. SSE `completed` 수신 시 결과 화면 자동 이동해야 한다.
3. SSE 재연결 5회 실패 시 오류 배너와 수동 재시도 버튼이 표시되어야 한다.
4. 결과 페이지 새로고침 후에도 동일 `simulationId`로 재조회되어야 한다.
5. 금액/수익률 표기가 FR-013 형식을 만족해야 한다.

### 11.4 완료 조건

1. FR-010~FR-015 시나리오 수동 점검 완료
2. NFR-003/NFR-004 점검 완료
3. 추적성 테이블의 모든 항목이 코드 단위로 매핑 완료
