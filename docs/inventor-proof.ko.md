# Inventor 외부 검증 프로토콜

이 프로토콜은 Palamedes가 좋은 글을 만드는지를 평가하지 않는다. 동일한 모델과 네 번의
호출을 사용하는 강한 tournament보다 외부 프로젝트에서 더 유용한 기회를 발원하고,
그 차이가 실제 결정을 거쳐 측정된 결과로 이어지는지를 평가한다.

## 통과 조건

- Palamedes 개발·튜닝에 사용되지 않은 독립 외부 프로젝트 정확히 3개
- 프로젝트마다 서로 다른 외부 owner와 사전 동결된 정보 packet
- `tournament`와 `palamedes` 각각 네 번의 호출
- 출처를 숨긴 뒤 프로젝트마다 confidence 60 이상의 독립 인간 리뷰 3개 이상
- Palamedes가 최소 2개 프로젝트에서 다수 선호
- 결과를 보기 전에 metric, 성공·실패 threshold, 측정 source를 고정
- 세 프로젝트 모두 실제 probe outcome 기록
- 그중 최소 2개에서 Palamedes 선택이 threshold 통과 결과에 귀속

코드, 모델 평가, repository star, 문서 품질은 이 게이트를 대신 통과시킬 수 없다.

## 실행

1. `experiments/inventor-proof-portfolio.example.json`을 복사하고 세 외부 owner와 함께
   placeholder를 채운다. owner는 해답이 아니라 아직 결정하지 못한 문제, 증거 경계,
   실제 probe를 제공한다.
2. 생성 전에 검증하고 run을 동결한다.

```bash
python3 palamedes_inventor_proof.py validate --portfolio <portfolio.json>
python3 palamedes_inventor_proof.py prepare --portfolio <portfolio.json> \
  --run-id inventor-proof-001
```

3. 기존 proof harness로 양쪽 조건을 생성하고 블라인드 packet을 만든다. seed는 리뷰가
   끝날 때까지 공개하지 않는다.

```bash
python3 palamedes_proof.py generate --run experiments/inventor-proof-runs/inventor-proof-001 --condition tournament
python3 palamedes_proof.py generate --run experiments/inventor-proof-runs/inventor-proof-001 --condition palamedes
python3 palamedes_proof.py blind --run experiments/inventor-proof-runs/inventor-proof-001 \
  --comparison-condition tournament --treatment-condition palamedes --seed '<private-random-seed>'
```

4. 각 독립 인간 리뷰어는 `blind/packet.json`만 받고 응답 JSON을 작성한다. 응답은 모든
   case와 rubric score, preference, rationale, decision difference, confidence를 포함해야
   한다. `reviewer_kind=human`, `reviewer_relationship=independent`,
   `origin_visible=false`가 아니면 import가 거부된다.

```bash
python3 palamedes_inventor_proof.py import-review --run <run> --response <review.json>
```

5. owner가 선택한 probe를 실제로 수행한 뒤 원시 evidence와 함께 outcome을 append-once로
   기록한다. `measurement_source`는 사전등록과 정확히 같아야 한다.

```bash
python3 palamedes_inventor_proof.py probe-outcome --run <run> --response <outcome.json>
python3 palamedes_inventor_proof.py score --run <run>
```

`inventor_claim_demonstrated=true`는 이 세 사례에 한정된 반복 외부 증거다. 사람 수준의
창의성, AGI, 보편적 우월성 또는 startup 성공을 의미하지 않는다.

## 재호출 자동 진행

다음 명령은 outreach 스레드를 확인하고 명시적 동의가 허용하는 단계까지만 진행한다.

```bash
python3 palamedes_inventor_operator.py
```

명시적인 긍정 답변에는 intake 양식을 한 번만 게시한다. 완성된 fenced JSON intake가
세 개 모이면 저장소를 얕게 clone하고 portfolio를 동결한 뒤 tournament와 Palamedes를
각 네 번 실행하고 비공개 seed로 블라인딩한다. 이후 독립 reviewer 모집 이슈를 연다.
Blind packet은 모든 owner가 `blind_packet_may_be_published=true`로 동의한 경우에만
공개 Gist로 배포한다. 모호한 답변, 잘못된 intake, 거절은 자동 추정하지 않고 멈춘다.

외부 댓글을 쓰지 않고 상태만 확인하려면 다음을 사용한다.

```bash
python3 palamedes_inventor_operator.py --read-only
```
