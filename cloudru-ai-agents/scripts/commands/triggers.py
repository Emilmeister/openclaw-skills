"""CLI handlers for `triggers` — attach event sources to an agent.

Two trigger types in UI: Telegram (bot pulls messages from @BotFather bot and
passes them into agent chat) and Schedule (cron-like periodic invocation).

The body schema is complex (variant type + whitelist + secret refs). CLI does
not hand-hold each shape — users pass a full body via `--config-json` or
`--config-file`. Use `triggers check-name` first; creation fails with 409 if
name is taken.
"""

import sys

from helpers import build_client, check_response, print_json, load_config_from_args


def cmd_list(args):
    client, project_id = build_client()
    not_in = args.not_in_statuses.split(",") if getattr(args, "not_in_statuses", None) else None
    resp = client.list_agent_triggers(project_id, args.agent_id,
                                       limit=args.limit, offset=args.offset,
                                       not_in_statuses=not_in)
    check_response(resp, f"listing triggers for agent {args.agent_id}")
    print_json(resp.json())


def cmd_get(args):
    client, project_id = build_client()
    resp = client.get_agent_trigger(project_id, args.agent_id, args.trigger_id)
    check_response(resp, f"getting trigger {args.trigger_id}")
    print_json(resp.json())


def cmd_check_name(args):
    client, project_id = build_client()
    resp = client.check_trigger_name(project_id, args.agent_id, args.name)
    check_response(resp, f"checking trigger name {args.name}")
    print_json(resp.json() if resp.text else {"available": True})


def cmd_create(args):
    body = load_config_from_args(args)
    if not body:
        print("Error: --config-json or --config-file required. Trigger body "
              "schema is complex (externalTriggerOptions variant). See docs.",
              file=sys.stderr)
        sys.exit(1)
    if args.name:
        body["name"] = args.name
    if "name" not in body:
        print("Error: 'name' is required (letters+digits+hyphen, 5-50 chars)",
              file=sys.stderr)
        sys.exit(1)
    client, project_id = build_client()
    resp = client.create_agent_trigger(project_id, args.agent_id, body)
    check_response(resp, f"creating trigger on agent {args.agent_id}")
    print_json(resp.json())


def cmd_update(args):
    body = load_config_from_args(args)
    if not body:
        print("Error: --config-json or --config-file required", file=sys.stderr)
        sys.exit(1)
    client, project_id = build_client()
    resp = client.update_agent_trigger(project_id, args.agent_id, args.trigger_id, body)
    check_response(resp, f"updating trigger {args.trigger_id}")
    print_json(resp.json() if resp.text else {})


def _confirm(action, target, auto_yes):
    if auto_yes:
        return
    if input(f"Confirm {action} on {target}? [y/N] ").strip().lower() not in ("y", "yes"):
        print("Aborted.", file=sys.stderr)
        sys.exit(1)


def cmd_delete(args):
    _confirm("delete", f"trigger {args.trigger_id}", args.yes)
    client, project_id = build_client()
    resp = client.delete_agent_trigger(project_id, args.agent_id, args.trigger_id)
    check_response(resp, f"deleting trigger {args.trigger_id}")
    print_json(resp.json() if resp.text else {"status": "deleted"})


COMMANDS = {
    "triggers.list": cmd_list,
    "triggers.get": cmd_get,
    "triggers.check-name": cmd_check_name,
    "triggers.create": cmd_create,
    "triggers.update": cmd_update,
    "triggers.delete": cmd_delete,
}
