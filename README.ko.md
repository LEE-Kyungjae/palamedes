# Palamedes

<p align="center">
  <a href="README.md">English</a> · <strong>한국어</strong>
</p>

<p align="center">
  <img src="assets/palamedes.png" alt="Palamedes" width="100%">
</p>

> **Palamedes는 실행 에이전트가 구현 방법을 계획하기 전에, 어떤 미션이
> 계획할 가치가 있는지를 판단합니다.**

Palamedes는 `planner → task → implementation` 앞에서 작동하는 연구 알파
단계의 자율 프리플래너이자 계획 상태 커널입니다. 중요한 신호를 발견하고,
서로 경쟁하는 해석과 미션을 만들고, 반증을 시도한 뒤 살아남은 미션만
하위 실행 에이전트에 전달합니다.

계획을 일회성 문서가 아닌 수정 가능한 상태로 다룹니다. 목표, 근거, 가설,
복원 지점뿐 아니라 관점이 왜 바뀌었는지, 무엇이 새롭게 보였는지, 새 관점이
무엇을 가릴 수 있는지, 다음에 어떤 탐색을 해야 하는지도 기록합니다.

Palamedes의 출발점은 다음 질문입니다.

> 확률적으로 평균적인 답을 향하는 언어 모델에서 창의성과 독창성은 어떻게
> 나올 수 있는가?

현재의 답은 한 번의 천재적인 생성이 아닙니다. 외부 증거와 충돌하고, 여러
해석이 경쟁하고, 기존 관점이 반증되면서 누적되는 작은 시야 변화가 새로운
선택지를 보이게 할 수 있다는 것입니다. 검색, RAG, 토론, 다중 에이전트는
텍스트를 늘릴 때가 아니라 실제 결정을 바꾸거나 압박할 때 의미가 있습니다.

Palamedes는 독창성이나 창업 성공을 보장하지 않습니다. 실행 이전 판단을
자동화할 수 있다는 가설을 세우고, 그 권한을 성과로 증명하려는 시스템입니다.
상세한 영어 명세는 [README.md](README.md), 현재 연구 질문과 반론은
[PALAMEDES_INQUIRY.md](PALAMEDES_INQUIRY.md)에 있습니다.

## 현재 상태

**Research Alpha.** 계획 상태 커널은 구현되어 있고, 자율 프리플래너는
검증 중인 제품 가설입니다.

| 증거 수준 | 현재 결과 |
| --- | --- |
| 안정적인 계획 상태 커널 | 수정, 복원, 충돌 처리, QA, 호환성 검증 구현 |
| 제한된 프리플래너 계약 | 미션 및 실험 스키마와 테스트 구현 |
| 내부 사고 개발 | 의존적인 추론 사이클 401개 기록 |
| 실제 레퍼런스 접촉 | 근거 1,624건, 구성요소 837개 색인 |
| 부적절한 검색 결과 차단 | 첫 처리 패킷을 9개 이유로 차단 |
| 동일 정보 기준선 대 비교군 | `proof-002`: 블라인드 모델 평가 9표 중 8표, 3개 사례 다수결 모두 팔라메데스 승리 |
| 생성 비용 | 팔라메데스가 기준선 입력 토큰의 4.26배 사용; 비용 보정 우위는 미증명 |
| 외부 의사결정 및 성과 개선 | 아직 증명하지 못함 |

첫 교차 저장소 실험은 `insight-rag`를 대상으로 합니다. 첫 검색 처리 결과가
실제 과제와 무관하자 Palamedes는 이를 권위 있는 근거로 포장하지 않고
차단했습니다. 이는 안전 프로토콜이 나쁜 입력을 거부할 수 있다는 증거이지,
Palamedes가 더 좋은 결정을 내린다는 증거는 아닙니다.

실행 가능한 3개 프로젝트 증명 프로그램은
[`experiments/PROOF.md`](experiments/PROOF.md)에 있습니다. 모델 생성 전에
동일 정보 패킷을 동결하고, one-shot 기준선과 Palamedes 4역할 조건을 분리하며,
평가 때 출처를 숨기고 호출·토큰 차이를 공개합니다. 블라인드 미션 선호만으로는
제품 주장을 통과시키지 않으며, 실제 downstream 선택과 사람의 upstream 노동
감소 기록이 함께 있어야 합니다.

