# shared 문서 운영 안내

shared/는 현재 TASK의 계약, 작업 과정, 근거, 비교, 검수와 인계 상태를 공유한다. 재사용 가능한
최종 결과물은 artifacts/, 누적 이력은 Git과 CHANGELOG에서 확인한다.

## 문서별 책임

| 문서 | 책임 |
|---|---|
| TASK.md | 사용자 원문, 대표 실행 방식, Stage Plan, 입출력과 완료 조건을 담은 작업 계약 |
| context.md | 현재 상태, Stage status 요약과 RELAY 인계 스냅샷 |
| DECISIONS.md | 사용자가 확정해야 할 중요한 방향 |
| RESEARCH.md | 작성 AI namespace의 원본 Claim/Source ID로 연결된 독립 조사 근거와 VERIFY 결과 |
| COMPARE.md | Normalized Claim과 원본 ID 매핑, VERIFY 결과와 Verified Set |
| DESIGN.md | 개발 DESIGN Stage의 설계 결과 |
| IMPLEMENTATION.md | 실제 구현, 실행·테스트 결과 |
| REVIEW.md | 선택·종합된 결과의 독립 최종 검증 |
| RESULT.md | 사용자 판단과 TASK 종료 상태 |

COMPARE는 후보를 비교하고 신뢰할 내용을 선별한다. REVIEW는 선택·종합된 결과가 TASK와 근거에
맞는지 독립 검증한다. RESULT는 artifact가 아니라 종료 기록이다.

새 TASK의 PARALLEL RESEARCH는 각 AI가 자기 namespace 원본 ID를 독립 생성한다. 같은 의미의
원본 Claim은 COMPARE에서만 Normalized Claim으로 묶고 원본 ID는 보존한다. 기존 TASK와 Git history의
`C-001`/`S-001` 기록은 당시 형식을 유지하며 일괄 변경하지 않는다.

## 작업 주기

1. 이전 TASK가 종료되고 Git에 보존됐는지 확인한다.
2. 보존되지 않았다면 local checkpoint를 제안하되 승인 없이 commit하지 않는다.
3. 새 TASK-ID로 필요한 shared 문서를 초기화한다.
4. TASK에 TASK-TYPE, 대표 EXECUTION, RELAY, CURRENT-STAGE, INPUT/OUTPUT-ARTIFACT와 Stage Plan을 기록한다.
5. 현재 Stage에 필요한 문서만 사용하고 적용하지 않는 문서는 해당 없음과 이유를 짧게 남긴다.
6. RELAY 때 context를 최신 상태로 갱신한다.
7. PARALLEL은 각 branch에서 독립 결과를 만든 뒤 COMPARE에서 식별 가능한 checkpoint를 비교한다.
8. 독립 REVIEW와 사용자 결정 후 artifact와 RESULT를 확정한다.

## 초기화와 작성 정보

- 이전 TASK 내용을 복사해 누적하지 않고 Git history에서 확인한다.
- 실질 작성자는 문서 상단에 실제 작성자, 확인 가능한 모델 또는 미확인, 실제 역할, 작성일과 TASK-ID를 기록한다.
- 단순 열람이나 오탈자 수정에는 작성 정보를 바꾸지 않는다.
- IMPLEMENTATION은 RELAY 중 여러 구현자의 범위를 작성자별 항목으로 누적할 수 있다.
- context는 완료·진행·남은 작업, Stage status 요약, Git·검증·산출물과 다음 인계를 간결하게 유지한다.
- 독립 검수를 수행하지 않았다면 REVIEW를 통과로 기록하지 않는다.
- RESULT에는 required, DONE, WAIVED, BLOCKED/미완료 Stage와 REVIEW 판정을 구분한다.

## 새 TASK 점검표

- [ ] TASK-ID와 사용자 원문 요청이 있다.
- [ ] TASK-TYPE, EXECUTION, RELAY, CURRENT-STAGE가 있다.
- [ ] Stage별 execution, agent(s), required, status가 있다.
- [ ] INPUT-ARTIFACT와 OUTPUT-ARTIFACT가 있다.
- [ ] 목표, 범위, 제약과 완료 조건이 있다.
- [ ] PARALLEL이면 기준 commit, 독립 작업선, 비교 담당·대상과 통합 기준이 있다.
- [ ] context만으로 같은 Stage와 역할을 이어받을 수 있다.
- [ ] FINAL 전 required Stage가 DONE 또는 승인 근거가 있는 WAIVED다.
- [ ] shared 과정 문서와 artifacts 최종 결과를 혼동하지 않았다.
- [ ] 사용자 중요 결정과 작은 내부 판단을 구분했다.
