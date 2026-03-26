---
name: cloudru-account-setup
description: Create a Cloud.ru service account and API key for Foundation Models. Use when the user needs to register a service account, obtain an API key via the Cloud.ru console, or bootstrap Cloud.ru API access from scratch.
homepage: https://cloud.ru/docs/foundation-models/ug/index
metadata: {"openclaw":{"emoji":"🔑","requires":{"anyBins":["python3","python"]}}}
---

# Cloud.ru Account Setup

## What this skill does

Creates a Cloud.ru service account and Foundation Models API key. After a successful run the user will have `CLOUD_RU_FOUNDATION_MODELS_API_KEY` ready to use.

## When to use

- The user wants to set up Cloud.ru API access from scratch.
- The user needs a new service account or API key for Cloud.ru Foundation Models.
- The user mentions Cloud.ru onboarding, registration, or bootstrap.

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
3. Capture the current browser state and extract the project URL:
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
   python3 {baseDir}/scripts/cloudru_account_bootstrap.py \
     --project-url '<project-url>' \
     --token '<cloudru-browser-token>'
   ```
   Add `--customer-id '<customer-id>'` if the URL does not expose it.
8. Read the JSON result. It contains:
   - the created service account response;
   - the created API key response, including the generated secret.

## Manual or no-browser flow

If the user already has the required values, skip the browser steps and run:

```bash
python3 {baseDir}/scripts/cloudru_account_bootstrap.py \
  --project-url '<project-url>' \
  --project-id '<project-id>' \
  --customer-id '<customer-id>' \
  --token '<cloudru-browser-token>'
```

## Safe handling

- Treat the returned API key as a secret.
- Show it only when the user explicitly needs it.
- Prefer moving it immediately into an env var or OpenClaw secret ref.
- Do not paste the raw key into config files unless the user asked for plaintext.

## What to return after a successful run

1. The created service account ID.
2. The created API key ID.
3. The Foundation Models API key secret, if the user asked to see it.
4. Next step: tell the user they can now use the key with Cloud.ru Foundation Models API.
