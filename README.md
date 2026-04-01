# Cloud.ru Skills for OpenClaw

Skills for working with [Cloud.ru](https://cloud.ru) services in the OpenClaw agent.

## Available skills

- **cloudru-account-setup** — create a Cloud.ru service account, Foundation Models API key, and IAM access key (`CP_CONSOLE_KEY_ID`/`CP_CONSOLE_SECRET`)
- **cloudru-foundation-models** — work with Cloud.ru Foundation Models API: list models, call completions, configure OpenClaw provider
- **cloudru-ml-inference** — deploy and manage ML models on Cloud.ru ML Inference (GPU): browse the predefined model catalog, deploy with one command, full CRUD, call inference endpoints (chat, embeddings, rerank)

## Quick start

### 1. Set up credentials

Use the `cloudru-account-setup` skill or set environment variables manually:

```bash
export CP_CONSOLE_KEY_ID="<your-key-id>"
export CP_CONSOLE_SECRET="<your-secret>"
export PROJECT_ID="<your-project-uuid>"
export CLOUD_RU_FOUNDATION_MODELS_API_KEY="<your-fm-api-key>"
```

### 2. Install ML Inference dependencies

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

### 3. Deploy a model

```bash
# Browse the catalog
python cloudru-ml-inference/scripts/ml_inference.py catalog

# See configs for a model
python cloudru-ml-inference/scripts/ml_inference.py catalog-detail <model_card_id>

# Deploy it
python cloudru-ml-inference/scripts/ml_inference.py deploy <model_card_id> --name "my-model"

# Call inference
python cloudru-ml-inference/scripts/ml_inference.py call <model_run_id> --prompt "Hello!"

# Clean up
python cloudru-ml-inference/scripts/ml_inference.py delete <model_run_id>
```

## Installation

Copy the skill folders to your OpenClaw skills directory:

```bash
cp -R cloudru-account-setup cloudru-foundation-models cloudru-ml-inference ~/.openclaw/skills/
```
