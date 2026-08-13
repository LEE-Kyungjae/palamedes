# Palamedes

<p align="center">
  <a href="README.md">English</a> · <strong>한국어</strong>
</p>

<p align="center">
  <img src="assets/palamedes.png" alt="Palamedes" width="100%">
</p>

## 안녕하세요

혹시 vLLM을 사용해 보신 적이 있으신가요? AI 모델을 설치하고 구동하는 엔진에는
큰 병목이 존재합니다. AI의 처리량과 메모리 효율을 개선한 아주 훌륭한 프로젝트가
vLLM입니다. 이제는 여러 AI 개발사의 기반으로 사용되는 이 프로젝트를 누가 처음
만들었는지 아시나요? 한국 개발자입니다.

이처럼 오픈소스 주요 생태계에서 상대적으로 소외되어 왔던 한국 개발자들이 조금씩
영향력을 넓혀 가는 사례가 생겨나고 있습니다. 저 또한 세계에 K-AI 강국을 알리고자
이 오픈소스를 만들어 공개했습니다. 많은 관심 부탁드립니다. ㅎㅎ

Palamedes(팔라메데스)를 아시나요? 그리스·로마 신화에서 트로이 전쟁에 참가하기 싫어
꾀병을 부리던 오디세우스를 간파해 전쟁에 참여시킨 지혜의 영웅입니다. 우리는 아직도
지혜를 갈구하고 있습니다.

대형 AI 서비스들이 등장해 `Plan → Task → Implement`를 담당하며 우리의 많은 노고를
덜어주고 있습니다. 하지만 이런 와중에도 사람은 계속 필요합니다. Google, Amazon과
같은 대기업들은 AX 전환 과정에서 인재들을 방출했지만, 여전히 인간의 판단과 감독이
필요한 영역이 계속 나타나면서 재고용이 이루어지기도 했습니다.

AI가 많은 일을 해주는데 왜 아직도 사람이 필요할까요? AI가 인간과 다르고, 인간의
사고 구조를 흉내 내려 해도 아직 완전히 따라 하지 못했기 때문입니다. 방향성을
제시하고, 의사결정을 내리고, 잘못된 기획을 바로잡으며, AI에게 넓은 시야와 인사이트를
제공하는 일은 아직 해결되지 않은 난제로 남아 있습니다. Palamedes는 이러한 부분을
해소하기 위해 개발되었습니다.

최신 AI 연구를 바탕으로 World Model과 RAG 등의 아이디어에서 영감을 얻어 세상을 보는
감각기관을 만들고, 그 감각기관을 통해 들어온 정보가 편향되어 있지는 않은지
추론합니다. 그리고 AI, 즉 추론기에 필요한 정보와 방향성을 제시합니다. AI의 앞단에서
AI와 소통하며 인간의 개입 없이 더 많은 일을 해낼 수 있는 능력을 부여하는 것이
목표입니다.

이 프로젝트는 AI 시대에 한 번 깊게 읽어볼 만한 프로젝트라고 생각합니다. 아직
채워지지 못한 부분도 많습니다. 직접 토큰을 소모해 체험하고 오류를 보완하며, PR과
적극적인 피드백을 받아 AGI에 한 걸음씩 다가가고자 합니다. 오픈소스 참여를
부탁드립니다.

> **현재 GitHub Star를 하나하나 모아 프로젝트의 관심도를 높이는 일이 절실합니다.
> Star 한 번씩 부탁드립니다!**

> **Palamedes는 실행 에이전트가 구현 방법을 정하기 전에 어떤 미션을 계획할
> 가치가 있는지 판단합니다.**

Palamedes는 오픈소스 로컬 우선 Goal Discovery·Goal Synthesis Engine입니다.
`planner -> task -> implementation`보다 앞에서 중요한 것을 관찰하고, 경쟁 해석을
만들고, 제품·사업 기회를 찾고, 가정을 공격한 뒤 경계가 명확한 미션을 downstream
에이전트에 전달합니다.

방향을 일회성 프롬프트가 아니라 수정 가능한 상태로 다룹니다. 증거, 가설, 관점 변화,
기각한 대안, 반증 조건, outcome과 restore 지점이 저장소에 남습니다.

