# 결과 비교 기록

## 작성 정보

- 작성자: Codex
- 모델: 미확인
- 역할: Normalized Claim 비교 템플릿 보강
- 작성일: 2026-08-27
- TASK-ID: TASK-2026-08-27-003

## 작업 식별

- TASK-ID: TASK-2026-08-27-003
- Stage: COMPARE / VERIFY
- 현재 TASK 적용: 해당 없음 — PARALLEL 미사용

## 비교 대상

| AI | branch | commit |
|---|---|---|
| Claude | 해당 없음 | 해당 없음 |
| Codex | 해당 없음 | 해당 없음 |
| Gemini | 해당 없음 | 해당 없음 |

## Normalized Claims

COMPARE만 N-Cxxx를 생성한다. N-C는 원본 Claim ID를 대체하지 않으며, 같은 의미의 주장만 묶는다.
인과관계나 주장 의미가 다른 유사 Claim은 별도 N-C로 유지한다.

### N-C001

- 정규화 주장:
- 원본 Claim:
  - Claude: CLAUDE-C003
  - Codex: CODEX-C008
  - Gemini: GEMINI-C002

#### AI별 판정

Claude:
- 상태: CONFIRMED
- Source: CLAUDE-S002

Codex:
- 상태: PROBABLE
- Source: CODEX-S005

Gemini:
- 상태: CONFIRMED
- Source: GEMINI-S004

#### 비교 결과

- 상태: VERIFY_REQUIRED
- 충돌 여부:
- 추가 검증:

## Source 관계

동일 URL 또는 원출처를 여러 AI가 발견한 경우 원본 Source ID는 유지하고, 독립 근거 수를 중복 계산하지
않는다. 필요할 때만 아래처럼 COMPARE 안에서 관계를 기록한다.

### SG-001

- source-origin: same
- 원출처:
- 원본 Source: CLAUDE-S002, CODEX-S005, GEMINI-S001

## 공통 주장

- Normalized Claim:
- 내용:

## 충돌 주장

- Normalized Claim 또는 원본 Claim:
- 충돌 내용:

## 한 AI만 발견한 중요 정보

- 원본 Claim ID:
- 발견 AI:
- 중요성:

## 출처 품질 비교

- Normalized Claim:
- 원본 Source ID별 품질 차이:

## 추가 검증 필요 항목

- Normalized Claim:
- 검증 질문:

## 재검증 결과

- Normalized Claim:
- 관련 원본 Claim/Source:
- 검증 결과:
- 최종 상태:
- unresolved 항목:

PARALLEL VERIFY는 가능한 한 Normalized Claim에서 관련 원본 Claim/Source까지 역추적한다.

## 채택한 주장

- Normalized Claim:
- 채택 이유:

## 제외한 주장과 이유

- Normalized Claim 또는 원본 Claim:
- 제외 이유:

## Verified Set

| Normalized Claim | 원본 Claim | 최종 상태 | 채택 Source | 검증 근거 | artifact 반영 |
|---|---|---|---|---|---|
| N-C001 | CLAUDE-C003 / CODEX-C008 / GEMINI-C002 | 해당 없음 | 해당 없음 | 해당 없음 | 해당 없음 |

최종 artifact는 가능하면 Normalized Claim 기준으로 근거를 추적한다. artifact 본문에 N-C ID를
노출할 필요는 없지만 REVIEW가 artifact 주장 → N-C → 원본 Claim/Source를 따라갈 수 있어야 한다.
