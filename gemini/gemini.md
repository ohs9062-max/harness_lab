# Gemini 작업 정책

공통 행동 규칙은 루트 `AGENTS.md`를 따른다. 코드 작업일 때만 `ENGINEERING_POLICY.md`를
추가로 확인한다. 이 문서는 Gemini의 기본 강점과 Stage별 행동만 정의한다.

## 기본 강점

- 다른 결과를 보지 않는 독립 조사
- 반대 관점과 반례 탐색
- 독립 검수
- 출처와 결과의 교차 검증

기본 강점은 절대 역할이 아니다. 사용자 지시, TASK, CURRENT-STAGE와 RELAY로 전달받은 역할이
Gemini라는 이름보다 우선한다.

## 실행 계약 확인

- 최초 요청을 받으면 DEFINE Coordinator로 TASK와 Stage Plan을 작성할 수 있다.
- 작업 전 Stage Plan의 execution, 담당, required, status와 WORKFLOW의 Exit Gate를 확인한다.
- required Stage를 임의로 생략하거나 WAIVED 처리하지 않는다.
- 결과 작성·수정에 참여했다면 같은 세션에서 독립 REVIEW를 겸하지 않는다.
- RELAY에서는 인계된 Stage status와 역할을 그대로 이어받는다.

## Stage별 행동

- `RESEARCH`: PARALLEL이면 다른 AI 결과를 보기 전에 독립 조사하고 주장·근거·출처를 `shared/RESEARCH.md`에 기록한다. 자기 Agent namespace ID를 사용하고 번호를 사전 조율하지 않는다.
- `COMPARE`: 후보별 공통·충돌 주장, 한 AI만 발견한 정보, 출처 품질과 추가 검증 필요 항목을 비교한다.
- `VERIFY`: 핵심 주장과 출처를 다시 확인해 Verified Set에 포함할 수 있는지 판단한다.
- `REVIEW`: 작성자의 설명을 전제로 삼지 않고 artifact, TASK, 근거 문서와 실제 diff·테스트를 독립 검증한다.
- 그 밖의 Stage: TASK가 지정한 완료 조건과 공통 규칙에 따라 수행한다.

연구 REVIEW는 synthesized artifact가 RESEARCH, COMPARE, VERIFY 근거와 일치하는지 확인한다.
개발 REVIEW는 TASK, DESIGN, IMPLEMENTATION, 결정, 실제 diff와 테스트를 직접 대조한다.
COMPARE는 후보 선별이고 REVIEW는 선택 결과의 독립 최종 검증이므로 섞지 않는다.

## PIPELINE과 PARALLEL

PIPELINE에서는 현재 Stage의 입력과 실제 파일을 확인하고 완료 조건을 충족한 뒤 다음 Stage로 넘긴다.
PARALLEL에서는 공통 기준의 별도 branch/worktree에서 독립 결과를 만들며 독립 작업 완료 전 다른
결과를 먼저 읽지 않는다. 자신의 병렬 결과에 대한 비교 의견은 독립 REVIEW로 기록하지 않는다.

## RELAY

RELAY를 받으면 `shared/context.md`, checkpoint와 실제 diff를 대조하고 전달받은 CURRENT-STAGE와
역할을 그대로 이어간다. IMPLEMENT 중이었다면 구현을 계속하며 Gemini라는 이유로 REVIEW부터 시작하지 않는다.

작업을 넘길 때는 현재 Stage, 완료·진행·남은 작업, 판단·검증 근거, branch/checkpoint, 산출물과
RELAY 사유를 context에 남긴다. 구현이나 작성에 참여했다면 같은 결과의 독립 REVIEW를 겸하지 않는다.

## 문서와 경계

- REVIEW에는 기준 branch, 대상 branch/commit, merge-base와 triple-dot diff 명령을 기록한다.
- shared 문서를 실질적으로 갱신하면 작성 정보에 실제 작성자, 확인 가능한 모델 또는 `미확인`, 실제 역할, 작성일과 TASK-ID를 기록한다.
- 테스트하지 않은 결과를 통과로 간주하지 않고 취향 차이를 결함으로 제시하지 않는다.
- finding은 위치, 원인, 근거와 재현 방법을 제시하며 오판은 원 기록을 숨기지 않고 정정한다.
