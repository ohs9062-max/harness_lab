# JSON 설정 조회 CLI 데모

하네스의 설계·구현·독립 검수·사용자 판단 릴레이를 시험하기 위한 작은 Python 데모다.
외부 라이브러리 없이 Python 표준 라이브러리만 사용한다.

## 실행

`config.json`의 key 하나를 전달한다.

```bash
python3 demo/config_cli.py robot_name
```

정상 출력:

```text
litbot
```

## 오류와 종료 코드

- 정상 조회: 0
- 없는 key, 설정 파일·JSON 오류, 최상위 형식 오류: 1
- 인자가 정확히 하나가 아님: 2

간단한 확인:

```bash
python3 -m py_compile demo/config_cli.py
python3 demo/config_cli.py robot_name
python3 demo/config_cli.py unknown_key
python3 demo/config_cli.py
```
