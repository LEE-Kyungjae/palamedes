# Palamedes

<p align="center">
  <a href="README.md">English</a> · <strong>한국어</strong>
</p>

<p align="center">
  <img src="assets/palamedes.png" alt="Palamedes" width="100%">
</p>

> **Palamedes는 실행 에이전트가 구현 방법을 계획하기 전에, 어떤 미션이
> 계획할 가치가 있는지를 판단합니다.**

Palamedes는 `planner → task → implementation` 앞에서 작동하는 연구 베타
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
| 자율 상위기획 발원 | Vision Genesis와 저비용 Vision Scout 구현; 실제 프로젝트에서 사용자가 주지 않은 founder prompt 발원 |
| 독립 인간·행동 검증 | 블라인드 검토 및 사전등록 행동 probe 경로 구현; 실제 독립 증거는 아직 없음 |

## 실제 프로젝트 데모

[![Palamedes와 Codex의 윷놀이 품질 사이클 데모](assets/demo/yut-gameplay-demo.jpg)](assets/demo/yut-gameplay-demo.mp4)

위 이미지를 누르면 35초 MP4 데모가 열립니다. 이 윷놀이는 Palamedes와 Codex의
1:1 반복 품질 사이클이 실제 화면·규칙 경계·접근성·모션 회귀를 개선한 산출물입니다.
다만 이는 Palamedes가 제품 성공이나 원래 기획 정렬을 보장한다는 증명이 아닙니다.
후속 감사에서는 잘 다듬어진 로컬 게임이 원래 온라인 멀티게임 목적과 어긋났다는
더 큰 범위 오류도 발견했습니다. 이 사례는 Palamedes의 국소 품질 탐색 능력과 함께,
상위 제품 목적을 먼저 고정해야 한다는 한계를 동시에 보여줍니다.

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
필수 여정은 append-only `.palamedes/product-alignment/events.jsonl` 원장에
보존되어 `/cycle`에 주입됩니다. `state.json`은 재생성 가능한 projection일
뿐입니다. 미션 승인은 제품 목적 충돌, 기존 역량을 검토하지 않은 신규 구축,
만료 제약의 무언 재사용, 필수 여정 증거 없는 단계 승격을 각각 차단합니다.
의미 해석은 모델이 출처 ID와 함께 제출하고, 결정론적 gate는 키워드로 제품
의도를 추측하지 않고 ID와 선언된 효과만 검증합니다.

### Vision Genesis: 보완 전에 최초 기획 발명

Palamedes는 이제 제품 세계를 발명하는 단계와 구현 미션으로 컴파일하는 단계를
분리합니다. 첫 `/cycle`과 근거 수준에 따른 투자 envelope가 소진될 때 다음 일곱
독립 역할이 자동으로 깨어납니다.

```text
사용자가 주지 않은 탐사 의제·질문 작성
  → 잠재 욕구·감정 해석
  → 먼 영역 유추 탐색
  → 메커니즘 강제 융합
  → 서로 다른 제품 세계 3개 구성
  → 매니악 비평과 자연어 상위 기획문 작성
  → 현실성·기회비용 통제
```

