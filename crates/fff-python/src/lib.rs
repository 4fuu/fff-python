use std::path::PathBuf;
use std::time::Duration;

use fff::file_picker::FilePicker;
use fff::frecency::FrecencyTracker;
use fff::query_tracker::QueryTracker;
use fff::{
    FFFMode, FilePickerOptions, FuzzySearchOptions, GrepSearchOptions, PaginationArgs, QueryParser,
    SharedFilePicker, SharedFrecency, SharedQueryTracker,
};
use pyo3::create_exception;
use pyo3::prelude::*;

create_exception!(fff_python, FFFException, pyo3::exceptions::PyException);

fn py_err<E: std::fmt::Display>(e: E) -> PyErr {
    PyErr::new::<FFFException, _>(format!("{}", e))
}

// ---------------------------------------------------------------------------
// Result types
// ---------------------------------------------------------------------------

#[pyclass]
#[derive(Clone)]
pub struct Score {
    #[pyo3(get)]
    pub total: i32,
    #[pyo3(get)]
    pub base_score: i32,
    #[pyo3(get)]
    pub filename_bonus: i32,
    #[pyo3(get)]
    pub special_filename_bonus: i32,
    #[pyo3(get)]
    pub frecency_boost: i32,
    #[pyo3(get)]
    pub distance_penalty: i32,
    #[pyo3(get)]
    pub current_file_penalty: i32,
    #[pyo3(get)]
    pub combo_match_boost: i32,
    #[pyo3(get)]
    pub path_alignment_bonus: i32,
    #[pyo3(get)]
    pub exact_match: bool,
    #[pyo3(get)]
    pub match_type: String,
}

impl From<&fff::Score> for Score {
    fn from(s: &fff::Score) -> Self {
        Self {
            total: s.total,
            base_score: s.base_score,
            filename_bonus: s.filename_bonus,
            special_filename_bonus: s.special_filename_bonus,
            frecency_boost: s.frecency_boost,
            distance_penalty: s.distance_penalty,
            current_file_penalty: s.current_file_penalty,
            combo_match_boost: s.combo_match_boost,
            path_alignment_bonus: s.path_alignment_bonus,
            exact_match: s.exact_match,
            match_type: s.match_type.to_string(),
        }
    }
}

#[pyclass]
#[derive(Clone)]
pub struct FileItem {
    #[pyo3(get)]
    pub relative_path: String,
    #[pyo3(get)]
    pub file_name: String,
    #[pyo3(get)]
    pub git_status: String,
    #[pyo3(get)]
    pub size: u64,
    #[pyo3(get)]
    pub modified: u64,
    #[pyo3(get)]
    pub access_frecency_score: i64,
    #[pyo3(get)]
    pub modification_frecency_score: i64,
    #[pyo3(get)]
    pub total_frecency_score: i64,
    #[pyo3(get)]
    pub is_binary: bool,
}

impl FileItem {
    fn from_core(item: &fff::FileItem, picker: &FilePicker) -> Self {
        Self {
            relative_path: item.relative_path(picker),
            file_name: item.file_name(picker),
            git_status: fff::git::format_git_status(item.git_status).to_string(),
            size: item.size,
            modified: item.modified,
            access_frecency_score: item.access_frecency_score as i64,
            modification_frecency_score: item.modification_frecency_score as i64,
            total_frecency_score: item.total_frecency_score() as i64,
            is_binary: item.is_binary(),
        }
    }
}

#[pyclass]
#[derive(Clone)]
pub struct DirItem {
    #[pyo3(get)]
    pub relative_path: String,
    #[pyo3(get)]
    pub dir_name: String,
    #[pyo3(get)]
    pub max_access_frecency: i32,
}

impl DirItem {
    fn from_core(item: &fff::DirItem, picker: &FilePicker) -> Self {
        Self {
            relative_path: item.relative_path(picker),
            dir_name: item.dir_name(picker),
            max_access_frecency: item.max_access_frecency(),
        }
    }
}

#[pyclass]
pub struct MixedFileItem {
    #[pyo3(get)]
    pub relative_path: String,
    #[pyo3(get)]
    pub file_name: String,
    #[pyo3(get)]
    pub git_status: String,
    #[pyo3(get)]
    pub size: u64,
    #[pyo3(get)]
    pub modified: u64,
    #[pyo3(get)]
    pub access_frecency_score: i64,
    #[pyo3(get)]
    pub modification_frecency_score: i64,
    #[pyo3(get)]
    pub total_frecency_score: i64,
    #[pyo3(get)]
    pub is_binary: bool,
}

