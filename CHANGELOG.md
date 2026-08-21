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
