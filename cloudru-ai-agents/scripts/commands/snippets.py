"""CLI handlers for `snippets` (Фрагменты) subcommand."""

import sys

from helpers import build_client, check_response, print_json, load_config_from_args


BLOCK_STYLES = [
    "SNIPPET_BLOCK_STYLE_PERSONALITY",
    "SNIPPET_BLOCK_STYLE_TASK",
    "SNIPPET_BLOCK_STYLE_CONTEXT",
    "SNIPPET_BLOCK_STYLE_CONSTRAINTS",
    "SNIPPET_BLOCK_STYLE_TONE_OF_VOICE",
    "SNIPPET_BLOCK_STYLE_ANSWER_EXAMPLES",
]


def cmd_list(args):
    client, project_id = build_client()
    block_styles = args.block_styles.split(",") if args.block_styles else None
    statuses = args.statuses.split(",") if args.statuses else None
    resp = client.list_snippets(project_id, limit=args.limit, offset=args.offset,
                                 name=args.search, block_styles=block_styles,
                                 statuses=statuses)
    check_response(resp, "listing snippets")
    print_json(resp.json())


def cmd_get(args):
    client, project_id = build_client()
    resp = client.get_snippet(project_id, args.snippet_id)
    check_response(resp, f"getting snippet {args.snippet_id}")
    print_json(resp.json())


def cmd_create(args):
    client, project_id = build_client()
    body: dict = load_config_from_args(args)
    if args.name:
        body["name"] = args.name
    if args.description is not None:
        body["description"] = args.description
    if args.content:
        body["content"] = args.content
    if args.content_file:
        with open(args.content_file) as f:
            body["content"] = f.read()
    if args.block_style:
        body["blockStyle"] = args.block_style
    if not body.get("name") or not body.get("content") or not body.get("blockStyle"):
        print("Error: --name, --content (or --content-file), and --block-style required",
              file=sys.stderr)
        sys.exit(1)
    resp = client.create_snippet(project_id, body)
    check_response(resp, "creating snippet")
    print_json(resp.json())


def cmd_update(args):
    """Update snippet. Snippet PATCH rejects `name` field (immutable) — only sends
    fields user explicitly set."""
    client, project_id = build_client()
    body: dict = load_config_from_args(args)
    if args.description is not None:
        body["description"] = args.description
    if args.content:
        body["content"] = args.content
    if args.content_file:
        with open(args.content_file) as f:
            body["content"] = f.read()
    if not body:
        print("Error: nothing to update — pass --content, --description or --config-json",
              file=sys.stderr)
        sys.exit(1)
    resp = client.update_snippet(project_id, args.snippet_id, body)
    check_response(resp, f"updating snippet {args.snippet_id}")
    print_json(resp.json() if resp.text else {})


def _confirm(action: str, target: str, auto_yes: bool):
    if auto_yes:
        return
    answer = input(f"Confirm {action} on {target}? [y/N] ")
    if answer.strip().lower() not in ("y", "yes"):
        print("Aborted.", file=sys.stderr)
        sys.exit(1)


def cmd_delete(args):
    _confirm("delete", f"snippet {args.snippet_id}", args.yes)
    client, project_id = build_client()
    resp = client.delete_snippet(project_id, args.snippet_id)
    check_response(resp, f"deleting snippet {args.snippet_id}")
    print_json(resp.json() if resp.text else {})


COMMANDS = {
    "snippets.list": cmd_list,
    "snippets.get": cmd_get,
    "snippets.create": cmd_create,
    "snippets.update": cmd_update,
    "snippets.delete": cmd_delete,
}
