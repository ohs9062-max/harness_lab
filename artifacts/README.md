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

현재 작업 중인 판단·진행 상태는 shared/, TASK 종료 기록은 shared/RESULT.md에 둔다.
