# 인지 워크플로

<p align="center">
  <a href="cognition-workflows.md">English</a> · <strong>한국어</strong>
</p>

Palamedes는 발견, 평가, commitment와 실행 권한이 서로 다른 작업이므로 별도의
워크플로를 제공합니다.

## Cognition cycle

```text
/cycle <context>
/cycle --mode product <context>
```

component·audit cycle은 context governor, interpreter, inventor, adversary와
selector를 실행합니다. product mode는 더 엄격한 v3 프로토콜을 사용합니다. 요청하지
않은 제품 기회를 찾는 발명가, 무관한 도메인의 아키텍처 원리를 옮기는 analogist,
실제 실패 기록에서 경계를 찾는 operator가 서로 독립적으로 후보를 만들고 동결합니다.
출처를 가린 adversary가 후보를 하나씩 검토하며, selector는 정제된 사본만 보고 선택할
뿐 수정하지 못합니다. 최종 draft는 host가 선택된 동결 후보에서만 발행합니다.
`/approve`와 delivery 권한은 계속 분리됩니다.

동결 evidence bundle에는 host가 만든 mission claim ledger가 포함됩니다. 직접 관측과
host가 검증한 record만 들어가며, 제한된 원문 claim, confidence와 custody를 보존합니다.
발명가는 source ID를 인용할 수 있지만 그 원문을 자신이 만든 수요·매출 주장으로
바꿀 수 없습니다. Advisory 해석, 가설, unknown과 reference code는 유용한 context지만
mission-citable 근거는 아닙니다. 동결된 v1 cycle을 resume하면 먼저 원래 v1 fingerprint를
검증한 뒤 v2 ledger를 만듭니다. Source-support 계약 이전의 legacy transfer mapping은
조용히 승격하지 않고 제외합니다.

product cycle 전에 Palamedes는 기능명이 아니라 운영 압력으로 다른 GitNexus 인덱스
저장소를 검색할 수 있습니다. 채택되는 근거는 저장소 경로, 전체 revision, symbol 범위,
해당 revision의 파일 hash와 excerpt hash에 묶입니다. Persisted packet은 bundle에
들어올 때 `git show <revision>:<path>`로 다시 읽습니다.
Packet 내부 hash가 서로 일치한다는 사실만으로 repository 근거가 되지는 않습니다.
Source claim anchor는 제한된 excerpt에 정확히 포함돼야 하지만, 이 검사는 인용 소속만
증명할 뿐 excerpt가 모델 해석을 의미론적으로 뒷받침한다는 사실까지 증명하지 않습니다.
Git 재검증은 commit된 파일과 범위를 증명하지만 과거 GitNexus ranking이나 symbol의
의미 분류까지 증명하지는 않습니다.
전이는 반드시 `원본 압력 → 인과
메커니즘/불변식 → 현재 제품 압력 → 적용법 → 적용 한계`를 설명하고 원본과 현재 제품
근거를 모두 인용해야 합니다. 설계·선택·배포·코드 재사용 권한은 모두 부정됩니다.
근거가 없거나 degraded이면 architecture 역할은 전례를 지어내지 않고 기권합니다. Raw
GitNexus excerpt만으로는 v3 analogist partition에 들어갈 수 없고, source·target·차이·한계·
권한 검증을 통과한 `palamedes-architecture-transfer/2` mapping만 전달됩니다. Stale
index, 접근 불가
저장소, partial query와 revision drift는 degradation으로 기록됩니다. 한 저장소의 실패가
근거 조작을 허용하거나 독립적으로 검증된 다른 source를 지우지는 않습니다.

Architecture query·transfer 준비 호출은 화면에 보이는 product role보다 먼저 실행되지만
동일한 cycle의 유료 작업입니다. Provider identity, attempt와 token usage가 precycle
artifact로 저장되고 같은 cycle budget을 소비합니다. Provider 예외와 잘못된 JSON/schema
시도도 rejected paid artifact로 남아 usage에서 사라지지 않습니다. Resume은 원래
provider/model identity와 동결 budget을 유지합니다.

