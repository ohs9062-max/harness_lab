# Harness Lab 운영 가이드

## 작성 정보

- 작성자: Codex
- 모델: 미확인
- 역할: V2 Stage 실행 계약 보강
- 작성일: 2026-08-27
- TASK-ID: TASK-2026-08-27-002

이 문서는 TASK 시작부터 Stage 전환, 재작업과 FINAL까지의 실제 운영 흐름을 설명한다. 공통 행동·권한·
Git 안전 규칙은 AGENTS.md, 코드 원칙은 ENGINEERING_POLICY.md, 문서별 책임은 shared/README.md를 따른다.

## 1. DEFINE — 한 줄 요청을 TASK로 변환

최초 요청을 받은 AI가 DEFINE Coordinator를 맡는다.

~~~text
USER-REQUEST 원문 보존
→ TASK-TYPE 결정
→ 대표 EXECUTION 결정
→ 필요한 Stage와 STAGE-PLAN 작성
→ INPUT/OUTPUT-ARTIFACT 정의
→ 목표·범위·제약·완료 조건 정의
~~~

단순 운영 판단은 Coordinator가 정한다. 중요한 범위·구조 변경, 사용자 의도가 갈리는 경우,
PARALLEL 여부가 품질·비용을 크게 바꾸는데 의도가 불명확한 경우는 사용자 의사결정 게이트를 따른다.

최상위 EXECUTION은 TASK의 대표 실행 성격이다. 실제 Stage별 execution과 담당은 STAGE-PLAN이
정본이며 최상위 값만 보고 모든 Stage를 같은 방식으로 수행하지 않는다.

~~~markdown
## Stage Plan

### RESEARCH
- execution: PARALLEL
- agents: Claude, Codex, Gemini
- required: true
- status: PENDING

### VERIFY
- execution: PIPELINE
- agent: Codex
- required: true
- status: PENDING
~~~

Stage 항목은 execution, agent 또는 agents, required, status만 필수로 한다.

## 2. Stage 상태와 전환

허용 status는 PENDING, IN_PROGRESS, DONE, WAIVED, BLOCKED다.

- 담당자는 시작할 때 IN_PROGRESS, Exit Gate를 충족했을 때만 DONE으로 갱신한다.
- required Stage는 원칙적으로 완료해야 한다.
- AI는 required Stage를 임의로 생략하지 않는다.
- 생략은 사용자 승인 또는 TASK에 명시된 예외가 있을 때만 WAIVED로 기록하며
  waived-by와 reason을 남긴다.
- PENDING, IN_PROGRESS, BLOCKED인 required Stage가 있으면 FINAL로 넘어가지 않는다.
- context에는 전체 계획을 복사하지 않고 Stage별 status 요약만 유지한다.

## 3. Research Workflow

일반 단일 조사:

~~~text
DEFINE → RESEARCH → VERIFY → SYNTHESIZE → REVIEW → FINAL
~~~

PARALLEL 조사:

~~~text
DEFINE → RESEARCH × N → COMPARE → VERIFY → SYNTHESIZE → REVIEW → FINAL
~~~

COMPARE는 독립 후보가 여러 개일 때만 필요하다. 연구 결과의 REVIEW는 최종 synthesized artifact를
작성·수정하지 않은 AI 또는 fresh independent session이 수행한다.

### Research 재조사 Loop

~~~text
VERIFY
├─ 근거 충분 → SYNTHESIZE
└─ 근거 부족·충돌 → RESEARCH → 필요 시 COMPARE → VERIFY
~~~

근거가 부족한 주장을 억지로 SYNTHESIZE에 포함하지 않는다. VERIFY 결과는 별도 문서를 만들지 않고
RESEARCH 또는 COMPARE에 기록하며 최종 통과 주장은 COMPARE의 Verified Set에서 식별 가능해야 한다.
단일 조사처럼 COMPARE를 사용하지 않는 TASK는 RESEARCH에 VERIFY 결과를 기록하고 artifact 근거로 연결한다.

## 4. Development Workflow와 재작업

~~~text
ANALYZE → DESIGN → IMPLEMENT → TEST → REVIEW
~~~

REVIEW 뒤에는 판정에 따라 진행한다.

~~~text
REVIEW
├─ PASS → FINAL
├─ FIX_REQUIRED → FIX → TEST → REVIEW
└─ BLOCKED → 원인과 필요한 사용자·외부 조치 기록
~~~

FIX 후 TEST와 독립 REVIEW를 생략하지 않는다. 같은 세션이 작성·수정한 결과를 스스로 독립
REVIEW했다고 기록할 수 없다.

## 5. Stage Exit Gate

### DEFINE 완료

- TASK 계약과 Stage Plan이 존재한다.
- 사용자 원문, 입출력 artifact, 목표·범위·제약과 완료 조건이 정의됐다.

