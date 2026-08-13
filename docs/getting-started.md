# Getting Started

<p align="center">
  <strong>English</strong> · <a href="getting-started.ko.md">한국어</a>
</p>

## Requirements

- Python 3.9 or newer
- A local repository or project directory
- One provider: Codex CLI, OpenRouter, OpenAI, Anthropic, Gemini, or an
  OpenAI-compatible local/hosted endpoint

## Install

```bash
git clone https://github.com/LEE-Kyungjae/Palamedes.git
cd Palamedes
python3 -m pip install -e .
palamedes init
```

Palamedes stores project state in `.palamedes/`. Commit that directory when you
want planning lineage to travel with the repository.

## Start with Codex authentication

```bash
codex login
palamedes chat --provider codex
```

## Start with OpenRouter

```bash
export OPENROUTER_API_KEY="..."
palamedes chat --provider openrouter
```

Set `PALAMEDES_OPENROUTER_MODEL` to override the default model.

## Start with the OpenAI Responses API

```bash
export OPENAI_API_KEY="..."
palamedes chat --provider openai
```

Set `PALAMEDES_OPENAI_MODEL` to override the default model.

## Start with Anthropic or Gemini

```bash
export ANTHROPIC_API_KEY="..."
palamedes chat --provider anthropic --model claude-sonnet-4-5

export GEMINI_API_KEY="..."
palamedes chat --provider gemini --model gemini-2.5-pro
```

`claude` is accepted as an alias for `anthropic`.

## Start with vLLM, Ollama, LM Studio, or another compatible endpoint

Palamedes accepts any streaming OpenAI Chat Completions endpoint. Local
endpoints do not require a key by default.

```bash
palamedes chat \
  --provider vllm \
  --model Qwen/Qwen3-32B \
  --provider-base-url http://127.0.0.1:8000/v1
```

For a protected or hosted compatible endpoint, keep the secret in an
environment variable and pass only its name:

```bash
export MY_LLM_KEY="..."
palamedes chat \
  --provider openai-compatible \
  --model my-model \
  --provider-base-url https://llm.example.com/v1 \
  --provider-api-key-env MY_LLM_KEY
```

`vllm`, `ollama`, and `lmstudio` are aliases for `openai-compatible`; the
endpoint remains explicit so Palamedes never guesses which local service owns
a port. The same provider flags are available to `palamedes watch`.

## First session

Inside the chat terminal:

```text
/think What product assumption is most likely to be wrong?
/opportunity Find retention, revenue, distribution, and operating opportunities.
/cycle Choose the smallest reversible mission that tests user value.
/approve
```

Palamedes proposes mission state but does not execute implementation work.

## Basic plan-state CLI

```bash
palamedes plan \
  --goal "Choose an evidence-backed direction" \
  --success-metric "Meet the preregistered metric within four weeks" \
  --planning-horizon "4 weeks" \
  --review-cadence "weekly"

palamedes evidence \
  --claim "The problem repeated in user interviews" \
  --source "interviews" \
  --confidence 72 \
  --axis market

palamedes hypothesis \
  --statement "The problem changes purchase behavior" \
  --confidence 55

palamedes show
palamedes qa
palamedes history
```

## Multiple workspaces

```bash
palamedes workspace add my-product /path/to/project
palamedes -w my-product show
palamedes -w /path/to/project chat --provider codex
```

## Verify the checkout

```bash
make check
```

For commands and recovery behavior, continue to
[operations reference](operations-reference.md). For reasoning modes, see
[cognition workflows](cognition-workflows.md).
