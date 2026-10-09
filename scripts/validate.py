#!/usr/bin/env python3
"""Validate the FORGE showcase examples in this repo.

Mirrors `tests/example_validation_tests.rs` in ncmlabs/forge, using the CLI:

  * `check = "ok"`      -> `forge check` must report no errors (warnings are
                           tolerated and counted, as in the core suite)
  * `check = "error"`   -> `forge check` must report errors containing `expect`
  * `merge = true`      -> one `forge check <paths...> --merge` (compose first);
                           non-merge cases are checked one file at a time, which
                           is what the core suite does per `SourceFile`
  * `run = "mock"`      -> `FORGE_MOCK=1 forge run <file>` per path, 120s timeout,
                           refused when the case has errors or warnings
  * `run = "live_only"` -> skipped (needs external agents, providers, credentials)

The FORGE binary is taken from the `FORGE` environment variable.

Usage: FORGE=./forge python3 scripts/validate.py
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "validation.toml"
MOCK_TIMEOUT_SECS = 120

ANSI = re.compile(r"\x1b\[[0-9;]*m")
# Ariadne report headers, e.g. "Error: unhandled uncertain ..." on stderr.
REPORT = re.compile(r"^(Error|Warning): (.*)$", re.MULTILINE)


def forge_binary() -> str:
    forge = os.environ.get("FORGE")
    if not forge:
        sys.exit("FORGE is not set (path to the forge binary, e.g. FORGE=./forge)")
    return forge


def run(args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        args, cwd=ROOT, env=env, capture_output=True, text=True, timeout=MOCK_TIMEOUT_SECS
    )


def check_case(forge: str, case: dict) -> tuple[bool, str, list[str], list[str]]:
    """Check one case; returns (passed, detail, errors, warnings)."""
    if case.get("merge"):
        invocations = [[*case["paths"], "--merge"]]
    else:
        invocations = [[path] for path in case["paths"]]

    output = ""
    for files in invocations:
        proc = run([forge, "check", *files])
        output += ANSI.sub("", proc.stdout + proc.stderr)
        if proc.returncode == 0:
            continue
        reports = REPORT.findall(output)
        if not reports:
            return False, f"forge check exited {proc.returncode} without diagnostics", [], []

    errors = [msg for kind, msg in REPORT.findall(output) if kind == "Error"]
    warnings = [msg for kind, msg in REPORT.findall(output) if kind == "Warning"]
    note = f" ({len(warnings)} warning(s))" if warnings else ""

    if case["check"] == "ok":
        if errors:
            return False, f"unexpected checker error: {errors[0]}", errors, warnings
        return True, f"check ok{note}", errors, warnings

    # check == "error": error diagnostics must carry every expected fragment.
    if not errors:
        return False, "expected checker errors but none were reported", errors, warnings
    missing = [text for text in case.get("expect", []) if text not in output]
    if missing:
        return False, f"missing expected diagnostic text: {missing}", errors, warnings
    return True, f"expected errors reported{note}", errors, warnings


def run_mock_case(forge: str, case: dict) -> tuple[bool, str]:
    """Run every path of a mock-runnable case with FORGE_MOCK=1."""
    env = {**os.environ, "FORGE_MOCK": "1"}
    for path in case["paths"]:
        try:
            proc = run([forge, "run", path], env=env)
        except subprocess.TimeoutExpired:
            return False, f"timed out after {MOCK_TIMEOUT_SECS}s: {path}"
        if proc.returncode != 0:
            detail = ANSI.sub("", proc.stderr).strip().splitlines()
            return False, f"mock run failed ({path}): {detail[-1] if detail else 'no output'}"
    return True, f"mock ran {len(case['paths'])} file(s)"


def main() -> int:
    forge = forge_binary()
    cases = tomllib.loads(MANIFEST.read_text())["cases"]
    failures = 0

    for case in cases:
        name = case["name"]
        if case.get("run") == "live_only":
            print(f"SKIP  {name} (live_only)")
            continue

        passed, detail, errors, warnings = check_case(forge, case)

        if passed and case.get("run") == "mock":
            if warnings:
                passed, detail = False, f"mock-runnable case has warnings: {warnings[0]}"
            else:
                passed, detail = run_mock_case(forge, case)
        if not passed:
            failures += 1
        print(f"{'PASS' if passed else 'FAIL'}  {name} - {detail}")

    total = len(cases)
    print(f"\n{total - failures}/{total} cases passed ({failures} failed)")
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.TimeoutExpired as exc:
        sys.exit(f"timeout: {exc}")
