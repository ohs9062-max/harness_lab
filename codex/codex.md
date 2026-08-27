# Codex 작업 정책

공통 행동 규칙은 루트 `AGENTS.md`를 따른다. 코드 작업일 때만 `ENGINEERING_POLICY.md`를
추가로 확인한다. 이 문서는 Codex의 기본 강점과 Stage별 행동만 정의한다.

## 기본 강점

- 구현과 수정
- 실행과 테스트
- 로그 기반 디버깅
- 변경·검증 결과 기록

기본 강점은 절대 역할이 아니다. 사용자 지시, TASK, CURRENT-STAGE와 RELAY로 전달받은 역할이
Codex라는 이름보다 우선한다.

## 실행 계약 확인

- 최초 요청을 받으면 DEFINE Coordinator로 TASK와 Stage Plan을 작성할 수 있다.
- 작업 전 Stage Plan의 execution, 담당, required, status와 WORKFLOW의 Exit Gate를 확인한다.
- required Stage를 임의로 생략하거나 WAIVED 처리하지 않는다.
- 결과 작성·수정에 참여했다면 같은 세션에서 독립 REVIEW를 겸하지 않는다.
- RELAY에서는 인계된 Stage status와 역할을 그대로 이어받는다.

## Stage별 행동

- `RESEARCH`: 독립 기술 조사를 수행하고 주장·근거·출처를 `shared/RESEARCH.md`에 기록할 수 있다. PARALLEL에서는 자기 Agent namespace ID를 사용하고 번호를 사전 조율하지 않는다.
- `IMPLEMENT`: DESIGN, 결정, 입력 artifact와 실제 코드를 대조해 필요한 범위만 수정한다.
- `TEST`: 실행 명령, 예상 결과, 실제 결과와 종료 코드를 구분해 기록한다.
- `FIX`: REVIEW finding을 실제 코드와 재현 결과로 확인한 뒤 범위 안에서 수정하고 재검증한다.
- 그 밖의 Stage: TASK가 지정한 완료 조건과 공통 규칙에 따라 수행한다.

IMPLEMENT와 TEST 결과는 `shared/IMPLEMENTATION.md`에 branch, 기준·대상 commit, 변경 파일과
검증 결과를 함께 기록한다. 자체 테스트는 구현 확인이지 독립 최종 REVIEW가 아니다.

## PIPELINE과 PARALLEL

PIPELINE에서는 현재 Stage의 입력과 실제 파일을 확인하고 완료 조건을 충족한 뒤 다음 Stage로 넘긴다.
PARALLEL에서는 공통 기준의 별도 branch/worktree에서 독립 결과를 만든다. 다른 AI의 조사나 구현을
먼저 복사하지 않으며 branch, checkpoint와 검증 근거를 남긴다. 사용자 승인 전 통합하지 않는다.

## RELAY

RELAY를 받으면 `shared/context.md`, checkpoint와 실제 diff를 대조하고 전달받은 CURRENT-STAGE와
역할을 그대로 이어간다. DESIGN 중이면 설계를, REVIEW 중이면 검수를 수행하며 구현부터 새로 시작하지 않는다.

작업을 넘길 때는 현재 Stage, 완료·진행·남은 작업, 변경 파일, branch/checkpoint, 실행·테스트 결과,
산출물과 RELAY 사유를 context에 남긴다. 구현이나 작성에 참여했다면 같은 결과의 독립 REVIEW를 겸하지 않는다.

## 문서와 경계

- shared 문서를 실질적으로 갱신하면 작성 정보에 실제 작성자, 확인 가능한 모델 또는 `미확인`, 실제 역할, 작성일과 TASK-ID를 기록한다.
- 관련 없는 리팩터링, 파일, 폴더나 의존성을 추가하지 않는다.
- 설계·결정과 실제 코드가 충돌하면 임의로 우회하지 않고 영향과 선택지를 알린다.
- 독립 REVIEW 결과는 사실관계 정정 외에 구현자가 임의로 바꾸지 않는다.
