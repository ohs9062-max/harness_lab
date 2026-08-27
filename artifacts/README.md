# artifacts

artifacts/는 현재 TASK의 과정 문서가 아니라, 검증·채택되어 후속 TASK에서 입력으로 재사용할
완성된 최종 결과물을 보관한다.

예시 구조:

- artifacts/<TASK-ID>/<의미 있는 결과물 이름>

파일 이름은 TASK 성격에 맞게 자유롭게 정한다. 예: naver_blog_strategy.md,
api_architecture.md, requirements_spec.md, research_summary.md.

artifact에는 가능하면 TASK-ID, 생성 근거, 검증 상태, 실제 주요 내용, 제외된 위험 요소와 후속 TASK가
사용할 입력 정보를 포함한다. 단순 메타데이터 문서가 아니라 다음 TASK가 바로 읽고 작업할 수 있는
결과물이어야 한다. 후속 TASK는 해당 경로를 shared/TASK.md의 INPUT-ARTIFACT에 기록한다.

간결한 provenance 메타데이터에는 가능하면 다음을 포함한다.

- TASK-ID, 생성일, 정보 기준일
- 상태: DRAFT / REVIEWED / USER_ACCEPTED
- 작성·종합 AI와 독립 검수 AI 또는 session
- 입력 artifact
- 근거 문서와 branch/commit
- Known Limitations

Research/Strategy artifact는 시간에 따라 바뀌는 알고리즘·API·제품 정책의 최신성을 판단할 수 있도록
가능하면 `정보 기준일: YYYY-MM-DD`를 기록한다. 메타데이터가 본문보다 커지지 않게 하고 실제로
후속 TASK가 사용할 완성된 내용이 artifact의 중심이어야 한다.

현재 작업 중인 판단·진행 상태는 shared/, TASK 종료 기록은 shared/RESULT.md에 둔다.
