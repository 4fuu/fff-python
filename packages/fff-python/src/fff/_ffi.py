"""Low-level ctypes bindings for libfff_c."""

from __future__ import annotations

import json
from ctypes import (
    CDLL,
    POINTER,
    Structure,
    cast,
    c_bool,
    c_char,
    c_char_p,
    c_int16,
    c_int32,
    c_int64,
    c_uint8,
    c_uint16,
    c_uint32,
    c_uint64,
    c_void_p,
)
from typing import Any

from ._platform import find_library


class FffError(Exception):
    """Error returned by the fff native library."""


class _CStruct(Structure):
    def __repr__(self) -> str:
        fields = ", ".join(f"{n}={getattr(self, n)!r}" for n, _ in self._fields_)
        return f"{self.__class__.__name__}({fields})"


class FffResult(_CStruct):
    _fields_ = [
        ("success", c_bool),
        ("_padding0", c_char * 7),
        ("error", c_char_p),
        ("handle", c_void_p),
        ("int_value", c_int64),
    ]


class FffCreateOptions(_CStruct):
    _fields_ = [
        ("version", c_uint32),
        ("_padding0", c_char * 4),
        ("base_path", c_char_p),
        ("frecency_db_path", c_char_p),
        ("history_db_path", c_char_p),
        ("enable_mmap_cache", c_bool),
        ("enable_content_indexing", c_bool),
        ("watch", c_bool),
        ("ai_mode", c_bool),
        ("_padding1", c_char * 4),
        ("log_file_path", c_char_p),
        ("log_level", c_char_p),
        ("cache_budget_max_files", c_uint64),
        ("cache_budget_max_bytes", c_uint64),
        ("cache_budget_max_file_size", c_uint64),
        ("enable_fs_root_scanning", c_bool),
        ("enable_home_dir_scanning", c_bool),
        ("_padding2", c_char * 6),
    ]


class FffLocation(_CStruct):
    _fields_ = [
        ("tag", c_uint8),
        ("_padding0", c_char * 3),
        ("line", c_int32),
        ("col", c_int32),
        ("end_line", c_int32),
        ("end_col", c_int32),
    ]


class FffFileItem(_CStruct):
    _fields_ = [
        ("relative_path", c_char_p),
        ("file_name", c_char_p),
        ("git_status", c_char_p),
        ("size", c_uint64),
        ("modified", c_uint64),
        ("access_frecency_score", c_int64),
        ("modification_frecency_score", c_int64),
        ("total_frecency_score", c_int64),
        ("is_binary", c_bool),
        ("_padding0", c_char * 7),
    ]


class FffScore(_CStruct):
    _fields_ = [
        ("total", c_int32),
        ("base_score", c_int32),
        ("filename_bonus", c_int32),
        ("special_filename_bonus", c_int32),
        ("frecency_boost", c_int32),
        ("distance_penalty", c_int32),
        ("current_file_penalty", c_int32),
        ("combo_match_boost", c_int32),
        ("path_alignment_bonus", c_int32),
        ("exact_match", c_bool),
        ("_padding0", c_char * 3),
        ("match_type", c_char_p),
    ]


class FffSearchResult(_CStruct):
    _fields_ = [
        ("items", POINTER(FffFileItem)),
        ("scores", POINTER(FffScore)),
        ("count", c_uint32),
        ("total_matched", c_uint32),
        ("total_files", c_uint32),
        ("location", FffLocation),
    ]


class FffMatchRange(_CStruct):
    _fields_ = [
        ("start", c_uint32),
        ("end", c_uint32),
    ]


class FffGrepMatch(_CStruct):
    _fields_ = [
        ("relative_path", c_char_p),
        ("file_name", c_char_p),
        ("git_status", c_char_p),
        ("line_content", c_char_p),
        ("match_ranges", POINTER(FffMatchRange)),
        ("context_before", POINTER(c_char_p)),
        ("context_after", POINTER(c_char_p)),
        ("size", c_uint64),
        ("modified", c_uint64),
        ("total_frecency_score", c_int64),
        ("access_frecency_score", c_int64),
        ("modification_frecency_score", c_int64),
        ("line_number", c_uint64),
        ("byte_offset", c_uint64),
        ("col", c_uint32),
        ("match_ranges_count", c_uint32),
        ("context_before_count", c_uint32),
        ("context_after_count", c_uint32),
        ("fuzzy_score", c_uint16),
        ("has_fuzzy_score", c_bool),
        ("is_binary", c_bool),
        ("is_definition", c_bool),
        ("_padding0", c_char * 3),
    ]


