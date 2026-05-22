---
license: mit
tags:
- text-to-image
- modal
- lens
- lens-turbo
- jimsky
base_model:
- microsoft/Lens
- microsoft/Lens-Turbo
pipeline_tag: text-to-image
---

# Jimsky Lens Modal Workbench

This is a lightweight private overlay/fork workspace for Microsoft Lens / Lens-Turbo.

It does **not** duplicate the 30GB Microsoft model weights. It points at:

- Upstream HF model: https://huggingface.co/microsoft/Lens
- Fast upstream HF model: https://huggingface.co/microsoft/Lens-Turbo
- Upstream GitHub: https://github.com/microsoft/Lens
- Jimsky GitHub fork/workbench: https://github.com/TheMindExpansionNetwork/Lens

## What is included

- Modal smoke-test receipt proving HF metadata/config/gallery access.
- Contact sheet from the tiny free/fast smoke test.
- Pointer docs for running the optional Lens-Turbo GPU generation lane.

## Why no weights here?

Lens-Turbo is about 30.65GB. Keeping this overlay lightweight avoids wasting storage and keeps setup fast/free-friendly. Runtime loads `microsoft/Lens-Turbo` directly into a Modal persistent HF cache.

## Modal quick start

```bash
cd /opt/data/workspace/github-forks/Lens
modal run modal_lens_workbench.py --mode smoke --repo-id microsoft/Lens-Turbo
```

Optional GPU generation:

```bash
modal run modal_lens_generate.py   --prompt "a moonlit cyberpunk DJ booth made of glass, glowing stickers"   --repo-id microsoft/Lens-Turbo --steps 4 --cfg 1.0 --seed 2045
```
