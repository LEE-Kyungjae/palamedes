# Product cognition v3 handoff — 2026-08-13

## 목표

Palamedes가 단순히 코드를 더 잘 작성하거나 일반적인 시니어 코드 리뷰를 하는 데서
멈추지 않고, 사용자가 직접 말하지 않은 제품·사업 기회를 발견하도록 만든다.

대표 수용 사례는 다음 두 가지다.

1. 반복 플레이, 콘텐츠 주기, 외형 보상, 세션 간 진행 부재 같은 신호를 보고
   `배틀패스`라는 답을 프롬프트에 노출하지 않은 채 선택적 반복 진행·수익 루프를
   가설로 세우고, 인과관계·운영 부담·가드레일·가역적 검증까지 제안한다.
2. 현재 제품과 주제가 다른 오픈소스 저장소에서 복구, 멱등성, 원장, 체크포인트,
   권한 분리 같은 구조적 메커니즘을 찾아 대상 제품의 압력에 맞게 변형하되,
   코드나 결론을 그대로 복사하지 않고 적용 한계와 반증 조건을 함께 제시한다.

## 완료한 작업

### 이미 원격에 반영된 체크포인트

- `771e62c Add partitioned product cognition and architecture transfer`
- `3f761b8 Harden product cognition evidence and governance`

주요 구현 내용:

- 제품 기회 발명가, 교차 도메인 아키텍처 유추자, 실패 경험 운영자를 서로 격리된
  partition으로 실행한다.
- 후보를 freeze한 뒤 출처가 가려진 adversary가 검토하고, selector가 원문 후보를
  변형하지 못하게 한다. 최종 draft는 host가 발행한다.
- evidence bundle v2와 host-owned mission claim ledger를 도입했다. 모델이 작성한
  `observed_signal`을 호스트가 검증한 증거처럼 세탁할 수 없다.
- GitNexus 근거는 revision, 파일, 줄 범위, excerpt를 다시 검증한다. 아키텍처 전이는
  `source pressure → mechanism → target pressure → adaptation → limits`의 완전한 계약과
  정확한 excerpt anchor를 가져야 한다.
- 가격, 보상, 출시 등 전문 권한 gate는 일반 `/approve`로 해제되지 않는다.
- product-v3 resume은 provider/model과 frozen evidence custody를 보존한다.
- 아키텍처 준비 호출과 실패한 유료 호출도 budget/usage에 포함한다.
- 정답을 하드코딩한 정적 fixture는 의미 능력의 acceptance test가 아님을 명시하고
  이름을 `product_cognition_contract_fixture`로 바꿨다.

### 이 체크포인트에서 추가한 방어

- 성공 outcome을 변조된 `direct_failure_ids`에 넣어 실패 경험의 권위를 얻는 경로를
  차단했다. allowlist는 구조화된 outcome에서 호스트가 다시 계산하며 partition도
  독립적으로 adverse 상태를 확인한다.
- 현재 knowledge store에는 exact claim을 원 관측에 묶는 독립적인 host attestation이
  없으므로, 저장된 knowledge의 자기선언 `claim_type`, `evidence_layer`, custody만으로
  mission evidence가 되지 않게 했다. 현재 knowledge는 안전하게 advisory로 취급한다.
- v3의 직접 JSON API가 version/authority만 붙인 축약 아키텍처 mapping을 검증된 전이로
  받아들이지 않게 했다. 완전한 v2 필드, source support, snapshot binding, target scope,
  mutation fingerprint를 요구한다. 이 공개 SHA fingerprint는 무결성 검사이지 출처
  인증 서명이 아님을 코드와 계약에 명시했다.

## 실제 smoke에서 확인한 것

정답 어휘(`battle`, `season pass`, `paid track` 등)를 inventor-visible 입력에서 제거한
게임 fixture로 live Codex smoke를 돌렸을 때 `Cross-Mode Legacy Chronicle` 계열의
비경쟁적 계정 진행 루프를 스스로 제안했다.

- 지속 milestone → 계정 정체성 → 재방문·cross-mode 플레이 → 선택적 외형 가치/수익
- 이벤트 dedup, 목표/아이템 제작 주기, 공정성 및 고객지원 부담
- 무료·가역적 cohort probe, falsifier, rollback, 권한 사전조건
- blind adversary는 후보를 qualified로 판정했다.

GitNexus live smoke에서는 서로 다른 저장소의 멱등성·복구 메커니즘을 가져와
실험 버전/계정/목표/매치 이벤트를 키로 쓰는 폐기 가능한 shadow ledger와
duplicate/crash replay probe로 변형했다. 또한 이 구조가 수요, 가격, 유지율을
증명하지 않는다는 transfer limit을 보존했다.

