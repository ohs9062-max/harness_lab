# 현재 작업

## 작성 정보

- 작성자: Codex
- 모델: 미확인
- 역할: V2 문서 구조 구현
- 작성일: 2026-08-27
- TASK-ID: TASK-2026-08-27-001

## 작업 메타데이터

- TASK-ID: TASK-2026-08-27-001
- USER-REQUEST: 현재 harness_lab 저장소를 문서 기반 하네스 V2 구조로 정리해줘.
- TASK-TYPE: DEVELOPMENT
- EXECUTION: PIPELINE
- RELAY: ALLOWED
- CURRENT-STAGE: FINAL
- INPUT-ARTIFACT: 없음
- OUTPUT-ARTIFACT: 없음 — 이번 결과는 저장소의 운영 문서 구조 자체임

## 목표

- 한 줄 요청을 조사·설계·구현·검수 Stage로 연결할 수 있는 문서 계약을 만든다.
- PIPELINE/PARALLEL 실행 방식과 RELAY 인계 방식을 분리한다.
- AI가 중단되어도 context만으로 같은 Stage와 역할을 이어받을 수 있게 한다.
- 최종 결과를 artifact로 보존하고 후속 TASK가 입력으로 재사용할 수 있게 한다.

## 범위

- 루트 운영 문서, AI별 역할 문서와 shared 문서 구조 개선
- shared/RESEARCH.md, shared/COMPARE.md, artifacts/ 추가
- 현재 작업 기록을 V2 메타데이터로 전환

## 제약

- 문서 구조 개선만 수행하고 orchestrator, 자동 실행 스크립트, DB나 자동 branch manager를 만들지 않는다.
- 기존 Git 안전·사용자 승인·독립 검수 정책을 유지한다.
- force push, branch 삭제, reset --hard를 수행하지 않는다. push와 master merge는 사용자 후속 명시 승인 후 수행했다.
- 같은 규칙을 여러 문서에 장황하게 중복하지 않는다.

## 필요한 Stage

ANALYZE → DESIGN → IMPLEMENT → TEST → REVIEW → FINAL

## 완료 조건

- AGENTS만으로 PIPELINE/PARALLEL/RELAY 차이와 Stage 우선 원칙을 이해할 수 있다.
- TASK와 context가 요구된 V2 필드를 갖춘다.
- PARALLEL RESEARCH를 독립 기록하고 COMPARE에서 선별할 수 있다.
- COMPARE와 REVIEW, shared와 artifacts의 책임이 분리된다.
- artifact를 후속 TASK의 INPUT-ARTIFACT로 지정할 수 있다.
- Git 안전, merge-base/triple-dot, 작성 정보와 ENGINEERING_POLICY 정본 역할이 유지된다.
- 불필요한 파일·자동화·코드가 추가되지 않고 Markdown 검증을 통과한다.
