"""High-level FileFinder API."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from ._ffi import FffCreateOptions, FffError, get_native_lib
from ._types import (
    DirItem,
    DirSearchResult,
    FileItem,
    GrepResult,
    HealthCheck,
    MixedDirItem,
    MixedFileItem,
    MixedSearchResult,
    ScanProgress,
    Score,
    SearchResult,
)


class FFFException(Exception):
    """High-level FFF error."""


@dataclass(frozen=True, slots=True)
class GrepCursor:
    """Opaque cursor for paginating grep results."""

    _offset: int


class FileFinder:
    """High-performance fuzzy file finder backed by the fff native library."""

    def __init__(
        self,
        base_path: str | os.PathLike[str],
        *,
        frecency_db_path: str | os.PathLike[str] | None = None,
        history_db_path: str | os.PathLike[str] | None = None,
        enable_mmap_cache: bool = True,
        enable_content_indexing: bool = True,
        watch: bool = True,
        ai_mode: bool = False,
        log_file_path: str | os.PathLike[str] | None = None,
        log_level: str = "",
        cache_budget_max_files: int = 0,
        cache_budget_max_bytes: int = 0,
        cache_budget_max_file_size: int = 0,
        enable_fs_root_scanning: bool = False,
        enable_home_dir_scanning: bool = False,
    ) -> None:
        self._lib = get_native_lib()
        self._handle: int | None = None

        opts = FffCreateOptions()
        opts.version = 1
        opts.base_path = self._to_bytes(str(base_path))
        opts.frecency_db_path = self._to_bytes(str(frecency_db_path)) if frecency_db_path else None
        opts.history_db_path = self._to_bytes(str(history_db_path)) if history_db_path else None
        opts.enable_mmap_cache = enable_mmap_cache
        opts.enable_content_indexing = enable_content_indexing
        opts.watch = watch
        opts.ai_mode = ai_mode
        opts.log_file_path = self._to_bytes(str(log_file_path)) if log_file_path else None
        opts.log_level = self._to_bytes(log_level) if log_level else None
        opts.cache_budget_max_files = cache_budget_max_files
        opts.cache_budget_max_bytes = cache_budget_max_bytes
        opts.cache_budget_max_file_size = cache_budget_max_file_size
        opts.enable_fs_root_scanning = enable_fs_root_scanning
        opts.enable_home_dir_scanning = enable_home_dir_scanning

        try:
            self._handle = self._lib.create_instance(opts)
        except FffError as e:
            raise FFFException(f"Failed to create FileFinder: {e}") from e

    @staticmethod
    def _to_bytes(s: str) -> bytes:
        return s.encode("utf-8")

    def _ensure_alive(self) -> int:
        if self._handle is None:
            raise FFFException("FileFinder has been destroyed")
        return self._handle

    def destroy(self) -> None:
        """Free the native instance and stop background watchers."""
        if self._handle is not None:
            self._lib.destroy(self._handle)
            self._handle = None

    def __del__(self) -> None:
        self.destroy()

    def __enter__(self) -> "FileFinder":
        return self

    def __exit__(self, *_: object) -> None:
        self.destroy()

    # --- search ---

    def search(
        self,
        query: str,
        *,
        current_file: str = "",
        max_threads: int = 0,
        page_index: int = 0,
        page_size: int = 0,
        combo_boost_multiplier: int = 0,
        min_combo_count: int = 0,
    ) -> SearchResult:
        handle = self._ensure_alive()
        raw = self._lib.search(
            handle,
            self._to_bytes(query),
            self._to_bytes(current_file),
            max_threads,
            page_index,
            page_size,
            combo_boost_multiplier,
            min_combo_count,
        )
        try:
            return self._parse_search_result(raw.contents)
        finally:
            self._lib.free_search_result(raw)

    def glob(
        self,
        pattern: str,
        *,
        current_file: str = "",
        max_threads: int = 0,
        page_index: int = 0,
        page_size: int = 0,
    ) -> SearchResult:
        handle = self._ensure_alive()
        raw = self._lib.glob(
            handle,
            self._to_bytes(pattern),
            self._to_bytes(current_file),
            max_threads,
            page_index,
            page_size,
        )
        try:
            return self._parse_search_result(raw.contents)
        finally:
            self._lib.free_search_result(raw)

    def directory_search(
        self,
        query: str,
        *,
        current_file: str = "",
        max_threads: int = 0,
        page_index: int = 0,
        page_size: int = 0,
    ) -> DirSearchResult:
        handle = self._ensure_alive()
        raw = self._lib.search_directories(
            handle,
            self._to_bytes(query),
            self._to_bytes(current_file),
            max_threads,
            page_index,
            page_size,
        )
        try:
            return self._parse_dir_search_result(raw.contents)
        finally:
            self._lib.free_dir_search_result(raw)

    def mixed_search(
        self,
        query: str,
        *,
        current_file: str = "",
        max_threads: int = 0,
        page_index: int = 0,
        page_size: int = 0,
        combo_boost_multiplier: int = 0,
        min_combo_count: int = 0,
    ) -> MixedSearchResult:
        handle = self._ensure_alive()
        raw = self._lib.search_mixed(
            handle,
            self._to_bytes(query),
            self._to_bytes(current_file),
            max_threads,
            page_index,
            page_size,
            combo_boost_multiplier,
            min_combo_count,
        )
        try:
            return self._parse_mixed_search_result(raw.contents)
        finally:
            self._lib.free_mixed_search_result(raw)

    # --- grep ---

    def grep(
        self,
        query: str,
        *,
        mode: Literal["plain", "regex", "fuzzy"] = "plain",
        max_file_size: int = 0,
        max_matches_per_file: int = 0,
        smart_case: bool = True,
        cursor: GrepCursor | None = None,
        page_limit: int = 0,
        time_budget_ms: int = 0,
        before_context: int = 0,
        after_context: int = 0,
        classify_definitions: bool = False,
    ) -> GrepResult:
        handle = self._ensure_alive()
        mode_code = {"regex": 1, "fuzzy": 2}.get(mode, 0)
        raw = self._lib.live_grep(
            handle,
            self._to_bytes(query),
            mode_code,
            max_file_size,
            max_matches_per_file,
            smart_case,
            cursor._offset if cursor else 0,
            page_limit,
            time_budget_ms,
            before_context,
            after_context,
            classify_definitions,
        )
        try:
            return self._parse_grep_result(raw.contents)
        finally:
            self._lib.free_grep_result(raw)

    def multi_grep(
        self,
        patterns: list[str],
        *,
        constraints: str = "",
        max_file_size: int = 0,
        max_matches_per_file: int = 0,
        smart_case: bool = True,
        cursor: GrepCursor | None = None,
        page_limit: int = 0,
        time_budget_ms: int = 0,
        before_context: int = 0,
        after_context: int = 0,
        classify_definitions: bool = False,
    ) -> GrepResult:
        handle = self._ensure_alive()
        if not patterns:
            raise ValueError("patterns must not be empty")
        raw = self._lib.multi_grep(
            handle,
            self._to_bytes("\n".join(patterns)),
            self._to_bytes(constraints),
            max_file_size,
            max_matches_per_file,
            smart_case,
            cursor._offset if cursor else 0,
            page_limit,
            time_budget_ms,
            before_context,
            after_context,
            classify_definitions,
        )
        try:
            return self._parse_grep_result(raw.contents)
        finally:
            self._lib.free_grep_result(raw)

    # --- lifecycle / index ---

    def scan_files(self) -> None:
        self._lib.scan_files(self._ensure_alive())

    def is_scanning(self) -> bool:
        return self._lib.is_scanning(self._ensure_alive())

    def get_base_path(self) -> str | None:
        return self._lib.get_base_path(self._ensure_alive())

    def get_scan_progress(self) -> ScanProgress:
        raw = self._lib.get_scan_progress(self._ensure_alive())
        try:
            p = raw.contents
            return ScanProgress(
                scanned_files_count=p.scanned_files_count,
                is_scanning=p.is_scanning,
                is_watcher_ready=p.is_watcher_ready,
                is_warmup_complete=p.is_warmup_complete,
            )
        finally:
            self._lib.free_scan_progress(raw)

    def wait_for_scan(self, timeout_ms: int = 5000) -> bool:
        return self._lib.wait_for_scan(self._ensure_alive(), timeout_ms)

    def wait_for_index_ready(self, timeout_ms: int = 5000) -> bool:
        deadline = time.time() * 1000 + timeout_ms
        while True:
            progress = self.get_scan_progress()
            if not progress.is_scanning and progress.is_warmup_complete:
                return True
            if time.time() * 1000 >= deadline:
                return False
            time.sleep(0.05)

    def reindex(self, new_path: str | os.PathLike[str]) -> None:
        self._lib.restart_index(self._ensure_alive(), self._to_bytes(str(new_path)))

    def refresh_git_status(self) -> int:
        return self._lib.refresh_git_status(self._ensure_alive())

    def track_query(self, query: str, selected_file_path: str | os.PathLike[str]) -> bool:
        return self._lib.track_query(
            self._ensure_alive(),
            self._to_bytes(query),
            self._to_bytes(str(selected_file_path)),
        )

    def get_historical_query(self, offset: int = 0) -> str | None:
        return self._lib.get_historical_query(self._ensure_alive(), offset)

    def health_check(self, test_path: str | os.PathLike[str] = "") -> HealthCheck:
        result = self._lib.health_check(self._ensure_alive(), self._to_bytes(str(test_path)))
        if isinstance(result, str):
            return json.loads(result)
        return result

    # --- parsers ---

    @staticmethod
    def _decode(s: bytes | None) -> str:
        if s is None:
            return ""
        return s.decode("utf-8", errors="replace")

    @classmethod
    def _parse_score(cls, score: Any) -> Score:
        return Score(
            total=score.total,
            base_score=score.base_score,
            filename_bonus=score.filename_bonus,
            special_filename_bonus=score.special_filename_bonus,
            frecency_boost=score.frecency_boost,
            distance_penalty=score.distance_penalty,
            current_file_penalty=score.current_file_penalty,
            combo_match_boost=score.combo_match_boost,
            path_alignment_bonus=score.path_alignment_bonus,
            exact_match=score.exact_match,
            match_type=cls._decode(score.match_type),
        )

    @classmethod
    def _parse_location(cls, loc: Any) -> Any:
        if loc.tag == 0:
            return None
        if loc.tag == 1:
            from ._types import LocationLine

            return LocationLine(type="line", line=loc.line)
        if loc.tag == 2:
            from ._types import LocationPosition

            return LocationPosition(type="position", line=loc.line, col=loc.col)
        from ._types import LocationRange, Position

        return LocationRange(
            type="range",
            start=Position(line=loc.line, col=loc.col),
            end=Position(line=loc.end_line, col=loc.end_col),
        )

    @classmethod
    def _parse_search_result(cls, raw: Any) -> SearchResult:
        items = []
        scores = []
        for i in range(raw.count):
            item = raw.items[i]
            items.append(
                FileItem(
                    relative_path=cls._decode(item.relative_path),
                    file_name=cls._decode(item.file_name),
                    git_status=cls._decode(item.git_status),
                    size=item.size,
                    modified=item.modified,
                    access_frecency_score=item.access_frecency_score,
                    modification_frecency_score=item.modification_frecency_score,
                    total_frecency_score=item.total_frecency_score,
                    is_binary=item.is_binary,
                )
            )
            scores.append(cls._parse_score(raw.scores[i]))
        return SearchResult(
            items=items,
            scores=scores,
            total_matched=raw.total_matched,
            total_files=raw.total_files,
            location=cls._parse_location(raw.location),
        )

    @classmethod
    def _parse_dir_search_result(cls, raw: Any) -> DirSearchResult:
        items = []
        scores = []
        for i in range(raw.count):
            item = raw.items[i]
            items.append(
                DirItem(
                    relative_path=cls._decode(item.relative_path),
                    dir_name=cls._decode(item.dir_name),
                    max_access_frecency=item.max_access_frecency,
                )
            )
            scores.append(cls._parse_score(raw.scores[i]))
        return DirSearchResult(
            items=items,
            scores=scores,
            total_matched=raw.total_matched,
            total_dirs=raw.total_dirs,
        )

    @classmethod
    def _parse_mixed_search_result(cls, raw: Any) -> MixedSearchResult:
        items = []
        scores = []
        for i in range(raw.count):
            item = raw.items[i]
            if item.item_type == 1:
                items.append(
                    MixedDirItem(
                        relative_path=cls._decode(item.relative_path),
                        dir_name=cls._decode(item.display_name),
                        max_access_frecency=item.access_frecency_score,
                    )
                )
            else:
                items.append(
                    MixedFileItem(
                        relative_path=cls._decode(item.relative_path),
                        file_name=cls._decode(item.display_name),
                        git_status=cls._decode(item.git_status),
                        size=item.size,
                        modified=item.modified,
                        access_frecency_score=item.access_frecency_score,
                        modification_frecency_score=item.modification_frecency_score,
                        total_frecency_score=item.total_frecency_score,
                        is_binary=item.is_binary,
                    )
                )
            scores.append(cls._parse_score(raw.scores[i]))
        return MixedSearchResult(
            items=items,
            scores=scores,
            total_matched=raw.total_matched,
            total_files=raw.total_files,
            total_dirs=raw.total_dirs,
            location=cls._parse_location(raw.location),
        )

    @classmethod
    def _parse_grep_result(cls, raw: Any) -> GrepResult:
        from ._types import GrepMatch, MatchRange

        items: list[GrepMatch] = []
        for i in range(raw.count):
            m = raw.items[i]
            ranges: list[MatchRange] = []
            for r_idx in range(m.match_ranges_count):
                r = m.match_ranges[r_idx]
                ranges.append(MatchRange(start=r.start, end=r.end))

            context_before: list[str] = []
            for c_idx in range(m.context_before_count):
                ptr = m.context_before[c_idx]
                context_before.append(cls._decode(ptr))

            context_after: list[str] = []
            for c_idx in range(m.context_after_count):
                ptr = m.context_after[c_idx]
                context_after.append(cls._decode(ptr))

            items.append(
                GrepMatch(
                    relative_path=cls._decode(m.relative_path),
                    file_name=cls._decode(m.file_name),
                    git_status=cls._decode(m.git_status),
                    line_content=cls._decode(m.line_content),
                    match_ranges=ranges,
                    context_before=context_before,
                    context_after=context_after,
                    size=m.size,
                    modified=m.modified,
                    total_frecency_score=m.total_frecency_score,
                    access_frecency_score=m.access_frecency_score,
                    modification_frecency_score=m.modification_frecency_score,
                    line_number=m.line_number,
                    byte_offset=m.byte_offset,
                    col=m.col,
                    fuzzy_score=m.fuzzy_score if m.has_fuzzy_score else None,
                    is_definition=m.is_definition,
                    is_binary=m.is_binary,
                )
            )
        return GrepResult(
            items=items,
            total_matched=raw.total_matched,
            total_files_searched=raw.total_files_searched,
            total_files=raw.total_files,
            filtered_file_count=raw.filtered_file_count,
            next_file_offset=raw.next_file_offset,
            regex_fallback_error=cls._decode(raw.regex_fallback_error) or None,
        )
