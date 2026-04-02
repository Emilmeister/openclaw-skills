# Cloud.ru Skills for OpenClaw

Skills for working with [Cloud.ru](https://cloud.ru) services in the OpenClaw agent.

## Available skills

- **cloudru-account-setup** — create a Cloud.ru service account, Foundation Models API key, and IAM access key (`CP_CONSOLE_KEY_ID`/`CP_CONSOLE_SECRET`)
- **cloudru-foundation-models** — work with Cloud.ru Foundation Models API: list models, call completions, configure OpenClaw provider
- **cloudru-ml-inference** — deploy and manage ML models on Cloud.ru ML Inference (GPU): browse the predefined model catalog, deploy with one command, full CRUD, call inference endpoints (chat, embeddings, rerank)
- **cloudru-vm** — create and manage Cloud.ru virtual machines: full VM lifecycle, disk management, floating IPs, security groups (open/close ports), SSH/SCP remote execution

## Quick start

### 1. Set up credentials

Use the `cloudru-account-setup` skill or set environment variables manually:

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

### 4. Create a virtual machine

```bash
# List available flavors and images
python cloudru-vm/scripts/vm.py flavors
python cloudru-vm/scripts/vm.py images

# Create a VM with SSH key
python cloudru-vm/scripts/vm.py create \
  --name my-vm \
  --flavor-name lowcost10-2-4 \
  --image-name ubuntu-22.04 \
  --zone-name ru.AZ-1 \
  --disk-size 20 --disk-type-name SSD \
  --login user1 --ssh-key-file ~/.ssh/id_ed25519.pub

# Manage lifecycle
python cloudru-vm/scripts/vm.py list
python cloudru-vm/scripts/vm.py stop <vm_id>
python cloudru-vm/scripts/vm.py start <vm_id>
python cloudru-vm/scripts/vm.py delete <vm_id>

# Open ports (security groups)
python cloudru-vm/scripts/vm.py sg-create --name web-sg --zone-name ru.AZ-1 --open-ports 22 80 443
python cloudru-vm/scripts/vm.py sg-rule-add <sg_id> --ports 8080
python cloudru-vm/scripts/vm.py sg-rule-delete <sg_id> <rule_id>

# SSH into VM / run commands remotely
python cloudru-vm/scripts/vm.py ssh <vm_id> -i ~/.ssh/key -c "uname -a"

# Copy files to/from VM
python cloudru-vm/scripts/vm.py scp <vm_id> -i ~/.ssh/key --local-path ./app.py --remote-path /home/user1/app.py
```

## Installation

Copy the skill folders to your OpenClaw skills directory:

```bash
cp -R cloudru-account-setup cloudru-foundation-models cloudru-ml-inference cloudru-vm ~/.openclaw/skills/
```
