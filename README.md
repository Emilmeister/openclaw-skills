# Cloud.ru Skills for AI Agents

Universal skills for working with [Cloud.ru](https://cloud.ru) services from any AI coding agent.

## Available skills

| Skill | Description |
|-------|-------------|
| **cloudru-account-setup** | Create a Cloud.ru service account, Foundation Models API key, and IAM access key |
| **cloudru-foundation-models** | Work with Cloud.ru Foundation Models API: list models, call completions |
| **cloudru-ml-inference** | Deploy and manage ML models on Cloud.ru ML Inference (GPU) |
| **cloudru-vm** | Create and manage Cloud.ru virtual machines |

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

ML Inference and VM skills require only `httpx`:

```bash
pip install httpx
```

### 3. Deploy a model (ML Inference)

```bash
python cloudru-ml-inference/scripts/ml_inference.py catalog
python cloudru-ml-inference/scripts/ml_inference.py deploy <model_card_id> --name "my-model"
python cloudru-ml-inference/scripts/ml_inference.py call <model_run_id> --prompt "Hello!"
```

### 4. Create a virtual machine

```bash
python cloudru-vm/scripts/vm.py flavors
python cloudru-vm/scripts/vm.py create \
  --name my-vm --flavor-name lowcost10-2-4 --image-name ubuntu-22.04 \
  --zone-name ru.AZ-1 --disk-size 20 --disk-type-name SSD \
  --login user1 --ssh-key-file ~/.ssh/id_ed25519.pub
```

## Usage with AI agents

Each skill folder contains a `SKILL.md` file that serves as the entry point. Point your agent to the relevant `SKILL.md` and it will have all the instructions it needs.

The skills are designed to be agent-agnostic — they work with Claude Code, Cursor, Windsurf, Cline, Aider, and any other agent that can read markdown instructions and run Python scripts.
