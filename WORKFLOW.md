# Harness Lab 운영 가이드

## 작성 정보

- 작성자: Codex
- 모델: 미확인
- 역할: V2 운영 흐름 문서화
- 작성일: 2026-08-27
- TASK-ID: TASK-2026-08-27-001

이 문서는 사용자가 파일 기반 하네스를 실제로 운영하는 순서를 설명한다. 공통 행동·권한·Git
안전 규칙은 `AGENTS.md`, 코드 구현 원칙은 `ENGINEERING_POLICY.md`, 문서별 책임과 초기화 기준은
`shared/README.md`를 따른다.

## 1. TASK 시작

```text
사용자 요청
→ TASK 정의
→ TASK-TYPE 결정
→ EXECUTION 결정
→ 필요한 Stage 결정
```

1. 이전 TASK가 종료되고 shared 기록이 Git에 보존됐는지 확인한다. 보존되지 않았다면 local
   checkpoint를 제안하되 승인 없이 commit하지 않는다.
2. 중복되지 않는 `TASK-YYYY-MM-DD-NNN`을 정한다.
3. `shared/TASK.md`에 사용자 원문, TASK-TYPE(`RESEARCH`, `DEVELOPMENT`, `MIXED`),
   EXECUTION(`PIPELINE`, `PARALLEL`), RELAY 허용 여부, 필요한 Stage, 입출력 artifact와 완료 조건을 쓴다.
4. 일반 새 개발 작업은 PIPELINE을 기본 후보로 볼 수 있다. PARALLEL 여부가 결과 품질을 크게
   바꾸고 사용자 의도가 불명확하면 사용자에게 확인한다.
5. 담당 AI는 역할 문서, context, 현재 Stage에 필요한 shared 문서와 실제 작업 대상을 확인한다.

## 2. PIPELINE

PIPELINE은 필요한 Stage를 순차 수행한다. AI 이름은 기본 배치 기준일 뿐 현재 Stage보다 우선하지 않는다.

연구·전략 작업의 대표 흐름:

```text
DEFINE → RESEARCH → COMPARE → VERIFY → SYNTHESIZE → FINAL
```

개발 작업의 대표 흐름:

```text
ANALYZE → DESIGN → IMPLEMENT → TEST → REVIEW → FIX(필요 시) → FINAL
```

대표 개발 배치는 Claude가 ANALYZE/DESIGN, Codex가 IMPLEMENT/TEST, Gemini가 REVIEW를 맡는
형태다. 단순 작업은 일부 Stage를 생략할 수 있고 사용자 지시와 TASK가 우선한다. Stage 전환 때
입력 문서·artifact, 실제 파일과 검증 상태를 확인하고 context를 현재 상태로 갱신한다.

## 3. PARALLEL

PARALLEL은 같은 Stage 또는 같은 문제를 여러 AI가 별도 branch/worktree에서 독립 수행한다.

```text
기준 branch/commit
├─ Claude worktree
├─ Codex worktree
└─ Gemini worktree
```

시작 전에 공통 기준 branch·commit, 각 작업선과 결과물 위치, 비교 담당, `shared/COMPARE.md`,
통합 기준 branch를 TASK에 기록한다. 각 AI는 같은 질문과 완료 기준을 사용하되 독립 작업을 마치기
전 다른 AI 결과를 먼저 읽거나 복사해 맞추지 않는다.

PARALLEL RESEARCH에서는 각 branch의 `shared/RESEARCH.md`에 조사 근거를 남긴다. 독립 결과를
checkpoint로 식별한 뒤 비교 담당이 `shared/COMPARE.md`에서 공통·충돌 주장, 한 AI만 발견한 정보,
출처 품질, 재검증 결과와 Verified Set을 정리한다. COMPARE는 후보 선별이며, 선택·종합된 결과에 대한
독립 최종 검증인 REVIEW와 다르다.

사용자가 선택하거나 승인하기 전에는 merge, cherry-pick 또는 수동 통합하지 않는다. 선택된 결과만
통합하고 통합본을 다시 검증한다.

## 4. RELAY

RELAY는 실행 방식이 아니라 현재 Stage가 중단될 때 같은 상태와 역할을 다른 AI에게 넘기는 인계 방식이다.
PIPELINE과 PARALLEL 어느 쪽에서도 토큰 한도, 세션 종료, AI 일시 사용 불가, 사용자 역할 교체 또는
환경 문제로 발생할 수 있다.

넘기는 AI는 `shared/context.md`에 현재 Stage와 STATUS, 완료·진행·남은 작업, 현재 역할, branch,
기준 branch, checkpoint, 변경 파일, 검증 상태, 산출물, 다음 확인 사항과 RELAY 사유를 기록한다.
이어받는 AI는 실제 파일과 Git 상태를 대조한 뒤 같은 Stage와 역할의 미완료 지점부터 계속한다.
자기 기본 강점을 이유로 DESIGN이나 REVIEW 등 다른 Stage에서 다시 시작하지 않는다.

## 5. local checkpoint commit

AI 간 인계·비교·검수 대상을 고정할 때 local checkpoint commit을 사용할 수 있다. 사용자 승인 없이
commit하지 않으며, 승인을 받지 못했거나 중단이 임박하면 미커밋 변경과 확인 방법을 context에 남긴다.

```text
local checkpoint commit = AI 간 인계·검수용 로컬 스냅샷
push                    = remote 저장소 반영
merge                   = 기준 branch에 변경 통합
```

local commit은 push나 master merge가 아니다. push, merge, force push, branch 삭제 등은
`AGENTS.md`의 Git 안전 규칙과 사용자 승인 범위를 따른다.

## 6. 다른 worktree 결과 검수

검수 AI는 대상 branch로 checkout할 필요 없이 자기 worktree에서 `git log`, `git show`, `git diff`로
확인한다. branch가 오래된 기준에서 갈라졌다면 merge-base와 triple-dot diff로 실제 작업 변경을 구분한다.

```bash
git merge-base <base-branch> <work-branch>
git diff <base-branch>...<work-branch>
```

`현재 base와 다름`은 `작업 AI가 삭제·변경함`과 같지 않다. REVIEW에는 기준 branch, 대상 branch와
commit, merge-base와 실제 diff 명령을 남긴다. 오판은 원 기록을 숨기지 않고 정정한다.

## 7. 사용자 의사결정

기존 기능·외부 인터페이스·중요 구조·보안·범위 변경, 정책 충돌, AI 간 중요한 의견 충돌처럼 결과
방향을 바꾸는 판단만 `shared/DECISIONS.md`에 기록한다. 작은 기술 세부는 담당 AI가 TASK와 정책
안에서 결정한다.

## 8. FINAL과 artifact

FINAL에서는 선택·종합된 결과를 독립 REVIEW와 사용자 판단에 연결한다. 재사용할 최종 결과물은
`artifacts/<TASK-ID>/<의미 있는 이름>`에 저장한다. shared 문서는 작업 과정이고 artifact는 다음
TASK가 `INPUT-ARTIFACT`로 사용할 수 있는 완성된 결과물이다.

`shared/RESULT.md`에는 채택·수정 후 채택·폐기·보류 상태, 최종 artifact 경로, 채택 branch/commit,
검수 결과, 병렬 선택·조합 여부, 남은 문제와 사용자 최종 결정을 기록한다. RESULT 자체를 최종
artifact로 사용하지 않는다.
