---
name: cloudru-foundation-models
description: Work with Cloud.ru Evolution Foundation Models via the OpenAI-compatible API. Use when the user wants to call Cloud.ru models, list available models, generate cURL or Python examples, or configure OpenClaw to use Cloud.ru as a custom model provider.
homepage: https://cloud.ru/docs/foundation-models/ug/index
metadata: {"openclaw":{"emoji":"☁️","requires":{"env":["CLOUD_RU_FOUNDATION_MODELS_API_KEY"]},"primaryEnv":"CLOUD_RU_FOUNDATION_MODELS_API_KEY"}}
---

# Cloud.ru Foundation Models

## What this skill does

Helps the user work with the Cloud.ru Foundation Models API:
1. list available models from `https://foundation-models.api.cloud.ru/v1/models`;
2. produce cURL and Python examples for chat completions;
3. configure OpenClaw to use Cloud.ru as a custom model provider.

## Important

Do NOT switch your own model provider to Cloud.ru unless the user explicitly asks you to. This skill is for helping the user work with Cloud.ru models, not for reconfiguring yourself.

## When to use

- The user wants to call Cloud.ru Foundation Models via API or code.
- The user asks how to list Cloud.ru models.
- The user wants to set up OpenClaw with Cloud.ru as a provider.
- The user mentions Cloud.ru Foundation Models or similar model names.

## Prerequisites

The user must have `CLOUD_RU_FOUNDATION_MODELS_API_KEY` set. If the key is missing, direct the user to the `cloudru-account-setup` skill first.

## How to use

1. Read `{baseDir}/references/api-usage.md` for cURL and Python examples.
2. Read `{baseDir}/references/openclaw-provider-setup.md` when the user wants OpenClaw configured to use Cloud.ru as a model provider.
3. Prefer fetching the live model catalog from `/v1/models` instead of hard-coding model IDs.
4. Model IDs can contain `/` — keep the full ID unchanged.

## What to return

- cURL or Python examples tailored to the user's request.
- OpenClaw provider config snippet or `openclaw onboard` command when asked.
- Current model IDs from the live catalog when relevant.

## Limitations

- Do not log or expose API keys in responses.
- Do not execute API calls with untrusted user input without validation.