class FffGrepResult(_CStruct):
    _fields_ = [
        ("items", POINTER(FffGrepMatch)),
        ("count", c_uint32),
        ("total_matched", c_uint32),
        ("total_files_searched", c_uint32),
        ("total_files", c_uint32),
        ("filtered_file_count", c_uint32),
        ("next_file_offset", c_uint32),
        ("regex_fallback_error", c_char_p),
    ]


class FffDirItem(_CStruct):
    _fields_ = [
        ("relative_path", c_char_p),
        ("dir_name", c_char_p),
        ("max_access_frecency", c_int32),
        ("_padding0", c_char * 4),
    ]


class FffDirSearchResult(_CStruct):
    _fields_ = [
        ("items", POINTER(FffDirItem)),
        ("scores", POINTER(FffScore)),
        ("count", c_uint32),
        ("total_matched", c_uint32),
        ("total_dirs", c_uint32),
        ("_padding0", c_char * 4),
    ]


class FffMixedItem(_CStruct):
    _fields_ = [
        ("item_type", c_uint8),
        ("_padding0", c_char * 7),
        ("relative_path", c_char_p),
        ("display_name", c_char_p),
        ("git_status", c_char_p),
        ("size", c_uint64),
        ("modified", c_uint64),
        ("access_frecency_score", c_int64),
        ("modification_frecency_score", c_int64),
        ("total_frecency_score", c_int64),
        ("is_binary", c_bool),
        ("_padding1", c_char * 7),
    ]


class FffMixedSearchResult(_CStruct):
    _fields_ = [
        ("items", POINTER(FffMixedItem)),
        ("scores", POINTER(FffScore)),
        ("count", c_uint32),
        ("total_matched", c_uint32),
        ("total_files", c_uint32),
        ("total_dirs", c_uint32),
        ("location", FffLocation),
    ]


class FffScanProgress(_CStruct):
    _fields_ = [
        ("scanned_files_count", c_uint64),
        ("is_scanning", c_bool),
        ("is_watcher_ready", c_bool),
        ("is_warmup_complete", c_bool),
        ("_padding0", c_char * 5),
    ]


