# AGENTS.md

Notes for coding agents working in `repos/built-in-skills`.

## Where to edit

- Skill content: `content/<slug>/`. Each skill folder is named by its slug and holds a `SKILL.md`.
- Lock entries: `content/built-in-skills.lock.json`. One entry per skill folder, with `slug`, `version`, `source`, `contentHash`.
- Bundle-level files: `content/.claude-plugin/plugin.json` and `content/.gitattributes`. Do not add other dot entries under `content/`; the release build ignores them.
- Maintenance tool: `scripts/built_in_skills.py`. Tests: `tests/test_built_in_skills.py`.

Nothing outside `content/` is publishable. Do not put scripts, tests or docs inside `content/`.

## Commands

```bash
python3 scripts/built_in_skills.py verify          # exit 1 and name each offending slug on drift
python3 scripts/built_in_skills.py hash <slug>     # print the sha256 content hash of one skill folder
python3 -m unittest discover -s tests -v           # tests for the tool and the real content
```

Standard library only. No third-party package and no Build Tools checkout is needed.

## Rules

- Lock hashes come from `hash <slug>`, not by hand. Run `verify` after any change under `content/`.
- A byte change of any kind is drift, including CRLF. Do not normalise line endings in skill files.
- Do not change the hash rule, the lock format or the lock schema path. The schema lives in `repos/hagibuild/schemas/` and is shipped in release packages. The rule is also implemented in `repos/hagibuild/pybuild/built_in_skills.py`; the two must agree, and `tests/test_built_in_skills.py` pins a fixture hash to keep them in step.
- `hagi` is copied from `repos/cli/skills/hagi/` (`HagiCode-org/cli`, path `skills/hagi`). Do not edit `content/hagi/` here; edit `repos/cli/skills/hagi/`, recopy the folder, and update its lock entry from a committed CLI ref.
- `visualise` comes from `HagiCode-org/skills-visualise`. Do not edit its files here without updating its lock entry from a committed ref in that repository. Do not edit or commit in `repos/skills-visualise` from this repository.
- A skill copied from another project needs its upstream license file in its folder (and a `NOTICE` file when upstream has one) and a row in `THIRD-PARTY-NOTICES.md`. When upstream has no license file, add a `LICENSE-NOTICE.md` instead and invent no copyright line. `tests/test_built_in_skills.py` fails when a lock source is missing from `THIRD-PARTY-NOTICES.md`.
- Do not commit or push unless the user asks.

See `README.md` for the layout, the hash rule and the update workflow.
