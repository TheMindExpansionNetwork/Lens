#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "AGENTS.md",
    "docs/JIMSKY_LENS_MODAL_WORKBENCH.md",
    "docs/JIMSKY_FORK_STRATEGY.md",
    "modal_lens_workbench.py",
    "modal_lens_generate.py",
]
NEEDLES = {
    "AGENTS.md": ["Fork Context", "microsoft/Lens", "Do not commit model weights", "Lens-Turbo"],
    "docs/JIMSKY_LENS_MODAL_WORKBENCH.md": ["metadata_smoke", "Lens-Turbo", "modal run modal_lens_workbench.py"],
    "modal_lens_workbench.py": ["metadata_smoke", "generate_lens_turbo", "lens-hf-cache", "Lens-Turbo"],
}
SECRET_RE = re.compile(r"(xai-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9_]{20,}|hf_[A-Za-z0-9]{20,}|api[_-]?key\s*=|secret\s*=|password\s*=)", re.I)


def main() -> int:
    ok = True
    for rel in REQUIRED:
        p = ROOT / rel
        if not p.exists():
            print(f"MISSING {rel}")
            ok = False
    for rel, needles in NEEDLES.items():
        p = ROOT / rel
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        missing = [n for n in needles if n not in text]
        if missing:
            print(f"MISSING_NEEDLES {rel}: {missing}")
            ok = False
    # Scan the Jimsky workbench layer, not all upstream source. Upstream Lens contains
    # harmless strings like OPENAI_API_KEY argument names for its optional reasoner.
    scan_rel_paths = [
        "AGENTS.md",
        "docs/JIMSKY_LENS_MODAL_WORKBENCH.md",
        "docs/JIMSKY_FORK_STRATEGY.md",
        "modal_lens_workbench.py",
        "modal_lens_generate.py",
        "scripts/verify_lens_workbench.py",
    ]
    hits = []
    for rel in scan_rel_paths:
        p = ROOT / rel
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        if SECRET_RE.search(text):
            hits.append(rel)
    if hits:
        print("SECRET_PATTERN_HITS", json.dumps(hits, indent=2))
        ok = False
    print("lens_workbench_verify", "OK" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
