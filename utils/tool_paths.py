"""
tool_paths.py
-------------
Resolve external enhancement binaries from bundled app folders or PATH.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def app_base_dirs() -> list[Path]:
    bases: list[Path] = []

    project_root = Path(__file__).resolve().parents[1]
    bases.append(project_root)

    if getattr(sys, "frozen", False):
        bases.append(Path(sys.executable).resolve().parent)

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        bases.append(Path(meipass))

    # Preserve order but remove duplicates.
    unique: list[Path] = []
    seen: set[str] = set()
    for base in bases:
        key = str(base).lower()
        if key not in seen:
            seen.add(key)
            unique.append(base)
    return unique


def _binary_candidates(
    tool_folder: str,
    binary_name: str,
    ai_category: str | None = None,
) -> list[Path]:
    names = [binary_name]
    if sys.platform.startswith("win") and not binary_name.endswith(".exe"):
        names.insert(0, f"{binary_name}.exe")

    candidates: list[Path] = []
    for base in app_base_dirs():
        ai_root = base / "ai"
        tool_root = base / "tools"
        if ai_category:
            category_root = ai_root / ai_category
            candidates.extend((category_root / tool_folder / name) for name in names)
            candidates.extend((category_root / f"{tool_folder}-ncnn-vulkan" / name) for name in names)
            candidates.extend((category_root / binary_name / name) for name in names)

        # Keep the previous flat ai/<tool>/ layout working for existing bundles.
        candidates.extend((ai_root / tool_folder / name) for name in names)
        candidates.extend((ai_root / f"{tool_folder}-ncnn-vulkan" / name) for name in names)
        candidates.extend((ai_root / binary_name / name) for name in names)
        candidates.extend((tool_root / tool_folder / name) for name in names)
        candidates.extend((tool_root / f"{tool_folder}-ncnn-vulkan" / name) for name in names)
        candidates.extend((tool_root / binary_name / name) for name in names)
    return candidates


def resolve_tool_binary(
    tool_folder: str,
    binary_name: str,
    ai_category: str | None = None,
) -> Path | None:
    for candidate in _binary_candidates(tool_folder, binary_name, ai_category):
        if candidate.exists():
            return candidate

    path_value = shutil.which(binary_name)
    if path_value:
        return Path(path_value)

    if sys.platform.startswith("win"):
        path_value = shutil.which(f"{binary_name}.exe")
        if path_value:
            return Path(path_value)

    return None


def resolve_rife_binary() -> Path | None:
    return resolve_tool_binary("rife", "rife-ncnn-vulkan", ai_category="frame_generation")


def resolve_realesrgan_binary() -> Path | None:
    return resolve_tool_binary("realesrgan", "realesrgan-ncnn-vulkan", ai_category="upscaling")
