# 현재 작업

## 작성 정보

- 작성자: Codex
- 모델: 미확인
- 역할: PARALLEL Research namespace 규칙 구현
- 작성일: 2026-08-27
- TASK-ID: TASK-2026-08-27-003

## 작업 메타데이터

- TASK-ID: TASK-2026-08-27-003
- USER-REQUEST: 현재 harness_lab의 PARALLEL Research에서 Claim ID / Source ID 충돌 문제를 문서 규칙으로 수정해줘.
- TASK-TYPE: DEVELOPMENT
- EXECUTION: PIPELINE
- RELAY: ALLOWED
- CURRENT-STAGE: REVIEW
- INPUT-ARTIFACT: 없음
- OUTPUT-ARTIFACT: 없음 — 기존 운영 문서 자체가 결과임

EXECUTION은 TASK의 대표 성격이다. 실제 Stage별 execution과 담당은 Stage Plan을 따른다.

## Stage Plan

### DEFINE
- execution: PIPELINE
- agent: Codex
- required: true
- status: DONE

### ANALYZE
- execution: PIPELINE
- agent: Codex
- required: true
- status: DONE

### DESIGN
- execution: PIPELINE
- agent: Codex
- required: true
- status: DONE

### IMPLEMENT
- execution: PIPELINE
- agent: Codex
- required: true
- status: DONE

### TEST
- execution: PIPELINE
- agent: Codex
- required: true
- status: DONE

### REVIEW
- execution: PIPELINE
- agent: independent session
- required: true
- status: PENDING

### FINAL
- execution: PIPELINE
- agent: User
- required: true
- status: PENDING

## 목표

- PARALLEL Research의 원본 Claim/Source ID 충돌을 작성 AI namespace로 제거한다.
- COMPARE가 의미 기준 Normalized Claim(N-Cxxx)으로 원본 Claim을 안전하게 묶게 한다.
- Source 원출처 중복과 artifact/REVIEW 역추적 규칙을 명확히 한다.

## 범위

- AGENTS, WORKFLOW, 역할 문서와 기존 shared RESEARCH/COMPARE/REVIEW 템플릿 보강
- TASK/context에는 Claim 상세 대신 진행 요약만 기록

## 제약

- 새 문서·프로그램·레지스트리를 만들지 않는다.
- 기존 TASK와 Git history의 C-001/S-001 기록을 대규모 rewrite하지 않는다.
- 상태값, Stage Plan, Exit Gate, WAIVED, RELAY와 REVIEW 정책을 유지한다.
- force push, reset --hard, branch 삭제를 하지 않는다. commit/push/merge는 사용자 승인으로 수행한다.

## 완료 조건

- 원본 Claim/Source가 Agent namespace로 구분된다.
- 원본 ID를 보존한 채 COMPARE만 N-Cxxx를 생성한다.
- 유사하지만 의미가 다른 Claim, 같은 원출처의 중복 판단 규칙이 있다.
- Verified Set, VERIFY, REVIEW가 artifact에서 원본 Source까지 역추적 가능하다.
- 단일 Research와 과거 기록 호환성이 유지된다.
- 15개 요구 검증과 git diff --check를 통과한다.
