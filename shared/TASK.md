# 현재 작업

## 작성 정보

- 작성자: Codex
- 모델: 미확인
- 역할: DEFINE Coordinator / Researcher
- 작성일: 2026-08-27
- TASK-ID: TASK-2026-08-27-004

## 작업 메타데이터

- TASK-ID: TASK-2026-08-27-004
- USER-REQUEST: 네이버 블로그 상위노출 전략을 조사하고, 검증된 최종 전략 결과물을 만들어줘.
- TASK-TYPE: RESEARCH
- EXECUTION: PIPELINE
- RELAY: ALLOWED
- CURRENT-STAGE: FINAL
- INPUT-ARTIFACT: 없음
- OUTPUT-ARTIFACT: artifacts/TASK-2026-08-27-004/naver_blog_exposure_strategy.md

EXECUTION은 TASK의 대표 성격이다. 실제 Stage별 execution과 담당은 Stage Plan을 따른다.

## Stage Plan

### DEFINE
- execution: PIPELINE
- agent: Codex
- required: true
- status: DONE

### RESEARCH
- execution: PIPELINE
- agent: Codex
- required: true
- status: DONE

### VERIFY
- execution: PIPELINE
- agent: Codex
- required: true
- status: DONE

### SYNTHESIZE
- execution: PIPELINE
- agent: Codex
- required: true
- status: DONE

### REVIEW
- execution: PIPELINE
- agent: independent session
- required: true
- status: DONE

### FINAL
- execution: PIPELINE
- agent: User
- required: true
- status: PENDING

## 목표

- 네이버가 공개한 검색·블로그 정책을 근거로 재현 가능한 상위 노출 전략을 만든다.
- 순위 보장을 주장하지 않고, 검색 반영·관련도·콘텐츠 품질·정책 준수·측정의 실행 항목을 구분한다.
- 다음 TASK에서 콘텐츠 운영 계획의 입력으로 쓸 수 있는 artifact를 남긴다.

## 범위

- 네이버 블로그 글의 검색 반영 조건, 노출 순서에 관련된 공개 요인, 금지·제한 행위, 운영 및 측정 루틴
- 공식 네이버 고객센터/서치 문서 중심의 근거 조사와 검증

## 제약

- 특정 키워드의 상위 고정 또는 노출을 보장하지 않는다.
- 공개되지 않은 알고리즘 가중치나 비공개 요인을 사실처럼 단정하지 않는다.
- 스팸, 숨김 키워드, 기계적 대량 생산, 대가성 표기 누락을 권장하지 않는다.
- 독립 REVIEW는 작성에 참여하지 않은 AI 또는 fresh independent session이 수행한다.

## 완료 조건

- 주요 전략 주장이 공식 근거와 연결되고 확인 불가 사항이 구분된다.
- artifact가 실행 순서, 점검표, 측정 기준과 알려진 한계를 포함한다.
- required Stage가 모두 DONE 또는 사용자 승인에 따른 WAIVED가 되어야 FINAL로 진행한다.
