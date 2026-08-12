# Project rules

## Scope

This repository develops the open-source `research-paper` skill. Keep the distributable skill under `skill/research-paper/`; keep contributor-facing documents and tests at the repository root.

## Architecture

- Keep `SKILL.md` as a thin router and invariant contract.
- Put detailed procedures one level below it in `references/`.
- Put deterministic, reusable checks in `scripts/`.
- Put copyable work products in `assets/templates/`.
- Do not add agent-role files unless a real workflow cannot be expressed through the current router and references.

## Safety and evidence

- Never add private manuscripts, unpublished data, personal paths, secrets, or copyrighted reference figures to fixtures.
- Use synthetic or anonymized fixtures and label them explicitly.
- Do not turn a warning-only check into a scientific truth claim.
- Preserve backward compatibility for CSV headers and CLI flags where practical.

## Development

- Use Python standard library by default. Pillow is the only runtime dependency for raster QA.
- Add or update tests for every behavior change.
- Run `python -m unittest discover -s tests -v` before delivery.
- Run the upstream skill validator and packager before release.
- Do not commit generated `.skill` files unless preparing a release artifact.
- Do not commit or push automatically.
