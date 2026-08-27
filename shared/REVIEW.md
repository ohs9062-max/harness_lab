# 독립 검수 기록

## 작성 정보

- 작성자: Codex
- 모델: 미확인
- 역할: 독립 검수 템플릿 초기화
- 작성일: 2026-08-27
- TASK-ID: TASK-2026-08-27-002

## 검수 상태

- TASK-ID: TASK-2026-08-27-002
- Stage: REVIEW
- 상태: PENDING
- 판정: 미수행
- 표준 판정: PASS / FIX_REQUIRED / BLOCKED

## 독립성 확인

- reviewer AI: 미배정
- reviewer session: 미배정
- 최종 결과 작성·수정 참여 여부: 확인 필요
- 독립성 충족 여부: 확인 필요

최종 결과물 작성·수정에 참여하지 않은 AI 또는 같은 AI의 fresh independent session만 독립
REVIEW를 수행한다. 같은 세션이 RESEARCH, COMPARE, SYNTHESIZE 또는 구현·수정 후 자기 결과를
독립 검수했다고 기록하지 않는다.

## 검수 대상

- 최종 artifact 또는 구현:
- 기준 branch:
- 대상 branch/commit:
- merge-base commit:
- 실제 diff 명령:

## 연구 TASK 검수 기준

최종 synthesized artifact가 RESEARCH/COMPARE/VERIFY 근거와 일치하고, 제외·미확인·기준일 정보가
숨겨지지 않았는지 확인한다.

## 개발 TASK 검수 기준

TASK Stage Plan, DESIGN, IMPLEMENTATION, DECISIONS, 실제 diff와 테스트를 직접 대조한다.
구현자의 설명을 그대로 신뢰하지 않는다.

## Findings

- 해당 없음 — 검수 미수행

## 판정 근거

- 해당 없음 — 검수 미수행

PASS만 FINAL 진행 조건을 충족한다. FIX_REQUIRED이면 FIX → TEST → 독립 REVIEW를 반복한다.
BLOCKED이면 원인과 필요한 사용자 또는 외부 조치를 context에 기록한다.
