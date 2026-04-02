---
name: cloudru-vm
description: Create and manage Cloud.ru virtual machines — full VM lifecycle, disks, networking, images, flavors. Uses the Cloud.ru Compute API via lightweight httpx-based client.
metadata: {"openclaw":{"emoji":"🖥️","requires":{"bins":["python3"],"env":["CP_CONSOLE_KEY_ID","CP_CONSOLE_SECRET","PROJECT_ID"]}}}
---

# Cloud.ru Virtual Machines Skill

Manage virtual machines on Cloud.ru: create, start/stop/reboot, resize, delete VMs. Also manage disks, view flavors, images, subnets, security groups, and availability zones.

# When to use

Use this skill when the user:
- Wants to create, manage, or delete virtual machines on Cloud.ru
- Needs to list flavors, images, subnets, or availability zones
- Wants to manage disks (create, attach, detach, delete)
- Needs to start, stop, or reboot a VM
- Asks about Cloud.ru compute/VM infrastructure

# Prerequisites

## Environment variables
- `CP_CONSOLE_KEY_ID` — Cloud.ru service account key ID
- `CP_CONSOLE_SECRET` — Cloud.ru service account secret
- `PROJECT_ID` — Cloud.ru project UUID

If these are not set, guide the user to the `cloudru-account-setup` skill.

## Dependencies

The only external dependency is `httpx`. Install if not present:
```bash
pip install httpx
```

# How to use

## CLI script

The main script is `{baseDir}/scripts/vm.py`. Run it from the `{baseDir}/scripts/` directory.

### VM lifecycle

```bash
# List VMs
python vm.py list
python vm.py list --state running

# Get VM details
python vm.py get <vm_id>

# Create VM (requires flavor, image, zone, login/password)
# IMPORTANT: --login and --password are required for most images (they set image_metadata)
python vm.py create \
  --name my-vm \
  --flavor-name lowcost10-2-4 \
  --image-name ubuntu-22.04 \
  --zone-name ru.AZ-1 \
  --disk-size 20 \
  --disk-type-name SSD \
  --login user1 \
  --password 'MySecurePass123!'

# Start / Stop / Reboot
python vm.py start <vm_id>
python vm.py stop <vm_id>
python vm.py reboot <vm_id>

# Update VM (rename, resize — VM must be stopped for resize)
python vm.py update <vm_id> --name new-name
python vm.py update <vm_id> --flavor-name lowcost10-4-8

# Delete VM
python vm.py delete <vm_id>

# Get VNC console URL
python vm.py vnc <vm_id>
```

### Infrastructure info

```bash
# List flavors (CPU/RAM/GPU configs)
python vm.py flavors
python vm.py flavors --cpu 4 --ram 8

# List OS images
python vm.py images

# List subnets, zones, disk types, security groups
python vm.py subnets
python vm.py zones
python vm.py disk-types
python vm.py security-groups
```

### Floating IP (public IP address)

Floating IPs are NOT managed via `vm.py` CLI — use `CloudruComputeClient` directly from Python.

To assign a public IP to a VM:

```python
from cloudru_client import CloudruComputeClient
import os

client = CloudruComputeClient(os.environ["CP_CONSOLE_KEY_ID"], os.environ["CP_CONSOLE_SECRET"])

# 1. Get VM interface ID
vm = client.get_vm("<vm_id>").json()
interface_id = vm["interfaces"][0]["id"]

# 2. Create floating IP attached to that interface
res = client.create_floating_ip({
    "name": "fip-my-vm",
    "project_id": os.environ["PROJECT_ID"],
    "availability_zone_name": "ru.AZ-1",  # must match VM's zone
    "interface_id": interface_id,
})
print(f"Public IP: {res.json()['ip_address']}")
```

To list or delete floating IPs:
```python
# List
fips = client.list_floating_ips(os.environ["PROJECT_ID"]).json()

# Delete
client.delete_floating_ip("<floating_ip_id>")
```

### Disk management

```bash
# List disks
python vm.py disks

# Create standalone disk
python vm.py disk-create --name data-disk --size 100 --zone-name ru.AZ-1 --disk-type-name SSD

# Attach / Detach
python vm.py disk-attach <disk_id> --vm-id <vm_id>
python vm.py disk-detach <disk_id> --vm-id <vm_id>

# Delete disk
python vm.py disk-delete <disk_id>
```

### Task tracking

Many operations are async. Track them:
```bash
python vm.py task <task_id>
```

## Typical workflow for creating a VM with public IP

1. Pick an availability zone: `python vm.py zones`
   - Available: `ru.AZ-1`, `ru.AZ-2`, `ru.AZ-3`
