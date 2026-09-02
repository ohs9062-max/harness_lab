# Harness Lab

여러 AI가 세 가지 실행 모드로 협업하는 문서 기반 하네스 환경이다.

## 실행 모드

| MODE | 이름 | 설명 |
|------|------|------|
| **A** | Parallel Competition | 같은 작업을 Codex/Gemini가 독립 수행 → Cross Review → Compare → 사용자 선택 |
| **B** | Relay | 같은 작업을 다른 AI가 이어받아 계속 수행 |
| **C** | Role Pipeline | Claude 설계 → Codex 구현/테스트 → Gemini 독립 검수 |

사용자는 어느 AI에게든 "A로 해", "B로 이어서 해", "C로 해"로 지시한다.
어떤 AI가 요청을 받든 동일한 실행 계약이 적용된다.

## 구조

- `AGENTS.md` — 모든 AI의 공통 행동·권한·Git 안전 규칙
- `MODES.md` — MODE A/B/C 실행 계약 정본 (상태 머신, Gate, Worker 규칙)
- `WORKFLOW.md` — TASK 시작부터 완료까지의 실제 운영 흐름
- `ENGINEERING_POLICY.md` — 코드 작성 원칙
- `claude/`, `codex/`, `gemini/` — AI별 기본 강점과 MODE별 행동
- `shared/` — 현재 TASK의 계약, 과정, 근거, 비교, 검수와 인계 상태
- `artifacts/` — 후속 TASK에서 재사용할 채택된 최종 결과물
- `demo/` — 실제 코드 작성·수정 실험 영역
- `CHANGELOG.md` — 하네스 정책과 문서 구조의 누적 변경 이력

## 시작

```text
사용자 요청 + MODE 지정
→ Entry AI가 TASK 정의 (shared/TASK.md)
→ Git Preflight
→ MODE에 따라 실행 (MODES.md)
→ 사용자 판단과 승인
→ artifacts에 최종 결과 보관
```

## 자동화 현황

| 구분 | 상태 |
|------|------|
| **Protocol** (문서 계약) | 이 저장소의 문서로 정의 완료 |
| **Runner** (자동 실행) | `demo/orchestrator`에 V1 프로토타입 존재. 완전 자동화 아님 |

현재 Worker 실행은 사용자가 해당 AI의 세션에서 직접 시작한다.
문서가 자동 실행되는 것은 아니다.

향후 Runner가 구현되면 `MODES.md`의 상태 머신과 Gate를 그대로 구현할 수 있다.

## 외부 프로젝트 적용

하네스를 외부 프로젝트에 적용할 때는 공통 문서, 역할 문서, `shared/`, `artifacts/`를
대상 프로젝트에 맞게 복사하고 `AGENTS.md`의 작업 범위를 실제 코드 위치에 맞춰 조정한다.