첫 역할은 사용자가 제공하지 않은 상위 탐사 프롬프트 4~6개를 직접 쓰고 2~3개를
선택합니다. 기본 adaptive 조건은 가정을 뒤집는 frontier 질문, 현재 제품 여정과
역량에 붙어 있는 conventional 질문, 먼 인간 메커니즘을 구체적인 제품 엔진과 잇는
bridge 질문을 반드시 경쟁시킵니다. 전체 후보는 최소 여섯 탐색 영역을 포함합니다.
이 역할은 이름 붙은 해법을 미리 심거나 자기 질문에 답하거나 구현 권한을 줄 수
없습니다. 선택된 의제는 후속 역할에 권한이 아닌 탐색 데이터로 전달됩니다. 따라서
프롬프트 최초 생성이 고정 system prompt 안에 숨지 않고 검토 가능한 산출물로 남습니다.
`/vision-agenda-ablation <case> <challenger> <comparator>`는 서로 다른
`adaptive|frontier|conventional` 전략 둘을 비교하며 기본값은 adaptive 대 강한 일반
제품 질문입니다. 두 조건은 동일 맥락, 같은 모델 계열, 같은 생성 역할
7회를 사용하고 출처를 가린 채 심판에게 전달됩니다. 기록에는 조건 순서·호출 수·점수·
custody가 남습니다. challenger 승리는 같은 모델·동일 호출의 기계 선호만 지지하며,
동일 토큰이나 사람 증거가 아닙니다. 동률 또는 conventional 승리에서는 우위를 주장하지
않습니다.
ablation 쌍은 사전등록된 1회 시도만 허용합니다. 첫 provider 호출 전에 `started`를
append하고 JSON 오류·provider 오류·심판 오류도 `failed`와 가능한 사용량을 보존한 채
시도를 소비합니다. 따라서 실패를 버리고 유리한 결과가 나올 때까지 재실행할 수 없습니다.
provider JSON은 원문 SHA-256·길이·파싱 방식을 호출별 custody로 남깁니다. 코드펜스나
텍스트 포장 안의 균형 잡힌 단일 객체 추출과 구조적 trailing comma 제거처럼 의미가
유일하게 보존되는 변환만 허용합니다. 누락된 쉼표·따옴표·필드처럼 해석이 갈리는 오류는
추측해 고치지 않고 실패시키며, 그 실패 호출도 토큰 사용량과 ablation 시도 예산에
포함합니다. 원문 내용 자체는 custody에 복제하지 않습니다.

감정 모델은 긍정 편향을 두지 않습니다. 소속·기쁨뿐 아니라 분노·경쟁·불안·
지위·습관·커뮤니티가 매개하는 감정도 후보이며 피해와 착취 경계를 함께
기록합니다. 유추 역할은 인접 소프트웨어 기능을 벗어나야 하고, 융합 역할은
복수 메커니즘을 결합해야 합니다. 제품 세계는 감정·행동의 반복 루프, 정체성,
사회적 결과, 수년간 확장 가능한 콘텐츠나 규칙 엔진을 포함합니다. 선택 비전은
`.palamedes/visions/`에 저장되고 다음 cognition의 가설 맥락으로 들어가지만
항상 `delivery_authority_granted: false`입니다. `/vision <context>`로 강제 실행하고
`/visions`로 최신 기획문을 볼 수 있습니다.

선택 역할은 상세 `vision_brief`와 별도로 180~1200자의 `founder_prompt`를 씁니다.
이 문장은 사용자가 주지 않은 인간 긴장·제품 메커니즘·감정/행동 루프·장기 확장 방향을
스스로 도입해야 하며, 내부 role/vision ID나 생성 과정 설명 없이 사람이 최초 기획 때
보낼 수 있는 독립 텍스트여야 합니다. “재미있게”, “참여를 높여라” 같은 일반 요청만으로는
인정되지 않습니다.

강제 실행과 자동 wake는 같은 구조화된 vision-context contract를 사용합니다. 사용자
맥락·제한된 저장소 관찰과 함께 출처가 있는 제품 목적, 기존 역량, 임시 제약, 열린
통합 격차, 제품 단계, outcome gate를 전달합니다. 제품 invariant는 잘 다듬어진 로컬
구현보다 우선하며 기존 역량을 검토하기 전 greenfield 발명을 허용하지 않습니다.
선택 비전의 product-ground-truth fingerprint는 mission lineage로 이어지고, 정렬 상태가
바뀌면 승인을 차단해 새 vision wake를 요구합니다. 반대로 기록된 목적을 진전시키고,
관련 기존 역량의 재사용 또는 기각 근거와 열린 통합 격차에 명시적으로 응답한 후속 미션은
승인할 수 있어 정렬 게이트가 자율 비전을 영구적인 제안으로만 가두지 않습니다.

