"""CLI handlers for `skills` (Навыки) subcommand."""

import json
import sys

from helpers import build_client, check_response, print_json, load_config_from_args


def _serialize_metadata(metadata: dict) -> dict:
    """Skill metadata is map<string,string>: serialize list/dict values as JSON strings."""
    out = {}
    for k, v in metadata.items():
        if isinstance(v, (list, dict)):
            out[k] = json.dumps(v, ensure_ascii=False)
        else:
            out[k] = str(v) if v is not None else ""
    return out


def cmd_list(args):
    client, project_id = build_client()
    resp = client.list_skills(project_id, limit=args.limit, offset=args.offset, name=args.search)
    check_response(resp, "listing skills")
    print_json(resp.json())


def cmd_get(args):
    client, project_id = build_client()
    resp = client.get_skill(project_id, args.skill_id)
    check_response(resp, f"getting skill {args.skill_id}")
    print_json(resp.json())


def cmd_create(args):
    client, project_id = build_client()
    body: dict = load_config_from_args(args)
    if args.name:
        body["name"] = args.name
    if args.description is not None:
        body["description"] = args.description
    if args.compatibility:
        body["compatibility"] = args.compatibility

    metadata = body.get("metadata") or {}
    if args.prompt:
        metadata["prompt"] = args.prompt
    if args.prompt_file:
        with open(args.prompt_file) as f:
            metadata["prompt"] = f.read()
    metadata.setdefault("resourcesSourceType", "objectStorage")
    metadata.setdefault("resourcesRepositoryUrl", "")
    metadata.setdefault("resourcesRepositorySecrets", "[]")
    metadata.setdefault("requirementsOsEnvironment", "")
    metadata.setdefault("requirementsAppsAndTools", "")
    metadata.setdefault("requirementsSecrets", "[]")
    metadata.setdefault("artifactPaths", "[]")
    body["metadata"] = _serialize_metadata(metadata)

    body.setdefault("allowedTools", body.get("allowedTools") or [])
    if not body.get("skillSource"):
        if args.git_url:
            body["skillSource"] = {"gitSource": {"gitUrl": args.git_url,
                                                  "accessToken": args.git_token or "",
                                                  "skillFolderPaths": (args.git_folder_paths.split(",") if args.git_folder_paths else []),
                                                  "paths": []}}
        else:
            body["skillSource"] = {"plaintext": {}}

    if not body.get("name"):
        print("Error: --name required", file=sys.stderr)
        sys.exit(1)
    resp = client.create_skill(project_id, body)
    check_response(resp, "creating skill")
    print_json(resp.json())


def cmd_analyze(args):
    """Probe git/file source for skill — returns fileTree + skillFolderPaths."""
    client, project_id = build_client()
    body: dict = load_config_from_args(args)
    if args.git_url:
        body = {"gitSource": {"gitUrl": args.git_url,
                               "accessToken": args.git_token or "",
                               "skillFolderPaths": [],
                               "paths": []}}
    if not body:
        print("Error: --git-url or --config-json required", file=sys.stderr)
        sys.exit(1)
    resp = client.analyze_skill_source(project_id, body)
    check_response(resp, "analyzing skill source")
    print_json(resp.json())


def _confirm(action: str, target: str, auto_yes: bool):
    if auto_yes:
        return
    answer = input(f"Confirm {action} on {target}? [y/N] ")
    if answer.strip().lower() not in ("y", "yes"):
        print("Aborted.", file=sys.stderr)
        sys.exit(1)


def cmd_delete(args):
    _confirm("delete", f"skill {args.skill_id}", args.yes)
    client, project_id = build_client()
    resp = client.delete_skill(project_id, args.skill_id)
    check_response(resp, f"deleting skill {args.skill_id}")
    print_json(resp.json() if resp.text else {})


COMMANDS = {
    "skills.list": cmd_list,
    "skills.get": cmd_get,
    "skills.create": cmd_create,
    "skills.delete": cmd_delete,
    "skills.analyze": cmd_analyze,
}
