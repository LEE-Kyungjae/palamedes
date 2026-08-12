# 인지 워크플로

<p align="center">
  <a href="cognition-workflows.md">English</a> · <strong>한국어</strong>
</p>

Palamedes는 발견, 평가, commitment와 실행 권한이 서로 다른 작업이므로 별도의
워크플로를 제공합니다.

## 4역할 cognition cycle

```text
/cycle <context>
```

cycle은 context governor, interpreter, inventor, adversary와 selector를 실행합니다.
후보의 fate를 보존하고 mission draft를 만듭니다. `/approve`는 draft를 저장하고
`/reject <reason>`은 기각을 기록합니다. 안전한 행동이 가능하면 검토 문서보다 작고
가역적인 행동을 우선합니다.

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
없습니다. 구독, 시즌, 배틀패스, 번들, 마켓플레이스처럼 익숙한 패턴도 제품에 맞는
인과 근거가 있으면 보존합니다.

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