2. Pick a flavor: `python vm.py flavors`
   - Cheapest: `lowcost10-1-1` (1 vCPU, 1 GB RAM)
   - Common: `lowcost10-2-4` (2 vCPU, 4 GB RAM)
3. Pick an OS image: `python vm.py images`
   - Common: `ubuntu-22.04`, `Ubuntu-24.04`
4. Pick a disk type: `python vm.py disk-types`
   - Available: `SSD`, `HDD`
5. Create the VM:
   ```bash
   python vm.py create --name my-vm \
     --flavor-name lowcost10-2-4 \
     --image-name ubuntu-22.04 \
     --zone-name ru.AZ-1 \
     --disk-size 20 --disk-type-name SSD \
     --login user1 --password 'SecurePass123!'
   ```
6. Wait for it to become `running`: `python vm.py get <vm_id>`
7. Assign a public IP (floating IP) — use Python snippet from the "Floating IP" section above
8. Connect: `ssh user1@<public_ip>`

## Important notes and gotchas

### VM creation

- **`--login` and `--password` are required** for most Cloud.ru images. They set `image_metadata` (login, password, hostname). Without them the API returns `image_metadata_required` error.
- **`--disk-type-name`** (`SSD` or `HDD`) is required. Without it the API returns `disk_type_id or disk_type_name should be set` error.
- **Minimum boot disk size is ~8-10 GB** for Ubuntu images. Smaller values (e.g. 5 GB) return `vm_root_disk_too_small` error. Maximum disk size is 16384 GB.
- Zone names use dots: `ru.AZ-1`, `ru.AZ-2`, `ru.AZ-3` (not `ru-9a`).
- The API (v1.1) creates VMs asynchronously — the VM starts in `creating` state and transitions through `creating` -> `running` (typically 30-90 seconds).
- VM names must match pattern: `^[a-zA-Z][a-zA-Z0-9.\-_]*$` (1-64 chars, must start with a letter).

### Stop / Start (приостановка / возобновление)

- `stop` sends `power_off` — VM transitions `running` -> `stopping` -> `stopped` (~15 seconds).
- `start` sends `power_on` — VM transitions `stopped` -> `starting` -> `running` (~30-40 seconds).
- `reboot` sends `reboot` — VM restarts without full shutdown.
- Resize (changing flavor) requires the VM to be `stopped` first.

### Deletion

- **If a floating IP is attached, delete it FIRST** before deleting the VM. Otherwise the API returns `floating_ip_can_not_be_detached_from_vm_in_current_state` (HTTP 422).
- Correct deletion order: 1) delete floating IP, 2) wait a few seconds, 3) delete VM.
- VM deletion is asynchronous — the VM goes through `deleting` state before being fully removed.

### Floating IP (public IP)

- Floating IPs are created separately and attached to a VM's network interface.
- The floating IP's availability zone **must match** the VM's zone.
- One interface can have only one floating IP. Assigning another returns `interface_connected_another_floating_ip` error.
- After creating a floating IP, the VM is accessible at the assigned public IP via SSH: `ssh <login>@<public_ip>`.

### Disk sizes (tested)

| Size | Type | Result |
|------|------|--------|
| 5 GB | SSD | Error: `vm_root_disk_too_small` |
| 10 GB | SSD | OK (minimum for Ubuntu) |
| 50 GB | SSD | OK |
| 200 GB | HDD | OK |

### Flavors (pricing tiers)

- `lowcost10-*` — cheapest tier, 10% guaranteed vCPU share (e.g. `lowcost10-1-1` = 1 vCPU, 1 GB RAM)
- `low-*` — low tier (e.g. `low-1-2` = 1 vCPU, 2 GB RAM)
- `gen-*` — general purpose, 100% guaranteed vCPU (e.g. `gen-2-8` = 2 vCPU, 8 GB RAM)
- `gpa100-*` — GPU flavors with A100 GPUs
- `free-tier-*` — free tier (limited availability)

### API response format

- List endpoints return `{"items": [...], "total": N}`.
- Exception: `zones` and `disk-types` return a plain array `[...]`.
- VM create (v1.1) accepts and returns an array (batch create support).
- Many operations are async — use `python vm.py task <task_id>` to track progress.

## Building custom Python code

When the user needs custom code beyond what the script provides, use the patterns from `{baseDir}/references/examples.md` to construct Python code with the `CloudruComputeClient` from `{baseDir}/scripts/cloudru_client.py`.

For full API reference, see `{baseDir}/references/api-reference.md`.

# Limitations

- Do not output secrets (CP_CONSOLE_KEY_ID, CP_CONSOLE_SECRET) to the user
- Do not run destructive commands (delete, stop) without user confirmation
- API base URL: `https://compute.api.cloud.ru`
