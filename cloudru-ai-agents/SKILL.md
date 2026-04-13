# Cloud.ru AI Agents

> **Name:** cloudru-ai-agents
> **Description:** Manage Cloud.ru AI Agents — agents, agent systems, and MCP servers. Full CRUD, lifecycle operations (suspend/resume), wait-for-running, marketplace browsing, and instance-types catalog via lightweight httpx-based client.
> **Required env:** `CP_CONSOLE_KEY_ID`, `CP_CONSOLE_SECRET`, `PROJECT_ID`
> **Required pip:** `httpx`

## What this skill does

Manages AI Agents resources on Cloud.ru AI Agents service. Supports:
- Full CRUD on **agents** (list/get/create/update/delete)
- Lifecycle ops: **suspend/resume/wait-for-running**
- Same for **agent-systems** and **mcp-servers**
- **Marketplace browsing**: search/browse agent and MCP server cards
- **Instance types catalog**: list available CPU/GPU configurations
- 401 auto-refresh of IAM bearer

## When to use

Use this skill when the user:
- wants to deploy, manage, or inspect agents on Cloud.ru AI Agents
- asks about Agent, Agent System, MCP server, or marketplace of agents
- needs to suspend/resume a running agent or MCP server
- wants to browse the Cloud.ru marketplace for ready-made agents or MCP servers
- mentions Evolution AI Agent, agent-ассистент, MCP-сервер, multi-agent system

## Prerequisites

The user must have these environment variables set:
- `CP_CONSOLE_KEY_ID` — Cloud.ru console service account key ID
- `CP_CONSOLE_SECRET` — Cloud.ru console service account secret
- `PROJECT_ID` — Cloud.ru project UUID

If credentials are missing, direct the user to the `cloudru-account-setup` skill (it automatically attaches the required `ai-agents.*.admin` service roles).

Install dependency:
```bash
pip install httpx
```

## How to use

Read `./references/api-reference.md` for endpoint details and body schemas. Read `./references/examples.md` for ready Python snippets.

### Common flows

```bash
# Browse marketplace for ready-to-deploy agents
python scripts/ai_agents.py marketplace list-agents --limit 10

# List available CPU/GPU instance types
python scripts/ai_agents.py instance-types list

# Create MCP server from marketplace card
python scripts/ai_agents.py mcp-servers create \
    --from-marketplace <card_id> \
    --name my-mcp --instance-type-id <id>
python scripts/ai_agents.py mcp-servers wait <mcp_id>

# Create agent bound to that MCP server
python scripts/ai_agents.py agents create \
    --from-marketplace <agent_card_id> \
    --name my-agent --instance-type-id <id> --mcp-server-id <mcp_id>
python scripts/ai_agents.py agents wait <agent_id>

# Inspect agent
python scripts/ai_agents.py agents get <agent_id>
# -> returns publicUrl for runtime access

# Lifecycle
python scripts/ai_agents.py agents suspend <agent_id>
python scripts/ai_agents.py agents resume <agent_id>
python scripts/ai_agents.py agents delete <agent_id> --yes
```

### Custom agents via JSON

For agents not in the marketplace or with custom configuration, supply full body via `--config-json` or `--config-file`:

```bash
python scripts/ai_agents.py agents create \
    --name custom-agent --instance-type-id <id> --mcp-server-id <mcp_id> \
    --config-json '{"options": {"systemPrompt": "You are a helpful assistant.", "llm": {"foundationModels": {"modelName": "GLM-4.7"}}}}'
```

See `./references/api-reference.md` for full body schema.

### Runtime invoke

Agents are reachable at `https://{agent_id}-agent.ai-agent.inference.cloud.ru` (`publicUrl` field from `get`). The invoke protocol is not documented publicly; this skill does not implement invoke in v1. Use the UI chat or reverse-engineer via DevTools.

## Env vars

```
CP_CONSOLE_KEY_ID    IAM access key ID (from cloudru-account-setup)
CP_CONSOLE_SECRET    IAM access key secret (from cloudru-account-setup)
PROJECT_ID           Cloud.ru project ID (from cloudru-account-setup)
CLOUDRU_ENV_FILE     Path to .env (default: .env in CWD)
```

## Limitations

- `prompts` and `triggers` are UI-only (no public API as of 2026-04-13).
- Runtime agent invocation (`POST <publicUrl>/...`) is not documented publicly and not implemented.
- Do not log or expose API keys/secrets in responses.
- `delete` requires explicit confirmation (`--yes` or interactive prompt).
