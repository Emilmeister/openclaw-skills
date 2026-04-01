---
name: cloudru-account-setup
description: Create a Cloud.ru service account, Foundation Models API key, and IAM access key (CP_CONSOLE_KEY_ID/CP_CONSOLE_SECRET). Use when the user needs to register a service account, obtain API credentials via the Cloud.ru console, or bootstrap Cloud.ru API access from scratch.
homepage: https://cloud.ru/docs/foundation-models/ug/index
metadata: {"openclaw":{"emoji":"🔑","requires":{"anyBins":["python3","python"]}}}
---

# Cloud.ru Account Setup

## What this skill does

Creates a Cloud.ru service account and the credentials needed for Cloud.ru services:
1. **Foundation Models API key** (`CLOUD_RU_FOUNDATION_MODELS_API_KEY`) — for the Foundation Models API.
2. **IAM access key** (`CP_CONSOLE_KEY_ID` + `CP_CONSOLE_SECRET`) — for IAM token-based authentication used by ML Inference and other Cloud.ru services.

After a successful run the user will have all credentials ready to use.

## When to use

- The user wants to set up Cloud.ru API access from scratch.
- The user needs a new service account or API key for Cloud.ru Foundation Models.
- The user needs `CP_CONSOLE_KEY_ID` and `CP_CONSOLE_SECRET` for ML Inference or other IAM-authenticated services.
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

## Access key creation (CP_CONSOLE_KEY_ID / CP_CONSOLE_SECRET)

The bootstrap script also creates an **access key** for IAM authentication. This is a separate credential from the Foundation Models API key.

The access key is created via:
```
POST /u-api/bff-console/v1/service-accounts/{service_account_id}/access_keys
Body: {"description": "<description>", "ttl": <days>}
```

The response contains:
- `key_id` — use as `CP_CONSOLE_KEY_ID`
- `secret` — use as `CP_CONSOLE_SECRET`
- `expired_at` — expiration timestamp

These credentials are used for IAM token-based authentication (`IAM_Auth` from `http-client-auth`), which is required by ML Inference and other Cloud.ru services that authenticate via `https://iam.api.cloud.ru/`.

To skip access key creation (e.g. if the user only needs Foundation Models), pass `--skip-access-key`.

To customize the access key, use:
- `--access-key-description` (default: `ml-inference-access-key`)
- `--access-key-ttl` (default: 30 days)

## Safe handling

- Treat the returned API key and access key as secrets.
- Show them only when the user explicitly needs them.
- Prefer moving them immediately into env vars or OpenClaw secret refs.
- Do not paste raw keys into config files unless the user asked for plaintext.

## What to return after a successful run

1. The created service account ID.
2. The Foundation Models API key ID and secret (for `CLOUD_RU_FOUNDATION_MODELS_API_KEY`).
3. The IAM access key credentials (for `CP_CONSOLE_KEY_ID` and `CP_CONSOLE_SECRET`).
4. The project ID (for `PROJECT_ID`).
5. A summary of which env vars to set:
   ```
   export CLOUD_RU_FOUNDATION_MODELS_API_KEY=<api_key_secret>
   export CP_CONSOLE_KEY_ID=<access_key_key_id>
   export CP_CONSOLE_SECRET=<access_key_secret>
   export PROJECT_ID=<project_id>
   ```
6. Next step: tell the user they can now use Cloud.ru Foundation Models and ML Inference.
