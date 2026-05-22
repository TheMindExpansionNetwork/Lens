"""Optional GPU Lens-Turbo generation lane for Modal.

Run only when we want a real generated image; the smoke workbench intentionally
lives in modal_lens_workbench.py so free/fast validation does not build this
heavy CUDA image.

Example:
    modal run modal_lens_generate.py \
      --prompt "a moonlit cyberpunk DJ booth made of glass, glowing stickers" \
      --repo-id microsoft/Lens-Turbo --steps 4 --cfg 1.0 --seed 2045
"""
from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import modal

APP_NAME = "jimsky-lens-generate"
REPO_ROOT = Path(__file__).resolve().parent
REMOTE_REPO = "/workspace/Lens"
LOCAL_DROP = Path("/opt/data/drops/lens-modal-workbench")

app = modal.App(APP_NAME)
hf_cache = modal.Volume.from_name("lens-hf-cache", create_if_missing=True)
outputs = modal.Volume.from_name("lens-outputs", create_if_missing=True)

gpu_image = (
    modal.Image.from_registry("nvidia/cuda:12.8.0-cudnn-devel-ubuntu22.04", add_python="3.12")
    .apt_install("git", "ffmpeg", "libgl1", "libglib2.0-0")
    .run_commands(
        "python -m pip install --upgrade pip setuptools wheel uv",
        "uv pip install --system torch torchvision --index-url https://download.pytorch.org/whl/cu128",
        "uv pip install --system --prerelease=allow accelerate==1.13.0 diffusers==0.38.0 einops==0.8.2 huggingface_hub==1.1.7 numpy pillow safetensors tokenizers tqdm transformers kernels",
    )
    .env({
        "PYTHONUNBUFFERED": "1",
        "HF_HOME": "/cache/huggingface",
        "HF_HUB_CACHE": "/cache/huggingface/hub",
        "HF_HUB_ENABLE_HF_TRANSFER": "1",
        "TOKENIZERS_PARALLELISM": "false",
    })
    .add_local_dir(str(REPO_ROOT), REMOTE_REPO)
)


def _now_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


@app.function(
    image=gpu_image,
    gpu="H100",
    cpu=8.0,
    memory=65536,
    timeout=7200,
    volumes={"/cache/huggingface": hf_cache, "/outputs": outputs},
    secrets=[modal.Secret.from_name("huggingface-secret")],
)
def generate_lens_turbo(
    prompt: str,
    repo_id: str = "microsoft/Lens-Turbo",
    base_resolution: int = 1024,
    aspect_ratio: str = "1:1",
    steps: int = 4,
    cfg: float = 1.0,
    seed: int = 2045,
) -> dict[str, Any]:
    import os
    import subprocess
    import sys

    run_id = _now_id()
    out_dir = Path("/outputs") / "generations" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        "inference.py",
        "--repo_id", repo_id,
        "--prompt", prompt,
        "--base_resolution", str(base_resolution),
        "--aspect_ratio", aspect_ratio,
        "--steps", str(steps),
        "--cfg", str(cfg),
        "--n", "1",
        "--seed", str(seed),
        "--out", str(out_dir),
        "--dtype", "bfloat16",
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{REMOTE_REPO}:{env.get('PYTHONPATH', '')}"
    proc = subprocess.run(cmd, cwd=REMOTE_REPO, env=env, text=True, capture_output=True, timeout=7000)
    (out_dir / "stdout.log").write_text(proc.stdout[-20000:])
    (out_dir / "stderr.log").write_text(proc.stderr[-20000:])
    if proc.returncode != 0:
        outputs.commit()
        raise RuntimeError(f"Lens generation failed rc={proc.returncode}; see {out_dir}/stderr.log")
    images = sorted(str(p) for p in out_dir.glob("*.png")) + sorted(str(p) for p in out_dir.glob("*.jpg"))
    receipt = {
        "ok": bool(images),
        "app": APP_NAME,
        "run_id": run_id,
        "repo_id": repo_id,
        "prompt": prompt,
        "base_resolution": base_resolution,
        "aspect_ratio": aspect_ratio,
        "steps": steps,
        "cfg": cfg,
        "seed": seed,
        "images": images,
        "output_dir": str(out_dir),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    (out_dir / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    outputs.commit()
    if not images:
        raise RuntimeError("Lens command completed but no image was found")
    first = Path(images[0])
    return {
        "receipt": receipt,
        "image_b64": base64.b64encode(first.read_bytes()).decode("ascii"),
    }


@app.local_entrypoint()
def main(
    prompt: str = "a moonlit cyberpunk DJ booth made of glass, glowing stickers, cinematic, high detail",
    repo_id: str = "microsoft/Lens-Turbo",
    base_resolution: int = 1024,
    aspect_ratio: str = "1:1",
    steps: int = 4,
    cfg: float = 1.0,
    seed: int = 2045,
):
    LOCAL_DROP.mkdir(parents=True, exist_ok=True)
    result = generate_lens_turbo.remote(
        prompt=prompt,
        repo_id=repo_id,
        base_resolution=base_resolution,
        aspect_ratio=aspect_ratio,
        steps=steps,
        cfg=cfg,
        seed=seed,
    )
    receipt = result["receipt"]
    img = LOCAL_DROP / f"lens_generation_{receipt['run_id']}.png"
    receipt_path = LOCAL_DROP / f"lens_generation_{receipt['run_id']}_receipt.json"
    img.write_bytes(base64.b64decode(result["image_b64"]))
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    print(f"LOCAL_IMAGE={img}")
    print(f"LOCAL_RECEIPT={receipt_path}")