첫 사전등록 비교인 [`proof-002`](experiments/proof-runs/proof-002/RESULT.md)에서
서로 상태를 공유하지 않는 Codex 블라인드 평가 세션 3개는 총 9표 중 8표를
Palamedes에 주었고, Palamedes는 세 사례 다수결을 모두 이겼습니다. 이는
독립적인 사람 검증이 아니라 모델 평가에 의한 초기 품질 증거입니다.
Palamedes는 기준선보다 입력 토큰을 4.26배 사용했으므로 비용 보정 우위와
실제 성과 개선은 아직 증명되지 않았습니다.

다음과 같은 상황에 적합합니다.

- 아이디어는 있지만 무엇부터 검증해야 하는지 모를 때
- AI로 빠르게 만들고 있지만 방향이 계속 흔들릴 때
- 하나의 방향을 선택하고 약한 방향을 버릴 명확한 이유가 필요할 때
- 근거, 실패 조건, 재계획 이력을 한곳에 남기고 싶을 때

## 제품 경계

Palamedes가 담당해야 하는 영역:

- 신호 해석과 아이디어 발견
- 경쟁하는 관점과 후보 미션 생성
- 비판, 반증, 방향 선택
- 미션 계약, 비목표, 계획 논리
- 성공·실패 기준
- 근거 기반 재계획과 복원

Palamedes가 담당하지 않는 영역:

- 작업 실행과 배포 자동화
- 범용 에이전트 런타임
- 워크플로 스케줄링
- 승인 없는 파일 변경
- 관찰하지 않은 성과의 주장

권한은 미션 경계에서 끝납니다.

```text
Palamedes
  미션 / 근거 / 가설 / 반증 조건 / 비목표
      ↓
외부 planner 또는 agent runtime
  계획 / 작업 / 도구 / 구현
      ↓
관찰된 결과를 Palamedes에 반환
```

## 구조

```text
palamedes/
├── palamedes.py                    # 계획 커널과 CLI
├── palamedes_chat.py               # AI 터미널과 인지 사이클
├── palamedes_observe.py            # 제한·마스킹된 작업공간 관찰
├── palamedes_watch.py              # 이벤트 기반 자율 관찰 루프
├── palamedes_mission.py            # 프리플래너 계약과 게이트
├── palamedes_server.py             # 로컬 HTTP 전송 계층
├── palamedes_sdk/                  # Python 클라이언트
├── schemas/experimental/           # 실험 계약
├── experiments/                    # 사전 등록된 평가
├── docs/inquiry/reasoning-cycles/  # 추론 계보
└── tests/contracts/                # 호환성 픽스처
```

```text
세계 신호와 누적 레퍼런스
  → 경쟁하는 해석
  → 후보 미션
  → 근거, 비판, 반증
  → 선택된 미션 계약과 비목표
  → planner → task → implementation
  → 관찰된 결과를 Palamedes에 환류
```

## 빠른 시작

로컬 CLI를 설치합니다.

```bash
python3 -m pip install -e .
```

### Codex 구독 인증 사용

이미 인증된 Codex CLI를 Palamedes의 추론 엔진으로 사용할 수 있습니다.

```bash
codex login

palamedes chat \
  --provider codex \
  --workspace /path/to/project
```

Codex provider는 프로젝트를 직접 탐색하는 실행 에이전트로 사용되지 않습니다.
각 호출은 격리된 임시 디렉터리에서 `read-only`, `ephemeral` 모드로 실행되고,
Palamedes가 만든 제한된 observation만 전달받습니다.

### OpenRouter 사용

```bash
export OPENROUTER_API_KEY="<new-key>"

palamedes chat \
  --provider openrouter \
  --model <provider/model> \
  --workspace /path/to/project
```

### OpenAI Responses API 사용

```bash
export OPENAI_API_KEY="<new-key>"

palamedes chat \
  --provider openai \
  --model gpt-5.6 \
  --workspace /path/to/project
```

API 키는 환경 변수에서만 읽고 세션 상태에 저장하지 않습니다.

## 대화형 AI 터미널

