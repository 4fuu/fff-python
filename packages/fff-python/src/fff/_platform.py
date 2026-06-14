"""Platform detection and native library resolution."""

from __future__ import annotations

import os
import platform
import sys
from pathlib import Path


def _lib_filename() -> str:
    system = platform.system()
    if system == "Windows":
        return "fff_c.dll"
    if system == "Darwin":
        return "libfff_c.dylib"
    return "libfff_c.so"


def _possible_lib_paths() -> list[Path]:
    filename = _lib_filename()
    candidates: list[Path] = []

    # 1. bundled binary next to the package
    here = Path(__file__).resolve().parent
    candidates.append(here / "bin" / filename)

    # 2. local cargo build from repo root
    # __file__ is packages/fff-python/src/fff/_platform.py
    repo_root = here.parents[3]
    candidates.append(repo_root / "target" / "release" / filename)
    candidates.append(repo_root / "target" / "debug" / filename)

    # 3. CARGO_TARGET_DIR override
    cargo_target = os.environ.get("CARGO_TARGET_DIR")
    if cargo_target:
        candidates.append(Path(cargo_target) / "release" / filename)
        candidates.append(Path(cargo_target) / "debug" / filename)

    # 4. system search paths are handled by ctypes.CDLL when no full path is given
    candidates.append(Path(filename))

    return candidates


def find_library() -> Path:
    """Return the path to the fff_c native library."""
    for path in _possible_lib_paths():
        if path.exists():
            return path

    searched = "\n".join(str(p) for p in _possible_lib_paths())
    raise FileNotFoundError(
        f"fff_c native library not found. Searched:\n{searched}\n"
        "Build from source with: cargo build --release -p fff-c"
    )


def get_lib_extension() -> str:
    system = platform.system()
    if system == "Windows":
        return "dll"
    if system == "Darwin":
        return "dylib"
    return "so"
