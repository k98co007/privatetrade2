# CI/CD Runbook v1.0.0

## 1. 목적
- 백엔드/프론트엔드 빌드 및 스모크 검증 절차를 로컬/CI에서 동일하게 재현한다.
- 배포 실패 시 롤백/복구 기준 절차를 정의한다.

## 2. 로컬 실행 절차

### 2.1 Backend (Python)
PowerShell 기준:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m compileall -q src
$env:PYTHONPATH = "src"
python -c "import marketdata, strategy, simulation, report, webapi; from webapi import create_app; app=create_app(); print('backend-smoke-ok', app.title)"
```

### 2.2 Frontend (Vite/React)
PowerShell 기준:

```powershell
Set-Location src/frontend
npm install
npm run typecheck
npm run build
Set-Location ../..
```

### 2.3 최소 실행 (복붙용)
프로젝트 루트(`c:\Dev\privatetrade2`) 기준, 터미널 2개를 사용한다.

터미널 1 (Backend):

```powershell
pip install -r requirements.txt
$env:PYTHONPATH = "src"
python -m uvicorn webapi:app --host 127.0.0.1 --port 8000 --reload
```

터미널 2 (Frontend):

```powershell
Set-Location src/frontend
npm.cmd install
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

접속:
- Frontend: `http://127.0.0.1:5173`
- Backend API 문서: `http://127.0.0.1:8000/docs`

참고:
- PowerShell 실행 정책으로 `npm` 오류가 나면 `npm.cmd`를 사용한다.

### 2.4 서버 로그 확인 (문제 분석용)
Backend 실행 시 아래처럼 실행하면 API 요청/응답, 예외, 시뮬레이션 상태 전이, SSE 연결 로그를 확인할 수 있다.

```powershell
$env:PYTHONPATH = "src"
python -m uvicorn webapi:app --host 127.0.0.1 --port 8000 --reload --log-level info
```

주요 로그 키워드:
- `request.start`, `request.end`, `request.error`
- `simulation.start.*`, `simulation.job.*`, `simulation.status.updated`
- `report.get.*`, `report.generate.*`
- `sse.connect.*`
- `dependency.timeout`, `exception.*`

## 3. CI 파이프라인
- 워크플로: `.github/workflows/ci-cd.yml`
- Stage:
  1) `backend-build`: 의존성 설치 → compile check → import smoke
  2) `frontend-build`: npm ci → typecheck → build → dist artifact 업로드
  3) `deploy-staging`: main push 시 artifact 기반 배포 핸드오프 검증(최소 구현)

## 4. 롤백/복구 전략

### 4.1 GitHub Actions 레벨
1. `main` 기준 마지막 성공 실행(run) 식별
2. 실패 커밋을 `git revert <sha>`로 반전 후 `main`에 머지
3. 파이프라인 재실행 후 `backend-build`, `frontend-build`, `deploy-staging` 성공 확인

### 4.2 프론트엔드 아티팩트 레벨
1. 실패 배포 직전 성공 run의 `frontend-dist` artifact 식별
2. 해당 artifact를 재배포 대상으로 승격(운영 배포 스크립트 연동 시)
3. 웹 상태 확인(정적 파일 서빙 상태/캐시 무효화)

### 4.3 백엔드 레벨
1. 실패 릴리즈 직전 태그/커밋으로 코드 롤백
2. 의존성 재설치 후 compile/import smoke 재검증
3. API 헬스체크 및 기본 엔드포인트 응답 확인

## 5. 제한사항
- 본 저장소에는 실 배포 인프라(Kubernetes/VM/Cloud CLI)가 정의되어 있지 않다.
- 따라서 `deploy-staging`은 배포 준비 검증 단계(artifact handoff)로 구성했다.
