# Cloud.ru Skills — Cross-Skill Workflows

## FM API vs ML Inference — when to use which

| | Foundation Models API | ML Inference (Model RUN) |
|---|---|---|
| **Model** | Pre-hosted by Cloud.ru | You deploy your own |
| **Pricing** | Pay per token (some models are free) | Pay per GPU-hour (fixed) |
| **GPU management** | None (serverless) | You choose GPU type and count |
| **Latency** | Higher (shared infra) | Lower (dedicated GPU) |
| **Models** | Cloud.ru catalog only | Any HuggingFace/Ollama model |
| **Auth** | API key (`CLOUD_RU_FOUNDATION_MODELS_API_KEY`) | IAM token or none (`isEnabledAuth`) |
| **Endpoint** | `https://foundation-models.api.cloud.ru/v1` | `https://<id>.modelrun.inference.cloud.ru/v1` |
| **Best for** | Quick experiments, low traffic, free models | Production, high traffic, custom models |

Both endpoints are **OpenAI-compatible** — same `/v1/chat/completions` format.

## Why two auth mechanisms

- **Foundation Models API** uses a simple API key (`CLOUD_RU_FOUNDATION_MODELS_API_KEY`) because it's a managed serverless service.
- **ML Inference** and **VM** use IAM credentials (`CP_CONSOLE_KEY_ID` + `CP_CONSOLE_SECRET`) because they manage cloud resources (GPUs, VMs) on your behalf.
- Both credential types are created by the `cloudru-account-setup` skill in one step.

## End-to-end workflow: from zero to working app

### Step 1: Create credentials (cloudru-account-setup)

```bash
python3 cloudru-account-setup/scripts/browser_login.py
```

This creates all credentials:
- `CLOUD_RU_FOUNDATION_MODELS_API_KEY` — for Foundation Models API
- `CP_CONSOLE_KEY_ID` + `CP_CONSOLE_SECRET` — for ML Inference and VM
- `PROJECT_ID` — your project UUID

Save them to `.env`:
```bash
cat > .env << 'EOF'
CLOUD_RU_FOUNDATION_MODELS_API_KEY=...
CP_CONSOLE_KEY_ID=...
CP_CONSOLE_SECRET=...
PROJECT_ID=...
EOF
```

### Step 2a: Use Foundation Models (fastest — no deploy needed)

```bash
# List available models (some are free!)
python3 cloudru-foundation-models/scripts/fm.py models

# Call a model
python3 cloudru-foundation-models/scripts/fm.py call openai/gpt-oss-120b --prompt "Hello!"
```

### Step 2b: Deploy your own model (ML Inference)

```bash
# Browse catalog
python3 cloudru-ml-inference/scripts/ml_inference.py catalog

# Deploy and wait
python3 cloudru-ml-inference/scripts/ml_inference.py deploy <model_card_id> --name my-model --wait

# Call it
python3 cloudru-ml-inference/scripts/ml_inference.py call <model_run_id> --prompt "Hello!"
```

### Step 3: Create a VM to host your app

```bash
# Create VM with Docker, public IP, wait for SSH
python3 cloudru-vm/scripts/vm.py create \
  --name app-server \
  --login user1 --ssh-key-file ~/.ssh/id_ed25519.pub \
  --cloud-init-file cloudru-vm/assets/cloud-init-docker.yaml \
  --wait --floating-ip --wait-ssh

# Wait for cloud-init (Docker install)
python3 cloudru-vm/scripts/vm.py ssh <vm_id> -i ~/.ssh/id_ed25519 -c "cloud-init status --wait"

# Open ports
python3 cloudru-vm/scripts/vm.py sg-rule-add <sg_id> --ports 8080
```

### Step 4: Deploy your app on the VM

```bash
# Upload files
python3 cloudru-vm/scripts/vm.py scp <vm_id> -i ~/.ssh/key \
  --local-path ./docker-compose.yml --remote-path /home/user1/docker-compose.yml

# Run
python3 cloudru-vm/scripts/vm.py ssh <vm_id> -i ~/.ssh/key \
  -c "cd /home/user1 && docker compose up -d"
```

Your app can call models at:
- FM API: `https://foundation-models.api.cloud.ru/v1`
- ML Inference: `https://<model_run_id>.modelrun.inference.cloud.ru/v1`
