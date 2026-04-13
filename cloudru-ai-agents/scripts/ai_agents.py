#!/usr/bin/env python3
"""Cloud.ru AI Agents CLI.

Manage Agents, Agent Systems, MCP Servers on Cloud.ru AI Agents API.

Requires environment variables:
  CP_CONSOLE_KEY_ID    IAM access key ID
  CP_CONSOLE_SECRET    IAM access key secret
  PROJECT_ID           Cloud.ru project ID

Run `ai_agents.py <group> --help` to see subcommands.
"""

import argparse
import os
import sys

from commands import COMMANDS


def _add_limit_offset(p):
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--offset", type=int, default=0)


def _add_config_source(p):
    p.add_argument("--config-json", help="Inline JSON body")
    p.add_argument("--config-file", help="Path to JSON file with body")


def build_parser():
    parser = argparse.ArgumentParser(prog="ai_agents", description="Cloud.ru AI Agents CLI")
    top = parser.add_subparsers(dest="group", required=True)

    # ---- agents ----
    agents = top.add_parser("agents", help="Manage agents")
    agsub = agents.add_subparsers(dest="subcommand", required=True)

    p = agsub.add_parser("list", help="List agents")
    _add_limit_offset(p)

    p = agsub.add_parser("get", help="Get agent details")
    p.add_argument("agent_id")

    p = agsub.add_parser("create", help="Create agent")
    p.add_argument("--name")
    p.add_argument("--description")
    p.add_argument("--instance-type-id")
    p.add_argument("--mcp-server-id")
    p.add_argument("--from-marketplace", help="Create from marketplace card ID")
    _add_config_source(p)

    p = agsub.add_parser("update", help="Update agent")
    p.add_argument("agent_id")
    _add_config_source(p)

    p = agsub.add_parser("delete", help="Delete agent")
    p.add_argument("agent_id")
    p.add_argument("--yes", action="store_true", help="Skip confirmation")

    p = agsub.add_parser("suspend", help="Suspend agent")
    p.add_argument("agent_id")

    p = agsub.add_parser("resume", help="Resume agent")
    p.add_argument("agent_id")

    p = agsub.add_parser("wait", help="Poll until agent reaches RUNNING/COOLED")
    p.add_argument("agent_id")
    p.add_argument("--timeout", type=int, default=600)

    # ---- systems ----
    systems = top.add_parser("systems", help="Manage agent systems")
    ssub = systems.add_subparsers(dest="subcommand", required=True)

    p = ssub.add_parser("list"); _add_limit_offset(p)
    p = ssub.add_parser("get"); p.add_argument("system_id")
    p = ssub.add_parser("create")
    p.add_argument("--name"); p.add_argument("--description"); p.add_argument("--instance-type-id")
    _add_config_source(p)
    p = ssub.add_parser("update"); p.add_argument("system_id"); _add_config_source(p)
    p = ssub.add_parser("delete"); p.add_argument("system_id"); p.add_argument("--yes", action="store_true")
    p = ssub.add_parser("suspend"); p.add_argument("system_id")
    p = ssub.add_parser("resume"); p.add_argument("system_id")
    p = ssub.add_parser("wait"); p.add_argument("system_id"); p.add_argument("--timeout", type=int, default=600)

    # ---- mcp-servers ----
    mcp = top.add_parser("mcp-servers", help="Manage MCP servers")
    msub = mcp.add_subparsers(dest="subcommand", required=True)

    p = msub.add_parser("list"); _add_limit_offset(p)
    p = msub.add_parser("get"); p.add_argument("mcp_id")
    p = msub.add_parser("create")
    p.add_argument("--name"); p.add_argument("--description"); p.add_argument("--instance-type-id")
    p.add_argument("--from-marketplace"); _add_config_source(p)
    p = msub.add_parser("update"); p.add_argument("mcp_id"); _add_config_source(p)
    p = msub.add_parser("delete"); p.add_argument("mcp_id"); p.add_argument("--yes", action="store_true")
    p = msub.add_parser("suspend"); p.add_argument("mcp_id")
    p = msub.add_parser("resume"); p.add_argument("mcp_id")
    p = msub.add_parser("wait"); p.add_argument("mcp_id"); p.add_argument("--timeout", type=int, default=600)

    # ---- instance-types ----
    it = top.add_parser("instance-types", help="Instance types catalog")
    itsub = it.add_subparsers(dest="subcommand", required=True)
    itsub.add_parser("list", help="List instance types")

    # ---- marketplace ----
    mp = top.add_parser("marketplace", help="Marketplace catalog")
    mpsub = mp.add_subparsers(dest="subcommand", required=True)

    p = mpsub.add_parser("list-agents")
    p.add_argument("--search"); _add_limit_offset(p)

    p = mpsub.add_parser("get-agent"); p.add_argument("card_id")

    p = mpsub.add_parser("list-mcp")
    p.add_argument("--search"); _add_limit_offset(p)

    p = mpsub.add_parser("get-mcp"); p.add_argument("card_id")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    key = f"{args.group}.{args.subcommand}"
    handler = COMMANDS.get(key)
    if handler is None:
        print(f"Unknown command: {key}", file=sys.stderr)
        sys.exit(1)
    handler(args)


if __name__ == "__main__":
    main()
