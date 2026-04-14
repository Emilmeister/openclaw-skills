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

    p = mpsub.add_parser("list-prompts")
    p.add_argument("--search"); _add_limit_offset(p)

    p = mpsub.add_parser("get-prompt"); p.add_argument("card_id")

    p = mpsub.add_parser("list-skills")
    p.add_argument("--search"); _add_limit_offset(p)

    p = mpsub.add_parser("list-snippets")
    p.add_argument("--search"); p.add_argument("--block-styles",
        help="Comma-separated PREDEFINED_SNIPPET_BLOCK_STYLE_* values")
    _add_limit_offset(p)

    # ---- prompts ----
    prompts = top.add_parser("prompts", help="Manage prompts (system prompts library)")
    psub = prompts.add_subparsers(dest="subcommand", required=True)

    p = psub.add_parser("list", help="List prompts")
    p.add_argument("--search", help="Filter by name substring")
    p.add_argument("--not-in-statuses",
        help="Comma-separated PROMPT_STATUS_* to exclude (default: DELETED, ON_DELETION)")
    _add_limit_offset(p)

    p = psub.add_parser("get"); p.add_argument("prompt_id")

    p = psub.add_parser("create", help="Create prompt (manual or from marketplace card)")
    p.add_argument("--name")
    p.add_argument("--description")
    p.add_argument("--prompt", help="Inline prompt text")
    p.add_argument("--prompt-file", help="Path to file with prompt text")
    p.add_argument("--from-marketplace", help="Marketplace prompt card ID")
    _add_config_source(p)

    p = psub.add_parser("update", help="Update prompt (full-body PATCH; merges with current state)")
    p.add_argument("prompt_id")
    p.add_argument("--name")
    p.add_argument("--description")
    p.add_argument("--prompt")
    p.add_argument("--prompt-file")
    _add_config_source(p)

    p = psub.add_parser("delete"); p.add_argument("prompt_id"); p.add_argument("--yes", action="store_true")

    p = psub.add_parser("versions", help="List prompt versions")
    p.add_argument("prompt_id")
    _add_limit_offset(p)

    # ---- snippets (Фрагменты) ----
    snippets = top.add_parser("snippets", help="Manage snippets (prompt fragments)")
    snsub = snippets.add_subparsers(dest="subcommand", required=True)

    p = snsub.add_parser("list", help="List snippets")
    p.add_argument("--search")
    p.add_argument("--block-styles",
        help="Comma-separated SNIPPET_BLOCK_STYLE_* (PERSONALITY/TASK/CONTEXT/CONSTRAINTS/TONE_OF_VOICE/ANSWER_EXAMPLES)")
    p.add_argument("--statuses", help="Comma-separated SNIPPET_STATUS_* values")
    _add_limit_offset(p)

    p = snsub.add_parser("get"); p.add_argument("snippet_id")

    p = snsub.add_parser("create")
    p.add_argument("--name")
    p.add_argument("--description")
    p.add_argument("--content", help="Inline snippet body")
    p.add_argument("--content-file", help="Path to file with snippet body")
    p.add_argument("--block-style", help="SNIPPET_BLOCK_STYLE_PERSONALITY|TASK|CONTEXT|CONSTRAINTS|TONE_OF_VOICE|ANSWER_EXAMPLES")
    _add_config_source(p)

    p = snsub.add_parser("update")
    p.add_argument("snippet_id")
    p.add_argument("--name"); p.add_argument("--description")
    p.add_argument("--content"); p.add_argument("--content-file")
    p.add_argument("--block-style")
    _add_config_source(p)

    p = snsub.add_parser("delete"); p.add_argument("snippet_id"); p.add_argument("--yes", action="store_true")

    # ---- skills (Навыки) ----
    skills = top.add_parser("skills", help="Manage skills (Anthropic-style markdown skills)")
    sksub = skills.add_subparsers(dest="subcommand", required=True)

    p = sksub.add_parser("list"); p.add_argument("--search"); _add_limit_offset(p)
    p = sksub.add_parser("get"); p.add_argument("skill_id")

    p = sksub.add_parser("create", help="Create skill (plaintext or from git)")
    p.add_argument("--name")
    p.add_argument("--description")
    p.add_argument("--compatibility", help="Compatibility note (e.g. 'Python 3.11+')")
    p.add_argument("--prompt", help="Inline skill body (plaintext source)")
    p.add_argument("--prompt-file", help="Path to .md file with skill body")
    p.add_argument("--git-url", help="Import from git URL (sets gitSource)")
    p.add_argument("--git-token", help="Git access token if private repo")
    p.add_argument("--git-folder-paths", help="Comma-separated paths inside repo")
    _add_config_source(p)

    p = sksub.add_parser("delete"); p.add_argument("skill_id"); p.add_argument("--yes", action="store_true")

    p = sksub.add_parser("analyze", help="Analyze git source — preview fileTree before create")
    p.add_argument("--git-url"); p.add_argument("--git-token")
    _add_config_source(p)

    # ---- workflows (Preview) ----
    workflows = top.add_parser("workflows", help="AI Workflows (low-code, read-only via CLI)")
    wsub = workflows.add_subparsers(dest="subcommand", required=True)
    p = wsub.add_parser("list"); p.add_argument("--search"); _add_limit_offset(p)
    p = wsub.add_parser("get"); p.add_argument("workflow_id")
    p = wsub.add_parser("delete"); p.add_argument("workflow_id"); p.add_argument("--yes", action="store_true")

    # ---- triggers ----
    triggers = top.add_parser("triggers", help="Agent triggers (Telegram/Email/Schedule)")
    tsub = triggers.add_subparsers(dest="subcommand", required=True)
    p = tsub.add_parser("list", help="List triggers attached to an agent")
    p.add_argument("agent_id")
    _add_limit_offset(p)

    # ---- evo-claws (Preview) ----
    ec = top.add_parser("evo-claws", help="Evo Claw managed gateways (read-only)")
    ecsub = ec.add_subparsers(dest="subcommand", required=True)
    p = ecsub.add_parser("list"); _add_limit_offset(p)
    p = ecsub.add_parser("get"); p.add_argument("evoclaw_id")

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
