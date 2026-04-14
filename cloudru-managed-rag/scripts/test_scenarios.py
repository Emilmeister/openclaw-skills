#!/usr/bin/env python3
"""Тестовые сценарии для Managed RAG скилла.

Проверяет все пользовательские сценарии:
  1. Пользователь начинает с нуля — list, нет KB
  2. Пользователь хочет посмотреть свои KB — list
  3. Пользователь хочет детали KB — get
  4. Пользователь хочет версии — versions, version-detail
  5. Пользователь хочет искать — search
  6. Пользователь хочет ответ — ask
  7. Пользователь хочет удалить KB — delete
  8. Пользователь хочет setup --dry-run — проверка pipeline без API
  9. Ошибки: несуществующий KB, невалидный запрос

Запуск: cd scripts && python3 test_scenarios.py
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

PASS = 0
FAIL = 0
RESULTS = []


_SAFE_ARG_RE = re.compile(r"^[a-zA-Z0-9_./:@=,{}\[\] \"'-]+$")


def _validate_cmd_args(cmd: list[str]) -> None:
    """Validate CLI arguments to prevent injection."""
    for arg in cmd:
        if not _SAFE_ARG_RE.match(arg):
            raise ValueError(f"Unsafe command argument detected: {arg!r}")


def run(description: str, cmd: list[str], expect_success: bool = True,
        expect_in_output: str | None = None, expect_not_in_output: str | None = None) -> bool:
    """Run a CLI command and check expectations."""
    global PASS, FAIL

    _validate_cmd_args(cmd)
    full_cmd = [sys.executable, "managed_rag.py"] + cmd
    try:
        result = subprocess.run(
            full_cmd, capture_output=True, text=True, timeout=120,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        output = result.stdout + result.stderr
        success = (result.returncode == 0) == expect_success

        if expect_in_output and expect_in_output not in output:
            success = False
        if expect_not_in_output and expect_not_in_output in output:
            success = False

    except subprocess.TimeoutExpired:
        output = "TIMEOUT"
        success = False
    except Exception as e:
        output = str(e)
        success = False

    status = "PASS" if success else "FAIL"
    if success:
        PASS += 1
    else:
        FAIL += 1

    RESULTS.append((status, description))
    print(f"  [{status}] {description}")
    if not success:
        # Show truncated output for debugging
        print(f"         cmd: {' '.join(cmd)}")
        print(f"         exit: {result.returncode if 'result' in dir() else '?'}")
        snippet = output.strip()[:200] if output else "(empty)"
        print(f"         output: {snippet}")
    return success


def main():
    # Check we have .env
    if not os.environ.get("CP_CONSOLE_KEY_ID"):
        # Try loading from .env
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, _, v = line.partition("=")
                        v = v.strip().strip('"').strip("'")
                        os.environ.setdefault(k.strip(), v)

    if not os.environ.get("CP_CONSOLE_KEY_ID"):
        print("Нет credentials в .env — пропускаю тесты с API")
        sys.exit(1)

    kb_id = os.environ.get("MANAGED_RAG_KB_ID", "")
    print(f"Using KB: {kb_id or '(not set)'}\n")

    # =========================================================================
    print("=== Сценарий 1: Пользователь смотрит список KB ===")
    # =========================================================================
    run("list — показывает KB",
        ["list"],
        expect_in_output="knowledge_bases")

    # =========================================================================
    print("\n=== Сценарий 2: Пользователь смотрит детали KB ===")
    # =========================================================================
    if kb_id:
        run("get — детали KB по ID",
            ["get", "--kb-id", kb_id],
            expect_in_output="status")

        run("get — детали KB из env (без --kb-id)",
            ["get"],
            expect_in_output="status")
    else:
        print("  [SKIP] нет MANAGED_RAG_KB_ID")

    # =========================================================================
    print("\n=== Сценарий 3: Пользователь смотрит версии KB ===")
    # =========================================================================
    version_id = None
    if kb_id:
        run("versions — список версий",
            ["versions", "--kb-id", kb_id],
            expect_in_output="versions")

        # Grab version_id from output for next test
        try:
            _validate_cmd_args(["versions", "--kb-id", kb_id])
            result = subprocess.run(
                [sys.executable, "managed_rag.py", "versions", "--kb-id", kb_id],
                capture_output=True, text=True, timeout=30,
                cwd=os.path.dirname(os.path.abspath(__file__)),
            )
            data = json.loads(result.stdout)
            versions = data.get("versions", [])
            if versions:
                version_id = versions[0].get("version_id")
        except Exception:
            pass

        if version_id:
            run("version-detail — детали версии",
                ["version-detail", "--version-id", version_id, "--kb-id", kb_id],
                expect_in_output="version_id")
        else:
            print("  [SKIP] нет version_id для version-detail")
    else:
        print("  [SKIP] нет MANAGED_RAG_KB_ID")

    # =========================================================================
    print("\n=== Сценарий 4: Пользователь ищет по документам ===")
    # =========================================================================
    if kb_id:
        run("search — семантический поиск",
            ["search", "--query", "test", "--limit", "2"],
            expect_in_output="chunks")

        run("search — с указанием KB",
            ["search", "--query", "requirements", "--limit", "1", "--kb-id", kb_id],
            expect_in_output="chunks")
    else:
        print("  [SKIP] нет MANAGED_RAG_KB_ID")

    # =========================================================================
    print("\n=== Сценарий 5: Пользователь задаёт вопрос (RAG) ===")
    # =========================================================================
    if kb_id:
        run("ask — вопрос через RAG pipeline",
            ["ask", "--query", "What is this document about?", "--limit", "2"],
            expect_in_output="chunks")
    else:
        print("  [SKIP] нет MANAGED_RAG_KB_ID")

    # =========================================================================
    print("\n=== Сценарий 6: Setup dry-run ===")
    # =========================================================================
    # CP_CONSOLE_KEY_ID/SECRET/PROJECT_ID already in env from .env
    run("setup --dry-run — preview без API",
        ["setup",
         "--docs-path", os.path.dirname(os.path.abspath(__file__)),
         "--kb-name", "dry-run-test",
         "--bucket-name", "dry-run-bucket",
         "--dry-run"],
        expect_in_output="dry_run")

    # =========================================================================
    print("\n=== Сценарий 7: Обработка ошибок ===")
    # =========================================================================
    run("get — несуществующий KB → ошибка",
        ["get", "--kb-id", "00000000-0000-0000-0000-000000000000"],
        expect_success=False)

    run("search — без query → ошибка argparse",
        ["search"],
        expect_success=False)

    run("setup — без обязательных аргов → ошибка",
        ["setup"],
        expect_success=False)

    # =========================================================================
    print("\n=== Сценарий 8: Удаление тестовой KB ===")
    # =========================================================================
    # Find an AB test KB to delete (expendable)
    delete_kb_id = None
    try:
        result = subprocess.run(
            [sys.executable, "managed_rag.py", "list"],
            capture_output=True, text=True, timeout=30,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        data = json.loads(result.stdout)
        for kb in data.get("knowledge_bases", []):
            if kb.get("name", "").startswith("ab-test-"):
                delete_kb_id = kb["id"]
                break
    except Exception:
        pass

    if delete_kb_id:
        run(f"delete — удаление тестовой KB ({delete_kb_id[:8]}...)",
            ["delete", "--kb-id", delete_kb_id],
            expect_in_output="deleted")
    else:
        print("  [SKIP] нет expendable KB для удаления")

    # =========================================================================
    print(f"\n{'='*50}")
    print(f"ИТОГО: {PASS} passed, {FAIL} failed из {PASS+FAIL}")
    print(f"{'='*50}")
    for status, desc in RESULTS:
        print(f"  [{status}] {desc}")

    sys.exit(1 if FAIL > 0 else 0)


if __name__ == "__main__":
    main()
