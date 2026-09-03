# Harness Lab

한 번의 자연어 작업 목표를 받아 로컬 Claude/Codex/Gemini CLI에 역할을 배정하고, 결과 인계·결정론적 검사·독립 검수·수정 루프까지 실행하는 다중 AI 하네스다.

## 바로 실행

```bash
# 환경과 인증 가능한 CLI 확인
python3 -m demo.orchestrator --doctor

# 계획만 확인(모델 호출/파일 변경 없음)
python3 -m demo.orchestrator "이 저장소의 설정 로더를 구현하고 테스트해" --dry-run

# Coordinator가 계획을 만들고 실제 AI CLI 실행
python3 -m demo.orchestrator "이 저장소의 설정 로더를 구현하고 테스트해" --execute

# Coordinator 호출 없이 정책 기반 계획으로 실행
python3 -m demo.orchestrator "이 저장소의 설정 로더를 구현하고 테스트해" \
  --execute --deterministic-plan
```

외부 Git 저장소에는 `--repo /absolute/path`를 사용한다. 추가 검사는 `--check "python3 -m pytest -q"`처럼 반복 지정할 수 있다. Runner는 shell 문자열을 실행하지 않고 argv로 분해한다.

## 자동 실행 흐름

```text
사용자 목표
  → Git Preflight
  → Coordinator(Codex) 또는 deterministic routing
  → Claude 중심 DESIGN/ANALYZE (실패 시 역할 fallback)
  → Codex 중심 IMPLEMENT (공유 작업 트리에 실제 반영)
  → CHECK (test/lint/typecheck/build 자동 발견)
  → Gemini 독립 REVIEW
      ├─ PASS → FINAL
      ├─ FIX_REQUIRED → Codex FIX → CHECK → fresh REVIEW
      └─ BLOCKED/무판정/반복 초과 → BLOCKED
```

AI 출력은 `.harness/runs/<TASK-ID>/outputs/`에 분리 저장되고 `handoff.json`과 제한된 inline excerpt로 후속 AI에 전달된다. `state.json`은 현재 상태, `events.jsonl`은 상태 전이 감사 로그다. 로그의 일반적인 secret 패턴은 마스킹되고 크기가 제한된다.

## 안전 원칙

- Runner는 commit, merge, push, reset, branch 삭제를 하지 않는다.
- 설계/검수 Agent는 read-only, 구현/FIX Agent만 workspace-write/auto-edit 권한을 받는다.
- 병렬 Stage는 read-only만 허용하며 `min_success` quorum을 설정할 수 있다.
- 구현 Agent와 REVIEW Agent가 겹치는 계획은 거부한다.
- 명시적인 `VERDICT: PASS`가 없으면 완료하지 않는다.
- 결정론적 검사 실패는 LLM REVIEW 전에 차단한다.
- CLI 인증/쿼터 장애 시 설정된 fallback Agent를 시도하고 모든 실패를 기록한다.

## 저장소 문서

- `AGENTS.md`: 공통 권한·Git·보안 규칙
- `MODES.md`: MODE A(경쟁), B(인계), C(역할 파이프라인) 계약
- `WORKFLOW.md`: 수동 운영과 자동 Runner 흐름
- `ENGINEERING_POLICY.md`: 구현 원칙
- `claude/`, `codex/`, `gemini/`: 모델별 역할 정책
- `shared/`: 현재 작업 계약·설계·구현·검수·결과
- `artifacts/`: 채택된 재사용 결과물
- `demo/orchestrator/`: 표준 라이브러리 기반 자동 Runner

## 테스트

```bash
python3 -m unittest discover -s demo/orchestrator/tests -p "test_*.py" -v
```

MODE를 명시하지 않은 한 Runner는 자동 완성을 목표로 MODE C를 사용한다. MODE A는 독립 구현 비교와 사용자 선택이 필요한 경우, MODE B는 기존 작업선 인계에 사용한다.
