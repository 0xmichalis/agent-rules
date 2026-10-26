#!/usr/bin/env python3
"""Install a local rule snapshot and the native global instruction entry files."""

from datetime import datetime, timezone
import errno
from pathlib import Path
import os
import re
import shutil
import sys
import tempfile


RESOURCES = ("AGENTS.md", "README.md", "rules", ".claude/rules", ".claude/skills")
ENTRIES = (".codex/AGENTS.md", ".claude/CLAUDE.md")
HERMES_START = "<!-- agent-rules:start -->"
HERMES_END = "<!-- agent-rules:end -->"
HERMES_PROFILE_FILES = ("config.yaml", ".env", "SOUL.md", "profile.yaml", "auth.json", "state.db")


def hermes_home_path(home):
    configured = os.environ.get("HERMES_HOME", "").strip()
    return Path(configured).expanduser().resolve() if configured else home / ".hermes"


def hermes_soul_content(existing, rules):
    section = f"{HERMES_START}\n{rules.rstrip()}\n{HERMES_END}"
    if HERMES_START not in existing and HERMES_END not in existing:
        return section + "\n\n" + existing
    if existing.count(HERMES_START) != 1 or existing.count(HERMES_END) != 1:
        raise ValueError("Invalid agent-rules managed section in Hermes SOUL.md")
    start, end = existing.index(HERMES_START), existing.index(HERMES_END)
    if end < start:
        raise ValueError("Invalid agent-rules managed section in Hermes SOUL.md")
    return existing[:start] + section + existing[end + len(HERMES_END):]


def remove(path):
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


def move_path(source, destination):
    try:
        source.rename(destination)
    except OSError as error:
        if error.errno != errno.EXDEV:
            raise
        shutil.move(str(source), str(destination))


def install(source, home):
    source, home = Path(source).resolve(), Path(home).resolve()
    if not (source / "AGENTS.md").is_file():
        raise ValueError("Source must contain AGENTS.md")
    agent_dir = home / ".agents"
    target = agent_dir / "agent-rules"
    if source == target:
        raise ValueError("Run the installer from the source checkout")
    agent_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    backup = agent_dir / "backups" / "agent-rules" / stamp
    replaced = []
    with tempfile.TemporaryDirectory(prefix=".install-rules-", dir=agent_dir) as tmp:
        stage = Path(tmp)
        payload = stage / "payload"
        payload.mkdir()
        for name in RESOURCES:
            original, copied = source / name, payload / name
            if not original.exists():
                continue
            copied.parent.mkdir(parents=True, exist_ok=True)
            if original.is_dir():
                shutil.copytree(original, copied)
            else:
                shutil.copy2(original, copied)
        replacements = [(target, payload)]
        for index, entry in enumerate(ENTRIES):
            link = stage / ("entry-" + str(index))
            link.symlink_to(target / "AGENTS.md")
            replacements.append((home / entry, link))
        legacy = home / ".config/opencode/AGENTS.md"
        if legacy.is_symlink() and legacy.readlink() == target / "AGENTS.md":
            replacements.append((legacy, None))
        hermes_home = hermes_home_path(home)
        profiles = sorted(
            path for path in (hermes_home / "profiles").glob("*")
            if path.is_dir() and not path.is_symlink()
            and path.name != "default"
            and re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", path.name)
            and not (path.parent / ".deleted" / path.name).exists()
            and any((path / name).is_file() or (path / name).is_symlink()
                    for name in HERMES_PROFILE_FILES)
        )
        rules = (payload / "AGENTS.md").read_text(encoding="utf-8")
        for index, profile in enumerate([hermes_home, *profiles]):
            soul = profile / "SOUL.md"
            existing = soul.read_text(encoding="utf-8") if soul.exists() else ""
            prepared = stage / ("hermes-soul-" + str(index))
            prepared.write_text(hermes_soul_content(existing, rules), encoding="utf-8")
            if soul.exists():
                shutil.copymode(soul, prepared)
            else:
                prepared.chmod(0o600)
            replacements.append((soul, prepared))
        if (payload / ".claude/rules").is_dir():
            link = stage / "scoped-rules"
            link.symlink_to(target / ".claude/rules", target_is_directory=True)
            replacements.append((home / ".claude/rules/agent-rules", link))
        try:
            for destination, prepared in replacements:
                destination.parent.mkdir(parents=True, exist_ok=True)
                saved = None
                if destination.exists() or destination.is_symlink():
                    if destination.is_relative_to(home):
                        relative = destination.relative_to(home)
                    else:
                        relative = Path("hermes-home") / destination.relative_to(hermes_home)
                    saved = backup / relative
                    saved.parent.mkdir(parents=True, exist_ok=True)
                    move_path(destination, saved)
                replaced.append((destination, saved))
                if prepared is not None:
                    move_path(prepared, destination)
        except Exception:
            for destination, saved in reversed(replaced):
                try:
                    remove(destination)
                    if saved is not None:
                        move_path(saved, destination)
                except Exception as rollback_error:
                    print(
                        f"Rollback failed for {destination}: {rollback_error}. "
                        f"Backups retained at {backup}",
                        file=sys.stderr,
                    )
            raise
    return backup if backup.exists() else None


if __name__ == "__main__":
    checkout = Path(__file__).resolve().parents[1]
    previous = install(checkout, Path.home())
    print("Installed shared rules from", checkout)
    print("Native entry files:", ", ".join(ENTRIES))
    print("Hermes defaults: managed sections in", hermes_home_path(Path.home()), "and existing profiles")
    if previous:
        print("Previous installation and instructions saved in", previous)
