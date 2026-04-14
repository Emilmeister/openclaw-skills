# Cloud.ru AI Agents — API Reference

## Base URLs

- **BFF (used by skill)**: `https://console.cloud.ru/u-api/ai-agents/v1`
- Raw public API: `https://ai-agents.api.cloud.ru/api/v1` — **has server-side bugs on POST /agents** (nil pointer / invalid UUID on missing defaults). Skill uses BFF instead; both accept the same IAM Bearer.
- IAM auth: `https://iam.api.cloud.ru/api/v1/auth/token`

## Authentication

All calls require `Authorization: Bearer <IAM_TOKEN>`. Exchange access key pair for bearer:

```
POST https://iam.api.cloud.ru/api/v1/auth/token
Body: {"keyId": "<CP_CONSOLE_KEY_ID>", "secret": "<CP_CONSOLE_SECRET>"}
Response: {"access_token": "<token>"}
```

Token TTL ~30 minutes. `IAMAuth` auto-refreshes on 401.

## Endpoints

All endpoints under `/u-api/ai-agents/v1/`. Placeholders: `{projectId}`, `{agentId}`, `{systemId}`, `{mcpId}`, `{cardId}`.

### Agents

| Method | Path | Purpose |
|---|---|---|
| GET | `/{projectId}/agents?limit=100&offset=0` | List |
| GET | `/{projectId}/agents/{agentId}` | Get |
| POST | `/{projectId}/agents` | Create |
| PATCH | `/{projectId}/agents/{agentId}` | Update |
| DELETE | `/{projectId}/agents/{agentId}` | Delete |
| PATCH | `/{projectId}/agents/suspend/{agentId}` | Suspend |
| PATCH | `/{projectId}/agents/resume/{agentId}` | Resume |

### Agent Systems

Same pattern under `/{projectId}/agentSystems/...`.

### MCP Servers

Same pattern under `/{projectId}/mcpServers/...`.

### Catalog & Marketplace

| Method | Path | Purpose |
|---|---|---|
| GET | `/{projectId}/instanceTypes` | Instance types catalog (CPU/GPU) |
| GET | `/marketplace/agents?limit=N&search=Q` | Agent cards |
| GET | `/marketplace/agents/{cardId}` | Agent card details |
| GET | `/marketplace/mcpServers?limit=N&search=Q` | MCP server cards |
| GET | `/marketplace/mcpServers/{cardId}` | MCP card details |
| GET | `/{projectId}` | Project info (quotes/status) |

## Response envelopes

- List endpoints: `{"data": [...], "total": N}`
- Error endpoints: `{"code": N, "message": "...", "details": [{"@type": "...", "fieldViolations": [...], "Recommendation": "...", "HelpLink": "..."}]}`

## Statuses

All statuses are prefixed with entity name:

### `AGENT_STATUS_*`
`RESOURCE_ALLOCATION`, `PULLING`, `RUNNING`, `COOLED`, `ON_SUSPENSION`, `SUSPENDED`, `ON_DELETION`, `DELETED`, `FAILED`, `LLM_UNAVAILABLE`, `TOOL_UNAVAILABLE`, `IMAGE_UNAVAILABLE`.

### `AGENT_SYSTEM_STATUS_*`
Same as agents plus `AGENT_UNAVAILABLE`. Max 10 agents per system.

### `MCP_SERVER_STATUS_*`
`AVAILABLE`, `RUNNING`, `COOLED`, `SUSPENDED`, `FAILED`, `IMAGE_UNAVAILABLE`, `WAITING_FOR_SCRAPPING`, `ON_DELETION`, `DELETED`, `RESOURCE_ALLOCATION`, `PULLING`, `ON_SUSPENSION`.

## Body schemas (summary)

### Create Agent

Required: `name` (kebab-case, 3-125 chars), `instanceTypeId` (UUID), `mcpServerId` (UUID).

```json
{
  "name": "my-agent",
  "description": "...",
  "instanceTypeId": "<uuid>",
  "mcpServerId": "<uuid>",
  "imageSource": {
    "marketplaceAgentId": "<card-uuid>"
  },
  "options": {
    "systemPrompt": "You are ...",
    "llm": {
      "foundationModels": {"modelName": "GLM-4.7"}
    },
    "env": [{"name": "KEY", "value": "VALUE"}],
    "scaling": {"minScale": 0, "maxScale": 1}
  },
  "integrationOptions": {
    "authOptions": {"tokenAuth": {}}
  },
  "exportedPorts": [8080]
}
```

### Create MCP Server

Required: `name`, `instanceTypeId`.

```json
{
  "name": "my-mcp",
  "description": "...",
  "instanceTypeId": "<uuid>",
  "imageSource": {
    "marketplaceMcpServerId": "<card-uuid>"
  },
  "exposedPorts": [8080],
  "environmentOptions": {},
  "scaling": {"minScale": 0, "maxScale": 1},
  "integrationOptions": {"authOptions": {"tokenAuth": {}}}
}
```

### Create Agent System

Required: `name`, `instanceTypeId`, `agents[]` (up to 10 agent IDs).

```json
{
  "name": "my-system",
  "description": "...",
  "instanceTypeId": "<uuid>",
  "agents": ["<agent-uuid>", "..."],
  "orchestratorOptions": {"routing": "a2a"}
}
```

For exhaustive field list see upstream OpenAPI:
https://cloud.ru/docs/api/cdn/ai-agents/ug/_specs/openapi__ai-agents.yaml

## Public URL formats

- Agent: `https://{agent_id}-agent.ai-agent.inference.cloud.ru`
- MCP server: exposed via `publicUrl` field in `get` response.

## Known API quirks

- Project info returns quotas under key `quotes` (sic), not `quotas`.
- `suspend` on already-SUSPENDED returns `HTTP 200 {}` (idempotent).
- Error responses include `Recommendation` and `HelpLink` fields — useful for user diagnostics.
- **Raw `/api/v1/` at `ai-agents.api.cloud.ru` fails on `POST /agents`** with `nil pointer dereference` or `invalid UUID length: 0` regardless of body shape (some required UUIDs like `serviceAccountId`/`logGroupId` are not defaulted). Use BFF `/u-api/ai-agents/v1/` at `console.cloud.ru` — same Bearer token, BFF injects the missing defaults.
- `instanceTypes` list returns empty `[]` unless `?isActive=true` is passed.
- Create returns `{"mcpServerId": "..."}` / `{"agentId": "..."}` (not `{"id": "..."}`), while `get` returns envelope `{"mcpServer": {...}}` / `{"agent": {...}}` / `{"agentSystem": {...}}`. `wait` must unwrap envelope before reading `.status`.
- Marketplace `get` returns envelope `{"predefinedMcpServer": {...}}` / `{"predefinedAgent": {...}}`.
- `agents` create requires `options.llm.foundationModels.modelName`, `mcpServers: [{mcpServerId}]` (array, not scalar), and explicit `agentType` (`AGENT_TYPE_FROM_HUB` for marketplace, `AGENT_TYPE_CUSTOM` otherwise).
