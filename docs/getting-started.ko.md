# 시작하기

<p align="center">
  <a href="getting-started.md">English</a> · <strong>한국어</strong>
</p>

## 요구 사항

- Python 3.9 이상
- 로컬 저장소 또는 프로젝트 디렉터리
- Codex CLI, OpenRouter, OpenAI API 중 하나

## 설치

```bash
git clone https://github.com/LEE-Kyungjae/Palamedes.git
cd Palamedes
python3 -m pip install -e .
palamedes init
```

프로젝트 상태는 `.palamedes/`에 저장됩니다. 계획 계보를 저장소와 함께 공유하려면 이
디렉터리를 commit하세요.

## Codex 인증으로 시작

```bash
codex login
palamedes chat --provider codex
```

## OpenRouter로 시작

```bash
export OPENROUTER_API_KEY="..."
palamedes chat --provider openrouter
```

기본 모델은 `PALAMEDES_OPENROUTER_MODEL`로 변경할 수 있습니다.

## OpenAI Responses API로 시작

```bash
export OPENAI_API_KEY="..."
palamedes chat --provider openai
```

기본 모델은 `PALAMEDES_OPENAI_MODEL`로 변경할 수 있습니다.

## 첫 세션

대화형 터미널에서 다음을 실행합니다.

```text
/think 어떤 제품 가정이 가장 틀렸을 가능성이 높은가?
/opportunity 리텐션, 수익, 유통과 운영 기회를 찾아라.
/cycle 사용자 가치를 검증하는 가장 작은 가역적 미션을 선택하라.
/approve
```

Palamedes는 미션 상태를 제안하지만 구현 작업을 실행하지 않습니다.

## 기본 plan-state CLI

```bash
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
  --statement "이 문제가 구매 행동을 바꾼다" \
  --confidence 55

palamedes show
palamedes qa
palamedes history
```

## 여러 작업공간

```bash
palamedes workspace add my-product /path/to/project
palamedes -w my-product show
palamedes -w /path/to/project chat --provider codex
```

## checkout 검증

```bash
make check
```

명령과 복구 동작은 [운영 레퍼런스](operations-reference.ko.md), 사고 경로는
[인지 워크플로](cognition-workflows.ko.md)를 참고하세요.
