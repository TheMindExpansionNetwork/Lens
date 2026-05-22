# Jimsky Lens Fork Strategy

## Repos

- Upstream source: https://github.com/microsoft/Lens
- Jimsky fork: https://github.com/TheMindExpansionNetwork/Lens
- Hugging Face models:
  - https://huggingface.co/microsoft/Lens
  - https://huggingface.co/microsoft/Lens-Turbo
  - https://huggingface.co/microsoft/Lens-Base

## Branch model

- `main`: upstream-compatible Jimsky working branch with lightweight Modal/docs additions.
- `upstream/main`: Microsoft source of truth.
- `jimsky/*`: future product/runtime experiments.
- `vendor-sync/*`: safe upstream merge branches.

## Sync commands

```bash
git fetch upstream --prune
git checkout main
git pull origin main
git checkout -b vendor-sync/upstream-$(date +%Y%m%d)
git merge upstream/main
```

Resolve conflicts, run verification, then merge/push. Do not reset away Jimsky files.

## Safety

- Do not commit HF/model cache, checkpoints, safetensors, generated image batches, tokens, `.env`, or private deployment info.
- Keep Modal secrets in Modal, not git.
- Keep large model artifacts on Hugging Face/Modal volumes.
