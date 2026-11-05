#!/usr/bin/env python3
"""Install the reviewed local skills and retire overlapping local entry points."""
import argparse
import json
import re
import shutil
import subprocess
import tomllib
from datetime import datetime, timezone
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
RETIRED = ("sprint", "retro", "improve")


def disable_retired_codex_plugins(text):
    for name in RETIRED:
        pattern = (r'(?m)(^\[plugins\."' + re.escape(name)
                   + r'@claude-local"\][ \t]*(?:#[^\n]*)?\n)(.*?)(?=^\[|\Z)')
        def disable(match):
            body = re.sub(r"(?m)^([ \t]*enabled[ \t]*=[ \t]*)true([ \t]*(?:#[^\n]*)?)$",
                          r"\g<1>false\g<2>", match[2])
            if not re.search(r"(?m)^[ \t]*enabled[ \t]*=", body):
                body = "enabled = false\n" + body
            return match[1] + body
        text = re.sub(pattern, disable, text, flags=re.DOTALL)
    parsed = tomllib.loads(text)
    for name in RETIRED:
        entry = parsed.get("plugins", {}).get(f"{name}@claude-local")
        if entry is not None and entry.get("enabled") is not False:
            raise RuntimeError(f"Could not disable {name} in Codex configuration")
    return text


def configure_codex(text):
    text = disable_retired_codex_plugins(text)
    env = tomllib.loads(text).get("shell_environment_policy", {}).get("set", {})
    if env.get("JEV_DISABLED") == "1":
        return text
    pattern = r'(?ms)(^\[shell_environment_policy\.set\][^\n]*\n)(.*?)(?=^\[|\Z)'
    def update(match):
        body, count = re.subn(r'(?m)^[ \t]*(?:JEV_DISABLED|"JEV_DISABLED")[ \t]*=.*$',
                              'JEV_DISABLED = "1"', match[2])
        if not count:
            body = 'JEV_DISABLED = "1"\n' + body
        return match[1] + body
    if re.search(pattern, text):
        text = re.sub(pattern, update, text)
    else:
        text += '\n[shell_environment_policy.set]\nJEV_DISABLED = "1"\n'
    assert tomllib.loads(text)['shell_environment_policy']['set']['JEV_DISABLED'] == '1'
    return text


def guard(path, follow_symlink=False):
    path = Path(path)
    if follow_symlink:
        path = path.resolve(strict=True)
    probe = path if path.is_dir() and not path.is_symlink() else path.parent
    while not probe.exists():
        probe = probe.parent
    check = subprocess.run(["git", "-C", str(probe), "rev-parse", "--is-inside-work-tree"],
                           capture_output=True, text=True)
    if check.returncode == 0 and check.stdout.strip() == "true":
        raise RuntimeError(f"Refusing to install inside a git checkout: {path}")


