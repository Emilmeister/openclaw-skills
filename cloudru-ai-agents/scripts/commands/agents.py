"""CLI handlers for `agents` subcommand."""

import sys
import time

from helpers import build_client, check_response, print_json, load_config_from_args


WAIT_FINAL_SUCCESS = {"AGENT_STATUS_RUNNING", "AGENT_STATUS_COOLED"}
WAIT_FINAL_FAIL = {
    "AGENT_STATUS_FAILED",
    "AGENT_STATUS_LLM_UNAVAILABLE",
    "AGENT_STATUS_TOOL_UNAVAILABLE",
    "AGENT_STATUS_IMAGE_UNAVAILABLE",
    "AGENT_STATUS_ON_DELETION",
    "AGENT_STATUS_DELETED",
}
WAIT_POLL_INTERVAL = 15


def cmd_list(args):
    client, project_id = build_client()
    resp = client.list_agents(project_id, limit=args.limit, offset=args.offset)
    check_response(resp, "listing agents")
    print_json(resp.json())


def cmd_get(args):
    client, project_id = build_client()
    resp = client.get_agent(project_id, args.agent_id)
    check_response(resp, f"getting agent {args.agent_id}")
    print_json(resp.json())


def _build_create_body(args, client, project_id) -> dict:
    """Combine --from-marketplace card + --config-json/file + simple flags into create body."""
    body: dict = load_config_from_args(args)
    if args.from_marketplace:
        card_resp = client.get_marketplace_agent(project_id, args.from_marketplace)
        check_response(card_resp, f"fetching marketplace card {args.from_marketplace}")
        raw = card_resp.json()
        card = raw.get("predefinedAgent", raw)
        body.setdefault("imageSource", {})["marketplaceAgentId"] = card.get("id", args.from_marketplace)
        body.setdefault("description", card.get("description", ""))
        body.setdefault("agentType", "AGENT_TYPE_FROM_HUB")
        model_id = card.get("modelId")
        if model_id:
            options = body.setdefault("options", {})
            llm = options.setdefault("llm", {})
            fm = llm.setdefault("foundationModels", {})
            fm.setdefault("modelName", model_id)
    else:
        body.setdefault("agentType", "AGENT_TYPE_CUSTOM")
    if args.name:
        body["name"] = args.name
    if args.description:
        body["description"] = args.description
    if args.instance_type_id:
        body["instanceTypeId"] = args.instance_type_id
    if args.mcp_server_id:
        existing = body.get("mcpServers") or []
        if not any(m.get("mcpServerId") == args.mcp_server_id for m in existing):
            existing.append({"mcpServerId": args.mcp_server_id})
        body["mcpServers"] = existing
    return body


def cmd_create(args):
    client, project_id = build_client()
    body = _build_create_body(args, client, project_id)
    resp = client.create_agent(project_id, body)
    check_response(resp, "creating agent")
    print_json(resp.json())


def cmd_update(args):
    client, project_id = build_client()
    body = load_config_from_args(args)
    if not body:
        print("Error: --config-json or --config-file required for update", file=sys.stderr)
        sys.exit(1)
    resp = client.update_agent(project_id, args.agent_id, body)
    check_response(resp, f"updating agent {args.agent_id}")
    print_json(resp.json())


def _confirm_destructive(action: str, target: str, auto_yes: bool) -> None:
    if auto_yes:
        return
    answer = input(f"Confirm {action} on {target}? [y/N] ")
    if answer.strip().lower() not in ("y", "yes"):
        print("Aborted.", file=sys.stderr)
        sys.exit(1)


def cmd_delete(args):
    _confirm_destructive("delete", f"agent {args.agent_id}", args.yes)
    client, project_id = build_client()
    resp = client.delete_agent(project_id, args.agent_id)
    if resp.status_code == 404:
        print(f"Agent {args.agent_id} already deleted", file=sys.stderr)
        return
    check_response(resp, f"deleting agent {args.agent_id}")
    print_json(resp.json() if resp.text else {"status": "deleted"})


def cmd_suspend(args):
    client, project_id = build_client()
    resp = client.suspend_agent(project_id, args.agent_id)
    check_response(resp, f"suspending agent {args.agent_id}")
    print_json(resp.json() if resp.text else {"status": "suspended"})


def cmd_resume(args):
    client, project_id = build_client()
    resp = client.resume_agent(project_id, args.agent_id)
    check_response(resp, f"resuming agent {args.agent_id}")
    print_json(resp.json() if resp.text else {"status": "resumed"})


def cmd_wait(args):
    client, project_id = build_client()
    deadline = time.time() + args.timeout
    last_status = None
    while time.time() < deadline:
        resp = client.get_agent(project_id, args.agent_id)
        check_response(resp, f"polling agent {args.agent_id}")
        raw = resp.json()
        data = raw.get("agent", raw)
        status = data.get("status")
        if status != last_status:
            print(f"status={status}", file=sys.stderr)
            last_status = status
        if status in WAIT_FINAL_SUCCESS:
            print_json(data)
            return
        if status in WAIT_FINAL_FAIL:
            print(f"Agent reached failure state: {status}", file=sys.stderr)
            reason = data.get("statusReason")
            if reason:
                print(f"statusReason: {reason}", file=sys.stderr)
            sys.exit(1)
        time.sleep(WAIT_POLL_INTERVAL)
    print(f"Timeout after {args.timeout}s. Last status: {last_status}", file=sys.stderr)
    sys.exit(1)


COMMANDS = {
    "agents.list": cmd_list,
    "agents.get": cmd_get,
    "agents.create": cmd_create,
    "agents.update": cmd_update,
    "agents.delete": cmd_delete,
    "agents.suspend": cmd_suspend,
    "agents.resume": cmd_resume,
    "agents.wait": cmd_wait,
}
