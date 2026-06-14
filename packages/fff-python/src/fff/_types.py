"""Python data types for FFF search results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypedDict


@dataclass(frozen=True, slots=True)
class FileItem:
    relative_path: str
    file_name: str
    git_status: str
    size: int
    modified: int
    access_frecency_score: int
    modification_frecency_score: int
    total_frecency_score: int
    is_binary: bool


@dataclass(frozen=True, slots=True)
class DirItem:
    relative_path: str
    dir_name: str
    max_access_frecency: int


@dataclass(frozen=True, slots=True)
class Score:
    total: int
    base_score: int
    filename_bonus: int
    special_filename_bonus: int
    frecency_boost: int
    distance_penalty: int
    current_file_penalty: int
    combo_match_boost: int
    path_alignment_bonus: int
    exact_match: bool
    match_type: str


@dataclass(frozen=True, slots=True)
class LocationLine:
    type: Literal["line"]
    line: int


@dataclass(frozen=True, slots=True)
class LocationPosition:
    type: Literal["position"]
    line: int
    col: int


@dataclass(frozen=True, slots=True)
class LocationRange:
    type: Literal["range"]
    start: "Position"
    end: "Position"


@dataclass(frozen=True, slots=True)
class Position:
    line: int
    col: int


Location = LocationLine | LocationPosition | LocationRange


@dataclass(frozen=True, slots=True)
class SearchResult:
    items: list[FileItem]
    scores: list[Score]
    total_matched: int
    total_files: int
    location: Location | None = None


@dataclass(frozen=True, slots=True)
class DirSearchResult:
    items: list[DirItem]
    scores: list[Score]
    total_matched: int
    total_dirs: int


MixedFileItem = FileItem
MixedDirItem = DirItem


@dataclass(frozen=True, slots=True)
class MixedSearchResult:
    items: list[MixedFileItem | MixedDirItem]
    scores: list[Score]
    total_matched: int
    total_files: int
    total_dirs: int
    location: Location | None = None


@dataclass(frozen=True, slots=True)
class MatchRange:
    start: int
    end: int


@dataclass(frozen=True, slots=True)
class GrepMatch:
    relative_path: str
    file_name: str
    git_status: str
    line_content: str
    match_ranges: list[MatchRange]
    context_before: list[str]
    context_after: list[str]
    size: int
    modified: int
    total_frecency_score: int
    access_frecency_score: int
    modification_frecency_score: int
    line_number: int
    byte_offset: int
    col: int
    fuzzy_score: int | None
    is_definition: bool
    is_binary: bool


@dataclass(frozen=True, slots=True)
class GrepResult:
    items: list[GrepMatch]
    total_matched: int
    total_files_searched: int
    total_files: int
    filtered_file_count: int
    next_file_offset: int
    regex_fallback_error: str | None


@dataclass(frozen=True, slots=True)
class ScanProgress:
    scanned_files_count: int
    is_scanning: bool
    is_watcher_ready: bool
    is_warmup_complete: bool


class HealthCheck(TypedDict, total=False):
    version: str
    git: dict
    file_picker: dict
    frecency: dict
    query_tracker: dict
