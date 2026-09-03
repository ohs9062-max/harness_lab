# Harness Lab

한 번의 목표를 Claude/Codex/Gemini CLI에 분배하고 Git worktree, 인계, 검사,
검수, 수정과 사용자 선택까지 실행하는 V3 다중 AI Harness다. 문서는 계약의 정본이고
`demo/orchestrator` Runner가 MODE A/B/C 계약을 구현한다.

## 실행

```bash
python3 -m demo.orchestrator --doctor

# A: Codex/Gemini 독립 경쟁 → WAITING_USER
python3 -m demo.orchestrator "로그인 기능을 만들어" --mode A --execute

# A: 기존 TASK 선택을 Codex가 통합
python3 -m demo.orchestrator --mode A --resume TASK-ID \
  --selection SELECT_GEMINI --execute

# B: 기존 작업선에서 Gemini가 남은 Stage를 계속
python3 -m demo.orchestrator --mode B --resume TASK-ID \
  --relay-agent gemini --execute

# C: Claude 설계 → Codex 구현/검사 → Gemini 검수
python3 -m demo.orchestrator "설정 로더를 구현하고 테스트해" --mode C --execute
```

기본 MODE는 C이고 기본 실행은 dry-run이다. `--deterministic-plan`은 Coordinator 모델
호출 없이 정책 계획을 만들며, `--fake-agents`는 외부 AI를 호출하지 않는 테스트용이다.
외부 저장소는 `--repo /absolute/path`, 추가 검사는 `--check "python3 -m pytest -q"`로 지정한다.

## MODE

- A: 같은 base commit에서 `task/<TASK-ID>/codex`, `task/<TASK-ID>/gemini`를 만들고
  독립 구현·테스트·checkpoint 후에만 Cross Review와 1회 Response를 수행한다.
  `.harness/runs/<TASK-ID>/compare.md` 생성 후 반드시 `WAITING_USER`에서 멈춘다.
- B: 새 worktree를 만들지 않는다. 기존 state의 branch/worktree/checkpoint와 실제
  `git status/log/diff`를 대조하고, Git을 정본으로 미완료 Stage부터 이어간다.
- C: `task/<TASK-ID>/pipeline` worktree 하나에서 Claude→Codex→Gemini가 결과를 넘긴다.
  `FIX_REQUIRED`면 기본 Codex, 실제 fallback 구현자가 있었다면 그 writer가 FIX한다.

`PIPELINE`과 `PARALLEL`은 Stage 내부 실행 전략이며 사용자 MODE A/B/C가 아니다.

## Git과 상태

- AI Worker write는 base/master에서 금지된다.
- A/B/C task worktree의 local checkpoint commit은 Runner 실행 승인 범위다.
- A의 base 통합은 사용자 선택 후 Codex만 수행한다. push, force push, reset, branch 삭제는 하지 않는다.
- 런타임 정본은 `.harness/runs/<TASK-ID>/state.json`이다.
- `handoff.json`, `events.jsonl`, `outputs/`, A의 `compare.md`와 `selection.json`이 실행 근거를 보존한다.
- REVIEW는 마지막 비어 있지 않은 줄의 명시적 `VERDICT: PASS|FIX_REQUIRED|BLOCKED`만 인정한다.

## 주요 문서

- `AGENTS.md`: 공통 권한·Git·보안 규칙
- `MODES.md`: MODE A/B/C 상태 머신 정본
- `WORKFLOW.md`: 실제 운영과 CLI 재개 흐름
- `ENGINEERING_POLICY.md`: 코드 변경 원칙
- `claude/`, `codex/`, `gemini/`: 모델별 역할
- `shared/`: 사람이 읽는 현재 TASK 장기 기록
- `demo/orchestrator/`: 자동 Runner

## 테스트

```bash
python3 -m unittest discover -s demo/orchestrator/tests -p "test_*.py" -v
git diff --check
```
