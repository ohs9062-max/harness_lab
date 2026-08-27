# Harness Lab

여러 AI가 작업 Stage를 순차 또는 병렬로 수행하고, 조사·설계·구현·검수의 상태와 근거를 파일로
전달하는 문서 기반 협업 하네스다. 특정 AI가 토큰 한도나 세션 종료로 중단되어도 RELAY를 통해
같은 Stage와 역할을 다른 AI가 이어받고, 채택된 결과는 후속 TASK에서 재사용할 artifact로 남긴다.

## 핵심 개념

- `PIPELINE`: 필요한 Stage를 순서대로 수행하는 실행 방식
- `PARALLEL`: 같은 Stage나 문제를 여러 AI가 독립 수행하는 실행 방식
- `RELAY`: 실행 도중 현재 Stage와 역할을 다른 AI가 이어받는 인계 방식
- `Stage`: TASK 성격에 맞게 선택하는 현재 작업 단계
- `STAGE-PLAN`: Stage별 실행 방식, 담당, 필수 여부와 상태를 기록하는 실제 실행 계약
- `artifact`: 검증·채택되어 다음 TASK의 입력으로 재사용할 완성된 결과물

## 목적

1. 여러 AI가 작업 Stage를 분담하거나 병렬 수행한다.
2. 각 결과와 근거를 파일 기반으로 전달·비교·검증한다.
3. 토큰·세션 종료 시 RELAY로 현재 작업을 이어간다.
4. 최종 검증 결과를 artifact로 남긴다.
5. 이후 TASK가 기존 artifact를 입력으로 재사용한다.

예를 들어 `TASK-2026-08-27-001`이 “네이버 블로그 상위노출 전략 조사”를 수행해
`artifacts/TASK-2026-08-27-001/naver_blog_strategy.md`를 만들면, 후속 TASK는 해당 경로를
`INPUT-ARTIFACT`로 지정해 자동화 프로그램 개발을 시작할 수 있다.

## 구조

- `AGENTS.md` — 모든 AI의 공통 행동·권한·Git 안전 규칙
- `ENGINEERING_POLICY.md` — 코드 작성 원칙
- `WORKFLOW.md` — 사용자를 위한 실제 운영 흐름
- `claude/`, `codex/`, `gemini/` — AI별 기본 강점과 Stage별 행동
- `shared/` — 현재 TASK의 계약, 과정, 근거, 비교, 검수와 인계 상태
- `artifacts/` — 후속 TASK에서 재사용할 채택된 최종 결과물
- `demo/` — 실제 코드 작성·수정 실험 영역
- `CHANGELOG.md` — 하네스 정책과 문서 구조의 누적 변경 이력

문서별 세부 책임과 새 TASK 초기화 기준은 `shared/README.md`에서 확인한다.

## 시작

```text
사용자 요청
→ DEFINE Coordinator가 TASK와 Stage Plan·입출력 정의
→ WORKFLOW에 따라 수행
→ context로 현재 상태와 RELAY 인계 유지
→ 독립 검증과 사용자 판단
→ artifacts에 최종 결과 보관
→ RESULT에 종료 상태 기록
```

일반 새 개발 작업은 PIPELINE을 기본 후보로 볼 수 있지만, PARALLEL 여부가 결과 품질을 크게
바꾸고 사용자 의도가 불명확하면 사용자에게 확인한다. 어떤 실행 방식에서도 현재 Stage와
RELAY로 전달된 역할이 AI의 기본 강점보다 우선한다. TASK의 최상위 `EXECUTION`은 대표 성격이고
실제 Stage별 실행은 `STAGE-PLAN`을 따른다.

## 외부 프로젝트 적용

하네스를 외부 프로젝트에 적용할 때는 공통 문서, 역할 문서, `shared/`, `artifacts/`를
대상 프로젝트에 맞게 복사하고 `AGENTS.md`의 작업 범위를 실제 코드 위치에 맞춰 조정한다.