이 결과는 목표 방향의 능력이 생겼다는 강한 신호지만, 독립적인 사람의 holdout 평가가
없으므로 제품 수준의 의미 품질이 완전히 검증됐다고 주장하지 않는다.

## 반드시 보존할 불변식

1. inventor-visible prompt나 fixture에 원하는 해답 어휘를 넣지 않는다.
2. generic Git/workspace metadata만으로 제품 수요·매출 claim을 발행하지 않는다.
3. 모델 문장을 evidence claim으로 복사하지 않는다. host claim ledger 원문만 사용한다.
4. raw GitNexus 검색 hit는 검증된 transfer mapping이 아니다.
5. 아키텍처 전이는 주제 유사성이 아니라 압력·메커니즘·변형·한계로 연결한다.
6. specialized authority gate는 일반 승인으로 해제하지 않는다.
7. 정적 fixture 통과를 자율적 의미 추론 성공으로 부르지 않는다.
8. 모든 유료 호출과 실패 호출을 budget에 포함한다.

## 종료 전 검증 결과

이 문서를 포함한 최종 작업 트리에서 다음을 확인했다.

- product cognition/architecture/evidence 정적 회귀: `79 passed`
- chat/knowledge 통합 회귀: `122 passed`
- `make test`: 신규 계약군 `109 passed`, core `1564 passed`
- `make compile`: 통과
- 변경 파일 Ruff 검사: 통과
- `git diff --check`: 통과
- GitNexus 손상된 FTS cache를 삭제하고 전체 재분석: 통과
  (`45,350 nodes`, `134,818 edges`, `186 clusters`, `300 flows`)

테스트 통과는 계약·라우팅·custody의 회귀 방지를 뜻한다. 모델의 자율적인 의미 품질은
위 live smoke와 앞으로 수행할 positive/negative holdout 평가로 별도로 판단해야 한다.

## 남은 일

우선순위 순서:

1. 숨겨진 positive fixture와 같은 형식의 negative control을 live provider로 함께 평가한다.
   negative control은 반복 사용, 콘텐츠 cadence, entitlement 신호가 없어야 하며 recurring
   progression 답을 상투적으로 내면 실패다.
2. selector prompt 수정 뒤, qualified 제품 후보가 실제 `commit`까지 이어지는 live run을
   다시 캡처한다. 이전 run은 제품 viability와 bounded probe viability를 혼동해 defer했다.
3. 외부 사람 또는 분리된 holdout judge가 기회 발견, 인과 깊이, 운영 현실성,
   반증 가능성, genericness를 평가하게 한다.
4. knowledge claim을 다시 mission-citable로 승격하려면 exact claim과 원 관측을 묶는
   host-owned attestation store/validator를 새로 설계한다. 그 전에는 advisory가 맞다.
5. 아키텍처 integrity envelope는 변조 탐지이지 인증이 아니다. 직접 API가 완전한
   untrusted boundary가 되어야 한다면 opaque host capability 또는 ingest 시 Git 재검증을
   요구한다.

## 다음 세션 시작 절차

```bash
cd /Users/ze/work/palamedes
git pull --ff-only
git status --short
git log -3 --oneline
sed -n '1,260p' docs/inquiry/2026-08-13-product-cognition-handoff.md
node .gitnexus/run.cjs status
```

그 다음 검증:

```bash
python3 -m pytest -q \
  tests/test_palamedes_architecture_transfer.py \
  tests/test_palamedes_evidence_bundle.py \
  tests/test_palamedes_cognition_v3.py \
  tests/test_palamedes_product_cognition_contract_fixture.py
python3 -m pytest -q tests/test_palamedes_chat.py tests/test_palamedes_knowledge.py
make test
make compile
python3 -m ruff check \
  palamedes_architecture_transfer.py \
  palamedes_cognition_v3.py \
  palamedes_evidence_bundle.py \
  tests/test_palamedes_architecture_transfer.py \
  tests/test_palamedes_cognition_v3.py \
  tests/test_palamedes_evidence_bundle.py
git diff --check
```

복사해서 사용할 재개 요청:

> `docs/inquiry/2026-08-13-product-cognition-handoff.md`를 먼저 읽고 남은 일부터 이어가라.
> 목표는 코드 리뷰가 아니라, 말하지 않은 제품·사업 기회 발견과 무관한 오픈소스의
> 구조적 메커니즘 전이다. 먼저 HEAD와 테스트를 확인하고, 답 어휘가 없는 positive 및
> negative live semantic eval을 수행하라. 정적 contract fixture를 의미 평가로 오인하지
> 말고, 완료 후 GitNexus를 재인덱싱하고 커밋·푸시하라.