```text
palamedes> /observe
palamedes> /think 우리가 놓친 가장 중요한 질문은 무엇인가?
palamedes> /challenge 현재 제품 방향
palamedes> /research 결정 전에 어떤 근거가 더 필요한가?
palamedes> /mission 계획할 가치가 있는 최강의 미션을 만들어라
palamedes> /cycle 독립적인 인지 압력으로 미션을 찾아라
palamedes> /preview
palamedes> /approve
palamedes> /handoff
palamedes> /outcome success 사전 약속한 결과가 관찰되었다
```

주요 명령:

- `/observe`: 프로젝트, Git, TODO, 계획 상태, 중앙 ref 신호 관찰
- `/think`: 지금 빠진 사고 방식을 선택해 수행
- `/challenge`: 가정과 반증 조건 공격
- `/research`: 커밋 전에 필요한 최소 외부 근거 식별
- `/mission`: 계획을 변경하지 않고 구조화된 미션 초안 생성
- `/cycle`: interpreter, inventor, adversary, selector 독립 호출
- `/preview`: 최신 미션 초안 검토
- `/approve`: 승인된 초안을 계획, 근거, 가설, probe로 투영
- `/reject`: 이유와 함께 초안 거부
- `/handoff`: planner용 불변 미션 계약 확인
- `/outcome`: 관찰된 결과를 추가하고 연결 상태 갱신

세션은 프로젝트의 `.palamedes/chat/` 아래 JSONL로 저장됩니다.

## 작업공간 관찰

AI를 호출하지 않고 프로젝트를 관찰합니다.

```bash
palamedes observe --workspace /path/to/project
```

명시한 테스트만 관찰에 포함할 수 있습니다.

```bash
palamedes observe \
  --workspace /path/to/project \
  --test-command "python3 -m unittest" \
  --test-timeout 300
```

관찰 대상:

- README, AGENTS, 빌드 매니페스트, 일부 최상위 문서의 제한된 발췌와 해시
- Git HEAD, 브랜치, 작업 트리, diff 통계, 최근 커밋
- 출처 파일과 줄 번호를 포함한 TODO/FIXME/HACK
- 계획 지문, 근거 수, 열린 가설, 예정된 probe
- 중앙 ref 저장소 경로, revision, symlink, dirty 상태
- 명시적으로 실행한 테스트의 종료 코드와 제한된 출력
- 이전 observation과 달라진 신호

일반적인 자격 증명 파일은 제외하고 API 키, 토큰, 비밀번호, 개인 키 패턴을
마스킹합니다. 파일 수와 바이트 수가 제한되며, 사용자가 지정하지 않은 테스트는
실행하지 않습니다.

## 제한된 자율 watch

모델 호출 없이 한 번 판단합니다.

```bash
palamedes watch --workspace /path/to/project --once
```

Codex를 연결한 저비용 자율 루프:

```bash
palamedes watch \
  --workspace /path/to/project \
  --interval 300 \
  --auto-cognition \
  --provider codex \
  --max-calls-per-wake 2 \
  --max-calls-per-day 10 \
  --max-calls-total 20
```

| 관찰된 신호 | 선택되는 사고 |
| --- | --- |
| 변화 없음, 중복 신호, 최초 baseline | 대기 |
| 주요 문서 변경 | interpreter 1회 |
| 중앙 ref revision 변경 | interpreter + inventor |
| 계획 변경 | adversary + selector |
| 구현 변경 | interpreter + adversary |
| 명시적 테스트 실패 | interpreter + adversary |
| 미션 결과 추가 | outcome analyst |
| 독립 신호 세 종류 이상 변경 | 전체 4역할 사이클 |

기본값은 5분 간격, wake당 2회, UTC 기준 하루 10회, 누적 20회입니다.
전체 사이클에는 4회 호출이 필요하므로 기본 설정에서는 자동 차단됩니다.
명시적으로 허용하려면 `--max-calls-per-wake 4`를 사용합니다.

동일한 신호는 반복 호출하지 않습니다. 시도된 호출은 실패하더라도 예산에
반영됩니다. Codex JSONL이 보고한 입력, 캐시 입력, 출력, 추론 토큰도
`.palamedes/watch/` 상태에 기록됩니다.

