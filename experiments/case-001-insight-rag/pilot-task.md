# Frozen Paired Pilot Task

Status: task frozen; condition runs not started

Target repository: `/Users/ze/work/gahyeonbot`

Target revision: `8c40240cf90cb13f6a00c36c9656167acad63df7`

Frozen at: 2026-07-25

## Task shown to both conditions

> Make one Discord voice-assistant turn traceable across audio capture, STT,
> OpenRouter chat, and TTS. A single opaque turn identifier must be created once
> and remain available at every boundary and failure log. Preserve current
> provider readiness and fallback behavior. Do not expose message text, audio,
> credentials, or user-identifying content in the identifier or new logs.

The task deliberately states the required outcome without prescribing MDC,
method parameters, context objects, headers, or a tracing library. The
experiment asks whether a retrieved implementation reference changes that
architectural choice usefully.

## Frozen target files

| File | SHA-256 |
| --- | --- |
| `VoiceAssistantService.java` | `1e082cb7ab4c7775e37002ba367d1a084f475864746605af94bc0aed6c6728d5` |
| `OpenAiTranscriptionProvider.java` | `d1438897062216ff335a497232dc07f13acc3aa795342ab30cc9922858499ec7` |
| `OpenRouterAssistantProvider.java` | `741408c8d940206d1da59f0c72a90a215776ac411cdb0d00d471060c96717508` |
| `AssistantChatProvider.java` | `5c8e6c7bd45b53a8ffc290f767650f6a30c546f1c793bf0e1323c5edfe26d968` |
| `SpeechToTextProvider.java` | `bacb1e0fffedbe389593ec5bddccf00aad5fcf04c7a262793557f8c0ca96e330` |
| `TtsService.java` | `709e16551480b768058f514b84c24f352f8c2f409e776405903b54a8f080e2b4` |
| `TtsProvider.java` | `2cb576982f629a05fc0e9e40f0648ce7ecfe4e8f759f4eb68350fbac8bbad0d2` |

Both conditions may inspect the same target revision. Neither may read later
commits, the other condition's worktree, or this experiment's selected mission
and evaluation notes.

## Conditions

### Control

- fresh coding-agent context;
- frozen task and target repository only;
- no Insight-RAG output and no manually supplied reference repository;
- same model, reasoning level, wall-clock limit, and tool permissions as
  treatment.

### Treatment

- identical fresh context and resource budget;
- one recommendation packet produced by the frozen Insight-RAG revision from
  the exact task above;
- packet must include component paths, typed evidence, limitations, and source
  revision;
- no additional human curation after seeing either condition's output.

If Insight-RAG cannot produce a real repository-backed packet without changing
its frozen code or index, record `treatment_unavailable`; do not substitute a
manually selected reference and call it a treatment.

## Required deliverables from each condition

1. a pre-edit architecture decision;
2. the selected reference or explicit decision to use none;
3. a patch confined to an isolated branch or disposable worktree;
4. focused regression tests;
5. commands and results;
6. known limitations and rollback note;
7. elapsed time, model configuration, token estimate, and human corrections.

## Acceptance properties

The evaluator must check behavior rather than implementation vocabulary:

- one identifier is created per accepted utterance;
- the same identifier reaches STT, chat, and every attempted TTS segment;
- success and failure logs identify the stage and turn without logging content;
- concurrent turns cannot overwrite or exchange identifiers;
- provider interfaces cannot silently drop trace context;
- existing readiness, conversation-history, and TTS fallback behavior remains;
- secrets, transcript text, audio bytes, guild/user IDs, and usernames are not
  newly copied into trace identifiers or diagnostic payloads;
- focused tests fail when a boundary drops or replaces the identifier.

## Review order

1. Strip condition labels and normalize formatting.
2. Judge acceptance-property coverage and causal coherence.
3. Judge severe regressions and privacy leakage.
4. Compare implementation choice and correction burden.
5. Only then reveal whether a recommendation was used.

Novelty and explanation length are not scoring dimensions.

## Predeclared interpretation

- treatment wins only if its reference changes a relevant architectural choice
  and blinded review prefers the resulting action without a resource or safety
  violation;
- equivalent outputs mean this case did not demonstrate decision-changing
  value, even if the recommendation text looks good;
- control victory is evidence against the current Insight-RAG value thesis;
- treatment unavailability is an operational finding, not a quality win or
  loss.
