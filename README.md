# Harness Lab

여러 AI 에이전트가 같은 작업을 이어받거나, 전문 역할에 따라 순차 수행하거나,
독립 worktree에서 병렬 수행하고 상태와 결과를 파일 기반으로 인계·비교·통합하는 환경이다.

Harness Lab의 공식 운영 모드는 세 개다.

- `RELAY`: 다른 AI가 현재 역할과 미완료 작업을 이어받는다.
- `PIPELINE`: Claude 설계, Codex 구현, Gemini 검수를 기본 순서로 수행한다.
- `PARALLEL`: 각 AI가 독립 결과를 만든 뒤 비교하여 사용자 승인 결과를 통합한다.

일반적인 새 개발 작업의 기본 MODE는 `PIPELINE`이며 사용자 지정 MODE가 항상 우선한다.

## 구조

- `README.md` — 하네스의 목적과 문서 구조 안내
- `CHANGELOG.md` — 하네스 정책·역할·문서 구조의 의미 있는 변경 이력
- `AGENTS.md` — AI 협업, 권한, Git 안전 규칙의 정본
- `ENGINEERING_POLICY.md` — 코드 구현 원칙의 정본
- `WORKFLOW.md` — 사용자를 위한 실제 운영 순서
- `claude/` — Claude 역할 정의
- `codex/` — Codex 역할 정의
- `gemini/` — Gemini 역할 정의
- `shared/` — 작업 목표, 사용자 결정, 설계, 구현, 검수, 인계 및 결과 문서
  - `shared/README.md` — shared 문서별 책임, 작업 주기와 초기화 기준
- `demo/` — 실제 코드 작성 및 수정 영역

## 현재 상태

- 하네스 기본 문서와 역할별 정책 구성을 완료했다.
- 첫 파이프라인 데모인 JSON 설정 조회 CLI를 구현·독립 검수하고 `master`에 반영했다.
- 데모 사용법은 `demo/README.md`, 실제 작업 결과는 `shared/RESULT.md`에서 확인한다.

## 시작

사용자는 `WORKFLOW.md`에서 작업 시작, 역할 릴레이, checkpoint, worktree 검수,
최종 판단까지의 운영 순서를 확인한다. AI는 `AGENTS.md`와 자신의 역할 문서를
정본으로 삼고 현재 `shared/TASK.md`와 `shared/context.md`를 확인한다.

기본 순서는 `WORKFLOW 확인 → TASK와 MODE 작성 → 작업 수행 → REVIEW → RESULT`이다.
`shared/` 문서는 현재 작업 주기의 기록이며 다음 작업을 시작할 때 새 TASK에 맞춰 갱신한다.
새 TASK 전 보존·초기화 절차는 `shared/README.md`, 하네스 자체의 누적 변화는
`CHANGELOG.md`에서 확인한다.

## 외부 프로젝트 적용

이 하네스를 외부 프로젝트에 적용할 때는 다음을 참고한다.

- `AGENTS.md`, `ENGINEERING_POLICY.md`, `WORKFLOW.md`와 AI별 역할 문서를 대상 프로젝트에 복사한다.
- `shared/` 디렉토리를 대상 프로젝트에 생성한다.
- `demo/` 대신 실제 프로젝트 디렉토리를 작업 범위로 지정한다.
- `AGENTS.md` 2번(작업 범위)을 대상 프로젝트 구조에 맞게 수정한다.
