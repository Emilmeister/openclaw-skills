---
name: cloudru-foundation-models
description: Connect OpenClaw and other OpenAI-compatible clients to Cloud.ru Evolution Foundation Models. Use when you need to bootstrap Cloud.ru Foundation Models access through the Cloud.ru console, create a service account and API key, list available models from https://foundation-models.api.cloud.ru/v1/models, or generate OpenClaw custom-provider config for Cloud.ru.
homepage: https://cloud.ru/docs/foundation-models/ug/index
metadata: { "openclaw": { "emoji": "☁️", "requires": { "anyBins": ["python3", "python"] }, "primaryEnv": "CLOUD_RU_FOUNDATION_MODELS_API_KEY" } }
---

# Cloud.ru Foundation Models

## What this skill does

Use this skill to:
1. bootstrap a Cloud.ru Foundation Models API key from the Cloud.ru web console;
2. create the required Cloud.ru service account and API key;
3. fetch the live model catalog from `https://foundation-models.api.cloud.ru/v1/models`;
4. produce OpenAI-compatible cURL or Python examples;
5. produce an OpenClaw custom-provider snippet or onboarding command.

## Prefer browser-assisted onboarding

When browser control is available, prefer the browser tool or the equivalent `openclaw browser ...` commands.

If browser control is unavailable, ask the user for one of these:
- an already-created Cloud.ru Foundation Models API key; or
- the current Cloud.ru project URL, plus the Cloud.ru console bearer token retrieved from the browser.

## Browser-assisted onboarding flow

1. Open the Cloud.ru login page:
   ```bash
   openclaw browser open https://console.cloud.ru/static-page/login-destination
   ```
2. Ask the user to log in and open the target project in the Cloud.ru console.
3. Capture the current browser state as JSON and extract the current project URL:
   ```bash
   openclaw browser evaluate --fn 'window.location.href'
   ```
4. Extract `project_id` from the URL.
   - The user-supplied flow also refers to `secret_id`.
   - The service-account API needs `customerId`.
   - Treat `secret_id` as an alias for `customerId` when it is present in the URL.
   - If `customerId` cannot be inferred, ask the user for it explicitly and pass `--customer-id` to the script.
5. Extract the Cloud.ru browser token:
   ```bash
   openclaw browser evaluate --fn 'JSON.parse(localStorage["oidc.user:https://id.cloud.ru/auth/system/:e95a1db5-a61c-425b-ae62-26d3a7e224f7"])["access_token"]'
   ```
6. If the hard-coded storage key is absent, inspect local storage and find the key that starts with `oidc.user:https://id.cloud.ru/auth/system/`, then parse `access_token` from that JSON value.
7. Run the bundled bootstrap script:
   ```bash
   python3 {baseDir}/scripts/cloudru_foundation_models_bootstrap.py \
     --project-url '<project-url>' \
     --token '<cloudru-browser-token>'
   ```
   Add `--customer-id '<customer-id>'` if the URL does not expose it.
8. Read the JSON result. It contains:
   - the created service account response;
   - the created API key response, including the generated secret;
   - the live model list;
   - an OpenClaw provider snippet and onboarding command.

## Manual or no-browser flow

If the user already has the required values, skip the browser steps and run:

```bash
python3 {baseDir}/scripts/cloudru_foundation_models_bootstrap.py \
  --project-url '<project-url>' \
  --project-id '<project-id>' \
  --customer-id '<customer-id>' \
  --token '<cloudru-browser-token>'
```

If the user already has `CLOUD_RU_FOUNDATION_MODELS_API_KEY`, skip the bootstrap flow and use the references below to generate examples or OpenClaw config.

## Safe handling

- Treat the returned API key as a secret.
- Show it only when the user explicitly needs it.
- Prefer moving it immediately into an env var or OpenClaw secret ref.
- Do not paste the raw key into config files unless the user asked for plaintext.

## What to return after a successful run

1. the created service account ID;
2. the created API key ID;
3. the Foundation Models API key secret, if the user asked to see it;
4. the current model IDs;
5. one minimal cURL example;
6. one minimal OpenAI SDK example;
7. one OpenClaw custom-provider snippet or `openclaw onboard` command.

## References

- Read `references/api-usage.md` for cURL and Python examples.
- Read `references/openclaw-provider-setup.md` when the user wants OpenClaw configured to use Cloud.ru as a model provider.
