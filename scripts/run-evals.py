#!/usr/bin/env python3
"""Check how a real model acts on the skills' text in fixed scenarios.

run-evals.py [--model ID] [--runs N] [--ref GIT_REF] [--case NAME]

Each case in evals/cases.json gives a model the named skill files, a scenario
and a question with a JSON answer, then matches one answer field against a
regular expression. A case passes only when every run passes. --ref reads the
skills from a git ref, to show a new case fails on the text before a change.
Runs `claude -p` without tools or local settings; real runs cost money.
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]


def skill_text(path, ref):
    if ref:
        return subprocess.run(["git", "-C", str(SOURCE), "show", f"{ref}:skills/{path}"],
                              capture_output=True, text=True, check=True).stdout
    return (SOURCE / "skills" / path).read_text()


def prompt(case, ref):
    skills = "\n\n".join(f"<skill path=\"{p}\">\n{skill_text(p, ref)}\n</skill>" for p in case["skills"])
    return (f"You are an agent following these skills exactly.\n\n{skills}\n\n"
            f"Scenario: {case['scenario']}\n\n{case['question']}")


def answer(text, model, cwd):
    out = subprocess.run(["claude", "-p", text, "--model", model, "--tools", "", "--setting-sources", "",
                          "--no-session-persistence"], capture_output=True, text=True, timeout=300, cwd=cwd)
    start = out.stdout.find("{")
    if out.returncode or start < 0:
        raise RuntimeError((out.stderr or out.stdout).strip()[-300:])
    return json.JSONDecoder().raw_decode(out.stdout[start:])[0]


def passes(case, reply):
    value = reply.get(case["check"]["key"])
    values = value if isinstance(value, list) else [value]
    return any(isinstance(v, str) and re.search(case["check"]["matches"], v.strip()) for v in values)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", default="claude-haiku-5-5")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--ref")
    parser.add_argument("--case")
    a = parser.parse_args(argv)
    cases = [c for c in json.loads((SOURCE / "evals/cases.json").read_text()) if a.case in (None, c["name"])]
    failed = 0
    with tempfile.TemporaryDirectory() as cwd:
        for case in cases:
            replies = []
            for _ in range(a.runs):
                try:
                    replies.append(answer(prompt(case, a.ref), a.model, cwd))
                except (RuntimeError, json.JSONDecodeError, subprocess.TimeoutExpired) as e:
                    replies.append({"error": str(e)})
            good = sum(passes(case, r) for r in replies)
            failed += good < a.runs
            print(f"{'PASS' if good == a.runs else 'FAIL'} {case['name']} {good}/{a.runs}")
            if good < a.runs:
                print("  " + json.dumps(next(r for r in replies if not passes(case, r)))[:400])
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
