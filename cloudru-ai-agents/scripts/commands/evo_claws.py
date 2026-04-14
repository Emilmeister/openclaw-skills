"""CLI handlers for `evo-claws` (Evo Claw, Preview) subcommand.

Evo Claw — managed OpenClaw gateway as a service. CLI поддерживает
только read; create/delete делается через UI/marketplace конфиг.
"""

from helpers import build_client, check_response, print_json


def cmd_list(args):
    client, project_id = build_client()
    statuses = args.statuses.split(",") if getattr(args, "statuses", None) else None
    resp = client.list_evo_claws(project_id, limit=args.limit, offset=args.offset,
                                  statuses=statuses)
    check_response(resp, "listing evo-claws")
    print_json(resp.json())


def cmd_get(args):
    client, project_id = build_client()
    resp = client.get_evo_claw(project_id, args.evoclaw_id)
    check_response(resp, f"getting evo-claw {args.evoclaw_id}")
    print_json(resp.json())


COMMANDS = {
    "evo-claws.list": cmd_list,
    "evo-claws.get": cmd_get,
}