### RESEARCH 완료

- 주요 주장에 Claim ID와 근거가 연결됐다.
- 출처가 Source ID로 기록됐다.
- 확인 불가 사항과 추가 검증 필요 항목이 구분됐다.

### COMPARE 완료

- 모든 비교 대상 branch/commit과 Claim ID가 식별됐다.
- 공통·충돌 주장과 한 AI만 발견한 정보를 확인했다.
- Verified 후보와 추가 VERIFY 대상을 식별했다.

### VERIFY 완료

- 중요 주장을 재검증했다.
- 검증 실패 주장과 unresolved 항목을 분리했다.
- 최종 결과에 사용할 수 있는 주장을 식별했다.

### SYNTHESIZE 완료

- 검증된 정보만 반영하고 추측·미확인 내용을 사실처럼 섞지 않았다.
- 실제 내용이 있는 최종 artifact 후보를 만들었다.

### DESIGN 완료

- 구현자가 판단할 수 있는 설계, 영향 범위, 제약과 검증 방법이 있다.

### IMPLEMENT 완료

- 요구 구현을 완료하고 실제 변경 범위를 기록했다.

### TEST 완료

- 필요한 테스트를 실제 수행하고 명령·결과를 기록했다.
- 실패를 숨기지 않고 미해결 상태를 구분했다.

### REVIEW 완료

- 독립 검수 조건을 충족한 reviewer가 실제 결과와 근거를 확인했다.
- 판정이 PASS, FIX_REQUIRED, 필요 시 BLOCKED 중 하나다.

### FINAL 완료

- 모든 required Stage가 DONE 또는 사용자 근거가 있는 WAIVED다.
- 최종 artifact 또는 최종 구현과 provenance가 식별됐다.
- 생략 Stage를 포함해 RESULT와 사용자 최종 결정을 기록했다.

## 6. PIPELINE과 PARALLEL 운영

PIPELINE은 해당 Stage 담당자가 입력과 실제 파일을 확인해 Exit Gate를 충족한 뒤 다음 Stage로 넘긴다.
PARALLEL은 TASK Stage Plan에 지정된 Stage만 공통 기준의 별도 branch/worktree에서 독립 수행한다.

PARALLEL 시작 전 기준 branch·commit, 작업선, 결과 위치, 비교 담당과 통합 기준 branch를 TASK에
기록한다. 독립 작업 완료 전 다른 결과를 먼저 읽거나 복사하지 않는다. 결과는 checkpoint로 식별하고
COMPARE에서 정보 채택 가능성을 선별한다. 사용자 승인 전 merge·cherry-pick·수동 통합하지 않는다.

## 7. REVIEW 독립성과 판정

독립 reviewer는 최종 결과 작성·수정에 참여하지 않은 AI이거나 같은 AI의 fresh independent
session이어야 한다. 예를 들어 Gemini RESEARCH session과 Gemini Independent Review session은
서로 다른 session이어야 한다.

대체로 통과, 거의 완료, 문제 없어 보임은 표준 판정이 아니며 Stage를 자동 전환하지 않는다.
REVIEW 문서에는 reviewer/session, 결과 작성 참여 여부, 대상 artifact 또는 commit과 판정을 기록한다.

## 8. RELAY

RELAY는 현재 Stage와 역할을 다른 AI에게 넘기는 인계 방식이다. 넘기는 AI는 context에 Stage status
요약, 완료·진행·남은 작업, branch/checkpoint, 검증 상태와 다음 확인 위치를 남긴다. 이어받는 AI는
실제 파일과 Git 상태를 대조하고 같은 Stage와 status에서 계속한다.

## 9. local checkpoint와 worktree 검수

checkpoint commit은 AI 간 인계·비교·검수용 로컬 스냅샷이며 push나 master merge가 아니다.
commit·push·merge는 AGENTS.md의 사용자 승인 정책을 따른다.

다른 worktree는 merge-base와 triple-dot diff로 실제 작업 변경을 검수한다.

~~~bash
git merge-base <base-branch> <work-branch>
git diff <base-branch>...<work-branch>
~~~

현재 base와 다름만으로 작업 AI가 파일을 삭제·변경했다고 단정하지 않는다. REVIEW에 기준·대상
branch/commit, merge-base와 실제 명령을 남긴다.

## 10. FINAL과 artifact

FINAL 전에 Stage Plan의 모든 required Stage를 검사한다. 미완료 Stage는 완료하거나 사용자 승인으로
WAIVED 처리해야 하며 RESULT에 생략 사실과 근거를 남긴다.

재사용할 결과는 artifacts/<TASK-ID>/<의미 있는 이름>에 저장한다. RESULT에는 Stage 상태 요약,
REVIEW 판정, artifact 경로, 채택 branch/commit과 사용자 최종 결정을 기록한다.
