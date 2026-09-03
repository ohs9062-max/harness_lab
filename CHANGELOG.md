# Harness Lab 변경 이력

하네스 자체의 정책, 역할, 문서 구조와 운영 방식에서 발생한 의미 있는 변경을
시간순으로 누적한다. 이 문서는 append-only 이력이며 현재 TASK의 진행 상태나
구현 결과를 대신하지 않는다. 현재 작업 상태는 `shared/context.md`, 작업별 최종
결과는 `shared/RESULT.md`, 상세 변경 이력은 Git 기록을 정본으로 확인한다.

## 기록 기준

- `AGENTS.md`, `ENGINEERING_POLICY.md`, `WORKFLOW.md`의 중요 정책 변경
- 역할 분담이나 검수 흐름 변경
- `shared/` 문서 구조와 작업 주기 운영 방식 변경
- 하네스 데모의 추가·제거 또는 완료 기준 변경
- 여러 작업에서 재사용할 가치가 있는 운영상 교훈

단순 오탈자, 개별 TASK의 구현 상세, 커밋별 파일 목록은 기록하지 않는다.

## 2026-08-21 — shared 문서 운영 안내와 변경 이력 분리

- `CHANGELOG.md`를 추가하여 하네스 자체 변화의 누적 이력을 현재 작업 기록과 분리했다.
- `shared/README.md`를 추가하여 shared 문서별 책임, 작업 주기, 초기화 기준과 상태 구분을 명시했다.
- 루트 `README.md`와 `WORKFLOW.md`에서 새 문서와 새 TASK 시작 절차를 연결했다.
- 관련 작업: `TASK-2026-08-21-001`.

## 2026-08-21 — RELAY·PIPELINE·PARALLEL 운영 모드 정립

- 현재 역할을 다음 AI가 이어받는 `RELAY`, 기본 전문 역할을 순차 수행하는 `PIPELINE`, 독립 대안을
  비교하는 `PARALLEL`을 공식 MODE로 구분했다.
- 일반 개발은 `PIPELINE`을 기본값으로 하고 모든 AI가 `shared/TASK.md`의 MODE를 먼저 확인하도록 했다.
- RELAY context 인계 필드, PARALLEL worktree/checkpoint와 사용자 승인 후 통합 규칙을 역할·운영 문서에 맞췄다.
- 관련 작업: `TASK-2026-08-21-002`.

## 2026-08-27 — 문서 기반 하네스 V2

- 이 정의는 2026-08-21 항목의 “세 운영 모드” 구조를 대체한다. 이전 항목은 당시 이력으로 보존한다.
- 실행 방식은 `PIPELINE`과 `PARALLEL`로 한정하고 `RELAY`를 실행 중 사용할 수 있는 인계 방식으로 분리했다.
- AI 고정 역할보다 사용자 지시, TASK, 현재 Stage와 RELAY 전달 역할을 우선하도록 운영 기준을 바꿨다.
- 독립 조사 `RESEARCH`, 후보 선별 `COMPARE`, 독립 최종 검증 `REVIEW`의 책임을 분리했다.
- `artifacts/`를 추가해 shared 과정 문서와 후속 TASK에서 재사용할 최종 결과물을 구분했다.
- TASK 계약과 context 인계 필드를 V2 메타데이터로 보강했다.
- 관련 작업: `TASK-2026-08-27-001`.

## 2026-08-27 — V2 Stage 실행 계약 보강

- Stage별 execution·담당·필수 여부·상태를 기록하는 Stage Plan과 DEFINE Coordinator를 도입했다.
- Stage Exit Gate, 사용자 승인 WAIVED 규칙과 FINAL 진입 조건을 명확히 했다.
- Research Claim/Source 추적과 VERIFY 결과, artifact provenance 구조를 보강했다.
- 독립 REVIEW 판정과 REVIEW/FIX 및 RESEARCH/VERIFY 재작업 Loop를 명확히 했다.
- 관련 작업: `TASK-2026-08-27-002`.

## 2026-09-02 — V3 재설계: MODE A / B / C 아키텍처

- 이 항목은 이전 모든 문서 구조를 대체하는 V3 재설계다. 과거 항목은 당시 이력으로 보존한다.
- 사용자가 "A/B/C로 해"로 지시하는 세 가지 실행 모드를 정의했다.
  - MODE A (Parallel Competition): 같은 작업을 Codex/Gemini가 독립 수행 → Cross Review → Compare → 사용자 선택
  - MODE B (Relay): 같은 작업을 다른 AI가 이어받아 계속
  - MODE C (Role Pipeline): Claude 설계 → Codex 구현 → Gemini 검수
- `MODES.md`를 신규 생성하여 A/B/C 실행 계약의 정본으로 사용한다.
- `AGENTS.md`를 핵심 공통 규칙만 남기고 대폭 축소했다. (448줄 → ~160줄)
- `WORKFLOW.md`를 MODE A/B/C별 운영 흐름으로 재작성했다.
- `README.md`를 A/B/C 소개와 Protocol/Runner 자동화 현황으로 갱신했다.
- 역할 문서 3개(`claude/claude.md`, `codex/codex.md`, `gemini/gemini.md`)를 MODE 우선 규칙으로 재작성했다.
- `shared/README.md`를 `WORKFLOW.md`로 통합하고 삭제했다.
- `무제.base`(빈 파일)를 삭제했다.
- `shared/` 문서 9개를 빈 템플릿으로 초기화했다.
- Git Preflight를 필수 Gate로 도입했다.
- Entry AI와 Worker AI를 구분했다.
- MODE A에서 Cross Review → Response → Compare → WAITING_USER 흐름을 명확히 했다.
- Protocol(문서 계약)과 Runner(자동 실행)의 경계를 명시했다.
- 기존 PIPELINE/PARALLEL은 내부 구현 용어로 유지하되 사용자 최상위 계약은 A/B/C로 통일했다.

## 2026-08-27 — PARALLEL Research ID namespace 보강

- AI별 Claim/Source namespace를 도입하고 기존 기록은 당시 형식으로 유지했다.
- COMPARE의 Normalized Claim(N-Cxxx)으로 의미가 같은 원본 Claim만 매핑하도록 했다.
- 동일 원출처를 여러 독립 근거로 중복 계산하지 않도록 Source 관계 규칙을 명확히 했다.
- 관련 작업: `TASK-2026-08-27-003`.

## 2026-09-03 — 실행 가능한 멀티 AI Orchestrator 통합

- 문서 계약 중심 V3에 실제 Claude/Codex/Gemini CLI 자동 실행 Runner를 연결했다.
- 역할별 최소권한, fallback/quorum, 구조화된 인계와 감사 로그, 결정론적 CHECK 우선, 독립 REVIEW/FIX 재검사 Gate를 구현했다.
- Stage별 분리 worktree와 자동 commit을 제거하고 MODE C 공유 작업 트리에서 결과가 실제로 이어지도록 정리했다.
- 실제 fixture E2E와 31개 회귀 테스트, 독립 Antigravity 검수 PASS로 동작을 확인했다.
- 관련 작업: `TASK-2026-09-03-001`.
