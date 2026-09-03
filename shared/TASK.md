# 현재 작업

## 작성 정보

- 작성자: Codex
- 모델: GPT-5 계열 Codex
- 역할: Coordinator / 구현
- 작성일: 2026-09-03
- TASK-ID: TASK-2026-09-03-002

## 작업 메타데이터

- TASK-ID: TASK-2026-09-03-002
- USER-REQUEST: V3 문서 계약을 정본으로 MODE A/B/C 자동 Runner, worktree/checkpoint, resume와 Codex 통합을 구현한다.
- MODE: C (현재 Harness 자체 개선 작업)
- TARGET-REPOSITORY: /home/hs/rang/harness_lab
- BASE-BRANCH: master
- BASE-COMMIT: c8da2666df21a6b5b9659ace4634f12f3feb46c1
- STATUS: IN_PROGRESS

## Stage Plan

- DESIGN: DONE — 문서와 전체 Runner 대조
- IMPLEMENT: DONE — A/B/C worktree orchestration, resume, selection 구현
- TEST: IN_PROGRESS — fake agent와 임시 Git 저장소 검증
- REVIEW: NOT_RUN — 외부 AI 호출 금지 조건
- FINAL: PENDING

## 완료 조건

- A는 required 두 Worker, checkpoint, Cross Review/Response/Compare 후 WAITING_USER에서 멈춘다.
- 선택 resume 시 Codex가 선택 결과만 통합하고 CHECK/FINAL을 수행한다.
- B는 기존 worktree에서 실제 Git을 정본으로 남은 Stage부터 계속한다.
- C는 pipeline worktree에서 DESIGN→IMPLEMENT/CHECK→REVIEW/FIX를 수행한다.
- base Worker write, non-Git 실행, 무판정 REVIEW를 차단한다.
- 외부 AI 없이 전체 테스트와 `git diff --check`를 통과한다.