최초 발명과 사용자 아이디어 보완을 구분하기 위해 세 블라인드 benchmark도
추가했습니다. 생성기에는 제품 맥락만 제공하고 사람의 기획은 숨긴 뒤 별도
심판에게만 공개합니다. 컬렉션 case는 발견·컬렉션·아바타·문화 원천을 숨기고,
장르 융합 case는 서로 다른 퍼즐 규칙을 충돌시키는 인간 발상을 숨깁니다. social
case는 집단 소속감, 제한된 분노 표출, 소액 경제, 괴롭힘 방지·관계 복구 제약의
결합을 숨깁니다. `/vision-benchmark collection`, `/vision-benchmark fusion`,
`/vision-benchmark social`은 최초 발원·개념적
거리·감정 깊이·메커니즘 융합·세계 일관성·3년 확장성·인간 승인 가치를
기록합니다. fixture는 블라인드 구조와 평가 계약을 증명하며, 실제 모델의 점수는
별도 실증 결과이지 아키텍처만으로 보장되는 주장이 아닙니다.

`/vision-benchmark-suite all 3`은 모든 블라인드 case를 각각 3회 반복합니다(case당
1~5회로 제한). 각 trial과 인간 평가 packet은 서로 다른 ID를 가지며 suite manifest도
저장됩니다. `/vision-benchmark-summary`는 통과율, 축별 평균, 사람 기획과의 관계,
심판 custody, case 범위, 선택된 기획 제목의 다양성을 집계합니다. 각 trial의 비전
기억도 격리해 앞선 novelty exclusion이 뒤 표본을 인위적으로 다르게 만들지 못하게
합니다. 따라서 통과율은
높지만 같은 발상만 반복하는 경우를 안정적인 창의력으로 승격하지 않습니다. 반복된
모델 평가는 여전히 사람 증거가 아닙니다.
독창성 점수가 높아도 입력의 핵심 제품 목적을 빠뜨리면 통과할 수 없습니다. Vision
Genesis는 출처가 있는 context requirement를 제품 세계 구성과 비평까지 전달하고,
모든 core 항목이 충족돼야 선택합니다. benchmark gate v3는 상세 비전 평가와
founder-prompt 발원 평가를 분리합니다. 두 번째 블라인드 심판은 문제 재구성, 입력에 없던
메커니즘, 감정 가설, 제품 세계의 씨앗, 사람의 상위 프롬프트 대체 가능성을 채점합니다.
중앙 해결안이 입력에 이미 있었거나 문장이 일반 요청이면 상세 비전 점수와 무관하게
실패합니다. 인간 A/B packet도 상세 완성안이 아닌 `founder_prompt` 대 숨겨진 인간
기획문을 비교합니다. 기존 `core_requirements_satisfied`와 빈
`unmet_core_requirements`도 계속 PASS 조건입니다.

첫 gate-v3 실모델 표본 `vision-benchmark-edf12f163696`은 사람의 컬렉션 원안을 보지
않고 임시 관리·규칙 변형·양도·후손 재발견으로 이어지는 **The Caravan of Living
Games**를 발원했습니다. 동일 Codex 심판은 founder-prompt 5축을 94~98점으로 평가했지만
이는 상관된 기계 증거입니다. 9회 호출에 총 176,536토큰이 사용돼 비용 효율도 증명되지
않았습니다. 따라서 CLI는 이를 단순 PASS가 아니라
`MACHINE PASS (correlated same-provider judge)`로 표시합니다.

전체 Genesis를 모든 아이디어에 적용하는 비용 문제를 줄이기 위해 저비용
`Vision Scout` 경로도 제공합니다. `/vision-scout-benchmark collection|fusion|social`은
세 역할만 사용해 서로 다른 인과 영역의 후보 세 개를 만들고, 하나를 반증·선택하고,
현실성 관리자가 폐기 또는 블라인드 인간 검토만 결정하게 합니다. 선택된 founder
prompt는 숨겨진 사람 기획문을 보는 별도 심판 한 번으로 평가되므로 정상 경로는 생성
3회와 평가 1회입니다. machine pass가 열 수 있는 다음 단계는 인간 A/B packet뿐입니다.
Scout는 `full_genesis_authorized=false`와 `delivery_authority_granted=false`를 기록하며,
독립 사람 또는 행동 증거 없이 전체 Genesis나 구현으로 자동 승격할 수 없습니다.
검토 packet도 산출물 출처가 `vision_scout`인지 `vision_genesis`인지 명시해 저비용
초안을 완성된 비전으로 위장하지 않습니다.
같은 사례·맥락은 생성 호출 전에 1회 시도 원장에 기록되며, 응답 실패도 시도 예산을
소비해 약한 결과를 버리고 다시 뽑는 선택 편향을 막습니다.

