# 증거와 데모

<p align="center">
  <a href="evidence-and-demos.md">English</a> · <strong>한국어</strong>
</p>

Palamedes는 research alpha 단계입니다. 계약과 저장 동작은 폭넓게 검증됐지만 외부
의사결정을 개선한다는 주장은 아직 반증 가능한 제품 가설입니다.

## 증거 원장

| 주장 | 현재 증거 | 한계 |
| --- | --- | --- |
| revision 가능한 plan-state kernel이 작동한다 | revision, restore, fingerprint conflict, QA, conformance 테스트 | 더 나은 미션을 증명하지 않음 |
| 약한 reference treatment를 거부할 수 있다 | 첫 cross-repository packet을 명시적 이유로 차단 | 성공적인 차단은 생성 우위를 증명하지 않음 |
| 블라인드 검토에서 one-shot baseline보다 선호될 수 있다 | `proof-002`에서 모델 검토 9표 중 8표와 세 case 다수 획득 | 독립적인 사람·행동 결과 증거가 아님 |
| 더 깊은 cognition이 검토 품질을 높일 수 있다 | `proof-003`이 블라인드 비교와 비용을 기록 | 일반성과 downstream 효과는 미검증 |
| 사람 수준 창의성 또는 startup 성공 | 입증되지 않음 | 이런 주장을 허용하지 않음 |

## 비용과 귀속

첫 비교에서 Palamedes는 baseline보다 상당히 많은 입력 토큰을 사용했습니다. 따라서
호출과 토큰 비대칭을 공개하며 품질 선호를 비용 조정 우위로 바꾸지 않습니다. artifact
품질, 구현 결정, 수혜자 결과와 owner 노동도 서로 분리합니다.

## 실제 프로젝트 데모

윷 프로젝트는 역량과 실패 처리를 함께 보여줍니다. Palamedes가 제품 방향을 만들고
검토했지만 구현된 로컬 게임은 원래의 온라인 멀티플레이 의도에서 벗어났습니다. 이를
성공으로 다시 쓰지 않고 boundary failure 증거로 보존합니다.

![윷 게임플레이 데모](../assets/demo/yut-gameplay-demo.jpg)

[게임플레이 영상 보기](../assets/demo/yut-gameplay-demo.mp4)

## Vision 증거

Vision Genesis와 Vision Scout는 사람의 기획을 숨긴 case로 모델이 먼저 유용한 founder
prompt를 발원할 수 있는지 평가합니다. trial별 기억을 격리하고 완성안 평가와 발원
평가를 분리합니다. machine pass는 사람 검토만 열 수 있으며 delivery 권한이나 사람
수준 창의성을 증명하지 않습니다.

[Vision Genesis 실기록](vision-genesis-live-001.md)과
[인지 워크플로](cognition-workflows.ko.md)의 benchmark 명령을 참고하세요.

## 재현 경로

- [Proof 프로그램](../experiments/PROOF.md)
- [Proof portfolio](../experiments/proof-portfolio.json)
- [비용 portfolio](../experiments/proof-cost-portfolio.json)
- [첫 cross-repository 사전등록](../experiments/case-001-insight-rag/preregistration.md)
- [Cycle 401](implementation/empirical-cycles/cycle-401.md)
- [Inquiry 역사](inquiry/2026-07-25-origin-and-evolution.md)

모든 결과는 `주장 -> 증거 -> 한계 -> 다음 판별 관측`으로 읽어야 합니다. 생성된
confidence, debate, retrieval과 novelty 점수는 기록됐다는 이유만으로 독립 증거가
되지 않습니다.
