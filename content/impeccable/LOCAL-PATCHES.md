# Local patches

This folder is a copy of `pbakaus/impeccable`, path `.agents/skills/impeccable`, at ref `936867543ac2576920d663cc9803597f6044f3ac` (version 4.7.1). The files listed below differ from that upstream ref. Every other upstream file is kept byte-for-byte.

## Patched upstream files

Each patched file gets a short gate paragraph that points to `reference/data-preview.md`. The paragraph sits before a fixed step, so the command shows an SVG preview and asks Ask User Question before it acts. `audit` and `critique` show the preview inside their report and ask their follow-up question there.

- `reference/extract.md`: gate before Step 4.
- `reference/document.md`: gate before Step 3 of Scan mode. Seed mode has no preview.
- `reference/optimize.md`: gate before Optimization Strategy.
- `reference/audit.md`: preview after the Audit Health Score table. The closing follow-up prose is replaced with an Ask User Question choice.
- `reference/critique.md`: preview after the Design Health Score. "Ask the User" uses Ask User Question. Its existing rules are kept.
- `reference/overdrive.md`: direction-comparison preview before the pick, drawn as one in-context SVG of the surface with a labelled panel per direction. Stop is added as an option.
- `reference/bolder.md`: gate before The amplification. The gate paragraph draws the one planned move in place on the surface.
- `reference/quieter.md`: gate before Refine the Design. The gate paragraph places current and planned intensity as labelled marks on the in-context drawing of the surface.
- `reference/colorize.md`: gate before Apply at system scale.
- `reference/animate.md`: gate before Choose material by meaning. The gate paragraph places the motion timeline as an annotation on the in-context drawing of the moving element.
- `reference/delight.md`: gate before Build for the emotional moment.
- `reference/typeset.md`: gate before Apply. The gate paragraph places the stepped type-scale bars as an annotation on the in-context drawing.
- `reference/layout.md`: gate before Apply. The gate paragraph places the stepped spacing bars as an annotation on the in-context drawing.
- `reference/distill.md`: gate before Simplify the Design. The gate paragraph places the removal-and-merge bars as an annotation on the in-context drawing.

## Added files

- `reference/data-preview.md`: the shared rules for the preview gate. Which commands it covers, the values each preview may show, what the one SVG depicts for data and interface-changing commands, how to draw it, and how the confirmation works.
- `LOCAL-PATCHES.md`: this file.
- `LICENSE` and `NOTICE.md`: upstream license and notice, carried over unchanged, as listed in the repository README.

## Reapplying after a re-vendor

1. Copy the upstream folder at the new ref over this one.
2. `reference/data-preview.md` is not in upstream. Save a copy of it before the copy overwrites the folder, then put it back.
3. Reinsert the gate paragraph in each file listed under Patched upstream files, at the step named there. Redo the `audit` follow-up, the `critique` "Ask the User" sentence and the `overdrive` Stop option.
4. Update this list to match the new diff.
5. Run `python3 scripts/built_in_skills.py hash impeccable` and write the value into the lock entry's `contentHash`. Keep `source` and `version` at the new upstream values. Then run `python3 scripts/built_in_skills.py verify`.
