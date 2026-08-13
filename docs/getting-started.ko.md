# 시작하기

<p align="center">
  <a href="getting-started.md">English</a> · <strong>한국어</strong>
</p>

## 요구 사항

- Python 3.9 이상
- 로컬 저장소 또는 프로젝트 디렉터리
- Codex CLI, OpenRouter, OpenAI, Anthropic, Gemini 또는 OpenAI-compatible
  로컬·호스팅 endpoint 중 하나

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

## Anthropic 또는 Gemini로 시작

```bash
export ANTHROPIC_API_KEY="..."
palamedes chat --provider anthropic --model claude-sonnet-4-5

export GEMINI_API_KEY="..."
palamedes chat --provider gemini --model gemini-2.5-pro
```

`claude`는 `anthropic`의 alias로 사용할 수 있습니다.

## vLLM, Ollama, LM Studio 또는 compatible endpoint로 시작

Palamedes는 streaming OpenAI Chat Completions endpoint에 연결할 수 있습니다. 로컬
endpoint는 기본적으로 API key를 요구하지 않습니다.

```bash
palamedes chat \
  --provider vllm \
  --model Qwen/Qwen3-32B \
  --provider-base-url http://127.0.0.1:8000/v1
```

인증이 필요한 compatible endpoint에는 secret 값 대신 secret을 보관한 환경변수의
이름만 전달합니다.

```bash
export MY_LLM_KEY="..."
palamedes chat \
  --provider openai-compatible \
  --model my-model \
  --provider-base-url https://llm.example.com/v1 \
  --provider-api-key-env MY_LLM_KEY
```

`vllm`, `ollama`, `lmstudio`는 `openai-compatible`의 alias입니다. 어떤 로컬 서비스가
어떤 port를 사용하는지 Palamedes가 추측하지 않도록 endpoint는 명시적으로 받습니다.
같은 provider option을 `palamedes watch`에서도 사용할 수 있습니다.

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
