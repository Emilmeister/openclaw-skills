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
    statuses = args.statuses.split(",") if getattr(args, "statuses", None) else None
    not_in = args.not_in_statuses.split(",") if getattr(args, "not_in_statuses", None) else None
    resp = client.list_agents(project_id, limit=args.limit, offset=args.offset,
                               statuses=statuses, not_in_statuses=not_in)
    check_response(resp, "listing agents")
    print_json(resp.json())


def cmd_get(args):
    client, project_id = build_client()
    resp = client.get_agent(project_id, args.agent_id)
    check_response(resp, f"getting agent {args.agent_id}")
    print_json(resp.json())


def _dig(d: dict, *keys: str) -> dict:
    """Walk/create nested dicts so `d[k0][k1]...` is returned (ready to mutate)."""
    for k in keys:
        d = d.setdefault(k, {})
    return d


def _apply_agent_option_flags(body: dict, args) -> None:
    """Apply high-level flags that mirror what the UI create-form sends.

    Covers options.prompt, options.llm (model/params/thinking), options.scaling
    (min/max/keepAlive/rps), options.runtimeOptions (maxLlmCalls),
    options.memoryOptions (memory/session), neighbors, integrationOptions.logging.
    Each flag is optional; omit to leave server defaults.
    """
    if getattr(args, "system_prompt", None):
        _dig(body, "options", "prompt")["systemPrompt"] = args.system_prompt
    if getattr(args, "system_prompt_file", None):
        with open(args.system_prompt_file) as f:
            _dig(body, "options", "prompt")["systemPrompt"] = f.read()
    if getattr(args, "model_name", None):
        _dig(body, "options", "llm", "foundationModels")["modelName"] = args.model_name
    if getattr(args, "temperature", None) is not None:
        _dig(body, "options", "llm", "modelParameters")["temperature"] = args.temperature
    if getattr(args, "max_tokens", None) is not None:
        _dig(body, "options", "llm", "modelParameters")["maxTokens"] = args.max_tokens
    if getattr(args, "thinking", None):
        thinking = _dig(body, "options", "llm", "modelParameters", "thinking")
        if args.thinking == "off":
            thinking["enabled"] = False
        else:
            thinking["enabled"] = True
            thinking["level"] = f"THINKING_LEVEL_{args.thinking.upper()}"
    if getattr(args, "thinking_budget", None) is not None:
        _dig(body, "options", "llm", "modelParameters", "thinking")["budget"] = args.thinking_budget
    if getattr(args, "min_scale", None) is not None:
        _dig(body, "options", "scaling")["minScale"] = args.min_scale
    if getattr(args, "max_scale", None) is not None:
        _dig(body, "options", "scaling")["maxScale"] = args.max_scale
    if getattr(args, "keep_alive_min", None) is not None:
        scaling = _dig(body, "options", "scaling")
        scaling["isKeepAlive"] = args.keep_alive_min > 0
        scaling["keepAliveDuration"] = {"hours": 0, "minutes": args.keep_alive_min, "seconds": 0}
    if getattr(args, "rps", None) is not None:
        _dig(body, "options", "scaling", "scalingRules", "rps")["value"] = args.rps
    if getattr(args, "max_llm_calls", None) is not None:
        _dig(body, "options", "runtimeOptions")["maxLlmCalls"] = args.max_llm_calls
    if getattr(args, "memory_enabled", None) is not None:
        _dig(body, "options", "memoryOptions", "memory")["isEnabled"] = args.memory_enabled
    if getattr(args, "session_enabled", None) is not None:
        _dig(body, "options", "memoryOptions", "session")["isEnabled"] = args.session_enabled
    if getattr(args, "log_group_id", None):
        _dig(body, "integrationOptions", "logging").update({
            "isEnabledLogging": True, "logGroupId": args.log_group_id,
        })
    if getattr(args, "neighbors", None):
        nbrs = body.get("neighbors") or []
        for nid in args.neighbors.split(","):
            nid = nid.strip()
            if nid and not any(n.get("agentId") == nid for n in nbrs):
                nbrs.append({"agentId": nid})
        body["neighbors"] = nbrs


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
            _dig(body, "options", "llm", "foundationModels").setdefault("modelName", model_id)
    else:
        body.setdefault("agentType", "AGENT_TYPE_CUSTOM")
    if args.name:
        body["name"] = args.name
    if args.description:
        body["description"] = args.description
    if args.instance_type_id:
        body["instanceTypeId"] = args.instance_type_id
    # MCP: single (legacy) or multiple via --mcp-servers
    mcp_ids: list = []
    if args.mcp_server_id:
        mcp_ids.append(args.mcp_server_id)
    if getattr(args, "mcp_servers", None):
        mcp_ids.extend(x.strip() for x in args.mcp_servers.split(",") if x.strip())
    if mcp_ids:
        existing = body.get("mcpServers") or []
        for mid in mcp_ids:
            if not any(m.get("mcpServerId") == mid for m in existing):
                existing.append({"mcpServerId": mid})
        body["mcpServers"] = existing
    _apply_agent_option_flags(body, args)
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
    if args.name:
        body["name"] = args.name
    if args.description is not None:
        body["description"] = args.description
    if args.instance_type_id:
        body["instanceTypeId"] = args.instance_type_id
    _apply_agent_option_flags(body, args)
    if not body:
        print("Error: nothing to update (no flags, no --config-json)", file=sys.stderr)
        sys.exit(1)
    resp = client.update_agent(project_id, args.agent_id, body)
    check_response(resp, f"updating agent {args.agent_id}")
    print_json(resp.json() if resp.text else {})


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


def cmd_history(args):
    client, project_id = build_client()
    resp = client.get_agent_history(project_id, args.agent_id,
                                     limit=args.limit, offset=args.offset)
    check_response(resp, f"fetching history for agent {args.agent_id}")
    print_json(resp.json())


COMMANDS = {
    "agents.list": cmd_list,
    "agents.get": cmd_get,
    "agents.create": cmd_create,
    "agents.update": cmd_update,
    "agents.delete": cmd_delete,
    "agents.suspend": cmd_suspend,
    "agents.resume": cmd_resume,
    "agents.wait": cmd_wait,
    "agents.history": cmd_history,
}
