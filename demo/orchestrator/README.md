# Harness Lab V3 Runner

Python 표준 라이브러리로 Claude/Codex/Gemini CLI와 Git worktree를 실행한다.
최상위 `--mode A|B|C`는 Harness Protocol이고 Stage의 `PIPELINE|PARALLEL`과 별개다.

## CLI

```bash
python3 -m demo.orchestrator --doctor
python3 -m demo.orchestrator "목표" --mode A --execute
python3 -m demo.orchestrator --mode A --resume TASK-ID --selection SELECT_CODEX --execute
python3 -m demo.orchestrator --mode A --resume TASK-ID --selection SELECT_HYBRID \
  --instruction "사용자 통합 기준" --execute
python3 -m demo.orchestrator --mode B --resume TASK-ID --relay-agent gemini --execute
python3 -m demo.orchestrator "목표" --mode C --execute
```

선택 값은 `SELECT_CODEX`, `SELECT_GEMINI`, `SELECT_HYBRID`, `REWORK`, `CANCEL`이다.
새 실행은 request가 필요하고 resume은 기존 TASK-ID가 필요하다. MODE 미지정 시 C다.

## 실행 구조

- `engine.py`: MODE dispatch, Stage 실행, A 경쟁/선택, B relay, C REVIEW/FIX
- `worktree.py`: task worktree 생성, 등록 경로 검증, local checkpoint, diff
- `git_state.py`: repository/root/branch/HEAD/dirty/worktree Preflight와 B Git 근거
- `coordinator.py`: 명시 MODE 보존과 A/C plan 생성; B는 새 plan을 만들지 않음
- `state.py`: `.harness/runs/<TASK-ID>/` atomic state/handoff/event/output
- `checks.py`: shell 없는 argv 기반 test/lint/typecheck/build
- `prompt_builder.py`: 최소권한 역할 prompt와 bounded handoff
- `adapters/`: Claude plan/acceptEdits, Codex read-only/approve-for-me,
  Gemini plan/auto_edit, deterministic fake

## Worktree와 checkpoint

```text
.harness/worktrees/<TASK-ID>/
├── codex/       # MODE A
├── gemini/      # MODE A
└── pipeline/    # MODE C; MODE B가 이어받을 수 있음
```

A Worker와 C pipeline은 동일 frozen base commit에서 task branch를 만든다. MODE B는
state에 기록된 등록 worktree를 그대로 쓴다. Worker write를 base에서 시도하면 차단한다.
Runner는 task branch checkpoint만 commit한다. A의 명시적 선택 이후 Codex integration만
base working tree에 쓸 수 있고, 그 결과도 자동 commit/push하지 않는다.

## MODE A Gate

두 required Worker 각각에 대해 write 결과, 결정론적 check, checkpoint가 모두 필요하다.
한쪽이 실패하면 fallback 없이 `BLOCKED`이고 Cross Review 이후 단계는 실행하지 않는다.
두 Worker 완료 전 prompt에 상대 branch/diff/output/test를 넣지 않는다. 완료 후에는 양방향
Cross Review, Response 1회, runtime Compare를 거쳐 `WAITING_USER`가 된다.

## MODE B Gate

`load_state()`로 worktree/current-stage를 복구하고 실제 `git status`, `git log`, `git diff`를
확인한다. 기록과 다르면 Git을 사용하고 `git_discrepancies`와 event에 기록한다. relay Agent는
첫 미완료 AI Stage부터 계속하며 이후 CHECK/REVIEW/FINAL도 같은 worktree에서 수행한다.

## MODE C Gate

Claude DESIGN → Codex IMPLEMENT → CHECK → Gemini REVIEW를 pipeline worktree에서 실행한다.
명시적 PASS만 FINAL로 진행한다. FIX_REQUIRED면 writer FIX → CHECK → fresh REVIEW를 반복하고,
성공하면 pipeline checkpoint를 남긴다.

## 검증

```bash
python3 -m unittest discover -s demo/orchestrator/tests -p "test_*.py" -v
```

테스트에서는 `--fake-agents`와 임시 Git 저장소를 사용하므로 외부 AI 토큰을 소비하지 않는다.