```text
세계 신호와 레퍼런스
  -> 경쟁 해석
  -> 제품 기회와 후보 미션
  -> 증거, 비평과 반증
  -> 선택된 미션 계약 + non-goal
  -> planner -> task -> implementation
  -> 결과 신호가 Palamedes로 복귀
```

## 현재 상태

**Research Alpha.** Plan-state kernel은 구현되고 폭넓게 테스트됐습니다. 자율
pre-planner는 여전히 반증 가능한 제품 가설입니다.

| 영역 | 상태 |
| --- | --- |
| Revision, restore, fingerprint conflict, QA | 구현됨 |
| Mission cognition과 제한된 handoff | 구현됨 |
| Opportunity, invention, vision, pursuit | 실험적 |
| One-shot baseline보다 나은 검토 미션 | 초기 블라인드 모델 검토 증거 |
| 더 나은 외부 결과 또는 사람 수준 창의성 | 미입증 |

생성된 confidence, retrieval, debate나 novelty를 권한으로 바꾸지 않습니다. Proof 원장,
비용, 실패와 재현 방법은 [증거와 데모](docs/evidence-and-demos.ko.md)를 참고하세요.

## 주요 기능

- 하나의 수정 가능한 계획과 증거, 가설, restore history를 유지합니다.
- 독립적인 해석, 발명, adversarial review와 selector 역할을 실행합니다.
- 리텐션, 수익화, 콘텐츠, 유통, 플랫폼과 위험 기회를 찾습니다.
- 제품에 맞는 인과 근거가 있으면 익숙한 사업 패턴도 보존합니다.
- 관찰, 추론, 가치 판단, commitment와 실행을 분리합니다.
- 반증 조건, non-goal, reversal trigger와 제한된 probe를 만듭니다.
- 실행 에이전트와 통합하되 스스로 delivery 권한을 열지 않습니다.
- correlation을 causation으로 위장하지 않고 outcome을 기록합니다.

## 언제 사용하는가

- AI 구현 속도는 빠르지만 방향이 계속 흔들릴 때
- 여러 제품·연구 방향이 경쟁할 때
- 눈앞의 기능 요청이 더 큰 사업 기회를 숨길 수 있을 때
- 한 방향을 선택·보류·기각할 검토 가능한 이유가 필요할 때
- 구현 자체가 증거를 만들어야 할 때

Palamedes는 범용 실행 runtime, 자동 배포 도구, 창의성이나 사업 성공 보장 도구가
아닙니다. 승인, credential, side effect와 delivery 권한은 사람과 host가 유지합니다.

## 빠른 시작

Python 3.9 이상과 Codex CLI, OpenRouter 또는 OpenAI API key가 필요합니다.

```bash
git clone https://github.com/LEE-Kyungjae/Palamedes.git
cd Palamedes
python3 -m pip install -e .
palamedes init
codex login
palamedes chat --provider codex
```

대화형 터미널에서:

```text
/think 어떤 제품 가정이 가장 틀렸을 가능성이 높은가?
/opportunity 리텐션, 수익, 유통과 운영 기회를 찾아라.
/cycle 사용자 가치를 검증하는 가장 작은 가역적 미션을 선택하라.
/approve
```

OpenRouter, OpenAI, 작업공간 선택과 plan-state CLI는
[시작하기](docs/getting-started.ko.md)를 참고하세요.

## 핵심 워크플로

| 목적 | 명령 |
| --- | --- |
| 경쟁 해석 탐색 | `/think <topic>` |
| 다관점 제품 기회 발견 | `/opportunity <context>` |
| 제한된 미션 발원과 선택 | `/cycle <context>` |
| GitNexus 교차 도메인 근거를 포함한 분리형 제품 발명 | `/cycle --mode product <context>` |
| 구조적 제품 발명 탐색 | `/invent <context>` |
| 제품 세계 발원 | `/vision <context>` |
| 저비용 founder-prompt 탐색 | `/vision-scout <context>` |
| 증거 생산형 지식 작업 | `/pursue <objective>` |
| 저장소 현실 관찰 | `palamedes observe` |
| 변화 기반 제한 cognition | `palamedes watch --once` |

워크플로별 권한 경계는 [인지 워크플로](docs/cognition-workflows.ko.md)를
참고하세요. 제품 cycle의 architecture analogist에는 raw reference 검색 결과가 아니라
host validator를 통과한 transfer mapping만 전달됩니다. 미해결 전문 승인은 범용
`/approve` 명령으로 충족할 수 없습니다.

