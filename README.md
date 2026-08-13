# Harness Lab

여러 AI 에이전트가 역할을 분담하여 설계, 구현, 독립 검수를 수행하고,
결과를 파일 기반으로 인계하는 하네스 엔지니어링 실험 환경이다.

## 구조

- `README.md` — 하네스의 목적과 문서 구조 안내
- `AGENTS.md` — AI 협업, 권한, Git 안전 규칙의 정본
- `ENGINEERING_POLICY.md` — 코드 구현 원칙의 정본
- `WORKFLOW.md` — 사용자를 위한 실제 운영 순서
- `claude/` — Claude 역할 정의
- `codex/` — Codex 역할 정의
- `gemini/` — Gemini 역할 정의
- `shared/` — 작업 목표, 사용자 결정, 설계, 구현, 검수, 인계 및 결과 문서
- `demo/` — 실제 코드 작성 및 수정 영역

## 시작

사용자는 `WORKFLOW.md`에서 작업 시작, 역할 릴레이, checkpoint, worktree 검수,
최종 판단까지의 운영 순서를 확인한다. AI는 `AGENTS.md`와 자신의 역할 문서를
정본으로 삼고 현재 `shared/TASK.md`와 `shared/context.md`를 확인한다.

## 외부 프로젝트 적용

이 하네스를 외부 프로젝트에 적용할 때는 다음을 참고한다.

- `AGENTS.md`, `ENGINEERING_POLICY.md`, `WORKFLOW.md`와 AI별 역할 문서를 대상 프로젝트에 복사한다.
- `shared/` 디렉토리를 대상 프로젝트에 생성한다.
- `demo/` 대신 실제 프로젝트 디렉토리를 작업 범위로 지정한다.
- `AGENTS.md` 2번(작업 범위)을 대상 프로젝트 구조에 맞게 수정한다.
