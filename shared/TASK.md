# 현재 작업

## 작성 정보

- 작성자: Codex
- 모델: 미확인
- 역할: 하네스 작업 방식 문서화
- 작성일: 2026-08-21
- TASK-ID: TASK-2026-08-21-002

## 목표

Harness Lab의 세 공식 운영 모드를 공통 규칙과 각 AI 역할 문서에서 명확히 구분한다.

1. `RELAY`: 다른 AI가 이전 AI의 현재 역할과 미완료 작업을 그대로 이어받는다.
2. `PIPELINE`: Claude 설계, Codex 구현, Gemini 독립 검수를 기본 역할로 순차 수행한다.
3. `PARALLEL`: 각 AI가 독립 worktree에서 결과를 만들고 비교한 뒤 사용자 선택 결과를 통합한다.

## 운영 모드

- MODE: PIPELINE
- 현재 역할: 문서 정책 구현
- MODE 선택 근거: 일반적인 새 정책 작업이며 사용자가 Codex에게 직접 수정을 요청해 Claude 단계는 생략
- 다음 단계: 구현 변경을 checkpoint로 고정한 뒤 구현에 참여하지 않은 Gemini 또는 다른 AI의 독립 검수

## 범위

- 루트 `AGENTS.md`에 `RELAY`, `PIPELINE`, `PARALLEL` 선택과 행동 규칙을 기록한다.
- `codex/codex.md`, `claude/claude.md`, `gemini/gemini.md`에 각 방식에서의 실제 책임을 기록한다.
- 정본과 충돌하지 않도록 `WORKFLOW.md`, `shared/README.md`의 운영 안내를 맞춘다.
- 현재 shared 작업 문서를 새 TASK 기준으로 초기화하고 변경·검증 상태를 기록한다.

## 비범위

- 실제 병렬 branch/worktree를 생성하거나 merge하지 않는다.
- `demo/` 코드와 외부 프로젝트를 변경하지 않는다.
- 자동 인계·자동 merge 도구나 새 의존성을 추가하지 않는다.
- 이전에 중단한 Python 학습 리서치를 재개하지 않는다.
- 사용자 지시 없이 commit 또는 push하지 않는다.

## 완료 기준

- 세 MODE가 작업 연속성, 전문 역할 분담, 대안 비교라는 목적 기준으로 구분돼 있다.
- RELAY에서 AI 이름보다 현재 역할이 우선하고 PIPELINE에서 기본 역할 순서가 유지된다.
- PARALLEL 결과의 독립성, checkpoint, 비교, 사용자 승인과 통합 후 재검증 절차가 일관된다.
- TASK에서 허용 값 중 현재 MODE를 바로 식별할 수 있다.
- Markdown 구조, 용어, TASK-ID와 실제 diff를 검증한 결과가 기록돼 있다.

## 현재 상태

- 문서 구현과 자체 정합성 검증 완료.
- 독립 검수와 사용자 최종 판단은 아직 수행되지 않았다.
