"""CLI handlers for `systems` (agent-systems) subcommand."""

import sys
import time

from helpers import build_client, check_response, print_json, load_config_from_args


WAIT_FINAL_SUCCESS = {"AGENT_SYSTEM_STATUS_RUNNING", "AGENT_SYSTEM_STATUS_COOLED"}
WAIT_FINAL_FAIL = {
    "AGENT_SYSTEM_STATUS_FAILED",
    "AGENT_SYSTEM_STATUS_AGENT_UNAVAILABLE",
    "AGENT_SYSTEM_STATUS_IMAGE_UNAVAILABLE",
    "AGENT_SYSTEM_STATUS_ON_DELETION",
    "AGENT_SYSTEM_STATUS_DELETED",
}
WAIT_POLL_INTERVAL = 15


def cmd_list(args):
    client, project_id = build_client()
    resp = client.list_systems(project_id, limit=args.limit, offset=args.offset)
    check_response(resp, "listing systems")
    print_json(resp.json())


def cmd_get(args):
    client, project_id = build_client()
    resp = client.get_system(project_id, args.system_id)
    check_response(resp, f"getting system {args.system_id}")
    print_json(resp.json())


def _build_create_body(args) -> dict:
    body: dict = load_config_from_args(args)
    if args.name:
        body["name"] = args.name
    if args.description:
        body["description"] = args.description
    if args.instance_type_id:
        body["instanceTypeId"] = args.instance_type_id
    return body


def cmd_create(args):
    client, project_id = build_client()
    body = _build_create_body(args)
    resp = client.create_system(project_id, body)
    check_response(resp, "creating system")
    print_json(resp.json())


def cmd_update(args):
    client, project_id = build_client()
    body = load_config_from_args(args)
    if not body:
        print("Error: --config-json or --config-file required for update", file=sys.stderr)
        sys.exit(1)
    resp = client.update_system(project_id, args.system_id, body)
    check_response(resp, f"updating system {args.system_id}")
    print_json(resp.json())


def _confirm_destructive(action: str, target: str, auto_yes: bool) -> None:
    if auto_yes:
        return
    answer = input(f"Confirm {action} on {target}? [y/N] ")
    if answer.strip().lower() not in ("y", "yes"):
        print("Aborted.", file=sys.stderr)
        sys.exit(1)


def cmd_delete(args):
    _confirm_destructive("delete", f"system {args.system_id}", args.yes)
    client, project_id = build_client()
    resp = client.delete_system(project_id, args.system_id)
    if resp.status_code == 404:
        print(f"System {args.system_id} already deleted", file=sys.stderr)
        return
    check_response(resp, f"deleting system {args.system_id}")
    print_json(resp.json() if resp.text else {"status": "deleted"})


def cmd_suspend(args):
    client, project_id = build_client()
    resp = client.suspend_system(project_id, args.system_id)
    check_response(resp, f"suspending system {args.system_id}")
    print_json(resp.json() if resp.text else {"status": "suspended"})


def cmd_resume(args):
    client, project_id = build_client()
    resp = client.resume_system(project_id, args.system_id)
    check_response(resp, f"resuming system {args.system_id}")
    print_json(resp.json() if resp.text else {"status": "resumed"})


def cmd_wait(args):
    client, project_id = build_client()
    deadline = time.time() + args.timeout
    last_status = None
    while time.time() < deadline:
        resp = client.get_system(project_id, args.system_id)
        check_response(resp, f"polling system {args.system_id}")
        raw = resp.json()
        data = raw.get("agentSystem", raw)
        status = data.get("status")
        if status != last_status:
            print(f"status={status}", file=sys.stderr)
            last_status = status
        if status in WAIT_FINAL_SUCCESS:
            print_json(data)
            return
        if status in WAIT_FINAL_FAIL:
            print(f"System reached failure state: {status}", file=sys.stderr)
            reason = data.get("statusReason")
            if reason:
                print(f"statusReason: {reason}", file=sys.stderr)
            sys.exit(1)
        time.sleep(WAIT_POLL_INTERVAL)
    print(f"Timeout after {args.timeout}s. Last status: {last_status}", file=sys.stderr)
    sys.exit(1)


COMMANDS = {
    "systems.list": cmd_list,
    "systems.get": cmd_get,
    "systems.create": cmd_create,
    "systems.update": cmd_update,
    "systems.delete": cmd_delete,
    "systems.suspend": cmd_suspend,
    "systems.resume": cmd_resume,
    "systems.wait": cmd_wait,
}
