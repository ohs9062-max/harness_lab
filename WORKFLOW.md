# Harness Lab 운영 가이드

## 작성 정보

- 작성자: Codex
- 모델: GPT-5
- 역할: 문서 구조 개선
- 작성일: 2026-08-10
- TASK-ID: 미지정

이 문서는 사용자가 Orca, Git, Markdown 기반 하네스를 실제로 운영하는 순서를 설명한다.
AI 협업·권한·Git 안전 규칙은 `AGENTS.md`, 코드 원칙은 `ENGINEERING_POLICY.md`를 따른다.

## 1. 작업 시작

1. 작업 목표와 완료 기준을 확인한다.
2. `TASK-YYYY-MM-DD-NNN` 형식으로 TASK-ID를 정한다.
3. `shared/TASK.md`에 목표, 범위, 완료 기준을 작성한다.
4. 이어지는 사용자 결정이 있으면 `shared/DECISIONS.md`를 확인한다.
5. 담당 AI가 역할 문서와 관련 shared 문서를 읽고 작업을 시작한다.

## 2. 기본 순차 릴레이

기본 역할은 Claude(요구사항 분석·설계), Codex(구현·실행·테스트),
Gemini(독립 검수), 사용자(최종 판단)다.

```text
사용자 요청
→ Claude → shared/DESIGN.md
→ Codex → shared/IMPLEMENTATION.md
→ local checkpoint commit
→ Gemini → shared/REVIEW.md
→ 사용자 → shared/RESULT.md
```

Claude를 사용할 수 없거나 사용자가 단일 AI 작업을 명시한 경우에는
`AGENTS.md`의 역할 변경 및 단독 작업 예외를 따른다.

## 3. 병렬 작업과 worktree

Orca에서는 각 AI가 별도 branch/worktree에서 독립적으로 작업할 수 있다.

```text
master
├─ Claude worktree
├─ Codex worktree
└─ Gemini worktree
```

각 worktree의 미커밋 변경은 다른 worktree에서 자동으로 보이지 않는다.
검수할 변경은 식별 가능한 branch와 local checkpoint commit으로 남긴다.

## 4. local checkpoint commit

AI 간 인계 전에는 검수 가능한 변경과 관련 문서를 local checkpoint commit으로 고정하고,
인계 문서에 검수 대상 branch와 commit hash를 기록한다.
커밋 실행과 범위는 `AGENTS.md`의 승인 정책을 따르며, 사용자 지시 없이 임의로 commit하지 않는다.

```text
local checkpoint commit = AI 간 검수용 로컬 스냅샷
push                   = remote 저장소 반영
merge                  = 기준 branch 또는 master 반영
```

local commit은 push나 master merge가 아니다. push와 merge는 `AGENTS.md`에 따라
사용자 승인 없이 수행하지 않는다.

## 5. 다른 worktree 결과 검수

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

## 6. 사용자 의사결정

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

## 7. 작업 종료

Gemini 또는 구현에 참여하지 않은 독립 검수 AI가 `shared/REVIEW.md`를 작성하면
사용자가 최종 판단한다. `shared/RESULT.md`에는 `채택`, `수정 후 채택`, `폐기`,
`보류` 중 하나와 판단 근거, 최종 branch·commit, merge 및 push 여부를 기록한다.

작업 종료 후 다음 TASK를 시작하기 전에 `AGENTS.md`의 보존 규칙에 따라 shared 문서
상태를 정리하고, 새 TASK-ID와 `shared/TASK.md`로 다음 작업 주기를 시작한다.