class NativeLib:
    """Wrapper around the loaded libfff_c shared library."""

    def __init__(self) -> None:
        path = find_library()
        self._lib = CDLL(str(path))
        self._configure_types()

    def _configure_types(self) -> None:
        lib = self._lib

        # Create / destroy
        lib.fff_create_instance_with.argtypes = [POINTER(FffCreateOptions)]
        lib.fff_create_instance_with.restype = POINTER(FffResult)
        lib.fff_destroy.argtypes = [c_void_p]
        lib.fff_destroy.restype = None

        # Search
        lib.fff_search.argtypes = [
            c_void_p, c_char_p, c_char_p, c_uint32, c_uint32, c_uint32, c_int32, c_uint32,
        ]
        lib.fff_search.restype = POINTER(FffResult)
        lib.fff_glob.argtypes = [c_void_p, c_char_p, c_char_p, c_uint32, c_uint32, c_uint32]
        lib.fff_glob.restype = POINTER(FffResult)
        lib.fff_search_directories.argtypes = [c_void_p, c_char_p, c_char_p, c_uint32, c_uint32, c_uint32]
        lib.fff_search_directories.restype = POINTER(FffResult)
        lib.fff_search_mixed.argtypes = [
            c_void_p, c_char_p, c_char_p, c_uint32, c_uint32, c_uint32, c_int32, c_uint32,
        ]
        lib.fff_search_mixed.restype = POINTER(FffResult)

        # Grep
        lib.fff_live_grep.argtypes = [
            c_void_p, c_char_p, c_uint8, c_uint64, c_uint32, c_bool,
            c_uint32, c_uint32, c_uint64, c_uint32, c_uint32, c_bool,
        ]
        lib.fff_live_grep.restype = POINTER(FffResult)
        lib.fff_multi_grep.argtypes = [
            c_void_p, c_char_p, c_char_p, c_uint64, c_uint32, c_bool,
            c_uint32, c_uint32, c_uint64, c_uint32, c_uint32, c_bool,
        ]
        lib.fff_multi_grep.restype = POINTER(FffResult)

        # Index / scan
        lib.fff_scan_files.argtypes = [c_void_p]
        lib.fff_scan_files.restype = POINTER(FffResult)
        lib.fff_is_scanning.argtypes = [c_void_p]
        lib.fff_is_scanning.restype = c_bool
        lib.fff_get_base_path.argtypes = [c_void_p]
        lib.fff_get_base_path.restype = POINTER(FffResult)
        lib.fff_get_scan_progress.argtypes = [c_void_p]
        lib.fff_get_scan_progress.restype = POINTER(FffResult)
        lib.fff_wait_for_scan.argtypes = [c_void_p, c_uint64]
        lib.fff_wait_for_scan.restype = POINTER(FffResult)
        lib.fff_wait_for_watcher.argtypes = [c_void_p, c_uint64]
        lib.fff_wait_for_watcher.restype = POINTER(FffResult)
        lib.fff_restart_index.argtypes = [c_void_p, c_char_p]
        lib.fff_restart_index.restype = POINTER(FffResult)

        # Git / query tracking
        lib.fff_refresh_git_status.argtypes = [c_void_p]
        lib.fff_refresh_git_status.restype = POINTER(FffResult)
        lib.fff_track_query.argtypes = [c_void_p, c_char_p, c_char_p]
        lib.fff_track_query.restype = POINTER(FffResult)
        lib.fff_get_historical_query.argtypes = [c_void_p, c_uint64]
        lib.fff_get_historical_query.restype = POINTER(FffResult)
        lib.fff_health_check.argtypes = [c_void_p, c_char_p]
        lib.fff_health_check.restype = POINTER(FffResult)

        # Free functions
        lib.fff_free_result.argtypes = [POINTER(FffResult)]
        lib.fff_free_result.restype = None
        lib.fff_free_string.argtypes = [c_char_p]
        lib.fff_free_string.restype = None
        lib.fff_free_search_result.argtypes = [POINTER(FffSearchResult)]
        lib.fff_free_search_result.restype = None
        lib.fff_grep_result_get_count.argtypes = [POINTER(FffGrepResult)]
        lib.fff_grep_result_get_count.restype = c_uint32
        lib.fff_grep_result_get_regex_fallback_error.argtypes = [POINTER(FffGrepResult)]
        lib.fff_grep_result_get_regex_fallback_error.restype = c_char_p
        lib.fff_grep_result_get_match.argtypes = [POINTER(FffGrepResult), c_uint32]
        lib.fff_grep_result_get_match.restype = POINTER(FffGrepMatch)
        lib.fff_grep_match_get_relative_path.argtypes = [POINTER(FffGrepMatch)]
        lib.fff_grep_match_get_relative_path.restype = c_char_p
        lib.fff_grep_match_get_line_content.argtypes = [POINTER(FffGrepMatch)]
        lib.fff_grep_match_get_line_content.restype = c_char_p
        lib.fff_grep_match_get_match_ranges_count.argtypes = [POINTER(FffGrepMatch)]
        lib.fff_grep_match_get_match_ranges_count.restype = c_uint32
        lib.fff_grep_match_get_context_before_count.argtypes = [POINTER(FffGrepMatch)]
        lib.fff_grep_match_get_context_before_count.restype = c_uint32
        lib.fff_grep_match_get_context_after_count.argtypes = [POINTER(FffGrepMatch)]
        lib.fff_grep_match_get_context_after_count.restype = c_uint32
        lib.fff_free_grep_result.argtypes = [POINTER(FffGrepResult)]
        lib.fff_free_grep_result.restype = None
        lib.fff_free_dir_search_result.argtypes = [POINTER(FffDirSearchResult)]
        lib.fff_free_dir_search_result.restype = None
        lib.fff_free_mixed_search_result.argtypes = [POINTER(FffMixedSearchResult)]
        lib.fff_free_mixed_search_result.restype = None
        lib.fff_free_scan_progress.argtypes = [POINTER(FffScanProgress)]
        lib.fff_free_scan_progress.restype = None

    # --- helpers ---

    def _check_result(self, res: POINTER(FffResult)) -> tuple[c_void_p, int]:
        if not res:
            raise FffError("native function returned null result pointer")
        try:
            if not res.contents.success:
                msg = "unknown error"
                if res.contents.error:
                    msg = res.contents.error.decode("utf-8", errors="replace")
                raise FffError(msg)
            return res.contents.handle, res.contents.int_value
        finally:
            self._lib.fff_free_result(res)

    def _void_result(self, res: POINTER(FffResult)) -> None:
        self._check_result(res)

    def _bool_result(self, res: POINTER(FffResult)) -> bool:
        _, value = self._check_result(res)
        return bool(value)

    def _int_result(self, res: POINTER(FffResult)) -> int:
        _, value = self._check_result(res)
        return int(value)

    def _string_result(self, res: POINTER(FffResult)) -> str | None:
        handle, _ = self._check_result(res)
        if not handle:
            return None
        cstr = c_char_p(handle)
        try:
            raw = cstr.value
            return raw.decode("utf-8", errors="replace") if raw else None
        finally:
            self._lib.fff_free_string(cstr)

    def _json_result(self, res: POINTER(FffResult)) -> Any:
        text = self._string_result(res)
        if text is None:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text

    # --- public low-level API ---

    def create_instance(self, opts: FffCreateOptions) -> c_void_p:
        res = self._lib.fff_create_instance_with(opts)
        handle, _ = self._check_result(res)
        return handle

    def destroy(self, handle: c_void_p) -> None:
        self._lib.fff_destroy(handle)

    def search(
        self,
        handle: c_void_p,
        query: bytes,
        current_file: bytes,
        max_threads: int,
        page_index: int,
        page_size: int,
        combo_boost_multiplier: int,
        min_combo_count: int,
    ) -> POINTER(FffSearchResult):
        res = self._lib.fff_search(
            handle, query, current_file, max_threads, page_index, page_size,
            combo_boost_multiplier, min_combo_count,
        )
        handle_ptr, _ = self._check_result(res)
        return cast(handle_ptr, POINTER(FffSearchResult))

    def free_search_result(self, result: POINTER(FffSearchResult)) -> None:
        self._lib.fff_free_search_result(result)

    def glob(
        self,
        handle: c_void_p,
        pattern: bytes,
        current_file: bytes,
        max_threads: int,
        page_index: int,
        page_size: int,
    ) -> POINTER(FffSearchResult):
        res = self._lib.fff_glob(handle, pattern, current_file, max_threads, page_index, page_size)
        handle_ptr, _ = self._check_result(res)
        return cast(handle_ptr, POINTER(FffSearchResult))

    def search_directories(
        self,
        handle: c_void_p,
        query: bytes,
        current_file: bytes,
        max_threads: int,
        page_index: int,
        page_size: int,
    ) -> POINTER(FffDirSearchResult):
        res = self._lib.fff_search_directories(
            handle, query, current_file, max_threads, page_index, page_size,
        )
        handle_ptr, _ = self._check_result(res)
        return cast(handle_ptr, POINTER(FffDirSearchResult))

    def free_dir_search_result(self, result: POINTER(FffDirSearchResult)) -> None:
        self._lib.fff_free_dir_search_result(result)

    def search_mixed(
        self,
        handle: c_void_p,
        query: bytes,
        current_file: bytes,
        max_threads: int,
        page_index: int,
        page_size: int,
        combo_boost_multiplier: int,
        min_combo_count: int,
    ) -> POINTER(FffMixedSearchResult):
        res = self._lib.fff_search_mixed(
            handle, query, current_file, max_threads, page_index, page_size,
            combo_boost_multiplier, min_combo_count,
        )
        handle_ptr, _ = self._check_result(res)
        return cast(handle_ptr, POINTER(FffMixedSearchResult))

    def free_mixed_search_result(self, result: POINTER(FffMixedSearchResult)) -> None:
        self._lib.fff_free_mixed_search_result(result)

    def live_grep(
        self,
        handle: c_void_p,
        query: bytes,
        mode: int,
        max_file_size: int,
        max_matches_per_file: int,
        smart_case: bool,
        file_offset: int,
        page_limit: int,
        time_budget_ms: int,
        before_context: int,
        after_context: int,
        classify_definitions: bool,
    ) -> POINTER(FffGrepResult):
        res = self._lib.fff_live_grep(
            handle, query, mode, max_file_size, max_matches_per_file, smart_case,
            file_offset, page_limit, time_budget_ms, before_context, after_context,
            classify_definitions,
        )
        handle_ptr, _ = self._check_result(res)
        return cast(handle_ptr, POINTER(FffGrepResult))

    def multi_grep(
        self,
        handle: c_void_p,
        patterns: bytes,
        constraints: bytes,
        max_file_size: int,
        max_matches_per_file: int,
        smart_case: bool,
        file_offset: int,
        page_limit: int,
        time_budget_ms: int,
        before_context: int,
        after_context: int,
        classify_definitions: bool,
    ) -> POINTER(FffGrepResult):
        res = self._lib.fff_multi_grep(
            handle, patterns, constraints, max_file_size, max_matches_per_file, smart_case,
            file_offset, page_limit, time_budget_ms, before_context, after_context,
            classify_definitions,
        )
        handle_ptr, _ = self._check_result(res)
        return cast(handle_ptr, POINTER(FffGrepResult))

    def free_grep_result(self, result: POINTER(FffGrepResult)) -> None:
        self._lib.fff_free_grep_result(result)

    def scan_files(self, handle: c_void_p) -> None:
        self._void_result(self._lib.fff_scan_files(handle))

    def is_scanning(self, handle: c_void_p) -> bool:
        return self._lib.fff_is_scanning(handle)

    def get_base_path(self, handle: c_void_p) -> str | None:
        return self._string_result(self._lib.fff_get_base_path(handle))

    def get_scan_progress(self, handle: c_void_p) -> POINTER(FffScanProgress):
        res = self._lib.fff_get_scan_progress(handle)
        handle_ptr, _ = self._check_result(res)
        return cast(handle_ptr, POINTER(FffScanProgress))

    def free_scan_progress(self, progress: POINTER(FffScanProgress)) -> None:
        self._lib.fff_free_scan_progress(progress)

    def wait_for_scan(self, handle: c_void_p, timeout_ms: int) -> bool:
        return self._bool_result(self._lib.fff_wait_for_scan(handle, timeout_ms))

    def wait_for_watcher(self, handle: c_void_p, timeout_ms: int) -> bool:
        return self._bool_result(self._lib.fff_wait_for_watcher(handle, timeout_ms))

    def restart_index(self, handle: c_void_p, new_path: bytes) -> None:
        self._void_result(self._lib.fff_restart_index(handle, new_path))

    def refresh_git_status(self, handle: c_void_p) -> int:
        return self._int_result(self._lib.fff_refresh_git_status(handle))

    def track_query(self, handle: c_void_p, query: bytes, file_path: bytes) -> bool:
        return self._bool_result(self._lib.fff_track_query(handle, query, file_path))

    def get_historical_query(self, handle: c_void_p, offset: int) -> str | None:
        return self._string_result(self._lib.fff_get_historical_query(handle, offset))

    def health_check(self, handle: c_void_p, test_path: bytes) -> Any:
        return self._json_result(self._lib.fff_health_check(handle, test_path))


_lib: NativeLib | None = None


def get_native_lib() -> NativeLib:
    global _lib
    if _lib is None:
        _lib = NativeLib()
    return _lib
