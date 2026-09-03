# V3 Runner 계약 동기화 설계

## 작성 정보

- 작성자: Codex
- 모델: GPT-5 계열 Codex
- 역할: 분석 / 설계
- 작성일: 2026-09-03
- TASK-ID: TASK-2026-09-03-002

## 확인한 불일치

- MODE A는 문서만 있고 독립 worktree 경쟁, checkpoint, Cross Review, 선택 재개 코드가 없었다.
- MODE B는 `load_state()`가 있었지만 TASK-ID resume/relay 실행 경로가 없었다.
- MODE C는 base repository를 공유 workspace로 사용해 base 보호 계약과 충돌했다.
- Coordinator와 CLI가 MODE C에 고정되어 명시 MODE를 machine-readable하게 보존하지 못했다.
- 모든 자동 commit 금지 문구가 MODE A 필수 checkpoint 계약과 충돌했다.

## 설계

- 기존 Stage/adapter/check/state 코어는 유지한다.
- `worktree.py`가 A/C worktree와 A/B/C task checkpoint만 담당한다.
- `engine.py`가 mode를 dispatch하고 base runtime state와 worker cwd를 분리한다.
- A는 두 worktree 완료 전 상대 정보를 prompt에 넣지 않고, 완료 후 Cross Review/Response/Compare를 runtime에서 만든다.
- B는 state의 기존 worktree를 검증하고 실제 status/log/diff를 근거로 남은 Stage를 재개한다.
- C는 pipeline worktree 하나에서 기존 REVIEW/FIX loop를 그대로 사용한다.
