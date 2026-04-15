# Cloud.ru Skills for AI Agents

Universal skills for working with [Cloud.ru](https://cloud.ru) services from any AI coding agent.

## Available skills

| Skill | Description |
|-------|-------------|
| **cloudru-account-setup** | Create a Cloud.ru service account, Foundation Models API key, and IAM access key |
| **cloudru-foundation-models** | Work with Cloud.ru Foundation Models API: list models, call completions |
| **cloudru-ml-inference** | Deploy and manage ML models on Cloud.ru ML Inference (GPU) |
| **cloudru-vm** | Create and manage Cloud.ru virtual machines |
| **cloudru-managed-rag** | Set up and query managed RAG pipelines: knowledge bases, semantic search, LLM-powered Q&A |

## Quick start

### 1. Set up credentials

Use the `cloudru-account-setup` skill (browser-assisted) or set environment variables manually:

```bash
export CP_CONSOLE_KEY_ID="<your-key-id>"
export CP_CONSOLE_SECRET="<your-secret>"
export PROJECT_ID="<your-project-uuid>"
export CLOUD_RU_FOUNDATION_MODELS_API_KEY="<your-fm-api-key>"
```

### 2. Install dependencies

```bash
pip install httpx                # all skills
pip install boto3                # managed-rag (S3 upload)
pip install playwright           # account-setup (browser login)
playwright install chromium      # account-setup (one-time)
```

### 3. Call a Foundation Model

```bash
python cloudru-foundation-models/scripts/fm.py models
python cloudru-foundation-models/scripts/fm.py call "t-tech/T-lite-it-1.0" --prompt "Hello!"
```

### 4. Deploy a model (ML Inference)

```bash
python cloudru-ml-inference/scripts/ml_inference.py catalog
python cloudru-ml-inference/scripts/ml_inference.py deploy <model_card_id> --name "my-model" --wait
python cloudru-ml-inference/scripts/ml_inference.py call <model_run_id> --prompt "Hello!" --with-auth
```

### 5. Create a virtual machine

```bash
python cloudru-vm/scripts/vm.py flavors
python cloudru-vm/scripts/vm.py create \
  --name my-vm --flavor-name lowcost10-2-4 --image-name ubuntu-22.04 \
  --zone-name ru.AZ-1 --disk-size 20 --disk-type-name SSD \
  --login user1 --ssh-key-file ~/.ssh/id_ed25519.pub \
  --wait --floating-ip
```

### 6. Set up a RAG pipeline

```bash
python cloudru-managed-rag/scripts/managed_rag.py setup \
  --docs-path ./docs --kb-name "my-kb" --bucket-name "my-bucket"
python cloudru-managed-rag/scripts/managed_rag.py search --query "your question"
python cloudru-managed-rag/scripts/managed_rag.py ask --query "your question"
```

## Cross-skill workflows

See [WORKFLOW.md](WORKFLOW.md) for the FM API vs ML Inference decision matrix and an end-to-end walkthrough: credentials → model deployment → VM → app hosting.

## Usage with AI agents

Each skill folder contains a `SKILL.md` file that serves as the entry point. Point your agent to the relevant `SKILL.md` and it will have all the instructions it needs.

The skills are designed to be agent-agnostic — they work with Claude Code, Cursor, Windsurf, Cline, Aider, and any other agent that can read markdown instructions and run Python scripts.