첫 Scout 실모델 표본 `vision-scout-benchmark-5661177d748b`은 숨겨진 컬렉션 원안과
다른 ‘작은 게임의 행동이 하나의 지속 세계와 미래 가능성을 바꾸는’ founder prompt를
발원했습니다. 동일 Codex 심판은 5축 93~97점과 stronger를 기록했지만 상관된 기계
증거일 뿐입니다. 4회 호출·71,495토큰으로 기존 9회·176,536토큰보다 토큰 59.5%,
호출 55.6%가 적었습니다. 단일 표본이므로 기대 비용이나 사람 수준 창의성을 증명하지
않으며, 생성된 `vision-review-9db2913d3906`의 독립 인간 평가가 남아 있습니다.

고정 benchmark가 아닌 실제 프로젝트에서는 `/vision-scout <맥락>`을 사용합니다.
Palamedes는 현재 제품 ground truth와 저장소 관찰을 함께 읽되 2~3회 호출로 founder
prompt 후보를 선별해 화면에 표시합니다. core requirement가 미충족이면 2회 후
결정론적으로 폐기하고, 통과한 후보만 세 번째 governor 판단을 받습니다. 동일한 사용자 요청은 관찰 timestamp나 상태
파일이 바뀌어도 request fingerprint로 기존 Scout를 재사용하므로 반복 비용이 들지
않습니다. 원래 전체 context는 fingerprint만 공개 record에 두고 별도 local context
record에 보존해, 나중에 증거가 생기면 동일 정보 경계에서 Genesis를 이어갈 수 있습니다.

`/vision-scout-promote <vision-scout-id>`는 독립 인간 검토자 두 명 이상의 quorum,
confidence 60 이상, 모두 생성안 선호 또는 동급, 7개 축 평균 열세 5점 이내를 만족할
때만 전체 7역할 Genesis를 한 번 실행합니다. model reviewer와 팀 내부 reviewer는 이
quorum에 포함되지 않습니다. 재호출은 기존 promotion을 재사용하며, 승격 후에도
delivery 권한은 계속 false입니다. 현재 실프로젝트 Scout에는 비교용 독립 인간 packet을
자동 생성하지 않으므로, 이 승격 경로는 출처가 명확한 블라인드 Scout 검증에 우선
적용됩니다.

실프로젝트에는 행동 증거 경로도 있습니다. `/vision-scout-probe <id> <JSON>`으로
가설, 단일 metric, 비교 연산자와 threshold, 최소 표본(5 이상), 최대 30일, 데이터
출처를 결과 관찰 전에 고정합니다. `/vision-scout-probe-outcome <id> <JSON>`은 해당
probe ID, 관찰값, 사전등록 이상 표본, `measured|external_dataset` provenance, 출처와
관찰을 한 번만 기록합니다. 판정은 선언이 아니라 연산자와 threshold로 기계 계산되며,
실패 outcome도 교체할 수 없습니다. 성공한 행동 probe는 독립 인간 quorum의 대체
renewal 경로로 전체 Genesis만 열 수 있고 delivery 권한은 열지 않습니다.

실프로젝트 Scout도 생성 전에 request fingerprint별 1회 시도를 append-only 원장에
기록합니다. JSON 파싱이나 계약 검증 실패도 제공자 token custody와 함께 실패로 남고
같은 버전·요청의 재시도를 차단합니다. 출처 인용은 줄바꿈·연속 공백 정규화만 허용하며,
의미를 바꿔 쓴 문장은 계속 거절합니다.

