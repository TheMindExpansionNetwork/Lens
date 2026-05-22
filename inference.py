"""Single-shot CLI entry-point for the Lens text-to-image pipeline.

Example:

    python inference.py \\
        --prompt "A scenic landscape with a serene lake" \\
        --base_resolution 1024 --aspect_ratio 1:1 \\
        --steps 50 --cfg 4.0 --n 4 --seed 42 \\
        --out ./outputs

Use a different repo / local export with ``--repo_id``:

    python inference.py --repo_id ./lens-hf-export --prompt "a cat" --steps 4

Batch by joining prompts with `|`:

    python inference.py --prompt "a cat|a dog|a robot" ...
"""

from __future__ import annotations

import argparse
import os

import torch

from lens import LensGptOssEncoder, LensPipeline
from lens.resolution import SUPPORTED_ASPECT_RATIOS, SUPPORTED_BASE_RESOLUTIONS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lens text-to-image inference")
    parser.add_argument("--repo_id", type=str, default="microsoft/Lens",
                        help="HF repo id (or local path) of the assembled "
                             "Lens pipeline (model_index.json + subfolders).")
    parser.add_argument("--prompt", type=str, required=True,
                        help="Prompt(s). Use '|' to separate multiple prompts.")
    parser.add_argument("--base_resolution", type=int, default=1440,
                        choices=SUPPORTED_BASE_RESOLUTIONS)
    parser.add_argument("--aspect_ratio", type=str, default="1:1",
                        choices=SUPPORTED_ASPECT_RATIOS)
    parser.add_argument("--steps", type=int, default=20,
                        help="Number of denoising steps.")
    parser.add_argument("--cfg", type=float, default=5.0,
                        help="Classifier-free guidance scale.")
    parser.add_argument("--n", type=int, default=1,
                        help="Number of images per prompt.")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--out", type=str, default="./outputs")
    parser.add_argument("--dtype", type=str, default="bfloat16",
                        choices=["bfloat16", "float16", "float32"])
    parser.add_argument("--disable_mxfp4", action="store_true",
                        help="Disable dequantization of GPT-OSS text encoder.")
    parser.add_argument("--reasoner", action="store_true",
                        help="Enable prompt reasoner (uses local GPT-OSS unless "
                             "--api_url is set).")
    parser.add_argument("--api_url", type=str, default=None,
                        help="OpenAI-compatible base URL for the API reasoner.")
    parser.add_argument("--api_key", type=str, default=None,
                        help="API key for the OpenAI-compatible endpoint.")
    parser.add_argument("--api_model", type=str, default=None,
                        help="Model name to send to the OpenAI-compatible endpoint.")
    parser.add_argument("--offload", action="store_true",
                        help="Enable diffusers model CPU offload "
                             "(text_encoder->transformer->vae) to reduce peak VRAM.")
    return parser.parse_args()


def _torch_dtype(name: str) -> torch.dtype:
    return {"bfloat16": torch.bfloat16, "float16": torch.float16,
            "float32": torch.float32}[name]


def main() -> None:
    args = parse_args()
    prompts = [p.strip() for p in args.prompt.split("|") if p.strip()]
    if not prompts:
        raise SystemExit("No non-empty prompts after splitting on '|'.")

    os.makedirs(args.out, exist_ok=True)

    dtype = _torch_dtype(args.dtype)

    # Pre-load the text encoder so we can control MXFP4 dequantization. The
    # gpt-oss-20b weights on the hub are stored in MXFP4 and the loader will
    # try to keep them that way unless we pass an explicit Mxfp4Config that
    # asks for dequantization. MXFP4 kernels need Hopper-or-newer GPUs, so on
    # A100/V100 we may consider dequantizing to bf16/fp16.
    text_encoder_kwargs = {"subfolder": "text_encoder", "dtype": dtype}
    try:
        from transformers import Mxfp4Config
        text_encoder_kwargs["quantization_config"] = Mxfp4Config(
            dequantize=args.disable_mxfp4
        )
    except ImportError:
        # Older transformers without Mxfp4Config: nothing to do, the weights
        # will load as the loader sees fit.
        pass
    text_encoder = LensGptOssEncoder.from_pretrained(
        args.repo_id, **text_encoder_kwargs
    )

    pipe = LensPipeline.from_pretrained(
        args.repo_id, text_encoder=text_encoder, torch_dtype=dtype
    )

    if args.offload:
        pipe.enable_model_cpu_offload()
    else:
        pipe.to("cuda")

    if args.api_url or args.api_key or args.api_model:
        pipe.reasoner.openai_base_url = args.api_url
        pipe.reasoner.openai_api_key = args.api_key
        pipe.reasoner.openai_model = args.api_model

    generator = (
        torch.Generator(device=pipe._execution_device).manual_seed(int(args.seed))
        if args.seed is not None
        else None
    )

    out = pipe(
        prompt=prompts,
        base_resolution=args.base_resolution,
        aspect_ratio=args.aspect_ratio,
        num_inference_steps=args.steps,
        guidance_scale=args.cfg,
        num_images_per_prompt=args.n,
        generator=generator,
        enable_reasoner=args.reasoner,
    )

    # Save one file per (prompt, image-index) pair.
    images = list(out.images)
    expected_images = len(prompts) * args.n
    if len(images) != expected_images:
        raise RuntimeError(
            f"Pipeline returned {len(images)} images; expected {expected_images}."
        )
    img_iter = iter(images)
    for p_idx, prompt in enumerate(prompts):
        for s_idx in range(args.n):
            img = next(img_iter)
            fname = f"p{p_idx:03d}_s{s_idx:02d}.png"
            img.save(os.path.join(args.out, fname))
            print(f"saved {fname} :: {prompt!r}")
    refined = getattr(pipe, "_last_refined_prompts", prompts)
    if any(r != p for r, p in zip(refined, prompts)):
        print("\nRefined prompts:")
        for orig, ref in zip(prompts, refined):
            print(f"  {orig!r}\n    -> {ref!r}")


if __name__ == "__main__":
    main()
