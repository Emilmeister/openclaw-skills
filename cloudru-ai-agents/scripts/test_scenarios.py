#!/usr/bin/env python3
"""Integration-style scenarios for AI Agents CLI.

Runs a full E2E with cleanup in try/finally to avoid leaking resources.
Requires CP_CONSOLE_KEY_ID/SECRET/PROJECT_ID in env.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time

PASS = 0
FAIL = 0
RESULTS = []


def run(description: str, cmd: list, expect_success: bool = True,
        expect_in_output: str = None) -> dict:
    global PASS, FAIL
    full_cmd = [sys.executable, "ai_agents.py"] + cmd
    try:
        result = subprocess.run(
            full_cmd, capture_output=True, text=True, timeout=180,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        output = result.stdout + result.stderr
        success = (result.returncode == 0) == expect_success
        if expect_in_output and expect_in_output not in output:
            success = False
    except subprocess.TimeoutExpired:
        output = "TIMEOUT"
        success = False
        result = None

    status = "PASS" if success else "FAIL"
    if success:
        PASS += 1
    else:
        FAIL += 1
    print(f"  [{status}] {description}")
    if not success:
        print(f"         cmd: {' '.join(cmd)}")
        print(f"         exit: {result.returncode if result else '?'}")
        print(f"         output: {output.strip()[:300]}")
    RESULTS.append((status, description))
    return {"ok": success, "stdout": result.stdout if result else "", "output": output}


def main():
    if not os.environ.get("CP_CONSOLE_KEY_ID"):
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    if not os.environ.get("CP_CONSOLE_KEY_ID"):
        print("No CP_CONSOLE_KEY_ID — aborting")
        sys.exit(1)

    ts = int(time.time())
    mcp_name = f"e2e-mcp-{ts}"
    agent_name = f"e2e-agent-{ts}"

    mcp_id = None
    agent_id = None
    instance_type_id = None

    try:
        print("=== Read-only ===")
        run("instance-types list", ["instance-types", "list"])
        r = run("marketplace list-mcp", ["marketplace", "list-mcp", "--limit", "5"])
        mcp_card_id = None
        if r["ok"]:
            try:
                cards = json.loads(r["stdout"]).get("data", [])
                if cards:
                    mcp_card_id = cards[0]["id"]
                    print(f"    picked mcp card: {mcp_card_id}")
            except Exception:
                pass

        r = run("marketplace list-agents", ["marketplace", "list-agents", "--limit", "5"])
        agent_card_id = None
        if r["ok"]:
            try:
                cards = json.loads(r["stdout"]).get("data", [])
                if cards:
                    agent_card_id = cards[0]["id"]
                    print(f"    picked agent card: {agent_card_id}")
            except Exception:
                pass

        r = run("instance-types list (for id)", ["instance-types", "list"])
        if r["ok"]:
            try:
                items = json.loads(r["stdout"]).get("data", [])
                if items:
                    instance_type_id = items[0].get("id")
                    print(f"    picked instance type: {instance_type_id}")
            except Exception:
                pass

        if not instance_type_id or not mcp_card_id or not agent_card_id:
            print("\n[SKIP] E2E creation — missing instance_type_id or marketplace cards")
            return

        print("\n=== E2E create flow ===")
        r = run("mcp-servers create", [
            "mcp-servers", "create",
            "--name", mcp_name,
            "--instance-type-id", instance_type_id,
            "--from-marketplace", mcp_card_id,
        ])
        if r["ok"]:
            try:
                mcp_id = json.loads(r["stdout"])["id"]
                print(f"    created mcp: {mcp_id}")
            except Exception:
                pass

        if mcp_id:
            run("mcp-servers wait", ["mcp-servers", "wait", mcp_id, "--timeout", "300"])

            r = run("agents create", [
                "agents", "create",
                "--name", agent_name,
                "--instance-type-id", instance_type_id,
                "--mcp-server-id", mcp_id,
                "--from-marketplace", agent_card_id,
            ])
            if r["ok"]:
                try:
                    agent_id = json.loads(r["stdout"])["id"]
                    print(f"    created agent: {agent_id}")
                except Exception:
                    pass

            if agent_id:
                run("agents wait", ["agents", "wait", agent_id, "--timeout", "300"])
                run("agents get has publicUrl", ["agents", "get", agent_id],
                    expect_in_output="publicUrl")

    finally:
        print("\n=== Cleanup ===")
        if agent_id:
            run("cleanup agents delete", ["agents", "delete", agent_id, "--yes"])
        if mcp_id:
            run("cleanup mcp-servers delete", ["mcp-servers", "delete", mcp_id, "--yes"])

        print(f"\n{'='*50}")
        print(f"ИТОГО: {PASS} passed, {FAIL} failed из {PASS+FAIL}")
        print(f"{'='*50}")
        for status, desc in RESULTS:
            print(f"  [{status}] {desc}")

    sys.exit(1 if FAIL > 0 else 0)


if __name__ == "__main__":
    main()
