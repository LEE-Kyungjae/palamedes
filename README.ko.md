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

**Research Beta.** 계획 상태 커널은 충분히 구현·검증됐고, 1:1 프리플래너는
실제 프로젝트에서 반복 사용됐으며, 두 번의 사전등록 비교에서 내부 프로토타입
이상의 초기 증거를 확보했습니다. 이것이 창업이나 실제 사업 성과 개선까지
증명했다는 뜻은 아닙니다.

| 증거 수준 | 현재 결과 |
| --- | --- |
| 안정적인 계획 상태 커널 | 수정, 복원, 충돌 처리, QA, 호환성 검증 구현 |
| 제한된 프리플래너 계약 | 미션 및 실험 스키마와 테스트 구현 |
| 미션 품질 증명 | `proof-002`, `proof-003`에서 one-shot 및 동일 호출 강한 대조군 대비 블라인드 초기 증거 확보 |
| 1:1 Codex 협업 | 실제 구현 사이클에서 검증 가능한 제품 개선이 반복됨; Codex 단독 대비 Palamedes의 인과적 추가 기여는 아직 미분리 |
| 로컬 1:N 팀 인지 | Alpha: 출처·오래된 상태 차단·경쟁 가설·미션 소유권·제한 문맥·블라인드 commit–reveal 구현 |
| 1:N 추가 우위 | 현재 작동하는 1:1 Codex+Palamedes 루프 대비 아직 미증명 |
| 분산 팀 운영 | 미구현; 현재 원장은 동일 호스트의 트랜잭션 파일 방식 |
| 내부 사고 개발 | 의존적인 추론 사이클 401개 기록 |
| 실제 레퍼런스 접촉 | 근거 1,624건, 구성요소 837개 색인 |
| 부적절한 검색 결과 차단 | 첫 처리 패킷을 9개 이유로 차단 |
| 동일 정보 기준선 대 비교군 | `proof-002`: 블라인드 모델 평가 9표 중 8표, 3개 사례 다수결 모두 팔라메데스 승리 |
| 생성 비용 | 팔라메데스가 기준선 입력 토큰의 4.26배 사용; 비용 보정 우위는 미증명 |
| 동일 호출 강한 대조군 | `proof-003`: 양쪽 12회 호출·입력 토큰 1.045배에서 9표 중 7표, 3개 중 2개 사례 승리 |
| 귀속 가능한 후속 선택 | 1건 기록: `proof-002` 임무에 따라 기능 확장 전에 `proof-003` 동일 호출 실험 수행 |
| 소유자 사고노동 감소 | 아직 소유자 확인 없음 |

outcome은 하나의 성공·중단 값으로 합치지 않고 다음 의미를 분리합니다.

```text
관측 결과
  -> probe 완료 여부
  -> finding(결함, null, 예상 결과, 불리한 결과, 불충분)
  -> 현재 미션 disposition
  -> 필요한 경우 후속 미션의 정확한 범위
```

따라서 probe가 성공적으로 완료되고 해당 감사 미션이 중단되더라도, 발견된
제품 결함에는 별도의 제한된 생산 후속 미션이 남을 수 있습니다. 무관한 미션은
그 결과를 명시적으로 인정한 뒤 진행할 수 있지만, 필요한 후속 gate를 조용히
닫지는 못합니다.

outcome analyst는 표면 문구와 분리된 `causal_signature`와
`mechanism_summary`도 기록합니다. 같은 서명이 두 번 반복되면 개별 상태를
계속 열거하지 않고 제한된 프롬프트 설계 사이클을 엽니다.

```text
반복 causal signature
  → prompt architect: 더 높은 추상화의 경쟁 탐사 프롬프트 생성
  → prompt adversary: TODO 재포장·자기확증·범위확장 공격
  → prompt selector: 의사결정을 바꿀 의제 최대 하나 선택
  → 다음 cognition cycle에 선택 의제 제공
```

생성 프롬프트는 연구 질문·관점·비교·역할 순서·중단 조건만 바꿀 수 있습니다.
권한·증거·개인정보·승인·예산·반증 헌법은 변경할 수 없고 실행 권한도 얻지
않습니다. 선택된 의제는
`.palamedes/missions/prompt-intelligence/prompt-agendas/`에 보존됩니다.

outcome 해석은 작업의 줌 레벨과 레인도 기록합니다. 같은 표면에서 `micro`
outcome이 5회 연속되면 다음 국소 최적화 전에 component 또는 product 수준의
fresh-eyes 의제를 강제합니다. 명시된 정확성 계약이 없다고 가능성을 바로
폐기하지도 않습니다. 유망하지만 미검증인 생각은 정확성 주장과 미션 권한이
없는 `design_hypothesis`로 숙성하고, 실제 null 후보만 중단합니다. 구버전
outcome은 변경하지 않은 채 `/backfill-outcomes N`으로 최대 24개씩 새
메타학습 필드에 연결할 수 있습니다.

