"""Python bindings for FFF (Fast File Finder)."""

from __future__ import annotations

from fff._fff_python import (
    DirItem,
    DirSearchResult,
    FFFException,
    FileFinder,
    FileItem,
    GrepMatch,
    GrepResult,
    MatchRange,
    MixedDirItem,
    MixedFileItem,
    MixedSearchResult,
    ScanProgress,
    Score,
    SearchResult,
)

__version__ = "0.1.0"

__all__ = [
    "FFFException",
    "FileFinder",
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
    "__version__",
]
