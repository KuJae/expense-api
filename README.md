# 지출 관리 API (expense-api)

**배포 URL:** _Render 배포 후 기입_ · Swagger UI: `<배포 URL>/docs`

클라우드컴퓨팅실습 3주차 실습 기록입니다.
가계부(지출 관리) CRUD API를 FastAPI로 처음부터 만들어 Render에 배포했습니다.
데이터는 임시 저장소(파이썬 리스트)에 두며, 진짜 DB 연결은 4주차에 합니다.

## 엔드포인트

| 메서드 | 경로 | 하는 일 | 성공 코드 |
| --- | --- | --- | --- |
| GET | `/` | 환영 메시지 | 200 |
| GET | `/health` | 서버가 살아 있는지 확인 | 200 |
| GET | `/transactions` | 거래 목록 (`skip`·`limit`으로 페이지네이션) | 200 |
| POST | `/transactions` | 거래 등록 | 201 |
| GET | `/transactions/{id}` | 거래 단건 조회 (없으면 404) | 200 |
| DELETE | `/transactions/{id}` | 거래 삭제 (없으면 404) | 204 |

API 명세는 따로 쓰지 않았습니다 — FastAPI가 `/openapi.json`으로 자동 생성합니다.

**요청 본문(`TransactionCreate`) 규칙**

| 필드 | 타입 | 규칙 |
| --- | --- | --- |
| `amount` | float | 0보다 커야 함 |
| `type` | enum | `income` 또는 `expense` |
| `category` | str | 1~50자 |
| `description` | str \| None | 200자 이하, 생략 가능 |
| `occurred_on` | date | `2026-09-15` 형식 |

## 프로젝트 구조

```text
expense-api/
├── app/
│   ├── __init__.py            # 패키지 표시
│   ├── main.py                # 앱 생성 + 라우터 조립
│   ├── models.py              # Pydantic 스키마
│   └── routers/
│       ├── __init__.py
│       └── transactions.py    # 거래 경로 + 임시 저장소
├── requirements.txt           # Render가 설치할 패키지
├── render.yaml                # Render 배포 설정
└── .gitignore
```

## 로컬에서 실행하기

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
fastapi dev app/main.py          # http://127.0.0.1:8000/docs
```

프로젝트 루트(`expense-api`)에서 실행해야 합니다. 다른 폴더에서 치면 `Path does not exist app/main.py`가 납니다.

---

# 실습 기록

## ① 결과 확인

`/docs`에서 등록 → 조회 → 삭제를 돌리고, 지운 id를 다시 조회하면 404가 나는 것을 확인했습니다.

![Swagger UI](docs/swagger-ui.png)

같은 흐름을 터미널에서도 확인한 기록입니다.

```console
$ curl -s http://127.0.0.1:8000/
{"message":"지출 관리 API에 오신 것을 환영합니다"}

$ curl -s http://127.0.0.1:8000/health
{"status":"ok"}

# 등록 — 201, 서버가 id 와 created_at 을 채워 준다
$ curl -i -X POST http://127.0.0.1:8000/transactions \
    -H 'Content-Type: application/json' \
    -d '{"amount":12000,"type":"expense","category":"식비","description":"점심","occurred_on":"2026-09-15"}'
HTTP/1.1 201 Created
{"id":1,"amount":12000.0,"type":"expense","category":"식비","description":"점심",
 "occurred_on":"2026-09-15","created_at":"2026-09-20T23:50:16.912397"}

# 단건 조회 — 200
$ curl -s http://127.0.0.1:8000/transactions/2
{"id":2,"amount":3200.0,"type":"expense","category":"교통","description":null,
 "occurred_on":"2026-09-16","created_at":"2026-09-20T23:50:16.920598"}

# 없는 id 조회 — 404
$ curl -i http://127.0.0.1:8000/transactions/999
HTTP/1.1 404 Not Found
{"detail":"999번 거래를 찾을 수 없습니다"}

# 삭제 — 204 (본문 없음)
$ curl -i -X DELETE http://127.0.0.1:8000/transactions/2
HTTP/1.1 204 No Content

# 지운 id 를 다시 삭제 — 404
$ curl -i -X DELETE http://127.0.0.1:8000/transactions/2
HTTP/1.1 404 Not Found
{"detail":"2번 거래를 찾을 수 없습니다"}
```

**일부러 틀린 값을 보냈을 때 (422)** — 세 가지 위반을 한 번에 잡아냅니다.

```console
$ curl -i -X POST http://127.0.0.1:8000/transactions \
    -H 'Content-Type: application/json' \
    -d '{"amount":-1,"type":"unknown","category":"","occurred_on":"2026-09-15"}'
