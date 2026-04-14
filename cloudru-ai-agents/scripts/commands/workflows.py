"""CLI handlers for `workflows` (AI Workflows, Preview) subcommand.

Workflows — low-code графовые пайплайны (узлы + связи). В CLI поддерживаем
read-only + delete; full create/edit делается в IDE через UI.
"""

import sys

from helpers import build_client, check_response, print_json


def cmd_list(args):
    client, project_id = build_client()
    statuses = args.statuses.split(",") if getattr(args, "statuses", None) else None
    resp = client.list_workflows(project_id, limit=args.limit, offset=args.offset,
                                  search=args.search, statuses=statuses)
    check_response(resp, "listing workflows")
    print_json(resp.json())


def cmd_get(args):
    client, project_id = build_client()
    resp = client.get_workflow(project_id, args.workflow_id)
    check_response(resp, f"getting workflow {args.workflow_id}")
    print_json(resp.json())


def _confirm(action: str, target: str, auto_yes: bool):
    if auto_yes:
        return
    answer = input(f"Confirm {action} on {target}? [y/N] ")
    if answer.strip().lower() not in ("y", "yes"):
        print("Aborted.", file=sys.stderr)
        sys.exit(1)


def cmd_delete(args):
    _confirm("delete", f"workflow {args.workflow_id}", args.yes)
    client, project_id = build_client()
    resp = client.delete_workflow(project_id, args.workflow_id)
    check_response(resp, f"deleting workflow {args.workflow_id}")
    print_json(resp.json() if resp.text else {})


COMMANDS = {
    "workflows.list": cmd_list,
    "workflows.get": cmd_get,
    "workflows.delete": cmd_delete,
}
