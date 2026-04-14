"""CLI handlers for `mcp-servers` subcommand."""

import sys
import time

from helpers import build_client, check_response, print_json, load_config_from_args


WAIT_FINAL_SUCCESS = {"MCP_SERVER_STATUS_RUNNING", "MCP_SERVER_STATUS_COOLED"}
WAIT_FINAL_FAIL = {
    "MCP_SERVER_STATUS_FAILED",
    "MCP_SERVER_STATUS_IMAGE_UNAVAILABLE",
    "MCP_SERVER_STATUS_ON_DELETION",
    "MCP_SERVER_STATUS_DELETED",
    "MCP_SERVER_STATUS_WAITING_FOR_SCRAPPING",
}
WAIT_POLL_INTERVAL = 15


def cmd_list(args):
    client, project_id = build_client()
    not_in = args.not_in_statuses.split(",") if getattr(args, "not_in_statuses", None) else None
    resp = client.list_mcp_servers(project_id, limit=args.limit, offset=args.offset,
                                    not_in_statuses=not_in)
    check_response(resp, "listing mcp-servers")
    print_json(resp.json())


def cmd_get(args):
    client, project_id = build_client()
    resp = client.get_mcp_server(project_id, args.mcp_id)
    check_response(resp, f"getting mcp-server {args.mcp_id}")
    print_json(resp.json())


def _build_create_body(args, client, project_id) -> dict:
    body: dict = load_config_from_args(args)
    if args.from_marketplace:
        card_resp = client.get_marketplace_mcp_server(project_id, args.from_marketplace)
        check_response(card_resp, f"fetching marketplace mcp card {args.from_marketplace}")
        raw = card_resp.json()
        card = raw.get("predefinedMcpServer", raw)
        body.setdefault("imageSource", {})["marketplaceMcpServerId"] = card.get("id", args.from_marketplace)
        body.setdefault("description", card.get("description", ""))
    if args.name:
        body["name"] = args.name
    if args.description:
        body["description"] = args.description
    if args.instance_type_id:
        body["instanceTypeId"] = args.instance_type_id
    return body


def cmd_create(args):
    client, project_id = build_client()
    body = _build_create_body(args, client, project_id)
    resp = client.create_mcp_server(project_id, body)
    check_response(resp, "creating mcp-server")
    print_json(resp.json())


def cmd_update(args):
    client, project_id = build_client()
    body = load_config_from_args(args)
    if not body:
        print("Error: --config-json or --config-file required for update", file=sys.stderr)
        sys.exit(1)
    resp = client.update_mcp_server(project_id, args.mcp_id, body)
    check_response(resp, f"updating mcp-server {args.mcp_id}")
    print_json(resp.json())


def _confirm_destructive(action: str, target: str, auto_yes: bool) -> None:
    if auto_yes:
        return
    answer = input(f"Confirm {action} on {target}? [y/N] ")
    if answer.strip().lower() not in ("y", "yes"):
        print("Aborted.", file=sys.stderr)
        sys.exit(1)


def cmd_delete(args):
    _confirm_destructive("delete", f"mcp-server {args.mcp_id}", args.yes)
    client, project_id = build_client()
    resp = client.delete_mcp_server(project_id, args.mcp_id)
    if resp.status_code == 404:
        print(f"MCP server {args.mcp_id} already deleted", file=sys.stderr)
        return
    check_response(resp, f"deleting mcp-server {args.mcp_id}")
    print_json(resp.json() if resp.text else {"status": "deleted"})


def cmd_suspend(args):
    client, project_id = build_client()
    resp = client.suspend_mcp_server(project_id, args.mcp_id)
    check_response(resp, f"suspending mcp-server {args.mcp_id}")
    print_json(resp.json() if resp.text else {"status": "suspended"})


def cmd_resume(args):
    client, project_id = build_client()
    resp = client.resume_mcp_server(project_id, args.mcp_id)
    check_response(resp, f"resuming mcp-server {args.mcp_id}")
    print_json(resp.json() if resp.text else {"status": "resumed"})


def cmd_wait(args):
    client, project_id = build_client()
    deadline = time.time() + args.timeout
    last_status = None
    while time.time() < deadline:
        resp = client.get_mcp_server(project_id, args.mcp_id)
        check_response(resp, f"polling mcp-server {args.mcp_id}")
        raw = resp.json()
        data = raw.get("mcpServer", raw)
        status = data.get("status")
        if status != last_status:
            print(f"status={status}", file=sys.stderr)
            last_status = status
        if status in WAIT_FINAL_SUCCESS:
            print_json(data)
            return
        if status in WAIT_FINAL_FAIL:
            print(f"MCP server reached failure state: {status}", file=sys.stderr)
            reason = data.get("statusReason")
            if reason:
                print(f"statusReason: {reason}", file=sys.stderr)
            sys.exit(1)
        time.sleep(WAIT_POLL_INTERVAL)
    print(f"Timeout after {args.timeout}s. Last status: {last_status}", file=sys.stderr)
    sys.exit(1)


COMMANDS = {
    "mcp-servers.list": cmd_list,
    "mcp-servers.get": cmd_get,
    "mcp-servers.create": cmd_create,
    "mcp-servers.update": cmd_update,
    "mcp-servers.delete": cmd_delete,
    "mcp-servers.suspend": cmd_suspend,
    "mcp-servers.resume": cmd_resume,
    "mcp-servers.wait": cmd_wait,
}