```text
.palamedes/watch/
├── state.json    # 현재 cursor와 누적 예산
├── events.jsonl  # append-only wake 이벤트
└── wakes/        # 각 판단과 인지 산출물
```

watcher는 미션을 계획에 승인하거나 구현 작업을 실행하지 않습니다. 전체
사이클이 성공해도 검토 가능한 미션 초안까지만 저장합니다.

## 미션 권한 흐름

```text
/mission
  → 스키마 검증된 초안
  → /preview
  → /approve
  → 계획 + 근거 + 가설 + probe
  → planner handoff (실행 권한은 여전히 false)
  → /outcome
  → append-only 결과 + 연결 상태 갱신
```

```text
interpreter
  관찰과 경쟁 관점
      ↓ 동결된 산출물
inventor
  경쟁 미션 생성, 선택 권한 없음
      ↓ 동결된 산출물
adversary
  후보 공격과 공통 가정 압박, 선택 권한 없음
      ↓ 동결된 산출물
selector
  동결된 후보만 선택 / 보류 / 거부
      ↓
스키마 검증된 미션 초안

실제 /outcome
      ↓
outcome analyst
  예상 대 관찰 + 원인 분리 + 믿음 갱신
```

## 핵심 계획 CLI

```bash
palamedes init

palamedes plan \
  --goal "증거로 검증 가능한 방향을 선택한다" \
  --success-metric "4주 안에 사전 정의한 지표를 충족한다" \
  --planning-horizon "4 weeks" \
  --review-cadence "weekly"

palamedes evidence \
  --claim "사용자 인터뷰에서 문제가 반복 확인됐다" \
  --source "interviews" \
  --confidence 72 \
  --axis market

palamedes hypothesis \
  --statement "이 문제가 구매 결정에 영향을 준다" \
  --confidence 55

palamedes show
palamedes qa
palamedes history
```

주요 명령:

- `plan`, `replan`: 현재 계획 생성 및 근거 기반 수정
- `evidence`, `hypothesis`: 근거와 가설 기록
- `view`, `inquiry`, `encounter`: 관점 변화와 레퍼런스 영향 기록
- `probe`: 결과가 아니라 예상 학습을 가진 개발 단계 기록
- `qa`, `validate`, `health`: 상태 품질과 저장소 상태 검사
- `history`, `restore`: revision 확인과 복원
- `observe`, `watch`: 제한된 관찰과 예산 기반 자율 사고

전체 옵션은 다음으로 확인합니다.

```bash
palamedes --help
palamedes <command> --help
```

## HTTP API

```bash
python3 palamedes_server.py --host 127.0.0.1 --port 8787
```

주요 엔드포인트:

- `GET /plan`, `/qa`, `/health`, `/cycle`, `/history`, `/validate`, `/tools`
- `POST /plan`, `/evidence`, `/replan`, `/restore/preview`, `/restore`
- `POST /tools/<tool_name>`
- `POST /agent/act`

안전한 쓰기는 계획 fingerprint를 사용해 오래된 상태의 덮어쓰기를
차단합니다.

## 개발 및 검증

```bash
make check
make test
make compile
make schema-check
```

설치 가능한 Python SDK와 에이전트 wrapper, 안정성 등급, 동시성·복원·재시도
계약, 전체 HTTP 예제, 실험 설계와 세부 명령은
[영어 전체 문서](README.md)를 참고하세요.

## 설계 원칙

1. 실행 전에 목적을 명확히 한다.
2. 가정과 사실을 분리한다.
3. 경쟁 관점을 보존한다.
4. 레퍼런스의 존재와 실제 영향력을 구분한다.
5. 계획 변경 이유와 관점 변화를 기록한다.
6. 개발을 정보 획득 과정으로 취급한다.
7. 불확실성이 큰 곳부터 검증한다.
8. 되돌릴 수 있는 결정을 선호한다.
9. 결과를 관찰하기 전에는 성공을 주장하지 않는다.
10. 더 많은 텍스트가 아니라 더 나은 결정을 평가한다.

## 라이선스와 기여

저장소의 라이선스와 기여 방식은 영어 상세 문서 및 프로젝트 파일을
따릅니다. 번역에서 의미 차이가 생기면 [README.md](README.md)의 영어
명세를 기준으로 합니다.