#[pyclass]
pub struct MixedDirItem {
    #[pyo3(get)]
    pub relative_path: String,
    #[pyo3(get)]
    pub dir_name: String,
    #[pyo3(get)]
    pub max_access_frecency: i64,
}

#[pyclass]
#[derive(Clone)]
pub struct MatchRange {
    #[pyo3(get)]
    pub start: u32,
    #[pyo3(get)]
    pub end: u32,
}

#[pyclass]
#[derive(Clone)]
pub struct GrepMatch {
    #[pyo3(get)]
    pub relative_path: String,
    #[pyo3(get)]
    pub file_name: String,
    #[pyo3(get)]
    pub git_status: String,
    #[pyo3(get)]
    pub line_content: String,
    #[pyo3(get)]
    pub match_ranges: Vec<MatchRange>,
    #[pyo3(get)]
    pub context_before: Vec<String>,
    #[pyo3(get)]
    pub context_after: Vec<String>,
    #[pyo3(get)]
    pub size: u64,
    #[pyo3(get)]
    pub modified: u64,
    #[pyo3(get)]
    pub total_frecency_score: i64,
    #[pyo3(get)]
    pub access_frecency_score: i64,
    #[pyo3(get)]
    pub modification_frecency_score: i64,
    #[pyo3(get)]
    pub line_number: u64,
    #[pyo3(get)]
    pub byte_offset: u64,
    #[pyo3(get)]
    pub col: u32,
    #[pyo3(get)]
    pub fuzzy_score: Option<u16>,
    #[pyo3(get)]
    pub is_definition: bool,
    #[pyo3(get)]
    pub is_binary: bool,
}

impl GrepMatch {
    fn from_core(m: &fff::GrepMatch, file: &fff::FileItem, picker: &FilePicker) -> Self {
        Self {
            relative_path: file.relative_path(picker),
            file_name: file.file_name(picker),
            git_status: fff::git::format_git_status(file.git_status).to_string(),
            line_content: m.line_content.clone(),
            match_ranges: m
                .match_byte_offsets
                .iter()
                .map(|&(s, e)| MatchRange { start: s, end: e })
                .collect(),
            context_before: m.context_before.clone(),
            context_after: m.context_after.clone(),
            size: file.size,
            modified: file.modified,
            total_frecency_score: file.total_frecency_score() as i64,
            access_frecency_score: file.access_frecency_score as i64,
            modification_frecency_score: file.modification_frecency_score as i64,
            line_number: m.line_number,
            byte_offset: m.byte_offset,
            col: m.col as u32,
            fuzzy_score: m.fuzzy_score,
            is_definition: m.is_definition,
            is_binary: file.is_binary(),
        }
    }
}

#[pyclass]
pub struct SearchResult {
    #[pyo3(get)]
    pub items: Vec<FileItem>,
    #[pyo3(get)]
    pub scores: Vec<Score>,
    #[pyo3(get)]
    pub total_matched: u32,
    #[pyo3(get)]
    pub total_files: u32,
}

#[pyclass]
pub struct DirSearchResult {
    #[pyo3(get)]
    pub items: Vec<DirItem>,
    #[pyo3(get)]
    pub scores: Vec<Score>,
    #[pyo3(get)]
    pub total_matched: u32,
    #[pyo3(get)]
    pub total_dirs: u32,
}

#[pyclass]
pub struct MixedSearchResult {
    #[pyo3(get)]
    pub items: Vec<PyObject>,
    #[pyo3(get)]
    pub scores: Vec<Score>,
    #[pyo3(get)]
    pub total_matched: u32,
    #[pyo3(get)]
    pub total_files: u32,
    #[pyo3(get)]
    pub total_dirs: u32,
}

#[pyclass]
pub struct GrepResult {
    #[pyo3(get)]
    pub items: Vec<GrepMatch>,
    #[pyo3(get)]
    pub total_matched: u32,
    #[pyo3(get)]
    pub total_files_searched: u32,
    #[pyo3(get)]
    pub total_files: u32,
    #[pyo3(get)]
    pub filtered_file_count: u32,
    #[pyo3(get)]
    pub next_file_offset: u32,
    #[pyo3(get)]
    pub regex_fallback_error: Option<String>,
}

