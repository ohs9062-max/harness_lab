# 현재 작업

## 작성 정보

- 작성자: Codex
- 모델: GPT-5 계열 Codex
- 역할: Coordinator / 구현
- 작성일: 2026-09-03
- TASK-ID: TASK-2026-09-03-001

## 작업 메타데이터

- TASK-ID: TASK-2026-09-03-001
- USER-REQUEST: `harness_lab`과 `biz-ttori`를 전체 분석하여 재사용 가능한 AI 호출·역할·분배·인계·검수 기능을 현재 하네스 구조에 통합하고, 실제 AI CLI End-to-End 실행까지 검증한다.
- MODE: C (사용자 미지정; 요청의 설계→구현→독립검수 요구에 따라 기본 선택)
- TARGET-REPOSITORY: /home/hs/rang/harness_lab
- BASE-BRANCH: master
- BASE-COMMIT: 763146d16aef421a5f8b92c81ec13655789d55ed
- STATUS: COMPLETION_CANDIDATE (독립 REVIEW PASS)

## Stage Plan

### DESIGN
- agent: Codex (두 저장소 통합 분석 및 설계)
- status: DONE

### IMPLEMENT
- agent: Codex
- status: DONE

### TEST
- agent: Codex + 실제 Claude/Codex/Gemini CLI
- status: DONE

### REVIEW
- agent: Antigravity (`agy`, read-only 독립 검수)
- status: DONE
- verdict: PASS

## 목표

사용자가 자연어 목표를 한 번 입력하면 하네스가 작업을 구조화하고 적합한 AI CLI를 실제 호출하며, 단계 산출물을 다음 AI에 인계하고 결정론적 검사와 독립 REVIEW/FIX 루프를 거쳐 결과물을 완성한다.

## 범위

- 기존 Orchestrator V1의 CLI 어댑터, 계획, 상태, 로그, 테스트 코드 개선
- `biz-ttori`의 역할/권한 분리, 출력 제한, 테스트 우선 검수, 인계·감사 기록 개념 통합
- MODE C 자동 실행을 기본 경로로 구현하고 연구/병렬 읽기 작업 지원
- 실제 설치된 Claude/Codex/Gemini CLI 가용성 및 최소 E2E 검증

## 제약

- push, merge, 자동 commit을 수행하지 않는다.
- 비밀값을 로그나 shared 문서에 기록하지 않는다.
- 외부 저장소 `biz-ttori`는 읽기 전용으로 분석한다.
- 구현 AI와 최종 독립 reviewer를 분리한다.

## 완료 조건

- 단계별 결과가 실제 후속 단계에 전달된다.
- 구현/FIX는 공유 작업 트리에 반영되고 REVIEW는 명시적 verdict 없이는 통과하지 않는다.
- 결정론적 검사 실패 시 REVIEW 전에 중단한다.
- fake 기반 회귀 테스트와 실제 AI CLI 기반 E2E 실행 결과가 기록된다.
