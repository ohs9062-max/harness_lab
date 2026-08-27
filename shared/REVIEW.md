# 독립 검수 기록

## 작성 정보

- 작성자: Codex
- 모델: 미확인
- 역할: 검수 상태 초기화
- 작성일: 2026-08-27
- TASK-ID: TASK-2026-08-27-001

## 검수 상태

- TASK-ID: TASK-2026-08-27-001
- TASK-TYPE: DEVELOPMENT
- EXECUTION: PIPELINE
- Stage: REVIEW
- 상태: 미수행
- 현재 작성·수정에 참여하지 않은 AI 또는 별도 세션의 독립 검수가 필요하다.

## 연구 TASK 검수 기준

최종 synthesized artifact의 주장과 범위가 RESEARCH, COMPARE, VERIFY 근거와 일치하는지,
제외된 위험과 확인 불가 사항이 숨겨지지 않았는지 직접 확인한다.

## 개발 TASK 검수 기준

TASK, DESIGN, IMPLEMENTATION, 확정된 DECISIONS, 실제 diff와 실제 테스트를 직접 대조한다.
구현자의 설명을 그대로 신뢰하지 않는다.

## Git 검수 정보

검수 시 기준 branch, 대상 branch/commit, merge-base commit과
git diff <base>...<work-branch> 명령을 기록한다.

COMPARE는 여러 후보 비교·선별이고 REVIEW는 선택·종합된 결과의 독립 최종 검증이다.