실프로젝트 검증은 현재 V4까지 진행됐습니다. V3는 저장소 문맥만으로 “설득력 있는
문장보다 현실에 걸어 둔 작은 가설이 권위를 얻고, 생각을 바꾸는 일을 패배가 아니라
유능한 진전으로 느끼게 하는 의사결정 환경”을 발원했습니다. 이는 사용자가 직접 준
기능 목록의 재서술이 아닌 상위 제품 방향이지만, 3회 호출에 122,709토큰을 사용했습니다.
V4는 전체 문맥을 10KB 미만의 출처 보존 요약으로 압축해 성공 시 약 7.5만 토큰 수준을
목표로 했습니다. originator와 critic은 성공했으나 governor 제공자 호출이 실패했습니다.
이 실패 뒤 역할별 불변 체크포인트와 제한 재개를 구현해, 완료된 역할을 다시 생성하거나
유리한 결과가 나올 때까지 재시도하지 않고 남은 역할만 이어갈 수 있게 했습니다.
체크포인트 도입 전 발생한 V4 결과는 소급 복구하지 않습니다. 체크포인트가 처음부터
적용된 V5는 originator·critic·governor 세 결과와 72,401토큰을 모두 보존했습니다.
“만료 가능한 프로젝트 정체성 가설”이라는 새 방향을 만들었지만 critic이 핵심 비용·기간·
복구 한도를 `partial`로 판정한 뒤 governor가 인간 검토를 선택해 결정론적 gate가
차단했습니다. 이 과정은 후보 기각을 올바르게 지켰지만 정상적인 `discarded` 결과 대신
계약 실패로 끝나고 불필요한 세 번째 호출을 사용했습니다. V6는 critic이 후보를 모두
기각했거나 core requirement가 하나라도 미충족이면 governor를 호출하지 않고 2회
호출의 결정론적 `discarded` outcome으로 닫습니다. gate를 낮추지 않고 실패 의미와
비용만 바로잡은 변경입니다.

첫 V6 live one-shot `vision-scout-2a657a5bfc10`은 모든 core requirement를 통과해
세 번째 governor까지 실행됐고 70,736토큰을 사용했습니다. 선택 방향은 Palamedes가
결정·희생·반전·수혜자에서 “프로젝트가 어떤 builder 정체성이 되어 가는가”를 추론하고,
그 정체성을 표현하거나 의도적으로 반박하는 미션을 발원하게 하는 것입니다. 반복 감정은
인정·소속·자부심뿐 아니라 현재 작업이 표방 가치와 충돌할 때의 불편·분노·상실이며,
정체성은 만료 가능하고 반례·비공개 이견으로 수정돼야 합니다. governor는 블라인드 인간
검토만 선택했습니다. 이는 자율 발원의 두 번째 실사례지만 사람 선호나 행동 효과 증거는
아직 아닙니다.

실프로젝트 Scout가 `blind_human_review`를 선택하면 이제 비교 기준안을 꾸며내지 않고
단독 블라인드 packet을 자동 생성합니다. `/vision-scout-review-next`는 모델·저자 정보를
숨긴 founder prompt와 7개 절대 평가축, packet fingerprint를 보여줍니다.
`/vision-scout-review-submit <packet-id> <JSON>`으로 평가를 제출합니다. 서로 다른 독립
인간 2명이 confidence 60 이상, 모든 축 60 이상·평균 70 이상으로 모두 `advance`해야
사람 경로가 Genesis 승격 gate를 통과합니다. model·team·author·unknown 평가는 감사
기록에는 남지만 quorum에는 포함되지 않습니다. 이 단독 평가는 숨겨진 사람 원안과의
비열등성을 증명하지 않으므로 기존 A/B benchmark 증거와 합치지 않습니다.

새로 선택된 모든 비전은 delivery에 영향을 주기 전에 reality governor를
통과합니다. 전체 구현·최소 software probe·수동 probe·기존 역량 재사용/구매·
미구현·다른 기회 투자를 엔지니어링/AI/인프라/유지보수 비용, 가역성, 학습 가치,
기회비용으로 비교합니다. 추측 단계 비전은 `full_build`를 선택할 수 없고, 선택된
probe가 renewal evidence를 만들기 전에는 product/service/portfolio 규모의 구현
미션도 승인할 수 없습니다. debt·scale·kill guard는 후속 미션 lineage에 따라갑니다.
비용 추정은 집행 가능한 outcome 지평으로도 변환됩니다. speculative·behavioral·
demand·revenue 근거는 각각 1·2·3·5개 outcome 뒤에 새 비전과 투자 재평가를
강제합니다.

