# 현재 작업

## 작성 정보

- 작성자: Codex
- 모델: 미확인
- 역할: V2 Stage 실행 계약 보강
- 작성일: 2026-08-27
- TASK-ID: TASK-2026-08-27-002

## 작업 메타데이터

- TASK-ID: TASK-2026-08-27-002
- USER-REQUEST: 현재 harness_lab 저장소의 V2 문서 구조를 실제 운영에 더 적합하게 보완해줘.
- TASK-TYPE: DEVELOPMENT
- EXECUTION: PIPELINE
- RELAY: ALLOWED
- CURRENT-STAGE: REVIEW
- INPUT-ARTIFACT: 없음
- OUTPUT-ARTIFACT: 없음 — 저장소의 기존 운영 문서가 직접 결과임

EXECUTION은 TASK의 대표 실행 성격이다. 실제 Stage별 실행 방식과 담당은 아래 Stage Plan을 따른다.

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

- 한 줄 요청을 DEFINE Coordinator가 최소 TASK 계약과 Stage Plan으로 변환할 수 있게 한다.
- Stage별 execution·담당·required·status와 Exit Gate, waiver, 재작업 Loop를 명확히 한다.
- 연구 주장·출처·검증 결과와 artifact provenance를 추적할 수 있게 한다.
- 독립 REVIEW 조건과 표준 판정을 명확히 한다.

## 범위

- 기존 루트 운영 문서, 역할 문서와 shared 템플릿의 V2 정책 보강
- .obsidian 추적 상태와 무제.base 사용 여부 조사·보고

## 제약

- 지정된 기존 문서 안에서 해결하고 금지된 새 문서·프로그램·스크립트를 만들지 않는다.
- ENGINEERING_POLICY.md, .obsidian 파일과 무제.base를 변경·삭제하지 않는다.
- force push, reset --hard, branch 삭제와 사용자 승인 없는 commit·push·merge를 수행하지 않는다.
- 기존 Git 안전·보안·사용자 의사결정·merge-base/triple-dot 정책을 유지한다.

## 완료 조건

- 최상위 EXECUTION과 Stage별 execution의 의미가 구분된다.
- 단일/병렬 Research 흐름, 조건부 COMPARE와 독립 REVIEW가 구분된다.
- 모든 Stage의 Exit Gate와 FINAL gate, WAIVED 승인 근거가 정의된다.
- Claim/Source ID, VERIFY 결과, Verified Set을 추적할 수 있다.
- REVIEW와 research/development 재작업 Loop가 명확하다.
- artifact 기준일·상태·근거·검수 provenance를 확인할 수 있다.
- context만으로 현재 Stage status와 다음 작업을 이어받을 수 있다.
- 21개 검증 항목을 실제 문서와 Git 상태로 확인한다.
