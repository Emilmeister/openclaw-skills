---
name: cloudru-ml-inference
description: Manage Cloud.ru ML Inference model runs — browse the predefined model catalog, deploy models with one command, manage lifecycle, and call inference endpoints. Full CRUD and inference via the inference-clients Python SDK.
homepage: https://cloud.ru/docs/ml-platform/mlspace/concepts/inference/about-inference.html
metadata: {"openclaw":{"emoji":"🤖","requires":{"bins":["python3"],"env":["CP_CONSOLE_KEY_ID","CP_CONSOLE_SECRET","PROJECT_ID"]}}}
---

# Cloud.ru ML Inference

## What this skill does

Manages ML model deployments (Model Runs) on Cloud.ru ML Inference service. Supports:
- Predefined model catalog (browse, search, deploy with exact configs — no guessing)
- Full CRUD on model runs (create, list, get details, update, delete)
- Lifecycle operations (suspend, resume)
- Inference calls to running models (text generation, embeddings, rerank)
- Quota and runtime template queries
- Health checks (ping) for deployed models

## When to use

Use this skill when the user:
- wants to deploy or manage ML models on Cloud.ru ML Inference
- asks about Model RUN or Docker RUN on Cloud.ru
- wants to see what models are available in the Cloud.ru catalog
- needs to create, list, update, delete, suspend, or resume inference endpoints
- wants to call a deployed model for text generation, embeddings, or reranking
- asks about GPU quotas or available frameworks on Cloud.ru ML Inference

## Prerequisites

The user must have these environment variables set:
- `CP_CONSOLE_KEY_ID` — Cloud.ru console service account key ID
- `CP_CONSOLE_SECRET` — Cloud.ru console service account secret
- `PROJECT_ID` — Cloud.ru project UUID

If credentials are missing, direct the user to the `cloudru-account-setup` skill.

The `inference-clients` Python package and its dependencies must be installed. If not, run:
```bash
pip install \
    --index-url https://pkg.sbercloud.tech/artifactory/api/pypi/aicloud-pypi/simple \
    --extra-index-url https://pkg.sbercloud.tech/artifactory/api/pypi/sc-tt-pypi/simple \
    --extra-index-url https://pkg.sbercloud.tech/artifactory/api/pypi/proxies-pypi/simple \
    inference-clients http_client_retries evoapp-common evoapp-http-clients

pip install \
    --index-url https://pkg.sbercloud.tech/artifactory/api/pypi/sc-tt-pypi/simple \
    --no-deps --force-reinstall pydantic-extensions

pip install pydantic-settings
```

## How to use

1. Read `{baseDir}/references/api-reference.md` for the full API surface, enums, and data models.
2. Read `{baseDir}/references/examples.md` for ready-to-use Python code examples.
3. Use `{baseDir}/scripts/ml_inference.py` as the main script — it supports all operations via CLI subcommands.

### Deploying models (recommended flow)

Always prefer deploying from the predefined catalog — it uses exact, tested configurations:

```bash
# 1. Browse the catalog
python {baseDir}/scripts/ml_inference.py catalog

# 2. See detailed configs for a model
python {baseDir}/scripts/ml_inference.py catalog-detail <model_card_id>

# 3. Deploy it
python {baseDir}/scripts/ml_inference.py deploy <model_card_id> --name "my-model"
```

The `deploy` command fetches the exact GPU type, memory, framework version, serving options, and scaling from the catalog — nothing to guess or configure manually.

### Managing model runs

```bash
# List all model runs
python {baseDir}/scripts/ml_inference.py list

# Get model run details
python {baseDir}/scripts/ml_inference.py get <model_run_id>

# Delete a model run
python {baseDir}/scripts/ml_inference.py delete <model_run_id>

# Suspend / Resume
python {baseDir}/scripts/ml_inference.py suspend <model_run_id>
python {baseDir}/scripts/ml_inference.py resume <model_run_id>

# Get event history
python {baseDir}/scripts/ml_inference.py history <model_run_id>
```

### Calling deployed models

```bash
# Chat (OpenAI-compatible)
python {baseDir}/scripts/ml_inference.py call <model_run_id> \
    --prompt "Why is the sky blue?"

# Embeddings
python {baseDir}/scripts/ml_inference.py embed <model_run_id> \
    --texts "Hello world" "Another text"

# Rerank
python {baseDir}/scripts/ml_inference.py rerank <model_run_id> \
    --query "machine learning" --documents "ML is AI" "Weather is nice"

# Health check
python {baseDir}/scripts/ml_inference.py ping <model_run_id>
```

### Infrastructure queries

```bash
# GPU/CPU quota usage
python {baseDir}/scripts/ml_inference.py quotas

# Available framework versions
python {baseDir}/scripts/ml_inference.py frameworks
```

### Advanced: custom model deployment

For models not in the catalog, use `create` with manual parameters:
```bash
python {baseDir}/scripts/ml_inference.py create --name "my-llm" \
    --framework VLLM --resource GPU_A100 --task GENERATE \
    --source-type huggingface --repo "org/model" \
    --gpu-count 1 --gpu-memory 20 \
    --vllm-args '[{"key":"dtype","value":"bfloat16","parameterType":"PARAMETER_TYPE_ARG_KV_QUOTED"}]'
```

Note: the Cloud.ru API is strict about payload format. Prefer `deploy` from the catalog when possible.

### Building custom Python code

When the user needs custom code beyond what the script provides, use the patterns from `{baseDir}/references/examples.md` to construct Python code with the `inference-clients` SDK directly.

## What to return

- Results of operations in readable format (JSON or summary)
- Python code snippets when the user wants to integrate into their own code
- Model catalog browsing results with prices and specs

## Limitations

- Do not log or expose API keys/secrets in responses.
- Do not execute destructive operations (delete, suspend) without user confirmation.
- The inference call endpoint URL pattern is `https://<model_run_id>.modelrun.inference.cloud.ru`.
