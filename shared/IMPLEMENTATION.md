# 구현 기록

## 작성 정보

- 작성자: Codex
- 모델: GPT-5 계열 Codex
- 역할: IMPLEMENT / TEST
- 작성일: 2026-09-03
- TASK-ID: TASK-2026-09-03-001

## 구현 요약

- 기존 Stage별 worktree V1 엔진을 공유 작업 트리 기반 MODE C 자동 파이프라인으로 교체했다.
- `git_state.py`, `checks.py`를 추가해 Git Preflight/실행 중 변경 추적과 결정론적 검사 선실행을 구현했다.
- Claude/Codex/Gemini 어댑터에서 bypass/yolo를 제거하고 read-only/write 최소권한을 적용했다.
- Agent별 output, atomic `state.json`, `handoff.json`, masked `events.jsonl`, 60,000자 inline handoff를 구현했다.
- strict REVIEW verdict, 실제 변경 Gate, fallback/quorum, FIX→CHECK→fresh REVIEW, artifact FINAL Gate를 구현했다.
- 사용하지 않는 자동 commit/worktree V1 모듈을 제거하고 프로토콜/실행 문서를 실제 상태에 맞췄다.

## 자체 검증

- `python3 -m compileall -q demo/orchestrator`: PASS
- `python3 -m unittest discover -s demo/orchestrator/tests -p 'test_*.py' -v`: 31 tests PASS
- `python3 demo/orchestrator/tests/run_tests.py`: 31 tests PASS
- deterministic mixed dry-run: PASS
- `git diff --check`: PASS
- 실제 CLI E2E (`/tmp/harness-live-e2e.repxux`, TASK-2026-09-03-LIVE4): DONE
  - Claude DESIGN: 인증 없음으로 실패 기록
  - Gemini DESIGN fallback: 성공
  - Codex IMPLEMENT: `slugify.py` 실제 생성
  - Python unittest: 3/3 PASS
  - Gemini independent REVIEW: `VERDICT: PASS`
  - Git HEAD 불변, 자동 commit 없음

## 발견·수정한 실제 CLI 문제

- Codex `--sandbox`와 `--approve-for-me`가 상호배타임을 E2E에서 확인하고 write 호출을 `--approve-for-me` 단독으로 수정했다.
- gitignored `.harness`를 Gemini가 직접 읽지 못해 선행 결과를 제한된 inline excerpt로도 전달하도록 보강했다.
- 독립 검수에서 발견한 verdict/fallback, 로그 마스킹, reviewer/fixer 분리, CHECK 순서, rename·symlink·untracked snapshot 경계 문제를 수정하고 회귀 테스트로 고정했다.
