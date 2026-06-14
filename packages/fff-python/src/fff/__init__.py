"""Python bindings for FFF (Fast File Finder)."""

from __future__ import annotations

from ._ffi import FffError
from ._platform import find_library, get_lib_extension
from ._types import (
    DirItem,
    DirSearchResult,
    FileItem,
    GrepMatch,
    GrepResult,
    HealthCheck,
    Location,
    MatchRange,
    MixedDirItem,
    MixedFileItem,
    MixedSearchResult,
    ScanProgress,
    Score,
    SearchResult,
)
from .finder import FFFException, FileFinder, GrepCursor

__version__ = "0.1.0"

__all__ = [
    "FFFException",
    "FffError",
    "FileFinder",
    "GrepCursor",
    "find_library",
    "get_lib_extension",
    "FileItem",
    "DirItem",
    "Score",
    "SearchResult",
    "DirSearchResult",
    "MixedFileItem",
    "MixedDirItem",
    "MixedSearchResult",
    "MatchRange",
    "GrepMatch",
    "GrepResult",
    "ScanProgress",
    "HealthCheck",
    "Location",
    "__version__",
]