reference intelligence는 레퍼런스 컬렉션을 사용자 의무로 만들지 않습니다.
`/reference-intelligence`는 현재 작업공간만으로 출처가 있는 자기 모델과 미지
경계를 만들고 연구 질문 최대 하나를 선택합니다. ref가 없으면 경쟁 프로젝트를
지어내지 않고 `knowledge_gap` 가설만 허용합니다. 선택 경로나
`PALAMEDES_REF_ROOT`가 있을 때만 제한된 외부 관측을 더하며, 모든 능력·가설·
의제는 실제 source ID를 인용해야 합니다. 저장된 의제는 다음 cognition cycle의
방향에는 영향을 줄 수 있지만 `delivery_authority_granted: false`를 유지합니다.

outcome이 5개 이상인 프로젝트에서는 `/cycle`이 제한된 메타학습을 자동으로
깨웁니다. 한 cycle당 구 outcome 최대 12개를 읽기 전용 매핑하고, 자기/reference
모델이 없으면 최초 모델을 만들며, 같은 표면의 micro outcome 5회 연속을 필수
fresh-eyes 의제로 바꿉니다. 선택된 줌 의제는 참고 문구가 아니라 승인 gate입니다.
다른 `micro` 미션으로는 닫을 수 없고, 의제 ID를 명시적으로 인용한 component
이상 미션이 승인돼야 mission lineage와 함께 종료됩니다. 모델이
`"confidence":"90"`처럼 명백한 타입만 잘못 반환하면 알려진 필드에 한해
복구하고, 모호한 내용은 계속 거부합니다.

제품 정렬은 이제 국소 품질 최적화보다 먼저 적용됩니다. 출처가 있는 제품
불변 목적, 재사용 가능한 기존 역량, 임시 제약, 열린 통합 우회, 제품 단계별
필수 여정은 `.palamedes/product-alignment/state.json`에 보존되어 `/cycle`에
주입됩니다. 미션 승인은 제품 목적 충돌, 기존 역량을 검토하지 않은 신규 구축,
만료 제약의 무언 재사용, 필수 여정 증거 없는 단계 승격을 각각 차단합니다.
의미 해석은 모델이 출처 ID와 함께 제출하고, 결정론적 gate는 키워드로 제품
의도를 추측하지 않고 ID와 선언된 효과만 검증합니다.

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

두 번째 사전등록 비교인
[`proof-003`](experiments/proof-runs/proof-003/RESULT.md)은 Palamedes와 강한
4회 호출 후보 토너먼트를 비교했습니다. 양쪽 모두 총 12회 호출했고
Palamedes의 입력 토큰은 1.045배였습니다. Palamedes는 9표 중 7표와 세 사례
중 두 사례를 이겼습니다. 따라서 같은 모델·동일 호출이라는 좁은 주장은
입증됐지만, 독립적인 사람 평가나 실제 성과 우위까지 입증된 것은 아닙니다.

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

Paperclip 같은 1:N 팀에서는 Palamedes가 스케줄러가 되는 대신 공유 인지
원장을 제공할 수 있습니다. 에이전트별 관측 출처와 관측 편향, 서로 경쟁하는
가설, 단일 미션 소유권, 오래된 세계 상태 쓰기 충돌, 블라인드 commit–reveal
탐사, 결과 기여도를 보존합니다.
호출·예산·권한·큐·프로세스 수명은 계속 외부 호스트가 담당합니다. 자세한
계약은 [다중 에이전트 팀 통합 문서](docs/integration-agent-teams.md)에 있습니다.

```bash
palamedes team snapshot --state .palamedes/team-cognition.json
palamedes chat --provider codex --team-state .palamedes/team-cognition.json \
  --agent-id palamedes-main --agent-role strategist
```

팀 인지 흐름:

| 명령 | 역할 |
| --- | --- |
| `palamedes team observe` | 출처·관측 표면·신뢰도·표본 편향을 포함한 에이전트 관측 기록 |
| `palamedes team hypothesis` | 다른 해석을 덮어쓰지 않고 반증 가능한 가설 보존 |
| `palamedes team round-begin` | 독립 탐사의 참여자·질문·근거 경계 동결 |
| `candidate-hash` → `candidate-commit` → `candidate-reveal` | 먼저 공개된 제안이 후속 에이전트를 앵커링하는 현상 방지 |
| `palamedes team claim` / `release` | 스케줄링 권한을 가져오지 않고 미션당 활성 소유자 한 명 보장 |
| `palamedes team outcome` | 합계 100%의 명시적 기여도와 관측 결과 기록 |
| `palamedes team snapshot` | 보존된 전체 팀 원장 확인 |

