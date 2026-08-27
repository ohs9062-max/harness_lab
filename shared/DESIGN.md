# 설계 기록

## 작성 정보

- 작성자: Codex
- 모델: 미확인
- 역할: Stage 실행 계약 설계 및 구현
- 작성일: 2026-08-27
- TASK-ID: TASK-2026-08-27-002

## 작업 메타데이터

- TASK-ID: TASK-2026-08-27-002
- Stage: DESIGN
- 입력 artifact: 없음
- 관련 decision: D-001
- branch/commit: ohs9062-max/sol-low-to-middle / checkpoint 없음

## 설계 결과

- AGENTS에는 Coordinator, Stage Plan 준수, waiver, FINAL과 REVIEW 독립성 같은 공통 의무만 둔다.
- WORKFLOW에는 단일/병렬 연구 흐름, Exit Gate와 연구·개발 재작업 Loop 상세를 둔다.
- TASK는 대표 EXECUTION과 Stage별 execution·담당·required·status를 함께 기록한다.
- RESEARCH/COMPARE는 Claim ID와 Source ID로 주장·검증·채택을 연결한다.
- REVIEW는 독립성 정보와 PASS/FIX_REQUIRED/BLOCKED 판정을 기록한다.
- RESULT와 artifact는 Stage 상태, 검수, 기준일과 근거 commit을 연결한다.
- 새 운영 문서나 자동화는 만들지 않는다.

## 검증 기준

사용자가 제시한 21개 검증 항목, git diff --check, 금지 경로, 추적 파일 무변경과 최종 tree를 확인한다.