## 구조

```text
Palamedes plan state
  ├─ 증거와 가설
  ├─ 경쟁 관점과 결정
  ├─ 미션, probe, outcome과 gate
  ├─ revision, fingerprint와 restore
  └─ CLI / HTTP / Python client / agent adapter

Execution host
  ├─ credential과 process lifecycle
  ├─ 구현과 side effect
  └─ 관찰 가능한 outcome을 Palamedes에 반환
```

안정성과 실험적 표면은 [STABILITY.md](STABILITY.md), 계약 변경 정책은
[CONTRACT_VERSIONING.md](CONTRACT_VERSIONING.md)를 참고하세요.

## 문서

| 문서 | 내용 |
| --- | --- |
| [제품 개요](docs/product-overview.ko.md) | 목적, 구조, 경계, 상태 모델, 원칙 |
| [증거와 데모](docs/evidence-and-demos.ko.md) | Proof 원장, 비용, 실패, 데모, 재현 |
| [시작하기](docs/getting-started.ko.md) | 설치, provider, 첫 세션, 작업공간 |
| [인지 워크플로](docs/cognition-workflows.ko.md) | Cycle, Opportunity, Invention, Vision, Pursuit, Watch |
| [통합](docs/integrations.ko.md) | HTTP, Python client, agent host, adapter |
| [운영 레퍼런스](docs/operations-reference.ko.md) | CLI, 동시성, restore, storage, 검증 |

추가 문서:

- [Pre-planner contract](docs/palamedes-pre-planner-contract.md)
- [AgentScope 통합](docs/integration-agentscope.md)
- [Reference agent pattern](docs/reference-agent-patterns.md)
- [Proof 프로그램](experiments/PROOF.md)
- [기여 가이드](CONTRIBUTING.md)

영문·한국어 개요 문서는 같은 섹션 구조, 명령, 사실 주장과 안전 경계를 유지합니다.

## 개발

```bash
make check
```

개별 target은 `make compile`, `make test`, `make scaffold-test`,
`make schema-check`, `make package-check`입니다.

## 라이선스

Palamedes는 [MIT License](LICENSE)로 배포되는 오픈소스 소프트웨어입니다. 라이선스
조건에 따라 사용·복사·수정·병합·공개·배포·재허가하거나 판매할 수 있습니다.
복사본 또는 실질적인 일부에는 저작권 고지와 허가 고지를 포함해야 합니다.

Copyright (c) 2026 LEE Kyungjae.

## Star History

<a href="https://www.star-history.com/?repos=LEE-Kyungjae%2FPalamedes&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=LEE-Kyungjae/Palamedes&type=date&theme=dark&legend=top-left&sealed_token=U33QpKO_oklxBeuwOfEdD2Gmq-HJhb3IRggfqJjLvFbMCBcmMBC_xBJ1IbS5ewZAaCVBGrfDsfsVMvhp_-pKkFZmOIP10VTsbZZ74hIC2PQNEsZuL0Yko7Te7mGMTzosQ8TKrC0YAjqm4Qktj29JiWxxuVfFoilk-USU7M8FkvUL-3LFgWcL0BH8wTjx" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=LEE-Kyungjae/Palamedes&type=date&legend=top-left&sealed_token=U33QpKO_oklxBeuwOfEdD2Gmq-HJhb3IRggfqJjLvFbMCBcmMBC_xBJ1IbS5ewZAaCVBGrfDsfsVMvhp_-pKkFZmOIP10VTsbZZ74hIC2PQNEsZuL0Yko7Te7mGMTzosQ8TKrC0YAjqm4Qktj29JiWxxuVfFoilk-USU7M8FkvUL-3LFgWcL0BH8wTjx" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=LEE-Kyungjae/Palamedes&type=date&legend=top-left&sealed_token=U33QpKO_oklxBeuwOfEdD2Gmq-HJhb3IRggfqJjLvFbMCBcmMBC_xBJ1IbS5ewZAaCVBGrfDsfsVMvhp_-pKkFZmOIP10VTsbZZ74hIC2PQNEsZuL0Yko7Te7mGMTzosQ8TKrC0YAjqm4Qktj29JiWxxuVfFoilk-USU7M8FkvUL-3LFgWcL0BH8wTjx" />
 </picture>
</a>
