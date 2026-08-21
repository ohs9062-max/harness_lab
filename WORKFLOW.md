# Harness Lab 운영 가이드

## 작성 정보

- 작성자: Codex
- 모델: 미확인
- 역할: 세 운영 MODE 문서화
- 작성일: 2026-08-21
- TASK-ID: TASK-2026-08-21-002

이 문서는 사용자가 Orca, Git, Markdown 기반 하네스를 실제로 운영하는 순서를 설명한다.
AI 협업·권한·Git 안전 규칙은 `AGENTS.md`, 코드 원칙은 `ENGINEERING_POLICY.md`를 따른다.

## 1. 작업 시작

1. 이전 TASK가 종료되었고 관련 `shared/` 문서가 Git commit으로 보존됐는지 확인한다.
2. 보존되지 않았다면 사용자에게 local checkpoint를 제안하고, 승인 없이 commit하지 않는다.
3. 작업 목표와 완료 기준을 확인한다.
4. `TASK-YYYY-MM-DD-NNN` 형식으로 중복되지 않는 TASK-ID를 정한다.
5. `shared/README.md`의 초기화 기준에 따라 shared 작업 문서를 새 TASK로 전환한다.
6. `shared/TASK.md`에 목표, 범위, 비범위, 완료 기준과 MODE(`RELAY`, `PIPELINE`, `PARALLEL`)를 작성한다.
7. 이어지는 사용자 결정이 있으면 `shared/DECISIONS.md`에 기록한다.
8. 담당 AI가 역할 문서와 관련 shared 문서를 읽고 작업을 시작한다.

## 2. 작업 방식 선택

하네스의 공식 MODE는 다음 세 개다.

- `RELAY`: 다른 AI가 현재 역할과 미완료 작업을 이어받는다.
- `PIPELINE`: Claude, Codex, Gemini가 기본 전문 역할을 순서대로 수행한다.
- `PARALLEL`: 여러 AI가 독립 worktree에서 같은 목표의 대안을 만들고 비교한다.

일반적인 새 개발 작업의 기본 MODE는 `PIPELINE`이다. 사용자가 지정한 MODE가 우선하며 현재 MODE는
`shared/TASK.md`에서 확인한다. MODE가 없고 기존 작업 인계 또는 병렬 비교 여부가 불분명하면 사용자에게
확인한다.

## 3. MODE 1 — RELAY

기본 인계 순서는 다음과 같다.

```text
Codex → Claude → Gemini
```

각 AI는 `shared/context.md`, checkpoint, 실제 diff와 Git 상태를 기준으로 같은 TASK의 미완료 지점부터 계속한다. 인계는
Codex 구현 완료, Claude 설계 완료, Gemini 검수 시작 같은 역할 단계 전환을 뜻하지 않는다.
이어받은 AI가 실제 변경에 참여하면 그 결과의 독립 검수자로 간주하지 않는다.

넘기는 AI는 다음을 남긴다.

- 현재 branch/worktree, 기준 commit과 미커밋 변경
- 이전 작업자·모델과 현재 역할
- 완료한 범위와 판단 근거
- 현재 작업 중인 내용, 변경 파일과 실제 실행·테스트 결과
- 아직 끝나지 않은 항목과 다음 확인 파일

checkpoint commit은 유용하지만 사용자 승인 없이 만들지 않는다. Gemini 다음 담당이 필요하면
사용자가 지정한다.

## 4. MODE 2 — PIPELINE

PIPELINE은 기본 운영 모드다.

```text
사용자 요청
→ Claude → DESIGN
→ Codex → IMPLEMENTATION·실행·테스트
→ 사용자 승인에 따른 local checkpoint commit
→ Gemini → REVIEW
→ 사용자 → RESULT
```

각 담당은 이전 단계의 설명만 믿지 않고 실제 문서와 파일을 확인한다. 단순한 작업에서는 모든 역할을
거칠 필요가 없으며, 사용자가 역할 생략·단일 AI 작업·역할 변경을 지정하면 그 지시를 따른다.

## 5. MODE 3 — PARALLEL

Orca에서는 각 AI가 별도 branch/worktree에서 독립적으로 작업할 수 있다.

```text
master
├─ Claude worktree
├─ Codex worktree
└─ Gemini worktree
```

각 worktree의 미커밋 변경은 다른 worktree에서 자동으로 보이지 않는다. 병렬 TASK를 시작할 때
공통 기준 commit, 작업선별 branch/worktree, 비교 담당, 비교 기록 위치와 통합 기준 branch를 정한다.
각 AI는 같은 완료 기준을 사용하되 다른 결과를 복사하지 않고 자신의 결과와 검증 근거를 만든다.
비교할 변경은 식별 가능한 branch와 local checkpoint commit으로 남긴다.

