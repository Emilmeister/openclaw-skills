"""CLI handlers for `triggers` subcommand.

Триггеры (Telegram/Email/Schedule) привязываются к агенту:
GET /agents/{agentId}/triggers. UI вкладки в текущем релизе нет —
доступен только list через CLI.
"""

from helpers import build_client, check_response, print_json


def cmd_list(args):
    client, project_id = build_client()
    resp = client.list_agent_triggers(project_id, args.agent_id,
                                       limit=args.limit, offset=args.offset)
    check_response(resp, f"listing triggers for agent {args.agent_id}")
    print_json(resp.json())


COMMANDS = {
    "triggers.list": cmd_list,
}
