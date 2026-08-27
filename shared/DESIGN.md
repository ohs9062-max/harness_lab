# 설계 기록

## 작성 정보

- 작성자: Codex
- 모델: 미확인
- 역할: V2 문서 구조 설계 및 구현
- 작성일: 2026-08-27
- TASK-ID: TASK-2026-08-27-001

## 작업 메타데이터

- TASK-ID: TASK-2026-08-27-001
- Stage: DESIGN
- 입력 artifact: 없음
- 관련 decision: D-001, D-002
- branch/commit: ohs9062-max/sol-low-to-middle / checkpoint 없음

## 설계 결과

- AGENTS를 실행 방식, Stage 우선순위, RELAY와 Git 안전 규칙의 정본으로 유지한다.
- WORKFLOW는 사용자가 TASK 시작부터 FINAL까지 운영하는 절차만 설명한다.
- 역할 문서는 공통 규칙을 복제하지 않고 기본 강점과 Stage별 행동만 설명한다.
- TASK는 작업 계약, context는 현재 상태와 RELAY 인계 스냅샷으로 분리한다.
- RESEARCH는 단일 조사 근거, COMPARE는 후보 선별, REVIEW는 선택 결과의 독립 검증을 담당한다.
- shared는 과정, artifacts는 재사용 가능한 최종 결과, RESULT는 종료 기록으로 분리한다.
- ENGINEERING_POLICY에는 orchestration 내용을 넣지 않는다.

## 변경 대상

루트 운영 문서, 세 역할 문서, 현재 shared 문서와 신규 RESEARCH/COMPARE, artifacts/README.md.

## 검증 기준

TASK의 문서 검증 조건, git diff --check, 용어 검색, 실제 파일·Git 상태와 최종 tree를 확인한다.