후보가 요구한 승인과 probe authority precondition은 봉인된 미해결 specialized authority
gate로 컴파일됩니다. 선택된 제한 probe가 검토 가능한 draft가 될 수는 있지만 범용
`/approve`는 전문 gate를 충족하거나 가격·보상·출시·구현·delivery를 승인할 수 없습니다.

## Opportunity Scout

```text
/opportunity <product context>
/opportunities
```

사용자 욕구, 반복 행동, 수익화, 콘텐츠 경제, 사회적 구조, 라이브 운영, 유통,
플랫폼 확장과 위험 관점으로 제품을 회전해 봅니다. 이어서 결합도와 설계 불변식,
실패 전례, 2차 피드백, 운영 비용, migration과 rollback, 권한과 incentive, 달라진
제약, 사용되지 않는 capability를 숙련자 관점으로 살핍니다. 근거가 없으면 렌즈가
`no_signal`을 명시해야 하며, 모든 렌즈를 확인했다는 이유로 통찰을 지어낼 수 없습니다.

각 기회는 결론을 실제로 바꾼 관점 finding과 reframe을 추적합니다. 계산 가능한 2단계
인과 경로, 하류 효과에 대한 설계 대응, migration·운영 현실, 관측 가능한 반응까지
도달하는 가역적 행동 probe를 기록합니다. 검토 문서를 검증 행동처럼 통과시킬 수
없습니다. 이미 알려진 제품 archetype도 제품에 맞는 인과 근거가 있으면 보존하지만,
프롬프트가 해답 이름 목록을 주지는 않습니다. 제한된 제품 신호에서 스스로 추론해야
합니다.

Mission outcome은 제한된 경험 archive로 공급됩니다. 변경할 수 없는 관측 결과와 이후
해석을 분리합니다. 직접 실패 교훈은 실제 adverse·mixed·failed·blocked outcome을
인용해야 하며 유추나 추론이 직접 경험인 것처럼 주장할 수 없습니다. 모든 교훈에는
guardrail과 전이 한계를 함께 기록합니다.

초기 제품 구조 map은 아직 제한된 context를 모델이 추출한 결과이며 host가 보증한 claim
ledger가 아닙니다. record가 이 경계를 명시하고, 결정을 좌우하는 repository·시장 claim은
commitment 전에 host 또는 사람이 별도로 확인해야 합니다.

## Product Invention

```text
/invent <context>
/inventions
/invent-commit <candidate-id> <human rationale>
```

관습적 baseline을 기록하고 구조적 변화를 탐색한 뒤 겉모양만 새로운 아이디어를
공격합니다. 승자를 구현하지 않고 frontier를 보존합니다. 관측 공백은
`/invent-observations`로 보고 `/invent-observe`로 해소할 수 있습니다.

## Vision Genesis와 Vision Scout

```text
/vision <context>
/vision-scout <context>
/visions
```

Vision Genesis는 욕구, 먼 유추, 메커니즘 융합, 제품 세계와 비평을 탐색합니다.
Vision Scout는 전체 Genesis 전에 founder prompt를 발원하고 거르는 저비용 경로입니다.
승격에는 제한된 사람 또는 행동 증거가 필요하며 delivery 권한은 열리지 않습니다.

```text
/vision-benchmark collection
/vision-benchmark-suite all 3
/vision-scout-benchmark fusion
```

## 범용 Pursuit

```text
/pursue <objective>
/pursuits
```

연구, 분석, 글쓰기를 위한 증거 생산형 knowledge-work graph를 구성합니다. 외부 행동,
출판과 금융 권한은 별도입니다.

## Observation과 Watch

```bash
palamedes observe
palamedes watch --once
```

Observation은 제한된 작업공간 사실을 수집합니다. Watch는 호출·토큰 예산 안에서
변화가 cognition을 정당화하는지 평가합니다. 저장소에 코드가 있거나 모델 confidence가
높다는 사실만으로 사용자 가치가 입증되지는 않습니다.

## Outcome learning

승인된 미션에는 outcome을 기록할 수 있습니다. Outcome 분석은 보고된 결과, 귀속
가설, causal signature와 후속 gate를 분리합니다. 모호하거나 불리한 결과는 조용히
덮어쓰지 않고 다음 승인에 제약을 줍니다.

전체 명령은 대화형 터미널에서 `/help`로 확인하세요.