#[pyclass]
pub struct ScanProgress {
    #[pyo3(get)]
    pub scanned_files_count: u64,
    #[pyo3(get)]
    pub is_scanning: bool,
    #[pyo3(get)]
    pub is_watcher_ready: bool,
    #[pyo3(get)]
    pub is_warmup_complete: bool,
}

#[pyclass]
pub struct GrepCursor {
    #[pyo3(get)]
    pub offset: u32,
}

// ---------------------------------------------------------------------------
// FileFinder
// ---------------------------------------------------------------------------

#[pyclass]
pub struct FileFinder {
    picker: SharedFilePicker,
    frecency: SharedFrecency,
    query_tracker: SharedQueryTracker,
}

impl Drop for FileFinder {
    fn drop(&mut self) {
        if let Ok(mut guard) = self.picker.write() {
            guard.take();
        }
        if let Ok(mut guard) = self.frecency.write() {
            *guard = None;
        }
        if let Ok(mut guard) = self.query_tracker.write() {
            *guard = None;
        }
    }
}

#[pymethods]
impl FileFinder {
    #[new]
    #[pyo3(signature = (
        base_path,
        frecency_db_path=None,
        history_db_path=None,
        enable_mmap_cache=true,
        enable_content_indexing=true,
        watch=true,
        ai_mode=false,
        log_file_path=None,
        log_level=None,
        cache_budget_max_files=0,
        cache_budget_max_bytes=0,
        cache_budget_max_file_size=0,
        enable_fs_root_scanning=false,
        enable_home_dir_scanning=false,
    ))]
    #[allow(clippy::too_many_arguments)]
    fn new(
        base_path: &str,
        frecency_db_path: Option<String>,
        history_db_path: Option<String>,
        enable_mmap_cache: bool,
        enable_content_indexing: bool,
        watch: bool,
        ai_mode: bool,
        log_file_path: Option<String>,
        log_level: Option<String>,
        cache_budget_max_files: u64,
        cache_budget_max_bytes: u64,
        cache_budget_max_file_size: u64,
        enable_fs_root_scanning: bool,
        enable_home_dir_scanning: bool,
    ) -> PyResult<Self> {
        let shared_picker = SharedFilePicker::default();
        let shared_frecency = SharedFrecency::default();
        let query_tracker = SharedQueryTracker::default();

        if let Some(path) = frecency_db_path {
            let parent = PathBuf::from(&path).parent().map(PathBuf::from);
            if let Some(p) = parent {
                let _ = std::fs::create_dir_all(p);
            }
            let tracker = FrecencyTracker::open(&path).map_err(py_err)?;
            shared_frecency.init(tracker).map_err(py_err)?;
        }

        if let Some(path) = history_db_path {
            let parent = PathBuf::from(&path).parent().map(PathBuf::from);
            if let Some(p) = parent {
                let _ = std::fs::create_dir_all(p);
            }
            let tracker = QueryTracker::open(&path).map_err(py_err)?;
            query_tracker.init(tracker).map_err(py_err)?;
        }

        if let Some(path) = log_file_path {
            let level = log_level.as_deref();
            fff::log::init_tracing(&path, level, None).map_err(py_err)?;
        }

        let mode = if ai_mode {
            FFFMode::Ai
        } else {
            FFFMode::Neovim
        };

        let cache_budget = fff::ContentCacheBudget::from_overrides(
            cache_budget_max_files as usize,
            cache_budget_max_bytes,
            cache_budget_max_file_size,
        );

        FilePicker::new_with_shared_state(
            shared_picker.clone(),
            shared_frecency.clone(),
            FilePickerOptions {
                base_path: base_path.to_string(),
                enable_mmap_cache,
                enable_content_indexing,
                watch,
                mode,
                cache_budget,
                follow_symlinks: false,
                enable_fs_root_scanning,
                enable_home_dir_scanning,
            },
        )
        .map_err(py_err)?;

        Ok(Self {
            picker: shared_picker,
            frecency: shared_frecency,
            query_tracker,
        })
    }

    fn __enter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __exit__(&mut self, _exc_type: PyObject, _exc_value: PyObject, _traceback: PyObject) {}

    fn destroy(&mut self) -> PyResult<()> {
        if let Ok(mut guard) = self.picker.write() {
            *guard = None;
        }
        if let Ok(mut guard) = self.frecency.write() {
            *guard = None;
        }
        if let Ok(mut guard) = self.query_tracker.write() {
            *guard = None;
        }
        Ok(())
    }

    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (
        query,
        current_file=None,
        max_threads=0,
        page_index=0,
        page_size=0,
        combo_boost_multiplier=0,
        min_combo_count=0,
    ))]
    fn search(
        &self,
        query: &str,
        current_file: Option<String>,
        max_threads: u32,
        page_index: u32,
        page_size: u32,
        combo_boost_multiplier: i32,
        min_combo_count: u32,
    ) -> PyResult<SearchResult> {
        let picker_guard = self.picker.read().map_err(py_err)?;
        let picker = picker_guard
            .as_ref()
            .ok_or_else(|| py_err("File picker not initialized"))?;

        let qt_guard = self.query_tracker.read().map_err(py_err)?;

        let parser = QueryParser::default();
        let parsed = parser.parse(query);
        let result = picker.fuzzy_search(
            &parsed,
            qt_guard.as_ref(),
            FuzzySearchOptions {
                max_threads: max_threads as usize,
                current_file: current_file.as_deref(),
                project_path: Some(picker.base_path()),
                combo_boost_score_multiplier: combo_boost_multiplier,
                min_combo_count,
                pagination: PaginationArgs {
                    offset: page_index as usize,
                    limit: if page_size == 0 {
                        100
                    } else {
                        page_size as usize
                    },
                },
            },
        );

        let items: Vec<FileItem> = result
            .items
            .iter()
            .map(|i| FileItem::from_core(i, picker))
            .collect();
        let scores: Vec<Score> = result.scores.iter().map(Score::from).collect();

        Ok(SearchResult {
            items,
            scores,
            total_matched: result.total_matched as u32,
            total_files: result.total_files as u32,
        })
    }

    #[pyo3(signature = (
        pattern,
        current_file=None,
        max_threads=0,
        page_index=0,
        page_size=0,
    ))]
    fn glob(
        &self,
        pattern: &str,
        current_file: Option<String>,
        max_threads: u32,
        page_index: u32,
        page_size: u32,
    ) -> PyResult<SearchResult> {
        let picker_guard = self.picker.read().map_err(py_err)?;
        let picker = picker_guard
            .as_ref()
            .ok_or_else(|| py_err("File picker not initialized"))?;

        let result = picker.glob(
            pattern,
            FuzzySearchOptions {
                max_threads: max_threads as usize,
                current_file: current_file.as_deref(),
                project_path: Some(picker.base_path()),
                combo_boost_score_multiplier: 0,
                min_combo_count: 0,
                pagination: PaginationArgs {
                    offset: page_index as usize,
                    limit: if page_size == 0 {
                        100
                    } else {
                        page_size as usize
                    },
                },
            },
        );

        let items: Vec<FileItem> = result
            .items
            .iter()
            .map(|i| FileItem::from_core(i, picker))
            .collect();
        let scores: Vec<Score> = result.scores.iter().map(Score::from).collect();

        Ok(SearchResult {
            items,
            scores,
            total_matched: result.total_matched as u32,
            total_files: result.total_files as u32,
        })
    }

    #[pyo3(signature = (
        query,
        current_file=None,
        max_threads=0,
        page_index=0,
        page_size=0,
    ))]
    fn directory_search(
        &self,
        query: &str,
        current_file: Option<String>,
        max_threads: u32,
        page_index: u32,
        page_size: u32,
    ) -> PyResult<DirSearchResult> {
        let picker_guard = self.picker.read().map_err(py_err)?;
        let picker = picker_guard
            .as_ref()
            .ok_or_else(|| py_err("File picker not initialized"))?;

        let parser = QueryParser::new(fff_query_parser::DirSearchConfig);
        let parsed = parser.parse(query);
        let result = picker.fuzzy_search_directories(
            &parsed,
            FuzzySearchOptions {
                max_threads: max_threads as usize,
                current_file: current_file.as_deref(),
                project_path: Some(picker.base_path()),
                combo_boost_score_multiplier: 0,
                min_combo_count: 0,
                pagination: PaginationArgs {
                    offset: page_index as usize,
                    limit: if page_size == 0 {
                        100
                    } else {
                        page_size as usize
                    },
                },
            },
        );

        let items: Vec<DirItem> = result
            .items
            .iter()
            .map(|i| DirItem::from_core(i, picker))
            .collect();
        let scores: Vec<Score> = result.scores.iter().map(Score::from).collect();

        Ok(DirSearchResult {
            items,
            scores,
            total_matched: result.total_matched as u32,
            total_dirs: result.total_dirs as u32,
        })
    }

    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (
        query,
        current_file=None,
        max_threads=0,
        page_index=0,
        page_size=0,
        combo_boost_multiplier=0,
        min_combo_count=0,
    ))]
    fn mixed_search(
        &self,
        query: &str,
        current_file: Option<String>,
        max_threads: u32,
        page_index: u32,
        page_size: u32,
        combo_boost_multiplier: i32,
        min_combo_count: u32,
    ) -> PyResult<MixedSearchResult> {
        let picker_guard = self.picker.read().map_err(py_err)?;
        let picker = picker_guard
            .as_ref()
            .ok_or_else(|| py_err("File picker not initialized"))?;

        let qt_guard = self.query_tracker.read().map_err(py_err)?;

        let parser = QueryParser::new(fff_query_parser::MixedSearchConfig);
        let parsed = parser.parse(query);
        let result = picker.fuzzy_search_mixed(
            &parsed,
            qt_guard.as_ref(),
            FuzzySearchOptions {
                max_threads: max_threads as usize,
                current_file: current_file.as_deref(),
                project_path: Some(picker.base_path()),
                combo_boost_score_multiplier: combo_boost_multiplier,
                min_combo_count,
                pagination: PaginationArgs {
                    offset: page_index as usize,
                    limit: if page_size == 0 {
                        100
                    } else {
                        page_size as usize
                    },
                },
            },
        );

        Python::with_gil(|py| {
            let items: PyResult<Vec<PyObject>> = result
                .items
                .iter()
                .map(|item| match item {
                    fff::MixedItemRef::File(file) => {
                        let it = FileItem::from_core(file, picker);
                        Ok(Py::new(
                            py,
                            MixedFileItem {
                                relative_path: it.relative_path,
                                file_name: it.file_name,
                                git_status: it.git_status,
                                size: it.size,
                                modified: it.modified,
                                access_frecency_score: it.access_frecency_score,
                                modification_frecency_score: it.modification_frecency_score,
                                total_frecency_score: it.total_frecency_score,
                                is_binary: it.is_binary,
                            },
                        )?
                        .into_any())
                    }
                    fff::MixedItemRef::Dir(dir) => {
                        let it = DirItem::from_core(dir, picker);
                        Ok(Py::new(
                            py,
                            MixedDirItem {
                                relative_path: it.relative_path,
                                dir_name: it.dir_name,
                                max_access_frecency: it.max_access_frecency as i64,
                            },
                        )?
                        .into_any())
                    }
                })
                .collect();
            let scores: Vec<Score> = result.scores.iter().map(Score::from).collect();
            Ok(MixedSearchResult {
                items: items?,
                scores,
                total_matched: result.total_matched as u32,
                total_files: result.total_files as u32,
                total_dirs: result.total_dirs as u32,
            })
        })
    }

    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (
        query,
        mode="plain",
        max_file_size=0,
        max_matches_per_file=0,
        smart_case=true,
        cursor=None,
        page_limit=0,
        time_budget_ms=0,
        before_context=0,
        after_context=0,
        classify_definitions=false,
    ))]
    fn grep(
        &self,
        query: &str,
        mode: &str,
        max_file_size: u64,
        max_matches_per_file: u32,
        smart_case: bool,
        cursor: Option<&GrepCursor>,
        page_limit: u32,
        time_budget_ms: u64,
        before_context: u32,
        after_context: u32,
        classify_definitions: bool,
    ) -> PyResult<GrepResult> {
        let picker_guard = self.picker.read().map_err(py_err)?;
        let picker = picker_guard
            .as_ref()
            .ok_or_else(|| py_err("File picker not initialized"))?;

        let mode = match mode {
            "regex" => fff::GrepMode::Regex,
            "fuzzy" => fff::GrepMode::Fuzzy,
            _ => fff::GrepMode::PlainText,
        };

        let is_ai = picker.mode().is_ai();
        let parsed = if is_ai {
            QueryParser::new(fff_query_parser::AiGrepConfig).parse(query)
        } else {
            fff::grep::parse_grep_query(query)
        };

        let options = GrepSearchOptions {
            max_file_size: if max_file_size == 0 {
                10 * 1024 * 1024
            } else {
                max_file_size
            },
            max_matches_per_file: max_matches_per_file as usize,
            smart_case,
            file_offset: cursor.map(|c| c.offset as usize).unwrap_or(0),
            page_limit: if page_limit == 0 {
                50
            } else {
                page_limit as usize
            },
            mode,
            time_budget_ms,
            before_context: before_context as usize,
            after_context: after_context as usize,
            classify_definitions,
            trim_whitespace: false,
            abort_signal: None,
        };

        let result = picker.grep(&parsed, &options);
        let items: Vec<GrepMatch> = result
            .matches
            .iter()
            .map(|m| GrepMatch::from_core(m, result.files[m.file_index], picker))
            .collect();

        Ok(GrepResult {
            items,
            total_matched: result.matches.len() as u32,
            total_files_searched: result.total_files_searched as u32,
            total_files: result.total_files as u32,
            filtered_file_count: result.filtered_file_count as u32,
            next_file_offset: result.next_file_offset as u32,
            regex_fallback_error: result.regex_fallback_error,
        })
    }

    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (
        patterns,
        constraints=None,
        max_file_size=0,
        max_matches_per_file=0,
        smart_case=true,
        cursor=None,
        page_limit=0,
        time_budget_ms=0,
        before_context=0,
        after_context=0,
        classify_definitions=false,
    ))]
    fn multi_grep(
        &self,
        patterns: Vec<String>,
        constraints: Option<String>,
        max_file_size: u64,
        max_matches_per_file: u32,
        smart_case: bool,
        cursor: Option<&GrepCursor>,
        page_limit: u32,
        time_budget_ms: u64,
        before_context: u32,
        after_context: u32,
        classify_definitions: bool,
    ) -> PyResult<GrepResult> {
        let picker_guard = self.picker.read().map_err(py_err)?;
        let picker = picker_guard
            .as_ref()
            .ok_or_else(|| py_err("File picker not initialized"))?;

        if patterns.is_empty() || patterns.iter().all(|p| p.is_empty()) {
            return Err(py_err("patterns must not be empty"));
        }
        let patterns: Vec<&str> = patterns.iter().map(|s| s.as_str()).collect();

        let is_ai = picker.mode().is_ai();
        let parsed_constraints = constraints.as_ref().map(|c| {
            if is_ai {
                QueryParser::new(fff_query_parser::AiGrepConfig).parse(c)
            } else {
                fff::grep::parse_grep_query(c)
            }
        });
        let constraint_refs: &[fff::Constraint<'_>] = match &parsed_constraints {
            Some(q) => &q.constraints,
            None => &[],
        };

        let options = GrepSearchOptions {
            max_file_size: if max_file_size == 0 {
                10 * 1024 * 1024
            } else {
                max_file_size
            },
            max_matches_per_file: max_matches_per_file as usize,
            smart_case,
            file_offset: cursor.map(|c| c.offset as usize).unwrap_or(0),
            page_limit: if page_limit == 0 {
                50
            } else {
                page_limit as usize
            },
            mode: fff::GrepMode::PlainText,
            time_budget_ms,
            before_context: before_context as usize,
            after_context: after_context as usize,
            classify_definitions,
            trim_whitespace: false,
            abort_signal: None,
        };

        let result = picker.multi_grep(&patterns, constraint_refs, &options);
        let items: Vec<GrepMatch> = result
            .matches
            .iter()
            .map(|m| GrepMatch::from_core(m, result.files[m.file_index], picker))
            .collect();

        Ok(GrepResult {
            items,
            total_matched: result.matches.len() as u32,
            total_files_searched: result.total_files_searched as u32,
            total_files: result.total_files as u32,
            filtered_file_count: result.filtered_file_count as u32,
            next_file_offset: result.next_file_offset as u32,
            regex_fallback_error: result.regex_fallback_error,
        })
    }

    fn scan_files(&self) -> PyResult<()> {
        self.picker
            .trigger_full_rescan_async(&self.frecency)
            .map_err(py_err)
    }

    fn is_scanning(&self) -> PyResult<bool> {
        let guard = self.picker.read().map_err(py_err)?;
        Ok(guard.as_ref().map(|p| p.is_scan_active()).unwrap_or(false))
    }

    fn wait_for_scan(&self, timeout_ms: u64) -> PyResult<bool> {
        Ok(self.picker.wait_for_scan(Duration::from_millis(timeout_ms)))
    }

    fn get_scan_progress(&self) -> PyResult<ScanProgress> {
        let guard = self.picker.read().map_err(py_err)?;
        let picker = guard
            .as_ref()
            .ok_or_else(|| py_err("File picker not initialized"))?;
        let p = picker.get_scan_progress();
        Ok(ScanProgress {
            scanned_files_count: p.scanned_files_count as u64,
            is_scanning: p.is_scanning,
            is_watcher_ready: p.is_watcher_ready,
            is_warmup_complete: p.is_warmup_complete,
        })
    }

    fn get_base_path(&self) -> PyResult<Option<String>> {
        let guard = self.picker.read().map_err(py_err)?;
        Ok(guard
            .as_ref()
            .map(|p| p.base_path().to_string_lossy().to_string()))
    }

    fn reindex(&self, new_path: &str) -> PyResult<()> {
        let path = PathBuf::from(new_path);
        if !path.exists() {
            return Err(py_err(format!("Path does not exist: {}", new_path)));
        }
        let canonical = fff::path_utils::canonicalize(&path).map_err(py_err)?;

        let (warmup_caches, content_indexing, watch, mode, fs_root, home_dir) = {
            let guard = self.picker.write().map_err(py_err)?;
            if let Some(ref picker) = *guard {
                (
                    picker.has_mmap_cache(),
                    picker.has_content_indexing(),
                    picker.has_watcher(),
                    picker.mode(),
                    picker.fs_root_scanning_enabled(),
                    picker.home_dir_scanning_enabled(),
                )
            } else {
                (false, true, true, FFFMode::default(), false, false)
            }
        };

        FilePicker::new_with_shared_state(
            self.picker.clone(),
            self.frecency.clone(),
            FilePickerOptions {
                base_path: canonical.to_string_lossy().to_string(),
                enable_mmap_cache: warmup_caches,
                enable_content_indexing: content_indexing,
                watch,
                mode,
                cache_budget: None,
                follow_symlinks: false,
                enable_fs_root_scanning: fs_root,
                enable_home_dir_scanning: home_dir,
            },
        )
        .map_err(py_err)
    }

    fn refresh_git_status(&self) -> PyResult<i64> {
        self.picker
            .refresh_git_status(&self.frecency)
            .map_err(py_err)
            .map(|c| c as i64)
    }

    #[pyo3(signature = (query, selected_file_path))]
    fn track_query(&self, query: &str, selected_file_path: &str) -> PyResult<bool> {
        let file_path = fff::path_utils::canonicalize(selected_file_path).map_err(py_err)?;
        let project_path = {
            let guard = self.picker.read().map_err(py_err)?;
            guard.as_ref().map(|p| p.base_path().to_path_buf())
        };
        let project_path = match project_path {
            Some(p) => p,
            None => return Ok(false),
        };

        let mut qt_guard = self.query_tracker.write().map_err(py_err)?;
        if let Some(ref mut tracker) = *qt_guard {
            tracker
                .track_query_completion(query, &project_path, &file_path)
                .map_err(py_err)?;
            Ok(true)
        } else {
            Ok(false)
        }
    }

    fn get_historical_query(&self, offset: u64) -> PyResult<Option<String>> {
        let project_path = {
            let guard = self.picker.read().map_err(py_err)?;
            guard.as_ref().map(|p| p.base_path().to_path_buf())
        };
        let project_path = match project_path {
            Some(p) => p,
            None => return Ok(None),
        };

        let qt_guard = self.query_tracker.read().map_err(py_err)?;
        if let Some(ref tracker) = *qt_guard {
            tracker
                .get_historical_query(&project_path, offset as usize)
                .map_err(py_err)
        } else {
            Ok(None)
        }
    }

    #[pyo3(signature = (test_path=None))]
    fn health_check(&self, test_path: Option<String>) -> PyResult<String> {
        let test_path = test_path
            .map(PathBuf::from)
            .unwrap_or_else(|| std::env::current_dir().unwrap_or_default());

        let mut health = serde_json::Map::new();
        health.insert(
            "version".to_string(),
            serde_json::Value::String(env!("CARGO_PKG_VERSION").to_string()),
        );

        let mut git_info = serde_json::Map::new();
        let git_version = git2::Version::get();
        let (major, minor, rev) = git_version.libgit2_version();
        git_info.insert(
            "libgit2_version".to_string(),
            serde_json::Value::String(format!("{}.{}.{}", major, minor, rev)),
        );
        match git2::Repository::discover(&test_path) {
            Ok(repo) => {
                git_info.insert("available".to_string(), serde_json::Value::Bool(true));
                git_info.insert(
                    "repository_found".to_string(),
                    serde_json::Value::Bool(true),
                );
                if let Some(workdir) = repo.workdir() {
                    git_info.insert(
                        "workdir".to_string(),
                        serde_json::Value::String(workdir.to_string_lossy().to_string()),
                    );
                }
            }
            Err(e) => {
                git_info.insert("available".to_string(), serde_json::Value::Bool(true));
                git_info.insert(
                    "repository_found".to_string(),
                    serde_json::Value::Bool(false),
                );
                git_info.insert(
                    "error".to_string(),
                    serde_json::Value::String(e.message().to_string()),
                );
            }
        }
        health.insert("git".to_string(), serde_json::Value::Object(git_info));

        let mut picker_info = serde_json::Map::new();
        {
            let guard = self.picker.read().map_err(py_err)?;
            if let Some(ref picker) = *guard {
                picker_info.insert("initialized".to_string(), serde_json::Value::Bool(true));
                picker_info.insert(
                    "base_path".to_string(),
                    serde_json::Value::String(picker.base_path().to_string_lossy().to_string()),
                );
                picker_info.insert(
                    "is_scanning".to_string(),
                    serde_json::Value::Bool(picker.is_scan_active()),
                );
                let progress = picker.get_scan_progress();
                picker_info.insert(
                    "indexed_files".to_string(),
                    serde_json::Value::Number(progress.scanned_files_count.into()),
                );
            } else {
                picker_info.insert("initialized".to_string(), serde_json::Value::Bool(false));
            }
        }
        health.insert(
            "file_picker".to_string(),
            serde_json::Value::Object(picker_info),
        );

        let mut frecency_info = serde_json::Map::new();
        {
            let guard = self.frecency.read().map_err(py_err)?;
            frecency_info.insert(
                "initialized".to_string(),
                serde_json::Value::Bool(guard.is_some()),
            );
        }
        health.insert(
            "frecency".to_string(),
            serde_json::Value::Object(frecency_info),
        );

        let mut query_info = serde_json::Map::new();
        {
            let guard = self.query_tracker.read().map_err(py_err)?;
            query_info.insert(
                "initialized".to_string(),
                serde_json::Value::Bool(guard.is_some()),
            );
        }
        health.insert(
            "query_tracker".to_string(),
            serde_json::Value::Object(query_info),
        );

        serde_json::to_string(&health).map_err(|e| py_err(format!("JSON error: {}", e)))
    }
}

// ---------------------------------------------------------------------------
// Module
// ---------------------------------------------------------------------------

#[pymodule]
fn _fff_python(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<FileFinder>()?;
    m.add_class::<Score>()?;
    m.add_class::<FileItem>()?;
    m.add_class::<DirItem>()?;
    m.add_class::<MixedFileItem>()?;
    m.add_class::<MixedDirItem>()?;
    m.add_class::<SearchResult>()?;
    m.add_class::<DirSearchResult>()?;
    m.add_class::<MixedSearchResult>()?;
    m.add_class::<MatchRange>()?;
    m.add_class::<GrepMatch>()?;
    m.add_class::<GrepResult>()?;
    m.add_class::<ScanProgress>()?;
    m.add_class::<GrepCursor>()?;
    m.add("FFFException", m.py().get_type::<FFFException>())?;
    Ok(())
}
