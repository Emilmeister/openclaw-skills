"""CLI handlers for `marketplace` subcommand."""

from helpers import build_client, check_response, print_json


def cmd_list_agents(args):
    client, project_id = build_client()
    resp = client.list_marketplace_agents(project_id, search=args.search, limit=args.limit, offset=args.offset)
    check_response(resp, "listing marketplace agents")
    print_json(resp.json())


def cmd_get_agent(args):
    client, project_id = build_client()
    resp = client.get_marketplace_agent(project_id, args.card_id)
    check_response(resp, f"getting marketplace agent {args.card_id}")
    print_json(resp.json())


def cmd_list_mcp(args):
    client, project_id = build_client()
    resp = client.list_marketplace_mcp_servers(project_id, search=args.search, limit=args.limit, offset=args.offset)
    check_response(resp, "listing marketplace mcp-servers")
    print_json(resp.json())


def cmd_get_mcp(args):
    client, project_id = build_client()
    resp = client.get_marketplace_mcp_server(project_id, args.card_id)
    check_response(resp, f"getting marketplace mcp-server {args.card_id}")
    print_json(resp.json())


COMMANDS = {
    "marketplace.list-agents": cmd_list_agents,
    "marketplace.get-agent": cmd_get_agent,
    "marketplace.list-mcp": cmd_list_mcp,
    "marketplace.get-mcp": cmd_get_mcp,
}