독립 작업 뒤에는 다음 순서로 조율한다.

1. 비교 담당이 결과별 변경 파일, 동작, 테스트 결과와 미해결 문제를 직접 확인해 기록한다.
2. 공통점, 차이, 장단점, 충돌과 회귀 위험을 정리한다.
3. 중복 변경을 제거하고 함께 사용할 수 있는 부분과 양립할 수 없는 부분을 구분한다.
4. 중요한 선택은 사용자가 결정한다.
5. 사용자 승인으로 선택된 결과만 merge, cherry-pick 또는 수동 통합하고 통합 결과를 다시 검증한다.

여러 결과를 모두 합치는 것이 목표가 아니다. 요구사항을 가장 잘 충족하는 최종안을 근거에 따라
선택·합산하는 것이 목표다.

PARALLEL은 대안 비교가 실제로 가치 있는 범위에만 사용하며 세 AI 모두가 항상 완전한 구현을 만들
필요는 없다.

## 6. local checkpoint commit

AI 간 인계 전에는 가능하면 검증 가능한 변경과 관련 문서를 local checkpoint commit으로 고정하고,
인계 문서에 검수 대상 branch와 commit hash를 기록한다. 토큰 한계가 임박했거나 commit 승인을 받지
못했다면 미커밋 변경 상태와 확인 명령을 `shared/context.md`에 정확히 남기고 인계할 수 있다.
커밋 실행과 범위는 `AGENTS.md`의 승인 정책을 따르며, 사용자 지시 없이 임의로 commit하지 않는다.

```text
local checkpoint commit = AI 간 검수용 로컬 스냅샷
push                   = remote 저장소 반영
merge                  = 기준 branch 또는 master 반영
```

local commit은 push나 master merge가 아니다. push와 merge는 `AGENTS.md`에 따라
사용자 승인 없이 수행하지 않는다.

## 7. 다른 worktree 결과 검수

검수 AI는 작업 branch로 checkout하지 않고 현재 자기 worktree를 유지한다.
`git log`, `git show`, `git diff`로 대상 commit과 branch를 조사한다.

작업 branch가 현재 master보다 오래된 기준에서 갈라졌다면 merge-base 기준으로
그 AI가 실제로 만든 변경을 구분한다.

```bash
git merge-base master <work-branch>
git diff master...<work-branch>
```

현재 master와 다르다는 사실만으로 작업 AI가 파일을 삭제하거나 변경했다고 단정하지 않는다.
즉, `현재 master와 다름`은 `작업 AI가 해당 내용을 삭제/변경함`과 같지 않다.
검수 문서에는 기준 branch, 대상 branch, 대상 commit, merge-base commit과 실제 diff 명령을 남긴다.
finding의 사실관계가 나중에 잘못된 것으로 확인되면 원 기록을 숨기지 않고 정정 항목을 추가한다.

## 8. 사용자 의사결정

일반적인 내부 구현 세부는 담당 AI가 요구사항과 정책 안에서 판단한다.
다음처럼 결과 방향을 바꾸는 중요한 판단은 `shared/DECISIONS.md`에 기록하고 사용자 결정을 기다린다.

- 기존 기능 삭제 또는 동작 변경
- API 또는 외부 인터페이스 변경
- 중요한 데이터 구조 변경
- 시스템 구조 방향 변경
- `ENGINEERING_POLICY.md` 정책 간 충돌
- AI 간 중요한 의견 충돌
- 요구 범위 확대
- 여러 대안에 따라 결과 자체가 달라지는 경우

## 9. 작업 종료

구현에 참여하지 않은 Gemini 또는 다른 독립 검수 AI가 `shared/REVIEW.md`를 작성하면
사용자가 최종 판단한다. `shared/RESULT.md`에는 `채택`, `수정 후 채택`, `폐기`,
`보류` 중 하나와 판단 근거, 최종 branch·commit, merge 및 push 여부를 기록한다.

작업 종료 후 다음 TASK를 시작하기 전에 `AGENTS.md`의 보존 규칙에 따라 shared 문서
상태를 정리하고, 새 TASK-ID와 `shared/TASK.md`로 다음 작업 주기를 시작한다.
하네스 정책·역할·문서 구조가 의미 있게 바뀌었다면 개별 TASK 결과와 구분하여
루트 `CHANGELOG.md`에도 한 항목을 추가한다.
