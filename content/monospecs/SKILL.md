---
name: monospecs
description: Use when the user wants to initialize, inspect, validate or change a project's MonoSpecs configuration, which is the `.hagicode/monospecs.yaml` file that lists the managed child repositories of a monorepo. Covers initializing the file, adding repositories from URLs, and reordering repositories by recent activity with `ui.collapseToMore`. Triggers on monospecs, monospec, 仓库清单, 添加仓库, 初始化 monospecs, 重排仓库, collapseToMore.
---

# MonoSpecs

MonoSpecs is a project-level repository configuration convention. The file `.hagicode/monospecs.yaml` at the project root is the source of truth for the repository inventory: which child repositories the project manages, where they are cloned, their order, display names, tags and display metadata.

Use this skill to initialize the file, add repositories to it, and reorder them. Work directly on the file; no CLI or HagiTask session is needed.

## File shape

```yaml
version: "1.0"
commit_when_archive: false
repositories:
  - path: "repos/repository-name"
    code: "01"
    url: "https://github.com/owner/repository.git"
    displayName: "Repository"
    icon: "lucide:app-window"
    tags: [ frontend, react ]
    metadata:
      github:
        public: false
        visibility: "private"
        description: ""
        homepage: ""
        topics: []
    ui:
      collapseToMore: false
```

- Required: `version` and `repositories`. Each repository needs `path` and `url`; `displayName` should be present.
- Optional per repository: `code`, `icon`, `tags`, `metadata`, `ui`. Leave optional fields you did not set out of a new entry rather than inventing values.
- `workspace` and other top-level keys may exist. Preserve every key, comment and entry you do not mean to change.
- Order in `repositories` is the display order.

## Rules

- Stay inside the project root you were given. Write only `.hagicode/monospecs.yaml`.
- Repositories under `repos/` and any other read-only reference material are read-only. Never create, modify or delete files there. Reading their git state is fine.
- Do not commit, push or publish unless the user asks.
- Read the existing file first. Validate the whole document before and after every write: it parses as YAML, `version` and `repositories` exist, every entry has `path` and `url`, and no two entries share a `path` or `url`.
- If validation fails, stop without writing and report the field-level problem.
- Keep the edit minimal. Do not reformat, sort or rewrite entries you were not asked to touch.

## Operations

### Initialize

Create the file only when it is missing, in the selected project root.

1. Read the existing file first.
2. Missing: create `.hagicode/` and write `version: "1.0"`, `commit_when_archive: false` and `repositories: []`.
3. Present and valid: keep it unchanged and report the repository count.
4. Present but invalid: stop, write nothing, report the field-level diagnostics.
5. Report the path, the action taken, the validation result and the final state.

### Add repositories

Add one or more repositories from the URLs the user gave.

1. Read and validate the file and its `repositories` array.
2. Extract every valid absolute URL from the request, in input order.
3. For each URL infer the repository name, a relative `path` of `repos/<name>`, and a `displayName`. Use empty `tags`. If any value cannot be inferred reliably, stop and ask.
4. Normalize paths. Reject duplicates (same `path` or same `url`), missing fields and invalid URLs without writing.
5. Append the entries in URL input order, then validate the whole document again.
6. Report the inferred values, the file written, the validation result and the final repository count.

### Reorder repositories

Reorder by recent activity and collapse long-inactive repositories. Write only after the user explicitly confirms the preview.

1. Read the full `repositories` array. For each repository that is cloned locally, assess recent commits, branch sync state, uncommitted changes and recent-use records.
2. Put frequently or recently active repositories first with `ui.collapseToMore: false`. Put long-inactive ones later with `ui.collapseToMore: true`.
3. Keep fewer than 10 non-collapsed repositories. When more qualify, keep only the most active ones non-collapsed and put the rest in More.
4. When activity cannot be determined, keep the relative order and the existing values.
5. Show a preview: the evidence per repository, its proposed position, and its `collapseToMore` value. Then wait for explicit confirmation.
6. After confirmation change only the repository order and `ui.collapseToMore`, then validate the whole document.
7. Without confirmation, or after a failed validation, write nothing.

## After a change

`.hagicode/monospecs.yaml` drives repository cloning (`node scripts/clone-repos.mjs` in the monorepo). Adding an entry does not clone it. Tell the user to run the clone step, or run it only when asked.