benchmark의 평가 custody도 명시합니다. 생성자와 심판 callable·identity를 분리할
수 있으며 실제로 다른 provider인지 record에 남깁니다. 각 실행은 무작위 A/B 인간
평가 packet을 `.palamedes/vision-benchmarks/human-review/`에 만들고 정답 key는
`answer-keys/`에 별도 보관합니다. 같은 provider의 별도 심판은 상관된 증거이며
독립 증명으로 주장하지 않습니다. 실제 다른 심판은
`PALAMEDES_VISION_JUDGE_PROVIDER`와 선택적인 `PALAMEDES_VISION_JUDGE_MODEL`로
지정합니다. 완료한 블라인드 packet은 `/vision-review-submit <packet-id> <JSON>`으로
제출하며, 저자 정보는 별도 resolution record에서만 공개됩니다. 같은 reviewer의
중복 제출은 거절되고 `/vision-review-summary`가 사람 선호와 점수 차이를 집계합니다.
`/vision-review-next`는 정답 key 없이 가장 적게 평가된 packet을 보여줍니다. 각 응답은
`reviewer_kind: human|model`을 선언하며 model·미확인 응답은 감사 기록에는 남지만
사람 증거 합계에서는 제외됩니다.
또한 `reviewer_relationship: independent|team|author|unknown`을 기록해 사람 자기표시
평가와 독립된 사람 평가 수를 분리합니다.
`/vision-review-bundle`은 정답 key가 없는 독립 실행형 오프라인 검토 화면을 만듭니다.
화면이 내려받는 응답 JSON에는 정확한 packet fingerprint가 포함되며,
`/vision-review-import <response.json>`은 오래되거나 다른 packet의 응답을 저자 공개
전에 거절합니다.
`/vision-review-gate`는 사례별 독립 인간 quorum과 비열등성 기준을 적용합니다.
PASS여도 허용되는 주장은 `repeated_blind_human_founder_prompt_support`뿐이며 인간 수준
창의성이나 시장 성공 주장은 허용하지 않습니다.

저장소의 세 사례는 calibration이지 일반화 증명이 아닙니다. 외부 사람이 작성한 비공개
holdout은 `/vision-holdout-import <case.json>`으로 가져오고
`/vision-benchmark holdout:<case-id>`로 실행합니다. 숨겨진 기준안은 로컬
`.palamedes/vision-benchmarks/holdout-cases/`에 fingerprint와 함께 보관되며 생성기
prompt에 들어가지 않습니다. 인간 증거 게이트는 builtin 리뷰를 제외하고 외부 holdout
세 사례를 요구합니다. 작성자의 `independent` 표시는 자기신고이며 신원 검증이나
암호학적 sealing을 의미하지 않습니다. 로컬 상태 저장은 기록하지만 가져온 원본이
다른 저장소에 커밋된 적 없는지는 명시적으로 미확인 상태로 남깁니다.
작성자 ID는 비공개 answer key에만 보존되고 블라인드 packet에는 나오지 않으며 같은
stable ID로 자기 사례를 평가하면 거절합니다. 승격은 서로 다른 holdout fingerprint
세 개도 요구하므로 같은 사례의 이름만 바꿔 coverage를 만들 수 없습니다.
각 holdout은 가져올 때 `evaluation_trial_count`를 1~3회로 사전등록합니다. 생성기를
호출하기 전에 append-only 원장에 `started` 시도를 기록하므로 실패하거나 약한 생성도
시도 예산을 소비하며 사라질 수 없습니다. 승격 게이트의 모집단은 좋은 리뷰가 아니라
가져온 모든 사례와 사전등록된 모든 시도입니다. 각 시도마다 귀속 가능한 완료 기록과
독립 인간 reviewer quorum이 있어야 하므로 가장 잘 나온 실행만 평가하거나 불리한
사례를 조용히 빼고 통과할 수 없습니다. 이 로컬 원장은 단일 프로세스의 일반적인
선택 편향을 막지만 원격 타임스탬프 기관이나 동시성 안전 암호 원장은 아닙니다.

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

