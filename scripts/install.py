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


RESOURCES = ("AGENTS.md", "README.md", "rules", "skills")
ENTRIES = (".codex/AGENTS.md", ".claude/CLAUDE.md")
SCOPED_RULES = "rules/scoped"
# User skill directories read by Claude Code and Codex.
SKILL_ROOTS = (".claude/skills", ".agents/skills")
# Runner limits on installed text, verified against the noted releases.
# Hermes v0.23.2 truncates a SOUL.md beyond its 20,000-character default, the
# tightest limit any runner puts on AGENTS.md.
HERMES_SOUL_MAX_CHARS = 20_000
# Codex 0.162.0 rejects skills whose name or description exceeds these lengths.
SKILL_NAME_MAX_CHARS = 64
SKILL_DESCRIPTION_MAX_CHARS = 1_024
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


def check_length(label, text, limit):
    if len(text) > limit:
        raise ValueError(f"{label} has {len(text)} characters; the runner limit is {limit}")


def check_skill(skill):
    label = f"skills/{skill.parent.name}/SKILL.md"
    text = skill.read_text(encoding="utf-8")
    header = re.match(r"---\n(.*?)\n---\n", text, re.S)
    fields = dict(re.findall(r"^(name|description):[ \t]*(.*)$", header[1], re.M)) if header else {}
    for field, limit in (("name", SKILL_NAME_MAX_CHARS), ("description", SKILL_DESCRIPTION_MAX_CHARS)):
        value = fields.get(field, "").strip()
        if not value or value[0] in ">|":
            raise ValueError(f"{label} needs a single-line {field} in its front matter")
        check_length(f"{label} {field}", value, limit)


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
        rules = (payload / "AGENTS.md").read_text(encoding="utf-8")
        skills = sorted(path.parent for path in payload.glob("skills/*/SKILL.md"))
        for skill in skills:
            check_skill(skill / "SKILL.md")
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
        for index, profile in enumerate([hermes_home, *profiles]):
            soul = profile / "SOUL.md"
            existing = soul.read_text(encoding="utf-8") if soul.exists() else ""
            content = hermes_soul_content(existing, rules)
            check_length(f"Hermes {soul}", content, HERMES_SOUL_MAX_CHARS)
            prepared = stage / ("hermes-soul-" + str(index))
            prepared.write_text(content, encoding="utf-8")
            if soul.exists():
                shutil.copymode(soul, prepared)
            else:
                prepared.chmod(0o600)
            replacements.append((soul, prepared))
        if (payload / SCOPED_RULES).is_dir():
            link = stage / "scoped-rules"
            link.symlink_to(target / SCOPED_RULES, target_is_directory=True)
            replacements.append((home / ".claude/rules/agent-rules", link))
        names = {skill.name for skill in skills}
        for root in SKILL_ROOTS:
            for skill in skills:
                link = stage / ("skill-" + str(len(replacements)))
                link.symlink_to(target / "skills" / skill.name, target_is_directory=True)
                replacements.append((home / root / skill.name, link))
            installed = home / root
            for path in sorted(installed.iterdir()) if installed.is_dir() else ():
                if (path.name not in names and path.is_symlink()
                        and path.readlink() == target / "skills" / path.name):
                    replacements.append((path, None))
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
    print("Skills linked in:", ", ".join(SKILL_ROOTS))
    print("Hermes defaults: managed sections in", hermes_home_path(Path.home()), "and existing profiles")
    if previous:
        print("Previous installation and instructions saved in", previous)
