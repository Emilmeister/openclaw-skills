# OpenClaw provider setup for Cloud.ru Foundation Models

Use this after you already have `CLOUD_RU_FOUNDATION_MODELS_API_KEY`.

## Option A: onboarding

Interactive path:

1. Run `openclaw onboard`.
2. Choose **Custom Provider**.
3. Set compatibility to **OpenAI-compatible**.
4. Set base URL to `https://foundation-models.api.cloud.ru/v1`.
5. Set the model ID to a live Cloud.ru model ID from `/v1/models`, for example `GigaChat/GigaChat-2-Max`.
6. Paste the API key.

Non-interactive example:

```bash
export CUSTOM_API_KEY="$CLOUD_RU_FOUNDATION_MODELS_API_KEY"
openclaw onboard --non-interactive \
  --auth-choice custom-api-key \
  --custom-base-url "https://foundation-models.api.cloud.ru/v1" \
  --custom-model-id "GigaChat/GigaChat-2-Max" \
  --custom-api-key "$CUSTOM_API_KEY" \
  --custom-compatibility openai
```

## Option B: edit config directly

Example `openclaw.json` fragment:

```json
{
  "env": {
    "CLOUD_RU_FOUNDATION_MODELS_API_KEY": "<set-me>"
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "cloudru-foundation/GigaChat/GigaChat-2-Max"
      }
    }
  },
  "models": {
    "mode": "merge",
    "providers": {
      "cloudru-foundation": {
        "baseUrl": "https://foundation-models.api.cloud.ru/v1",
        "apiKey": "${CLOUD_RU_FOUNDATION_MODELS_API_KEY}",
        "api": "openai-completions",
        "models": [
          {
            "id": "GigaChat/GigaChat-2-Max",
            "name": "GigaChat 2 Max"
          },
          {
            "id": "ai-sage/GigaChat3-10B-A1.8B",
            "name": "GigaChat3-10B-A1.8B"
          }
        ]
      }
    }
  }
}
```

## Notes

- Keep the full Cloud.ru model ID, including the slash.
- If you want more than one Cloud.ru model in OpenClaw, add more items under `models.providers.cloudru-foundation.models`.
- Prefer secret refs or env vars over pasting the raw API key into config.
