"""Maintenance tool for the built-in skills in ``content/``: verify the folder against its lock file, or print a hash.

Standard library only, so it runs with any Python 3 interpreter and without the Build Tools repository::

    python scripts/built_in_skills.py verify
    python scripts/built_in_skills.py hash <slug>

Layout: ``content/<slug>/SKILL.md`` (plus supporting files), ``content/built-in-skills.lock.json`` and the
bundle-level entries in ``BUNDLE_LEVEL_ENTRIES``. Each lock entry records the slug, the version, the source
(``github`` with repository, ref and path, or ``local`` with path) and ``contentHash``.

Content hash (``sha256:<hex>``): list every regular file under the skill folder, with its path relative
to that folder in POSIX form, sorted by that path. Take the SHA-256 of each file's bytes as stored (no
line-ending normalisation). The hash is the SHA-256 of the UTF-8 text formed by writing, for each file in
that order, ``<relative path> TAB <file sha256 hex> LF``. The lock file and ``.gitattributes`` at the
bundle root belong to no skill and are not hashed.

Front matter rule (checked on every ``SKILL.md``, separate from the hash): the first line is ``---``, a later
line that is exactly ``---`` closes the block, and top-level ``name:`` and ``description:`` keys each have a
non-empty value (inline, quoted, or a ``>`` or ``|`` block scalar followed by a non-blank indented line).
It is a line-based check. ``invalid-front-matter`` names the slug and each missing or empty item.

The release build (``repos/hagibuild/pybuild/built_in_skills.py``) implements the same rules and checks.
``tests/test_built_in_skills.py`` pins the hash rule to a literal value and runs one shared fixture of front
matter texts, so the two cannot drift apart silently.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

CONTENT_DIR = Path(__file__).resolve().parent.parent / "content"
LOCK_FILE_NAME = "built-in-skills.lock.json"
SKILL_FILE_NAME = "SKILL.md"
# Dot-prefixed bundle-level entries that hold per-CLI files. They are not skills, so they are checked by
# their own rules and never against the lock file.
CLAUDE_PLUGIN_MANIFEST = ".claude-plugin/plugin.json"
CLAUDE_PLUGIN_NAME = "hagi"
BUNDLE_LEVEL_ENTRIES = (CLAUDE_PLUGIN_MANIFEST,)

KIND_MISSING_LOCK = "missing-lock-entry"
KIND_ORPHAN_LOCK = "orphan-lock-entry"
KIND_HASH_DRIFT = "hash-drift"
KIND_MISSING_SKILL_MD = "missing-skill-md"
KIND_LOCK_INVALID = "lock-invalid"
KIND_BUNDLE_ENTRY_INVALID = "bundle-entry-invalid"
KIND_INVALID_FRONT_MATTER = "invalid-front-matter"

_SLUG_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
_FRONT_MATTER_DELIMITER = "---"
_BLOCK_SCALAR_PATTERN = re.compile(r"^[>|][0-9+-]*$")
_FRONT_MATTER_KEYS = ("name", "description")


@dataclass(frozen=True)
class Finding:
    slug: str
    kind: str
    detail: str = ""


def _folder_slugs(root: Path) -> list[str]:
    return sorted(path.name for path in root.iterdir() if path.is_dir() and not path.name.startswith("."))


def content_hash(skill_dir: Path) -> str:
    """Hash one skill folder with the encoding described in the module docstring."""
    outer = hashlib.sha256()
    entries = sorted((path.relative_to(skill_dir).as_posix(), path) for path in skill_dir.rglob("*") if path.is_file())
    for relative, path in entries:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        outer.update(f"{relative}\t{digest}\n".encode("utf-8"))
    return f"sha256:{outer.hexdigest()}"


def _front_matter_value_ok(block: list[str], index: int, key: str) -> bool:
    """Whether the top-level ``key:`` line at ``index`` of the front matter block has a non-empty value."""
    raw = block[index][len(key) + 1 :].strip()
    if not raw or raw.startswith("#"):
        return False
    if raw[0] in "\"'":
        inner = raw[1:-1] if len(raw) >= 2 and raw[-1] == raw[0] else raw[1:]
        return bool(inner.strip())
    if _BLOCK_SCALAR_PATTERN.match(raw):
        for line in block[index + 1 :]:
            if line.strip():
                return line[:1] in (" ", "\t")
        return False
    return True


def front_matter_problems(text: str) -> list[str]:
    """Return the missing or empty items of a ``SKILL.md`` text; an empty list means the front matter passes.

    Line-based by design (see the module docstring). The same rule is implemented in
    ``repos/hagibuild/pybuild/built_in_skills.py``, and both suites run one shared fixture of texts.
    """
    lines = text.split("\n")
    if not lines or lines[0].rstrip() != _FRONT_MATTER_DELIMITER:
        return ["missing front matter block"]
    close = next((index for index in range(1, len(lines)) if lines[index].rstrip() == _FRONT_MATTER_DELIMITER), None)
    if close is None:
        return ["unclosed front matter block"]
    block = lines[1:close]
    problems: list[str] = []
    for key in _FRONT_MATTER_KEYS:
        index = next((i for i, line in enumerate(block) if line.startswith(f"{key}:")), None)
        if index is None:
            problems.append(f"missing {key}")
        elif not _front_matter_value_ok(block, index, key):
            problems.append(f"empty {key} value")
    return problems


def _front_matter_findings(skill_dir: Path) -> list[str]:
    try:
        text = (skill_dir / SKILL_FILE_NAME).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ["front matter block unreadable (not UTF-8)"]
    return front_matter_problems(text)


def _read_lock(root: Path) -> list[object]:
    lock_path = root / LOCK_FILE_NAME
    if not lock_path.is_file():
        raise ValueError(f"lock file missing: {LOCK_FILE_NAME}")
    try:
        data = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"lock file is not valid JSON: {exc}") from exc
    if not isinstance(data, dict) or data.get("schemaVersion") != 1 or not isinstance(data.get("skills"), list):
        raise ValueError("lock file must hold schemaVersion 1 and a skills list")
    return data["skills"]


def _entry_problems(entry: object) -> list[str]:
    if not isinstance(entry, dict):
        return ["entry is not an object"]
    problems: list[str] = []
    slug = entry.get("slug")
    if not isinstance(slug, str) or not _SLUG_PATTERN.match(slug):
        problems.append("slug is missing or not a folder name")
    version = entry.get("version")
    if not isinstance(version, str) or not version.strip():
        problems.append("version is missing")
    source = entry.get("source")
    if not isinstance(source, dict):
        problems.append("source is missing")
    else:
        kind = source.get("type")
        if kind == "github":
            required: tuple[str, ...] = ("repository", "ref", "path")
        elif kind == "local":
            required = ("path",)
        else:
            problems.append("source.type must be github or local")
            required = ()
        for key in required:
            value = source.get(key)
            if not isinstance(value, str) or not value.strip():
                problems.append(f"source.{key} is missing")
    recorded = entry.get("contentHash")
    if not isinstance(recorded, str) or not _HASH_PATTERN.match(recorded):
        problems.append("contentHash must be sha256 plus 64 lowercase hex digits")
    return problems


def _claude_manifest_problems(path: Path) -> list[str]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [f"is not valid JSON: {exc}"]
    if not isinstance(manifest, dict):
        return ["must be a JSON object"]
    problems: list[str] = []
    if manifest.get("name") != CLAUDE_PLUGIN_NAME:
        problems.append(f"name must be {CLAUDE_PLUGIN_NAME}")
    # The bundle keeps the flat <slug>/SKILL.md layout, so skill discovery must read the bundle root.
    if manifest.get("skills") != "./":
        problems.append('skills must be "./" so the flat layout is read from the bundle root')
    return problems


def _bundle_entry_problems(root: Path, relative: str) -> list[str]:
    path = root / relative
    if not path.is_file():
        return ["file is missing"]
    if relative == CLAUDE_PLUGIN_MANIFEST:
        return _claude_manifest_problems(path)
    return []


def verify(root: Path = CONTENT_DIR) -> list[Finding]:
    """Return every mismatch between the skill folders under ``root`` and its lock file. Writes nothing."""
    try:
        entries = _read_lock(root)
    except ValueError as exc:
        return [Finding(LOCK_FILE_NAME, KIND_LOCK_INVALID, str(exc))]

    findings: list[Finding] = []
    locked: dict[str, dict] = {}
    for index, entry in enumerate(entries):
        problems = _entry_problems(entry)
        if problems:
            slug = entry.get("slug") if isinstance(entry, dict) else None
            findings.append(Finding(str(slug or f"entry {index}"), KIND_LOCK_INVALID, "; ".join(problems)))
            continue
        if entry["slug"] in locked:
            findings.append(Finding(entry["slug"], KIND_LOCK_INVALID, "duplicate lock entry"))
            continue
        locked[entry["slug"]] = entry

    folders = set(_folder_slugs(root))
    for slug in sorted(folders | set(locked)):
        if slug not in folders:
            findings.append(Finding(slug, KIND_ORPHAN_LOCK, "no folder"))
            continue
        skill_dir = root / slug
        has_skill_md = (skill_dir / SKILL_FILE_NAME).is_file()
        if not has_skill_md:
            findings.append(Finding(slug, KIND_MISSING_SKILL_MD))
        else:
            problems = _front_matter_findings(skill_dir)
            if problems:
                findings.append(Finding(slug, KIND_INVALID_FRONT_MATTER, "; ".join(problems)))
        if slug not in locked:
            findings.append(Finding(slug, KIND_MISSING_LOCK))
            continue
        if not has_skill_md:
            continue
        recorded = locked[slug]["contentHash"]
        actual = content_hash(skill_dir)
        if actual != recorded:
            findings.append(Finding(slug, KIND_HASH_DRIFT, f"folder hashes to {actual}"))

    for relative in BUNDLE_LEVEL_ENTRIES:
        for problem in _bundle_entry_problems(root, relative):
            findings.append(Finding(relative, KIND_BUNDLE_ENTRY_INVALID, problem))
    return findings


def _add_root_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--content",
        type=Path,
        default=CONTENT_DIR,
        help="folder to check (default: content/ beside this script)",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify content/ against its lock file, or print a skill's hash.")
    commands = parser.add_subparsers(dest="command", required=True)
    verify_parser = commands.add_parser("verify", help="exit 1 and name each offending slug on any mismatch")
    _add_root_option(verify_parser)
    hash_parser = commands.add_parser("hash", help="print the sha256 content hash of one skill folder")
    _add_root_option(hash_parser)
    hash_parser.add_argument("slug", help="skill folder name, for example visualise")
    args = parser.parse_args(argv)

    root: Path = args.content
    if not root.is_dir():
        print(f"built-in skills folder missing: {root}", file=sys.stderr)
        return 2

    if args.command == "hash":
        if args.slug not in _folder_slugs(root):
            print(f"no skill folder named {args.slug!r} under {root}", file=sys.stderr)
            return 2
        print(content_hash(root / args.slug))
        return 0

    findings = verify(root)
    if findings:
        for finding in sorted(findings, key=lambda item: (item.slug, item.kind)):
            detail = f" ({finding.detail})" if finding.detail else ""
            print(f"{finding.slug}: {finding.kind}{detail}", file=sys.stderr)
        print(f"built-in skills verify failed: {len(findings)} problem(s)", file=sys.stderr)
        return 1
    print(f"built-in skills verify passed: {len(_folder_slugs(root))} skill folders match the lock file")
    return 0


if __name__ == "__main__":
    sys.exit(main())