모든 쓰기는 `--expected-world-version`을 사용할 수 있습니다. 오래된 상태를
가진 에이전트는 다른 관측을 덮어쓰지 않고 새 상태를 다시 읽어야 합니다.
전체 이력은 보존하지만 AI 프롬프트에는 최근 근거, 열린 가설, 활성 미션,
결과, 모든 후보가 공개된 탐사 라운드만 제한적으로 전달합니다. 이 팀 계층은
Research Beta 안의 동일 호스트용 Alpha 기능이며, 분산 팀은 같은 스키마와
버전 계약을 트랜잭션 저장소 뒤에 연결해야 합니다.

## 구조

```text
palamedes/
├── palamedes.py                    # 계획 커널과 CLI
├── palamedes_chat.py               # AI 터미널과 인지 사이클
├── palamedes_observe.py            # 제한·마스킹된 작업공간 관찰
├── palamedes_watch.py              # 이벤트 기반 자율 관찰 루프
├── palamedes_thought.py            # 미션 이전 생각·발견 숙성 계층
├── palamedes_knowledge.py          # 시간성을 가진 자기·외부 지식과 미지 경계
├── palamedes_epistemics.py         # 관측면·coverage·기준율 일반화 게이트
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
  → 설명되지 않은 잔여와 미완성 생각
  → 시간·영역이 다른 생각의 비자명한 연결
  → 경쟁하는 해석
  → 후보 미션
  → 근거, 비판, 반증
  → 선택된 미션 계약과 비목표
  → planner → task → implementation
  → 관찰된 결과를 Palamedes에 환류
```

문서·중앙 레퍼런스·완료된 구현 revision이 바뀌면 즉시 기능이나 미션을
제안하지 않는다. `noticer`가 특정 당사자를 미래 운영 장면에 놓고 목표와
제약을 부여한 뒤, 현재 설명에 흡수되지 않는 잔여를 최소 두 개 추출한다.
개발자 부재, 장애 복구, 규모·규제 변화, 반복 업무, 소유권 이전 같은
상황을 사용한다. `connector`는 여기서 한 칸 인접한 가능성으로 이동해
아직 관찰에서 묻지 않은 중요 질문과 가까운 제품·사업 기회를 기록한다.
새로움·잠재가치·불확실성·범위확장 위험은 각각 따로 점수화한다. 기존
가정을 바꾸고 제품을 재구성하며 가능한 결정을 달라지게 하는 연결만
discovery 후보로 남긴다. 생각은
`.palamedes/thoughts/thoughts/`, 발견 후보는
`.palamedes/thoughts/discoveries/`에 wake를 넘어 보존된다. 둘 다 미션이나
실행 권한을 갖지 않는다. 이후 full cognition wake가 이 발견들을 입력으로
받고 기존 adversary·selector를 통과한 경우에만 출처 discovery ID가 미션
초안에 연결된다.

미션 outcome은 결정 당시 이유, 예상, 실제 관찰, 예상과의 차이, 믿음 수정,
다음 probe를 포함한 경험으로 `.palamedes/thoughts/experiences/`에 압축된다.
이 경험은 이후 발견 wake의 입력으로 돌아간다. 이는 추적 가능한 발견
루프의 첫 구현이며, 아직 인간 수준의 통찰이나 사업 성과를 증명했다는
주장은 아니다.

새 작업공간 신호가 없어도 미해결 thought가 24시간 동안 숙성되지 않았다면
예산 안에서 한 번 재검토한다. 다시 관찰된 잔여는 강해지고, 연속 숙성에서
선택되지 않은 thought는 약해져 결국 보관된다. 동일한 일일·누적 모델 호출
예산이 적용되므로 무제한 자기 대화로 확장되지는 않는다.

noticer는 `.palamedes/knowledge/`에 제한적이고 수정 가능한 지식층도
관리한다. claim은 `internal_product`와 `external_world`, 그리고
사실·해석·규범·역량·제약을 구분한다. 모든 claim에는 실제 관찰 출처,
신뢰도, 유효 시점, 적용 범위, 관점, 영향받는 당사자, 규범적 가정,
알려진 제외 범위가 붙는다. 제품 코드나 주요 문서가 바뀌면 명시적인
unknown boundary를 남겨야 한다. 새 코드가 존재한다는 사실을 그 목적,
사용자, 가치까지 안다는 뜻으로 취급하지 않는다.

