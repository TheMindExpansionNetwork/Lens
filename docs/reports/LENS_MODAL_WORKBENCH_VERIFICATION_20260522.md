# Lens Modal Workbench Verification Receipt

Generated: 2026-05-22T19:29:11Z

## Repository state

- Upstream GitHub: `microsoft/Lens`
- Jimsky fork: `TheMindExpansionNetwork/Lens`
- Local path: `/opt/data/workspace/github-forks/Lens`
- HF overlay repo: `TheMindExpansionNetwork/Lens` (private, lightweight; no duplicated 30GB weights)

## Hugging Face model inspection

- `microsoft/Lens`: public, MIT, text-to-image, sha `d3e299d85b8cedb691f03aa1d44b7c824e02dcd3`
- `microsoft/Lens-Turbo`: public, MIT tag, text-to-image, sha `f21b81bed3bae7f93f16f5fd300af9c408f5816a`
- Lens-Turbo total listed file size: `30.651 GB`
- Fast default: `microsoft/Lens-Turbo`, 4 steps, CFG 1.0

## Checks run

- Python compile: `python3 -m py_compile modal_lens_workbench.py modal_lens_generate.py scripts/verify_lens_workbench.py lens/*.py inference.py` — PASS
- Workbench verifier: `python3 scripts/verify_lens_workbench.py` — PASS
- Git whitespace check: `git diff --check` — PASS
- Modal CPU/free-ish smoke: `modal run modal_lens_workbench.py --mode smoke --repo-id microsoft/Lens-Turbo` — PASS
- Visual QA: contact sheet loaded and displayed correctly.

## Modal smoke result

- Modal app: `jimsky-lens-workbench`
- Modal run: `https://modal.com/apps/m1ndb0t-2045/main/ap-7ODDvJiMipaYCXFnHUbbUN`
- Function: `metadata_smoke`
- Repo tested: `microsoft/Lens-Turbo`
- Smoke run id: `20260522T192910Z`
- Remote contact sheet: `/outputs/smoke/20260522T192910Z/lens_smoke_contact_sheet.jpg`
- Local contact sheet: `/opt/data/drops/lens-modal-workbench/lens_smoke_20260522T192910Z_contact_sheet.jpg`
- Local receipt: `/opt/data/drops/lens-modal-workbench/lens_smoke_20260522T192910Z_receipt.json`

## Notes

The smoke path intentionally avoids full checkpoint download and GPU spend. Full Lens-Turbo generation is available through `modal_lens_generate.py`, but the first run may download/cache about 30GB of model files and use H100 time.
