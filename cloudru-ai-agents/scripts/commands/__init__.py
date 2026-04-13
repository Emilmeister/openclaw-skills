"""Aggregate COMMANDS dict from all submodules."""

from commands.agents import COMMANDS as AGENTS_COMMANDS
from commands.systems import COMMANDS as SYSTEMS_COMMANDS
from commands.mcp_servers import COMMANDS as MCP_COMMANDS
from commands.instance_types import COMMANDS as IT_COMMANDS
from commands.marketplace import COMMANDS as MP_COMMANDS


COMMANDS = {}
COMMANDS.update(AGENTS_COMMANDS)
COMMANDS.update(SYSTEMS_COMMANDS)
COMMANDS.update(MCP_COMMANDS)
COMMANDS.update(IT_COMMANDS)
COMMANDS.update(MP_COMMANDS)
