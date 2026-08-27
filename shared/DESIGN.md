# 설계 기록

## 작성 정보

- 작성자: Codex
- 모델: 미확인
- 역할: namespace 규칙 설계 및 구현
- 작성일: 2026-08-27
- TASK-ID: TASK-2026-08-27-003

## 작업 메타데이터

- TASK-ID: TASK-2026-08-27-003
- Stage: DESIGN
- 입력 artifact: 없음
- 관련 decision: D-001
- branch/commit: ohs9062-max/sol-low-to-middle / checkpoint 없음

## 설계 결과

- 원본 Claim/Source는 작성 AI namespace를 사용하고 독립 RESEARCH 동안 번호를 조율하지 않는다.
- COMPARE만 N-Cxxx를 생성하며 원본 ID를 보존한 채 의미가 같은 Claim을 매핑한다.
- 인과관계나 의미가 다른 유사 Claim은 별도 N-C로 유지한다.
- 같은 원출처를 여러 AI가 찾은 경우 Source ID는 유지하되 독립 근거 수를 중복 계산하지 않는다.
- VERIFY와 REVIEW는 artifact에서 N-C와 원본 Claim/Source까지 역추적한다.
- 기존 기록을 일괄 변경하거나 새 레지스트리 문서를 만들지 않는다.
