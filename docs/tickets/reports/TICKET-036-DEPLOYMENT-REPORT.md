# TICKET-036 배포 파이프라인 보고서

## 1) 기본 정보

| 항목 | 내용 |
|------|------|
| **티켓 ID** | TICKET-036-CICD-DEPLOY |
| **상태** | 완료 (DONE) |
| **완료일** | 2026-02-16 |
| **파이프라인 파일** | `.github/workflows/ci-cd.yml` |
| **운영 문서** | `docs/cicd/cicd-runbook-v1.0.0.md` |

## 2) 파이프라인 구성

### 2.1 Stage 목록
1. `backend-build`
   - Python 3.11 환경 구성
   - `pip install -r requirements.txt`
   - `python -m compileall -q src`
   - `PYTHONPATH=src` 기반 import smoke 및 `create_app()` 생성 확인

2. `frontend-build`
   - Node 20 환경 구성
   - `npm ci` (`src/frontend`)
   - `npm run typecheck`
   - `npm run build`
   - `dist` artifact 업로드 (`frontend-dist`)

3. `deploy-staging` (최소 구현)
   - 조건: `main` branch push
   - `backend-build`, `frontend-build` 성공 후 실행
   - `frontend-dist` artifact 다운로드
   - 실제 인프라 미정 상태에서 배포 핸드오프 검증(placeholder)

## 3) 로컬 검증 실행 로그 (요약)

### 3.1 Backend
실행 명령 (PowerShell):

```powershell
python -m pip install -r c:\Dev\privatetrade2\requirements.txt
python -m compileall -q c:\Dev\privatetrade2\src
$env:PYTHONPATH='c:/Dev/privatetrade2/src'
python -c "import marketdata, strategy, simulation, report, webapi; from webapi import create_app; app=create_app(); print('backend-smoke-ok', app.title)"
```

결과:
- `requirements.txt` 의존성 설치/확인 성공
- compile check 성공
- 출력: `backend-smoke-ok PrivateTrade WEBAPI`

### 3.2 Frontend
실행 명령 (PowerShell):

```powershell
npm.cmd --version
npm.cmd install --prefix c:\Dev\privatetrade2\src\frontend
npm.cmd run --prefix c:\Dev\privatetrade2\src\frontend typecheck
npm.cmd run --prefix c:\Dev\privatetrade2\src\frontend build
```

결과:
- npm 11.6.2 확인
- 설치 성공 (`added 26 packages`)
- 타입체크 성공
- 빌드 성공 (`vite build`, `dist` 산출)

## 4) 환경 제한 및 대응

1. PowerShell execution policy로 `npm.ps1` 실행 제한 발생
   - 메시지: `PSSecurityException (UnauthorizedAccess)`
   - 대응: `npm` 대신 `npm.cmd` 사용하여 우회

2. 터미널 현재 경로 드리프트로 상대경로 `requirements.txt` 실패 가능
   - 대응: 로컬 검증 시 절대경로 기반 명령으로 재실행
   - CI에서는 workflow working directory/checkout으로 재현성 확보

## 5) 롤백/복구 절차

1. Git 레벨 롤백
   - 실패 커밋 식별 후 `git revert <sha>` 적용
   - `main` 재실행으로 `backend-build`, `frontend-build`, `deploy-staging` 정상 확인

2. 아티팩트 레벨 롤백 (프론트엔드)
   - 직전 성공 run의 `frontend-dist` artifact 재사용
   - 운영 배포 스크립트가 연결된 경우 해당 artifact 재배포

3. 백엔드 복구
   - 직전 안정 커밋/태그로 복원
   - `compileall` + import smoke 재검증
   - API 기본 응답 확인 후 서비스 전환

## 6) 결론

TICKET-036 범위(CI/CD 전용)에서 백엔드/프론트엔드 빌드 검증 파이프라인과 최소 배포 단계, 로컬 재현 절차, 롤백/복구 전략 문서화를 완료했다. 실 배포 인프라 연동은 저장소 범위 외이므로 placeholder stage로 구성했으며 추후 인프라 정의 시 `deploy-staging` 단계에 실제 명령을 확장하면 된다.
