# Harness Lab

여러 AI 에이전트가 역할을 분담하여 설계, 구현, 독립 검수를 수행하고,
결과를 파일 기반으로 인계하는 하네스 엔지니어링 실험 환경이다.

## 구조

- `AGENTS.md` — 공통 정책 정본 (모든 AI가 작업 전에 읽는다)
- `claude/` — Claude 역할 정의
- `codex/` — Codex 역할 정의
- `gemini/` — Gemini 역할 정의
- `shared/` — 작업 목표, 설계, 구현, 검수, 인계 문서
- `demo/` — 실제 코드 작성 및 수정 영역

## 시작

각 AI는 작업 전에 다음 순서로 문서를 확인한다.

1. `AGENTS.md`
2. 자신의 역할 문서 (`claude/claude.md`, `codex/codex.md`, `gemini/gemini.md`)
3. `shared/TASK.md` (현재 작업 목표)
4. `shared/context.md` (이전 세션 인계 상태)

## 외부 프로젝트 적용

이 하네스를 외부 프로젝트에 적용할 때는 다음을 참고한다.

- `AGENTS.md`와 AI별 역할 문서를 대상 프로젝트 루트에 복사한다.
- `shared/` 디렉토리를 대상 프로젝트에 생성한다.
- `demo/` 대신 실제 프로젝트 디렉토리를 작업 범위로 지정한다.
- `AGENTS.md` 2번(작업 범위)을 대상 프로젝트 구조에 맞게 수정한다.
