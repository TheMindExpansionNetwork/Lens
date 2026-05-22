"""Modal workbench for Microsoft Lens / Lens-Turbo.

Fast lane:
    modal run modal_lens_workbench.py --mode smoke

Optional GPU lane:
    modal run modal_lens_workbench.py --mode generate \
      --prompt "a moonlit cyberpunk DJ booth made of glass" \
      --repo-id microsoft/Lens-Turbo --steps 4 --cfg 1.0 --seed 2045
"""
from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import modal

APP_NAME = "jimsky-lens-workbench"
REPO_ROOT = Path(__file__).resolve().parent
REMOTE_REPO = "/workspace/Lens"
LOCAL_DROP = Path("/opt/data/drops/lens-modal-workbench")

app = modal.App(APP_NAME)
hf_cache = modal.Volume.from_name("lens-hf-cache", create_if_missing=True)
outputs = modal.Volume.from_name("lens-outputs", create_if_missing=True)

smoke_image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git")
    .pip_install("huggingface_hub==1.1.7", "pillow>=10.0.0")
    .env({
        "HF_HOME": "/cache/huggingface",
        "HF_HUB_CACHE": "/cache/huggingface/hub",
        "HF_HUB_ENABLE_HF_TRANSFER": "1",
    })
)


def _now_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


@app.function(
    image=smoke_image,
    cpu=1.0,
    memory=2048,
    timeout=600,
    volumes={"/cache/huggingface": hf_cache, "/outputs": outputs},
)
def metadata_smoke(repo_id: str = "microsoft/Lens-Turbo") -> dict[str, Any]:
    """CPU/free-ish smoke test: metadata + tiny files + contact sheet, no full weights."""
    from huggingface_hub import HfApi, snapshot_download
    from PIL import Image, ImageDraw

    run_id = _now_id()
    out_dir = Path("/outputs") / "smoke" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    api = HfApi()
    info = api.model_info(repo_id, files_metadata=True)
    siblings = info.siblings or []
    total_size = sum((getattr(s, "size", 0) or 0) for s in siblings)
    files = [getattr(s, "rfilename", "") for s in siblings]

    # Only tiny/config/gallery files: validates Hub access and Modal cache without 30GB checkpoint pull.
    tiny_patterns = [
        "README.md",
        "model_index.json",
        "scheduler/*",
        "tokenizer/tokenizer_config.json",
        "tokenizer/special_tokens_map.json",
        "text_encoder/config.json",
        "transformer/config.json",
        "vae/config.json",
        "assets/teaser.webp",
        "assets/gallery/000-*.png",
        "assets/gallery/000-*.txt",
        "assets/gallery/001-*.png",
        "assets/gallery/001-*.txt",
    ]
    local_repo = snapshot_download(
        repo_id=repo_id,
        allow_patterns=tiny_patterns,
        local_files_only=False,
    )

    images = []
    for p in sorted(Path(local_repo).glob("assets/gallery/*.png"))[:2]:
        images.append(p)
    teaser = Path(local_repo) / "assets/teaser.webp"
    if teaser.exists():
        images.insert(0, teaser)

    thumb_w, thumb_h = 320, 240
    sheet = Image.new("RGB", (thumb_w * max(1, len(images)), thumb_h + 60), "#101018")
    draw = ImageDraw.Draw(sheet)
    for idx, img_path in enumerate(images):
        im = Image.open(img_path).convert("RGB")
        im.thumbnail((thumb_w, thumb_h))
        x = idx * thumb_w + (thumb_w - im.width) // 2
        y = (thumb_h - im.height) // 2
        sheet.paste(im, (x, y))
        draw.text((idx * thumb_w + 8, thumb_h + 8), img_path.name[:36], fill=(230, 230, 240))
    if not images:
        draw.text((20, 20), "Lens metadata smoke OK - no gallery image matched", fill=(230, 230, 240))
    contact_sheet = out_dir / "lens_smoke_contact_sheet.jpg"
    sheet.save(contact_sheet, quality=92)

    receipt = {
        "ok": True,
        "app": APP_NAME,
        "run_id": run_id,
        "repo_id": repo_id,
        "sha": getattr(info, "sha", None),
        "private": getattr(info, "private", None),
        "tags": list(getattr(info, "tags", []) or [])[:30],
        "file_count": len(files),
        "total_size_gb": round(total_size / 1e9, 3),
        "tiny_cache_path": local_repo,
        "contact_sheet": str(contact_sheet),
        "contact_sheet_size": contact_sheet.stat().st_size,
        "sample_files": files[:20],
        "notes": "Smoke test intentionally avoided full checkpoint download; use generate_lens_turbo for GPU image creation.",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    receipt_path = out_dir / "receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    outputs.commit()
    hf_cache.commit()
    return {
        "receipt": receipt,
        "contact_sheet_b64": base64.b64encode(contact_sheet.read_bytes()).decode("ascii"),
        "receipt_b64": base64.b64encode(receipt_path.read_bytes()).decode("ascii"),
    }



@app.local_entrypoint()
def main(
    mode: str = "smoke",
    prompt: str = "a moonlit cyberpunk DJ booth made of glass, glowing stickers, cinematic, high detail",
    repo_id: str = "microsoft/Lens-Turbo",
    steps: int = 4,
    cfg: float = 1.0,
    seed: int = 2045,
):
    LOCAL_DROP.mkdir(parents=True, exist_ok=True)
    if mode == "smoke":
        result = metadata_smoke.remote(repo_id=repo_id)
        receipt = result["receipt"]
        stem = f"lens_smoke_{receipt['run_id']}"
        contact = LOCAL_DROP / f"{stem}_contact_sheet.jpg"
        receipt_path = LOCAL_DROP / f"{stem}_receipt.json"
        contact.write_bytes(base64.b64decode(result["contact_sheet_b64"]))
        receipt_path.write_bytes(base64.b64decode(result["receipt_b64"]))
        print(json.dumps(receipt, indent=2, sort_keys=True))
        print(f"LOCAL_CONTACT_SHEET={contact}")
        print(f"LOCAL_RECEIPT={receipt_path}")
    elif mode == "generate":
        raise RuntimeError(
            "Generation lives in modal_lens_generate.py so smoke mode stays fast/free: "
            "modal run modal_lens_generate.py --prompt '<prompt>' --repo-id microsoft/Lens-Turbo"
        )
    else:
        raise ValueError("mode must be smoke or generate")
