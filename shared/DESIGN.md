# 통합 설계

## 작성 정보

- 작성자: Codex
- 모델: GPT-5 계열 Codex
- 역할: 분석 / 설계
- 작성일: 2026-09-03
- TASK-ID: TASK-2026-09-03-001

## 채택할 요소

- `harness_lab`: MODE A/B/C 계약, 실제 Claude/Codex/Gemini CLI 어댑터, 상태/로그, fake 테스트, Git 안전 규칙
- `biz-ttori`: planner/coder/tester/reviewer 역할과 쓰기 권한 분리, 결정론적 도구 선검증, 구조화된 인계, 호출 timeout·출력 cap, 결과 자체를 보는 adversarial review

## V1 결함과 수정 방향

1. Stage마다 분리 worktree를 재사용해도 다른 Agent branch의 산출물이 전달되지 않는다. 자동 MODE C는 하나의 공유 대상 작업 트리를 사용하고, 병렬 읽기 Stage 결과는 런 디렉터리의 Agent별 파일로 격리한다.
2. Review verdict가 없으면 PASS로 처리한다. 명시적 `VERDICT: PASS|FIX_REQUIRED|BLOCKED`만 허용하며 누락은 BLOCKED다.
3. FIX가 reviewer worktree에서 수행되고 결과가 다음 review로 전달되지 않는다. 구현자/FIX는 동일 공유 작업 트리에서 수행하고 모든 선행 산출물 경로를 prompt에 전달한다.
4. 성공 시 자동 commit한다. Runner는 commit/merge/push를 하지 않고 Git diff와 런 상태만 기록한다.
5. 결정론적 검사가 LLM review 앞에 없다. 안전하게 탐지한 test/lint/build 명령 또는 사용자가 준 argv 명령을 CHECK stage에서 실행한다.

## 실행 구조

```text
한 번의 사용자 요청
  → Git preflight + CLI availability
  → Coordinator(Codex) JSON plan 또는 deterministic plan
  → DESIGN/RESEARCH (read-only AI, Agent별 output 저장)
  → IMPLEMENT/SYNTHESIZE (write AI, 공유 작업 트리)
  → CHECK (결정론적 명령)
  → REVIEW (다른 AI, read-only, 명시 verdict)
      ├─ PASS → FINAL + artifact/diff 확인
      ├─ FIX_REQUIRED → FIX(구현 AI) → CHECK → fresh REVIEW
      └─ BLOCKED/무판정/반복 초과 → BLOCKED
```

각 Stage 결과는 `.harness/runs/<TASK-ID>/outputs/<순번>-<STAGE>/<agent>.md`에 저장하고 `handoff.json` 및 `events.jsonl`로 다음 단계 입력과 상태 전이를 기록한다. 로그는 secret masking 후 크기를 제한한다.

## 안전/완료 Gate

- read-only 역할은 CLI별 읽기 전용 모드, write 역할은 workspace-write/auto-edit 모드만 사용한다.
- shell 문자열 실행 없이 argv로 검사 명령을 실행한다.
- 필수 Agent 실패, CHECK 실패, artifact 부재, REVIEW 무판정은 완료로 처리하지 않는다.
- Coordinator 출력은 schema/Stage 순서/역할 분리까지 검증한다.
