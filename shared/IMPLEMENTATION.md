# 구현 기록

Codex의 구현 및 자체 검증 기록이다. 최종 승인서는 아니다.

## 구현 내용

- `demo/config_cli.py`는 JSON 설정 파일을 표준 라이브러리 `json`으로 읽고, 하나의 key 인자를 받아 값을 출력한다.
- 설정값은 `demo/config.json`에 분리했으며, 현재 `robot_name` 값은 `litbot`이다.
- 인자 누락, 설정 파일 읽기 또는 JSON 파싱 실패, JSON 최상위 값이 객체가 아닌 경우, 없는 key를 명확한 오류와 비영(0) 종료 코드로 처리한다.
- YAML은 표준 라이브러리에 파서가 없으므로 요구사항에서 허용한 JSON 형식을 선택했다. 외부 라이브러리는 추가하지 않았다.

## 변경 파일

- `demo/config_cli.py`: JSON 설정 조회 CLI를 추가했다.
- `demo/config.json`: 코드에서 분리된 데모 설정값을 추가했다.
- `shared/IMPLEMENTATION.md`: 구현 및 자체 검증 결과를 기록했다.
- `shared/context.md`: Gemini 검수용 인계 상태를 갱신했다.

## 실행 및 테스트

다음 명령을 직접 실행했다.

```sh
python3 -m py_compile demo/config_cli.py
python3 demo/config_cli.py robot_name
python3 demo/config_cli.py unknown_key
python3 demo/config_cli.py
mv demo/config.json demo/config.json.testing-backup
python3 demo/config_cli.py robot_name
mv demo/config.json.testing-backup demo/config.json
python3 demo/config_cli.py robot_name
```

실제 결과:

- 컴파일 검사: 종료 코드 0.
- 존재하는 key: `litbot`, 종료 코드 0.
- 없는 key: `ERROR: key 'unknown_key' not found`, 종료 코드 1.
- 인자 없음: `ERROR: provide exactly one key`, 종료 코드 2.
- 설정 파일을 일시적으로 없앤 경우: `ERROR: could not read configuration: [Errno 2] No such file or directory: '.../demo/config.json'`, 종료 코드 1.
- 설정 파일을 복원한 뒤 재조회: `litbot`, 종료 코드 0.

## 설계와의 차이

- Claude 설계 문서는 이번 데모에 대해 작성되지 않았다. 사용자 지시에 따라 Codex가 최소 설계 판단과 구현을 함께 수행했다.

## 검수 요청 사항

- Gemini는 실제 변경 파일과 위 명령을 독립적으로 확인하고, 요구사항에 없는 구조나 의존성이 추가되지 않았는지 검수한다.
- 설정 파일이 없거나 손상됐을 때의 오류 메시지와 종료 코드가 사용 목적에 충분히 명확한지 확인한다.
