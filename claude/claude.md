# Claude 작업 정책

공통 행동 규칙은 루트 `AGENTS.md`를 따른다. 코드 작업일 때만 `ENGINEERING_POLICY.md`를
추가로 확인한다. 이 문서는 Claude의 기본 강점과 Stage별 행동만 정의한다.

## 기본 강점

- 요구사항 분석
- 구조와 설계 판단
- 여러 결과의 종합
- 불확실성과 사용자 결정 항목의 분리

기본 강점은 절대 역할이 아니다. 사용자 지시, TASK, CURRENT-STAGE와 RELAY로 전달받은 역할이
Claude라는 이름보다 우선한다.

## 실행 계약 확인

- 최초 요청을 받으면 DEFINE Coordinator로 TASK와 Stage Plan을 작성할 수 있다.
- 작업 전 Stage Plan의 execution, 담당, required, status와 WORKFLOW의 Exit Gate를 확인한다.
- required Stage를 임의로 생략하거나 WAIVED 처리하지 않는다.
- 결과 작성·수정에 참여했다면 같은 세션에서 독립 REVIEW를 겸하지 않는다.
- RELAY에서는 인계된 Stage status와 역할을 그대로 이어받는다.

## Stage별 행동

- `RESEARCH`: 다른 결과를 전제로 삼지 않고 독립 조사하며 주장·근거·출처를 `shared/RESEARCH.md`에 기록할 수 있다. PARALLEL에서는 자기 Agent namespace ID를 사용하고 번호를 사전 조율하지 않는다.
- `COMPARE` / `SYNTHESIZE`: 후보의 공통점·충돌·근거 품질을 구분하고 Verified Set을 바탕으로 일관된 결과를 종합할 수 있다.
- `ANALYZE` / `DESIGN`: 실제 저장소와 입력 artifact를 확인해 범위, 구조, 인터페이스, 위험, 검증 기준을 `shared/DESIGN.md`에 기록한다.
- 그 밖의 Stage: TASK가 지정한 완료 조건과 공통 규칙에 따라 수행한다.

## PIPELINE과 PARALLEL

PIPELINE에서는 현재 Stage의 입력과 실제 파일을 확인하고 완료 조건을 충족한 뒤 다음 Stage로 넘긴다.
PARALLEL에서는 공통 기준의 별도 branch/worktree에서 독립 결과를 만든다. 독립 작업 완료 전 다른
AI 결과를 먼저 읽거나 복사해 결론을 맞추지 않으며, 승인 전 merge하지 않는다.

## RELAY

RELAY를 받으면 `shared/context.md`, checkpoint와 실제 diff를 대조하고 전달받은 CURRENT-STAGE와
역할을 그대로 이어간다. IMPLEMENT 중이었다면 구현을 계속하고 REVIEW 중이었다면 검수를 계속한다.
기본 강점을 이유로 ANALYZE나 DESIGN부터 다시 시작하지 않는다.

작업을 넘길 때는 현재 Stage, 완료·진행·남은 작업, 판단 근거, branch/checkpoint, 검증 결과,
산출물과 RELAY 사유를 context에 남긴다. 구현이나 작성에 참여했다면 같은 결과의 독립 REVIEW를 겸하지 않는다.

## 문서와 경계

- shared 문서를 실질적으로 갱신하면 작성 정보에 실제 작성자, 확인 가능한 모델 또는 `미확인`, 실제 역할, 작성일과 TASK-ID를 기록한다.
- 실제 코드 확인 없이 설계를 확정하지 않는다.
- 관련 없는 구조 변경을 제안하지 않는다.
- 정책 충돌이나 결과를 바꾸는 중요한 선택은 `shared/DECISIONS.md`에서 사용자 판단을 요청한다.
