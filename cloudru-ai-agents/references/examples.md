# Cloud.ru AI Agents — Usage Examples

## 1. Browse marketplace and pick an MCP server

```python
from cloudru_client import CloudruAiAgentsClient

client = CloudruAiAgentsClient(key_id="...", key_secret="...")

resp = client.list_marketplace_mcp_servers(limit=5)
cards = resp.json()["data"]
for card in cards:
    print(card["id"], card["name"])
```

## 2. Create MCP server from marketplace card

```python
card = client.get_marketplace_mcp_server("<card-uuid>").json()

body = {
    "name": "my-mcp",
    "description": card.get("description", ""),
    "instanceTypeId": "<instance-type-uuid>",
    "imageSource": {"marketplaceMcpServerId": card["id"]},
}
resp = client.create_mcp_server(project_id, body)
resp.raise_for_status()
mcp_id = resp.json()["id"]
```

## 3. Poll until RUNNING

```python
import time

for _ in range(40):
    data = client.get_mcp_server(project_id, mcp_id).json()
    if data["status"] == "MCP_SERVER_STATUS_RUNNING":
        break
    if data["status"] in {"MCP_SERVER_STATUS_FAILED", "MCP_SERVER_STATUS_IMAGE_UNAVAILABLE"}:
        raise RuntimeError(f"MCP failed: {data['statusReason']}")
    time.sleep(15)
```

## 4. Create agent bound to the MCP server

```python
body = {
    "name": "my-agent",
    "description": "Helpful assistant",
    "instanceTypeId": "<instance-type-uuid>",
    "mcpServerId": mcp_id,
    "imageSource": {"marketplaceAgentId": "<agent-card-uuid>"},
    "options": {
        "systemPrompt": "You are a helpful assistant.",
        "llm": {"foundationModels": {"modelName": "GLM-4.7"}},
    },
}
resp = client.create_agent(project_id, body)
resp.raise_for_status()
agent = resp.json()
print("publicUrl:", agent["publicUrl"])
```

## 5. Lifecycle operations

```python
client.suspend_agent(project_id, agent_id)
client.resume_agent(project_id, agent_id)
client.delete_agent(project_id, agent_id)
```

## 6. Error handling with Recommendation/HelpLink

```python
resp = client.create_agent(project_id, {})
if not resp.is_success:
    data = resp.json()
    print(f"Error {resp.status_code}: {data.get('message')}")
    for detail in data.get("details", []):
        if "Recommendation" in detail:
            print("Recommendation:", detail["Recommendation"])
        if "HelpLink" in detail:
            print("See:", detail["HelpLink"])
```
