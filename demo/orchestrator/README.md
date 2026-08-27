# Harness Lab Orchestrator V1

Harness Lab의 다중 AI (Claude / Codex / Gemini) 실제 CLI를 자동 호출하여 협업 Stage를 실행하는 로컬 기반 최소 오케스트레이터입니다.

## 1. 아키텍처 및 흐름

```text
사용자 요청 (자연어 한 줄)
       │
       ▼
[Coordinator AI (Codex)] ──> Stage Plan JSON 계약 생성 및 유효성 검증
       │
       ▼
[Orchestrator Engine]
       │
       ├─▶ [RESEARCH Stage (PARALLEL)]
       │     ├─ Claude  (worktree: task/<TASK-ID>/claude) ──> shared/RESEARCH.md (CLAUDE-Cxxx)
       │     ├─ Codex   (worktree: task/<TASK-ID>/codex)  ──> shared/RESEARCH.md (CODEX-Cxxx)
       │     └─ Gemini  (worktree: task/<TASK-ID>/gemini) ──> shared/RESEARCH.md (GEMINI-Cxxx)
       │
       │   [Required Agent Gate: 3개 AI 성공 검증]
       │
       ├─▶ [COMPARE Stage (PIPELINE: Gemini)] ──> shared/COMPARE.md (N-Cxxx 정규화)
       ├─▶ [VERIFY Stage (PIPELINE: Codex)]   ──> Verified Set 확정
       ├─▶ [SYNTHESIZE Stage (PIPELINE: Claude)] ──> artifacts/<output_artifact> 초안 작성
       ├─▶ [REVIEW Stage (PIPELINE: Gemini)]  ──> shared/REVIEW.md (PASS / FIX_REQUIRED / BLOCKED)
       │     └─ FIX_REQUIRED 시 FIX Stage (Claude) ──> fresh REVIEW Loop (최대 2회)
       │
       ▼
[FINAL Stage (PIPELINE: User)] ──> 최종 산출물 완성 및 사용자 확인
```

## 2. 주요 모듈 구성

- `models.py`: TaskPlan, StageConfig, AgentExecutionResult, RuntimeState 데이터 모델
- `coordinator.py`: Coordinator AI (Codex) 기반 Stage Plan JSON 생성 및 엄격한 유효성 검증
- `prompt_builder.py`: Stage별/Agent별 구조화 프롬프트 생성기 (Namespace 규칙, Freshness Gate 포함)
- `worktree.py`: Git Worktree 격리 및 안전한 Local Checkpoint 생성기 (No push, No merge)
- `adapters/`: CLI 실행 어댑터
  - `codex.py`: `codex exec` 비대화형 어댑터
  - `claude.py`: `claude -p` 비대화형 어댑터
  - `gemini.py`: `gemini -p` 비대화형 어댑터
  - `fake.py`: 모의 테스트 및 단위 검증용 어댑터
- `engine.py`: Stage Plan 실행 엔진 (Parallel 실행, Gate 검사, Review & Fix Loop 관리)
- `state.py`: `.harness/runs/<TASK-ID>/state.json` 런타임 상태 및 마스킹된 로그 관리자
- `cli.py`: CLI 진입점 (`python -m demo.orchestrator`)

## 3. 사용법

### Dry-run (토큰 소비 없는 시뮬레이션)
```bash
python -m demo.orchestrator "네이버 블로그 상위노출 전략을 조사하고 검증된 최종 전략 결과물을 만들어줘." --dry-run
```

### 실제 실행 (Live AI CLI 호출)
```bash
python -m demo.orchestrator "네이버 블로그 상위노출 전략을 조사하고 검증된 최종 전략 결과물을 만들어줘." --execute
```

### 테스트 모드 (Fake Agent 기반 실행)
```bash
python -m demo.orchestrator "네이버 블로그 상위노출 전략 조사" --execute --fake-agents --deterministic-plan
```

### 테스트 러너 실행
```bash
python3 -m unittest discover -s demo/orchestrator/tests -p "test_*.py"
```
