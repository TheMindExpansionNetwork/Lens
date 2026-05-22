# Jimsky Lens Modal Workbench

This fork wires Microsoft Lens into a practical Modal workflow for fast, low-risk testing and later GPU image generation.

## What Lens is

Lens is a Microsoft 3.8B text-to-image model family. The fast lane is `microsoft/Lens-Turbo`, a distilled 4-step variant.

## Default strategy

1. **Free/fast smoke first**: run `metadata_smoke` to verify Hugging Face metadata, configs, tokenizer/gallery access, and Modal cache volume without downloading 30GB of model weights.
2. **Turbo generation when desired**: run the optional `generate_lens_turbo` H100 function with `microsoft/Lens-Turbo`, 4 steps, CFG 1.0.
3. **Keep outputs out of git**: generated images and receipts go to `/opt/data/drops/lens-modal-workbench/` and/or Modal Volume `lens-outputs`.

## Modal commands

From repo root:

```bash
# CPU/free-ish metadata + gallery smoke test
modal run modal_lens_workbench.py --mode smoke

# Optional GPU generation test; uses Lens-Turbo and persistent cache
# Separate file so smoke mode does not build the heavy CUDA image.
modal run modal_lens_generate.py \
  --prompt "a moonlit cyberpunk DJ booth made of glass, glowing stickers, cinematic, high detail" \
  --repo-id microsoft/Lens-Turbo \
  --steps 4 --cfg 1.0 --seed 2045
```

## Modal Volumes

- `lens-hf-cache`: Hugging Face cache and small repo metadata.
- `lens-outputs`: generated images, receipts, and smoke contact sheets.

## Cost discipline

- Smoke mode avoids full checkpoint downloads and should be fast.
- Full Lens/Turbo repo is ~30GB. First GPU run may spend time downloading/caching.
- Use `Lens-Turbo` first for cool stuff quickly. Use full `Lens` only when quality matters more than speed.

## Verification

```bash
python3 scripts/verify_lens_workbench.py
python3 -m py_compile modal_lens_workbench.py scripts/verify_lens_workbench.py
```
