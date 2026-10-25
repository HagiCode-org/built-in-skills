"""Tests for scripts/built_in_skills.py, run with ``python -m unittest discover -s tests -v``."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "built_in_skills.py"

_spec = importlib.util.spec_from_file_location("built_in_skills", SCRIPT)
assert _spec is not None and _spec.loader is not None
bis = importlib.util.module_from_spec(_spec)
# dataclasses resolves the module through sys.modules while the class body is executed.
sys.modules["built_in_skills"] = bis
_spec.loader.exec_module(bis)

# Hash of the fixture below, pinned to a literal. The Build Tools parity test asserts the same value for
# the same bytes (repos/hagibuild/tests/built_in_skills_fixtures.py), so the two implementations are tied.
PINNED_FIXTURE_HASH = "sha256:b2adc38125f08a8e0ad2074234b83cdb71bbcbeabaf8ccfeb7a0442cf6af29b6"

FIXTURE_SKILL_MD = b"---\nname: sample\n---\nbody\n"
FIXTURE_NOTES = b"notes\n"


def write_bundle(root: Path, slug: str = "sample") -> Path:
    """Write a consistent content folder with one skill, its lock entry and the plugin manifest."""
    skill = root / slug
    (skill / "reference").mkdir(parents=True, exist_ok=True)
    (skill / bis.SKILL_FILE_NAME).write_bytes(FIXTURE_SKILL_MD)
    (skill / "reference" / "notes.md").write_bytes(FIXTURE_NOTES)
    lock = {
        "schemaVersion": 1,
        "skills": [
            {
                "slug": slug,
                "version": "1.0.0",
                "source": {"type": "local", "path": f"tests/{slug}"},
                "contentHash": bis.content_hash(skill),
            }
        ],
    }
    write_lock(root, lock)
    write_manifest(root)
    (root / ".gitattributes").write_text("* -text\n", encoding="utf-8")
    return root


def write_lock(root: Path, lock: object) -> None:
    (root / bis.LOCK_FILE_NAME).write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")


def read_lock(root: Path) -> dict:
    return json.loads((root / bis.LOCK_FILE_NAME).read_text(encoding="utf-8"))


def write_manifest(root: Path, text: str | None = None) -> None:
    manifest = root / bis.CLAUDE_PLUGIN_MANIFEST
    manifest.parent.mkdir(parents=True, exist_ok=True)
    if text is None:
        text = json.dumps({"name": bis.CLAUDE_PLUGIN_NAME, "skills": "./"}, indent=2) + "\n"
    manifest.write_text(text, encoding="utf-8")


def snapshot(root: Path) -> dict[str, tuple[bytes, int]]:
    """Bytes and modification time of every file, so a test can prove verify wrote nothing."""
    return {
        path.relative_to(root).as_posix(): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def kinds(findings: list) -> set[tuple[str, str]]:
    return {(finding.slug, finding.kind) for finding in findings}


class VerifyTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = write_bundle(Path(self._tmp.name) / "content")

    def test_consistent_folder_has_no_findings(self) -> None:
        self.assertEqual(bis.verify(self.root), [])

    def test_passing_folder_writes_nothing(self) -> None:
        before = snapshot(self.root)
        self.assertEqual(bis.verify(self.root), [])
        self.assertEqual(snapshot(self.root), before)

    def test_folder_without_lock_entry_is_reported(self) -> None:
        write_bundle(self.root, slug="extra")
        lock = read_lock(self.root)
        lock["skills"] = [entry for entry in lock["skills"] if entry["slug"] != "extra"]
        write_lock(self.root, lock)
        self.assertIn(("extra", bis.KIND_MISSING_LOCK), kinds(bis.verify(self.root)))

    def test_lock_entry_without_folder_is_reported(self) -> None:
        lock = read_lock(self.root)
        ghost = dict(lock["skills"][0], slug="ghost")
        lock["skills"].append(ghost)
        write_lock(self.root, lock)
        self.assertIn(("ghost", bis.KIND_ORPHAN_LOCK), kinds(bis.verify(self.root)))

    def test_changed_file_is_hash_drift(self) -> None:
        (self.root / "sample" / "reference" / "notes.md").write_bytes(b"changed\n")
        self.assertIn(("sample", bis.KIND_HASH_DRIFT), kinds(bis.verify(self.root)))

    def test_crlf_line_endings_count_as_drift(self) -> None:
        (self.root / "sample" / bis.SKILL_FILE_NAME).write_bytes(FIXTURE_SKILL_MD.replace(b"\n", b"\r\n"))
        self.assertIn(("sample", bis.KIND_HASH_DRIFT), kinds(bis.verify(self.root)))

    def test_missing_skill_md_is_reported(self) -> None:
        (self.root / "sample" / bis.SKILL_FILE_NAME).unlink()
        self.assertIn(("sample", bis.KIND_MISSING_SKILL_MD), kinds(bis.verify(self.root)))

    def test_missing_lock_file_is_lock_invalid(self) -> None:
        (self.root / bis.LOCK_FILE_NAME).unlink()
        self.assertEqual(kinds(bis.verify(self.root)), {(bis.LOCK_FILE_NAME, bis.KIND_LOCK_INVALID)})

    def test_lock_file_that_is_not_json_is_lock_invalid(self) -> None:
        (self.root / bis.LOCK_FILE_NAME).write_text("{not json", encoding="utf-8")
        self.assertEqual(kinds(bis.verify(self.root)), {(bis.LOCK_FILE_NAME, bis.KIND_LOCK_INVALID)})

    def test_malformed_entry_is_lock_invalid(self) -> None:
        lock = read_lock(self.root)
        lock["skills"][0]["contentHash"] = "sha256:ABC"
        write_lock(self.root, lock)
        self.assertIn(("sample", bis.KIND_LOCK_INVALID), kinds(bis.verify(self.root)))

    def test_duplicate_entry_is_lock_invalid(self) -> None:
        lock = read_lock(self.root)
        lock["skills"].append(dict(lock["skills"][0]))
        write_lock(self.root, lock)
        self.assertIn(("sample", bis.KIND_LOCK_INVALID), kinds(bis.verify(self.root)))

    def test_manifest_with_wrong_name_is_bundle_entry_invalid(self) -> None:
        write_manifest(self.root, json.dumps({"name": "other", "skills": "./"}))
        self.assertIn(
            (bis.CLAUDE_PLUGIN_MANIFEST, bis.KIND_BUNDLE_ENTRY_INVALID), kinds(bis.verify(self.root))
        )

    def test_missing_manifest_is_bundle_entry_invalid(self) -> None:
        (self.root / bis.CLAUDE_PLUGIN_MANIFEST).unlink()
        self.assertIn(
            (bis.CLAUDE_PLUGIN_MANIFEST, bis.KIND_BUNDLE_ENTRY_INVALID), kinds(bis.verify(self.root))
        )

    def test_unknown_dot_entry_is_not_checked(self) -> None:
        (self.root / ".unlisted").mkdir()
        (self.root / ".unlisted" / "SKILL.md").write_text("not a skill\n", encoding="utf-8")
        self.assertEqual(bis.verify(self.root), [])


class HashTests(unittest.TestCase):
    def test_fixture_hash_is_pinned(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = write_bundle(Path(tmp) / "content")
            self.assertEqual(bis.content_hash(root / "sample"), PINNED_FIXTURE_HASH)

    def test_hash_command_prints_the_content_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = write_bundle(Path(tmp) / "content")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = bis.main(["hash", "sample", "--content", str(root)])
            self.assertEqual(status, 0)
            self.assertEqual(output.getvalue().strip(), PINNED_FIXTURE_HASH)

    def test_hash_command_rejects_unknown_slug(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = write_bundle(Path(tmp) / "content")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(bis.main(["hash", "nope", "--content", str(root)]), 2)


class CommandTests(unittest.TestCase):
    def test_verify_command_exits_one_and_names_the_slug(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = write_bundle(Path(tmp) / "content")
            (root / "sample" / "reference" / "notes.md").write_bytes(b"changed\n")
            errors = io.StringIO()
            with contextlib.redirect_stderr(errors):
                status = bis.main(["verify", "--content", str(root)])
            self.assertEqual(status, 1)
            self.assertIn(f"sample: {bis.KIND_HASH_DRIFT}", errors.getvalue())

    def test_verify_command_exits_zero_on_consistent_folder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = write_bundle(Path(tmp) / "content")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(bis.main(["verify", "--content", str(root)]), 0)

    def test_missing_folder_exits_two(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(bis.main(["verify", "--content", str(Path(tmp) / "absent")]), 2)


class RealContentTests(unittest.TestCase):
    def test_real_content_verifies(self) -> None:
        content = REPO / "content"
        self.assertTrue(content.is_dir(), f"missing {content}")
        self.assertEqual(bis.verify(content), [])

    def test_every_lock_source_is_in_the_third_party_notices(self) -> None:
        notices = (REPO / "THIRD-PARTY-NOTICES.md").read_text(encoding="utf-8")
        lock = json.loads((REPO / "content" / "built-in-skills.lock.json").read_text(encoding="utf-8"))
        for entry in lock["skills"]:
            repository = entry["source"].get("repository")
            if repository is not None:
                self.assertIn(f"`{repository}`", notices, f"{entry['slug']}: {repository} is not in THIRD-PARTY-NOTICES.md")

    def test_copied_skills_carry_a_license_file(self) -> None:
        # hagi and visualise are not edited here, so their license statement lives in THIRD-PARTY-NOTICES.md only.
        without_file = {"hagi", "visualise"}
        lock = json.loads((REPO / "content" / "built-in-skills.lock.json").read_text(encoding="utf-8"))
        for entry in lock["skills"]:
            if entry["slug"] in without_file:
                continue
            folder = REPO / "content" / entry["slug"]
            self.assertTrue(
                (folder / "LICENSE").is_file() or (folder / "LICENSE-NOTICE.md").is_file(),
                f"{entry['slug']} has neither LICENSE nor LICENSE-NOTICE.md",
            )


if __name__ == "__main__":
    unittest.main()