HTTP/1.1 422 Unprocessable Content
  amount   : Input should be greater than 0
  type     : Input should be 'income' or 'expense'
  category : String should have at least 1 character
```

경로 매개변수도 같습니다 — `GET /transactions/abc`는 `int`로 바꿀 수 없어 **422**입니다.
검증 코드를 한 줄도 쓰지 않았는데 막혔고, `create_transaction` 함수 본문은 실행조차 되지 않았습니다.

## ② 핵심 개념 되새김

- **CRUD 네 동작과 HTTP 메서드** — 만들기는 POST, 읽기는 GET, 고치기는 PUT/PATCH, 지우기는 DELETE다.
  "무엇을" 할지는 경로(`/transactions/3`)가, "어떻게" 할지는 메서드가 나눠 맡아서 같은 주소로도 다른 일을 시킬 수 있다.
- **Pydantic 검증이 막아 주는 것** — 잘못된 데이터가 내 함수에 **도착하기 전에** 걸러진다.
  `amount`에 음수, `type`에 오타, `category`에 빈 문자열을 넣으면 함수가 실행되기도 전에 422와 함께
  어디가 왜 틀렸는지 전부 돌려준다. 덕분에 함수 안에 "값이 있나 없나" 검사를 쓸 일이 없다.
- **`/docs`가 어디서 나오는가** — 내가 쓴 경로 선언(`@router.post("")`)과 타입 힌트, Pydantic 모델을
  FastAPI가 읽어 `/openapi.json`을 만들고, Swagger UI가 그 JSON을 그려 준 것이다.
  문서를 만드는 코드는 한 줄도 쓰지 않았고, 코드를 고치면 문서도 같이 바뀐다.

## ③ 자유 로그

<!-- 아래는 초안입니다. 본인 경험에 맞게 고쳐 쓰세요. -->

2주차에 메모 앱으로 CRUD를 맛만 봤는데, 이번 주에 같은 걸 제대로 짚으니 그때 넘어갔던 것들이
이제야 이어졌다. 특히 **모델을 요청용과 응답용으로 나누는 이유**가 와닿았다. 등록할 때는 `id`와
`created_at`이 없는 게 맞고(서버가 만드니까), 응답할 때는 있어야 한다 — 하나로 합쳤으면 "이건
넣어야 하나 말아야 하나"로 계속 헷갈렸을 것 같다.

가장 인상 깊었던 건 일부러 틀린 값을 보냈을 때였다. `amount: -1`, `type: "unknown"`,
`category: ""` 세 개를 한 번에 보냈는데 세 개 다 각각 이유를 붙여 돌려줬다. 내가 쓴 검증 코드는
`Field(gt=0)` 같은 선언 몇 줄뿐인데 그게 전부였다.

**단계 5의 파일 분리**가 처음엔 왜 필요한지 몰랐다. 잘 돌아가는 `main.py`를 굳이 쪼개는 게
번거로워 보였는데, 옮기고 나니 "데이터 모양은 `models.py`, 경로는 `routers/`"로 눈이 가는 자리가
정해져서 오히려 찾기 쉬워졌다. 대신 옮길 때 `@app.` 을 `@router.` 로 바꾸는 걸 놓치기 쉬워 보여서
옮긴 뒤에 파일을 한 번 훑으며 확인했다.

아직 안 풀린 것: 데이터가 서버를 끄면 사라진다. 워크북 심화 블록에 SQLite로 바꾸는 방법이 있는데
4주차가 정식이라고 해서 이번엔 넘겼다. 그리고 Render 무료 플랜이 15분마다 잠드는 것도, 지금은
"정상"이라고 하니 넘어가지만 실제 서비스라면 어떻게 하는지는 아직 모르겠다.

**AI 사용 기록** — Claude Code(Claude Opus 5)에게 워크북 단계 1~6을 그대로 따라 프로젝트를
만들게 했다. 검증은 AI 말을 믿지 않고 직접 돌려서 했다: 로컬 서버를 띄워 `/`·`/health`·`/docs`가
뜨는지, 등록이 201로 `id`를 돌려주는지, 없는 id가 404인지, `abc`가 422인지, 삭제가 204이고 같은 걸
다시 지우면 404인지를 하나씩 호출해 응답 코드와 본문을 눈으로 확인했다(위 ① 기록이 그 결과다).
일부러 틀린 값 세 개를 한 번에 보내 422 메시지가 세 건 다 나오는지도 확인했다.
`main.py`에 `@app.` 으로 시작하는 줄이 몇 개인지 세어 워크북 완성본과 대조하는 것도 해 봤다.
