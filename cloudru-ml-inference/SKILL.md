---
name: cloudru-ml-inference
description: Manage Cloud.ru ML Inference model runs — create, list, update, delete, suspend, resume, call inference endpoints, check quotas. Full CRUD and inference via the inference-clients Python SDK.
homepage: https://cloud.ru/docs/ml-platform/mlspace/concepts/inference/about-inference.html
metadata: {"openclaw":{"emoji":"🤖","requires":{"bins":["python3"],"env":["CP_CONSOLE_KEY_ID","CP_CONSOLE_SECRET","PROJECT_ID"]}}}
---

# Cloud.ru ML Inference

## What this skill does

Manages ML model deployments (Model Runs) on Cloud.ru ML Inference service. Supports:
- Full CRUD on model runs (create, list, get details, update, delete)
- Lifecycle operations (suspend, resume)
- Inference calls to running models (text generation, embeddings, rerank, image generation)
- Quota and runtime template queries
- Health checks (ping) for deployed models

## When to use

Use this skill when the user:
- wants to deploy or manage ML models on Cloud.ru ML Inference
- asks about Model RUN or Docker RUN on Cloud.ru
- needs to create, list, update, delete, suspend, or resume inference endpoints
- wants to call a deployed model for text generation, embeddings, reranking, or image generation
- asks about GPU quotas or available frameworks on Cloud.ru ML Inference
- mentions `inference-clients`, `ModelRunUsersApiClient`, or `CallModelApi`

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

### Script usage

```bash
# List all model runs
python {baseDir}/scripts/ml_inference.py list

# Get model run details
python {baseDir}/scripts/ml_inference.py get <model_run_id>

# Create a model run (vLLM example)
python {baseDir}/scripts/ml_inference.py create --name "my-llm" \
    --framework VLLM --resource GPU_A100 --task TEXT_2_TEXT_GENERATION \
    --source-type huggingface --repo "meta-llama/Llama-2-7b-chat-hf" \
    --gpu-count 1

# Delete a model run
python {baseDir}/scripts/ml_inference.py delete <model_run_id>

# Suspend / Resume
python {baseDir}/scripts/ml_inference.py suspend <model_run_id>
python {baseDir}/scripts/ml_inference.py resume <model_run_id>

# Call inference (OpenAI-compatible chat)
python {baseDir}/scripts/ml_inference.py call <model_run_id> \
    --prompt "Why is the sky blue?"

# Call embeddings
python {baseDir}/scripts/ml_inference.py embed <model_run_id> \
    --texts "Hello world" "Another text"

# Check quotas
python {baseDir}/scripts/ml_inference.py quotas

# List available framework versions
python {baseDir}/scripts/ml_inference.py frameworks

# Ping / health check
python {baseDir}/scripts/ml_inference.py ping <model_run_id>

# Get event history
python {baseDir}/scripts/ml_inference.py history <model_run_id>
```

### Building custom Python code

When the user needs custom code beyond what the script provides, use the patterns from `{baseDir}/references/examples.md` to construct Python code with the `inference-clients` SDK directly.

## What to return

- Results of operations in readable format (JSON or summary)
- Python code snippets when the user wants to integrate into their own code
- Guidance on choosing frameworks, GPU types, and model sources

## Limitations

- Do not log or expose API keys/secrets in responses.
- Do not execute destructive operations (delete, suspend) without user confirmation.
- The inference call endpoint URL pattern is `https://<model_run_id>.modelrun.inference.cloud.ru`.