중앙 ref도 더 이상 revision 신호로만 보지 않는다. 최대 8개 저장소의 대표
README를 각각 4 KB까지만 마스킹해 관찰한다. knowledge claim은 해당 bounded
observation에 실제로 존재하는 source ID만 인용할 수 있다. `cross_domain`
discovery는 활성 내부 claim과 외부 claim을 최소 하나씩 인용해야 하며,
관찰된 현실과 규범 판단, 배제된 당사자, 권리 위험, 시대 민감성을 각각
기록해야 한다. 따라서 흔하거나 합법적이거나 수익성이 있거나 역사적으로
용인됐다는 사실이 정당성으로 자동 변환되지 않는다.

Palamedes는 claim이 왜 보였는지도 observation surface로 기록한다. 여기에는
수집 방식, 선택·노출 과정, 관찰된 모집단과 빠진 모집단, visibility bias가
포함된다. epistemic profile은 자극 강도와 대표성, 관련성, 독립성, 지속성,
행동 근거, 기준율 근거를 분리하고, expression·exposure·behavior·outcome
증거를 구분한다. 각 claim에는 현재 허용되는 가장 좁은 추론과 금지되는
일반화가 함께 동결된다.
각 surface는 `origin_id`도 기록한다. 동일 원문을 복제한 여러 기사나
게시물은 출처 수만큼 독립적인 증거로 계산되지 않으며, 서로 다른 원자료
비율보다 높은 독립성을 주장할 수 없다.

모집단 수준 claim은 대표성 있는 표본과 분모를 가진 행동 또는 결과 근거가
없으면 거부된다. 강하게 노출된 게시물만으로는 이 게이트를 통과할 수 없다.
`.palamedes/epistemics/coverage.json`은 과대표집된 관측면, 빠진 모집단,
평범한 ambient baseline의 존재를 기록한다. discovery는 행동 기준율이
확보되기 전까지 `surface_anomaly`, `representativeness_unknown`,
`cross_check_required`, `bounded_opportunity` 중 하나에 머문다.
`mission_eligible` discovery ID만 자율 selector가 미션 출처로 주장할 수
있으며, 나머지는 폐기하지 않고 조사할 질문으로 계속 보존한다.
또한 mission eligibility에는 반대 표본 claim이 필요하므로, 하나의
지지 baseline만으로 자기 확증 루프를 만들 수 없다.

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
- `/reference-intelligence [path]`: ref 없이도 시작하는 자기 모델·연구 의제 생성
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
| 24시간 동안 숙성되지 않은 미해결 thought | noticer + connector 재검토 |
| 주요 문서 변경 | noticer + connector 숙성 |
| 중앙 ref revision 변경 | noticer + connector 숙성 |
| 계획 변경 | adversary + selector |
| 커밋 전 구현 변경 | interpreter + adversary |
| 완료된 Git revision 변경 | 당사자·미래상황 noticer + 인접 가능성 connector |
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
  + 인과 역할, 권한 범위, 선택 유형, 모든 후보의 후속 상태
      ↓
스키마 검증된 미션 초안

실제 /outcome
      ↓
outcome analyst
  예상 대 관찰 + 원인 분리 + 믿음 갱신
  + continue가 아니면 다음 승인을 제약하는 evidence gate
```

완료된 구현을 뒤늦게 평가한 사이클은 미션을 `originated`했다고 기록할
수 없다. `implementation_state_at_start=completed`이면 반드시
`causal_role=audited`, `decision_scope=audit_only`여야 한다. 또한 선택은
`exclusive`, `sequencing`, `conditional`, `portfolio`, `probe`를 구분하고,
모든 후보에 선택·거부·보류·조건부·대기 상태와 이유를 남긴다. 따라서
“이번에 고르지 않음”이 자동으로 “영구 폐기”로 둔갑하지 않는다.

outcome analyst가 `revise`, `stop`, `insufficient_evidence`를 내리면
`.palamedes/missions/outcome-gates.jsonl`에 열린 제약이 생성된다. 다음
미션은 `outcome_response`로 각 결과를 지목하고 증거 공백을 해결하는지,
독립적인 미션인지, 또는 부채를 의식적으로 감수하는지 설명해야 승인된다.
따라서 outcome은 단순 의견이 아니라 다음 행동에 영향을 준다. 사용자가
`/outcome`으로 입력한 관측은 `implementer_claim`으로 표시되며, 기록됐다는
이유만으로 독립 증거가 되지는 않는다.

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