Palamedes 본체는 프로젝트마다 복제하지 않고 한 번만 설치할 수 있습니다.
기존 프로젝트의 `.palamedes` 기록은 그대로 둔 채 이름만 전역 Registry에
등록합니다.

```bash
pipx install --force git+https://github.com/LEE-Kyungjae/Palamedes.git

palamedes workspace init /work/greedy --name greedy
palamedes workspace init /work/zaeze --name zaeze
palamedes workspace list

palamedes -w greedy chat --provider codex
palamedes -w zaeze observatory --limit 100
palamedes-server -w greedy --port 8787
```

Registry는 기본적으로 `~/.local/share/palamedes/workspaces.json`에 저장되며
`PALAMEDES_HOME`으로 위치를 바꿀 수 있습니다. `workspace remove <name>`은
전역 이름 연결만 지우고 프로젝트나 `.palamedes` 기록은 삭제하지 않습니다.
`-w`를 생략하면 현재 디렉터리를 작업공간으로 사용합니다.

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

provider가 토큰 사용량을 보고하면 각 cognition 역할 artifact에 입력·캐시 입력·출력·
전체 토큰을 표준 형식으로 보존합니다. Vision Genesis는 여섯 역할 호출을 합산하고
측정·미측정 custody를 기록합니다. OpenRouter streaming usage, OpenAI 완료 usage,
Codex JSONL usage가 같은 필드로 정규화되며 usage를 주지 않는 provider는 비용 0이
아니라 `unmetered`로 남습니다.
다음 자동 비전은 이 provider 합계를 이전 delivery 실비와 투자 envelope 옆에서 함께
받습니다.

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
palamedes> /outcome-json {"status":"mixed","observation":"probe 결과","actual_investment":{"engineering_days":0.5,"ai_cost":3,"input_tokens":12000,"output_tokens":1800,"monthly_infrastructure":0,"evidence_source":"measured","notes":"작업 기록 + provider export"}}
```

주요 명령:

- `/observe`: 프로젝트, Git, TODO, 계획 상태, 중앙 ref 신호 관찰
- `/reference-intelligence [path]`: ref 없이도 시작하는 자기 모델·연구 의제 생성
- `/reconcile`: 불변 handoff, outcome, gate와 lifecycle event를 읽어 dry-run
  projection 보고서와 proposal fingerprint를 만듭니다. 적용은 직전 검토 결과의
  fingerprint를 `/reconcile --apply <proposal-fingerprint>`로 정확히 제시해야 합니다.
  결정론적·멱등적 보정 event만 append하며 원본은 수정하지 않고 충돌은 unresolved로
  유지합니다.
- `python3 palamedes.py lifecycle-audit`는 불변 원천에서 lifecycle event 의미를
  독립 재생합니다. `lifecycle-reconcile`은 기본이 dry-run이며 정확한 fresh
  fingerprint에만 `--apply`를 허용합니다.
- `python3 palamedes.py gate-resolution --request request.json`은 증거 hash를 검증해
  읽기 전용 종료 제안을 만들며, 정확한 fingerprint만 resolution event와 gate
  revision을 append할 수 있습니다. 후속 미션 승인만으로는 gate가 닫히지 않습니다.
- `python3 palamedes.py storage`는 삭제나 재작성 없이 보존 등급, 고유 콘텐츠,
  중복 byte를 보여줍니다.
- `/satisfaction-json <JSON>`: 현재 Git/worktree fingerprint, 제한된 심볼·호출경로
  artifact, 주장별 필수 증거, 제품 목적 정렬과 신선도를 host가 검증합니다.
  `/satisfactions`는 요구사항별 최신 판정을 보여주며, 현재 snapshot에서 정렬된
  `already_satisfied` 요구사항은 같은 `requirement_id`의 구현 미션 승인을 차단합니다.
- `/alignment-candidate-json <JSON>`: 목적·역량·제약·통합 간극·surface stage 후보를
  append하되 활성 제품 기준은 바꾸지 않습니다. `/alignment-approve <candidate-id>`가
  인간 승인을 기록한 뒤 출처와 문구 variant를 역사 삭제 없이 병합하며,
  `/alignment`에서 surface별 projection을 확인합니다.
  승인 event가 권위 원장이며 projection은 이 event에서 재생성할 수 있습니다.
- outcome은 `validated_improvement`, `null_finding`, `already_satisfied`,
  `adverse_result`, `insufficient_evidence`, `blocked_by_environment`,
  `misaligned_mission`, `prototype_only` 중 정직한 `outcome_type`을 보존합니다.
- `/think`: 지금 빠진 사고 방식을 선택해 수행
- `/challenge`: 가정과 반증 조건 공격
- `/research`: 커밋 전에 필요한 최소 외부 근거 식별
- `/mission`: 계획을 변경하지 않고 구조화된 미션 초안 생성
- `/cycle`: context governor, interpreter, inventor, adversary, selector 독립 호출
  - context governor는 필수 조건·자율 영역·선호·참고 예시를 분리합니다. 참고
    예시와 현재 구현 경로는 clean-room interpreter와 inventor에게 노출되지 않고,
    후보 동결 후 adversary의 비교·드리프트 검사에만 제공됩니다.
- `/cycle --mode audit <context>` (`--skip-vision` 별칭): 제한된 감사를 위해 다섯
  cognition 역할만 호출합니다. 자동 Vision Genesis와 메타학습 provider 호출 및
  선택된 vision의 영향을 제외하고, 일반 `/cycle` 의미를 바꾸지 않은 채 동일 run
  ID의 역할별 진행 상태·소요 시간·토큰 custody를 출력합니다.
- `/cycle --resume <cycle-id>`: 실패했거나 중단된 cognition 실행을 보존된 문맥과
  검증된 역할 checkpoint에서 재개합니다. provider와 모델이 같아야 하며 완료된
  역할은 다시 호출하지 않고, 변조된 checkpoint는 차단합니다.
- `/context-ablation <cycle-id>`: 완료된 cycle의 상위 문맥을 고정하고 현재 구현
  경로를 숨긴 arm과 공개한 arm을 각각 새로 실행한 뒤, 출처를 가린 심판으로 문제
  프레임·인과 메커니즘·미션 계열의 이동을 비교합니다. 단일 shared-model 쌍은
  인과 증명이 아닙니다. 같은 명령을 반복하면 시도별 원본과 누적 방향 이동률·
  추상도 붕괴 신호율이 함께 보존됩니다.
- 일반 `/cycle <context>`는 provider 호출 전에 결정론적 비용 preflight를 수행합니다.
  Lookup은 host가 확인한 `already_satisfied` 요구사항에 0회, Micro는 schema 수리
  최대 1회를 포함한 mission compiler 1회, Component는 Vision/meta-learning 없이
  독립 5역할, Product만 전체 연구 경로를 사용합니다. `/cycle --mode
  lookup|micro|component|product <context>`로 명시할 수 있습니다. 범위가 모호하면
  Component로, 보안·개인정보·결제·삭제·migration·공개 API·배포·저장소 체결·
  비가역성·교차 surface·제품 불변조건 충돌은 더 깊은 모드로 승격합니다.
- `/preview`: 최신 미션 초안 검토
- `/approve`: 승인된 초안을 계획, 근거, 가설, probe로 투영
- `/reject`: 이유와 함께 초안 거부
- `/handoff`: planner용 불변 미션 계약 확인
- `/outcome`: 관찰된 결과를 추가하고 연결 상태 갱신
- `/outcome-json`: 같은 결과에 실제 작업일·AI 비용·토큰·월 인프라와 측정 출처를 귀속

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
전체 사이클에는 문맥 권한 분류를 포함해 5회 호출이 필요하므로 기본 설정에서는
자동 차단됩니다. 명시적으로 허용하려면 `--max-calls-per-wake 5`를 사용합니다.

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