def install(home, project_root=None):
    home = Path(home).resolve()
    guard(home)
    backup = home / ".local/state/tstack" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    export = home / ".agents/skills/claude-octopus"
    if export.exists() and not export.is_symlink():
        raise RuntimeError(f"Expected an exported Octopus symlink; left directory untouched: {export}")
    caches = [home / ".claude/plugins/cache/local/lib",
              home / ".claude-work/plugins/cache/local/lib",
              home / ".codex/plugins/cache/claude-local/lib"]
    # Reject known structural/configuration problems before the first write.
    guard(backup)
    guard(export)
    for host in (".claude", ".codex"):
        for skill in (SOURCE / "skills").iterdir():
            guard(home / host / "skills" / skill.name)
    files = [home / host / "settings.json" for host in (".claude", ".claude-work")]
    files.append(home / ".codex/config.toml")
    if project_root:
        files.append(Path(project_root) / "AGENTS.md")
    files.extend(path for cache in caches for path in cache.glob("*/skills/*/SKILL.md")
                 if path.parent.name in ("babysit-pr", "leave-pr-comment"))
    for path in files:
        if path.exists() or path.is_symlink():
            guard(path, follow_symlink=True)
            if path.name == "settings.json":
                data = json.loads(path.read_text())
                if (not isinstance(data, dict) or not isinstance(data.get("enabledPlugins", {}), dict)
                        or not isinstance(data.get("env", {}), dict)):
                    raise RuntimeError(f"Invalid plugin settings in {path}")
            elif path.name == "config.toml":
                configure_codex(path.read_text())
    backup.mkdir(parents=True)
    changes = []

    def save(path):
        path = Path(path)
        guard(path)
        item = {"path": str(path), "existed": path.exists() or path.is_symlink()}
        if item["existed"]:
            dest = backup / str(len(changes))
            if path.is_symlink():
                item["symlink"] = str(path.readlink())
            elif path.is_dir():
                shutil.copytree(path, dest, symlinks=True)
                item["backup"] = str(dest)
            else:
                shutil.copy2(path, dest)
                item["backup"] = str(dest)
        changes.append(item)
        (backup / "manifest.json").write_text(json.dumps(changes, indent=2) + "\n")

    def write(path, content):
        # Preserve a configuration symlink, but guard and back up its real file.
        if path.is_symlink():
            path = path.resolve(strict=True)
        if path.exists() and path.read_text() == content:
            return
        save(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    for host in (".claude", ".codex"):
        for skill in sorted((SOURCE / "skills").iterdir()):
            target = home / host / "skills" / skill.name
            save(target)
            if target.is_symlink():
                target.unlink()
            elif target.exists():
                shutil.rmtree(target)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(skill, target)
        # review-loop replaces upstream sol-loop; remove it so it is not discoverable.
        retired = home / host / "skills" / "sol-loop"
        if retired.is_symlink():
            save(retired)
            retired.unlink()
        elif retired.exists():
            save(retired)
            shutil.rmtree(retired)

    # Keep lib utilities and their callers. These aliases contain no delivery
    # logic; they forward to the single canonical tstack implementation.
    for cache in caches:
        for version in sorted(cache.glob("*")):
            for old, new in (("babysit-pr", "babysit-pr"),
                             ("leave-pr-comment", "leaving-pr-comments")):
                target = version / "skills" / old / "SKILL.md"
                if target.exists():
                    content = (f"---\nname: {old}\ndescription: Compatibility entry point; "
                               f"use the canonical {new} skill.\n---\n\n"
                               f"# {old}\n\nRead and follow the installed `{new}` skill "
                               "from the current host's user skills directory "
                               f"(`~/.claude/skills/{new}/SKILL.md` or "
                               f"`~/.codex/skills/{new}/SKILL.md`).\n"
                               "It owns the workflow and project communication rules. "
                               "Do not maintain a second implementation here.\n")
                    write(target, content)

    # Disable legacy plugin discovery without deleting package data or history.
    for host in (".claude", ".claude-work"):
        settings = home / host / "settings.json"
        if settings.exists():
            config = json.loads(settings.read_text())
            flags = config.setdefault("enabledPlugins", {})
            for key in ("octo@nyldn-plugins", *(f"{name}@local" for name in RETIRED)):
                flags[key] = False
            config.setdefault("env", {})["JEV_DISABLED"] = "1"
            write(settings, json.dumps(config, indent=2) + "\n")
    config_path = home / ".codex/config.toml"
    if config_path.exists():
        write(config_path, configure_codex(config_path.read_text()))

    if export.is_symlink():
        save(export)
        export.unlink()  # Preserve the source checkout and Octopus state.

    if project_root:
        instructions = Path(project_root) / "AGENTS.md"
        if instructions.exists():
            text = instructions.read_text()
            text = re.sub(r"(?ms)^## Team Sprint Mode\n.*?(?=^## |\Z)",
                          "## Delivery workflows\n\nUse the installed tstack skills for delivery: "
                          "full-stop prepares an open,\nunmerged PR; full-send merges only when "
                          "explicitly requested. review-loop and\ncouncil follow global model routing "
                          "and project permissions. process-lab owns\nproject obligations and "
                          "retrospectives. Keep Beads history; do not invoke\nretired sprint, retro, "
                          "or improve plugins. All edits obey the golden rule.\n\n", text)
            text = text.replace("`.beads/` — Beads databases: `sprint.db` (sprint board) and `retro.db` (retro actions board)",
                                "`.beads/` — Shared Beads database; board labels separate sprint and retro history")
            write(instructions, text)

    return backup, changes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--project-root", type=Path)
    args = parser.parse_args()
    backup, changes = install(args.home, args.project_root)
    print(json.dumps({"backup": str(backup), "changed_paths": len(changes)}, indent=2))
