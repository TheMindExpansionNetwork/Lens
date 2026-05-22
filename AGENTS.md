# Fork Context - TheMindExpansionNetwork/Lens

**Forked from**: microsoft/Lens
**Upstream**: https://github.com/microsoft/Lens
**Local path**: /opt/data/workspace/github-forks/Lens
**Primary HF models**: microsoft/Lens, microsoft/Lens-Turbo, microsoft/Lens-Base
**License**: MIT

## Purpose

This fork is the Jimsky / MindExpander Lens workbench for fast text-to-image experiments on Modal.

## Rules

- Keep `main` upstream-compatible and clearly label custom Modal/workbench files.
- Do not commit model weights, generated image batches, `.env`, tokens, credentials, private prompts, or Modal cache folders.
- Put generated outputs under `/opt/data/drops/lens-modal-workbench/` locally or a Modal Volume, not in git.
- Use `microsoft/Lens-Turbo` for the fast lane by default: 4 steps, CFG 1.0.
- Treat full Lens generation as a GPU/paid lane; start with metadata/import/cache smoke tests when the user asks for super-fast/free validation.
- Preserve upstream attribution and sync through `upstream/main` or `vendor-sync/*` branches.

## Modal lanes

- `metadata_smoke`: CPU/free-ish Modal test. Verifies HF repo metadata, downloads only tiny/config/gallery files, creates a contact sheet receipt.
- `modal_lens_generate.py` / `generate_lens_turbo`: optional H100 generation lane. Uses Lens-Turbo defaults and persistent HF cache. Run only when a real generated image is desired.
