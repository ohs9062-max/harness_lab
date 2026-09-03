# Harness Lab Automatic Runner

Python 표준 라이브러리만으로 실제 `claude`, `codex`, `gemini` CLI를 비대화형 실행한다. 자연어 요청 하나를 계획하고, 역할별 권한으로 실행하고, 산출물을 다음 Stage에 넘긴 뒤 테스트와 독립 검수/FIX 루프를 통과시킨다.

## 모듈

- `cli.py`: `--repo`, dry-run/execute, doctor, timeout, check 옵션
- `coordinator.py`: AI JSON 계획 또는 deterministic 역할 라우팅
- `models.py`: Stage/Plan/State 검증, read/write/system 권한, quorum, self-review 방지
- `engine.py`: Agent 실행, fallback, handoff, CHECK, REVIEW/FIX, FINAL Gate
- `checks.py`: Python/package.json 기반 검사 발견 및 shell 없는 실행
- `git_state.py`: read-only Git Preflight와 실행 중 변경 파일 추적
- `prompt_builder.py`: 역할별 지시와 크기 제한 inline handoff
- `state.py`: atomic state, masked output, handoff, JSONL audit event
- `adapters/`: Claude/Codex/Gemini 최소권한 CLI와 deterministic fake

## CLI

```bash
python3 -m demo.orchestrator --doctor
python3 -m demo.orchestrator "목표" --dry-run
python3 -m demo.orchestrator "목표" --execute
python3 -m demo.orchestrator "목표" --execute --deterministic-plan
python3 -m demo.orchestrator "목표" --execute --repo /path/to/repo \
  --check "python3 -m pytest -q" --max-review-cycles 2
```

기본값은 안전한 dry-run이다. 실제 호출은 `--execute`가 있어야 한다. `--deterministic-plan`은 Coordinator 모델 호출 없이 요청 키워드로 RESEARCH/DEVELOPMENT/MIXED를 분류하고 기본 MODE C 역할을 배치한다.

## 권한과 실패 처리

| 역할 | Claude | Codex | Gemini |
|---|---|---|---|
| read-only | `--permission-mode plan` | `--sandbox read-only` | `--approval-mode plan` |
| write | `--permission-mode acceptEdits` | `--approve-for-me` | `--approval-mode auto_edit` |

위험한 bypass/yolo 플래그는 사용하지 않는다. CLI 미인증·timeout·쿼터 실패는 해당 결과 파일에 남고 fallback이 있으면 다음 후보를 실행한다. 필수 성공 수(`min_success`)를 못 채우면 이후 Stage는 시작하지 않는다.

## 런 기록

```text
.harness/runs/<TASK-ID>/
├── state.json
├── handoff.json
├── events.jsonl
└── outputs/
    ├── 001-DESIGN/claude.md
    ├── 002-IMPLEMENT/codex.md
    └── 003-REVIEW/gemini.md
```

`.harness/`는 Git에서 제외한다. 일부 CLI가 ignored 파일 읽기를 막기 때문에 Runner는 선행 성공 결과의 최대 60,000자 excerpt와 CHECK 요약을 후속 prompt에 직접 포함한다.

## 완료 조건

- 필수 Agent/quorum 성공
- write Stage에서 실제 repository 변경 발생
- 발견되거나 지정된 결정론적 검사 성공(없으면 `WAIVED`로 명시)
- 독립 reviewer의 단일 명시 verdict `PASS`
- 지정된 output artifact가 있다면 파일 존재와 비어 있지 않음 확인
- Runner가 Git commit을 만들지 않았음
