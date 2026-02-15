# TICKET-036-CICD-DEPLOY: 빌드/배포 파이프라인 구성

## 기본 정보
- **티켓 ID**: TICKET-036-CICD-DEPLOY
- **유형**: CI/CD (빌드·배포)
- **담당**: CI/CD 담당 에이전트
- **상태**: DONE
- **우선순위**: High
- **버전**: 1.0.0
- **생성일**: 2026-02-16
- **완료일**: 2026-02-16
- **선행 조건**: TICKET-030~TICKET-035 (DONE)
- **후행 티켓**: TICKET-060-HLD-TEST-RUN, TICKET-061-LLD-TEST-RUN, TICKET-062-ILD-TEST-RUN

## 작업 범위
1. 백엔드/프론트엔드 빌드 파이프라인 정의
2. 기본 배포 절차 및 실행 스크립트 정리
3. 산출물 검증 리포트 작성

## 출력 산출물
- CI/CD 설정 파일(필요 시)
- `docs/tickets/reports/TICKET-036-DEPLOYMENT-REPORT.md`

## 수용 기준
1. 백엔드/프론트엔드 빌드 명령 자동화
2. 배포 절차 재현 가능 문서화
3. 실패 시 롤백/복구 절차 명시

## 완료 결과 요약
- GitHub Actions 파이프라인 추가: `.github/workflows/ci-cd.yml`
	- `backend-build`: Python 의존성 설치, `compileall`, import smoke
	- `frontend-build`: `npm ci`, `typecheck`, `build`, artifact 업로드
	- `deploy-staging`: `main` push 시 최소 배포 핸드오프 검증
- CI/CD 실행/운영 문서 추가: `docs/cicd/cicd-runbook-v1.0.0.md`
- 배포 보고서 작성 완료: `docs/tickets/reports/TICKET-036-DEPLOYMENT-REPORT.md`
- 로컬 검증 완료:
	- Backend: `python -m compileall -q src`, import smoke 성공
	- Frontend: `npm.cmd install`, `npm.cmd run typecheck`, `npm.cmd run build` 성공
