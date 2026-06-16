# fff-python

Python bindings for [FFF (Fast File Finder)](https://github.com/dmtrKovalenko/fff.nvim), built with [PyO3](https://pyo3.rs/) and [Maturin](https://www.maturin.rs/).

## Requirements

- Python >= 3.10
- Rust toolchain (to build the native extension)
- [uv](https://docs.astral.sh/uv/) (recommended)

## Development setup

```bash
cd packages/fff-python
uv sync --all-extras
uv run maturin develop --release
```

## Running tests

```bash
cd packages/fff-python
uv run pytest -v
```

## Standalone example

```bash
cd packages/fff-python
uv run python examples/basic.py .
```

## Basic usage

```python
from fff import FileFinder

with FileFinder("/path/to/project", watch=False) as finder:
    finder.wait_for_scan(timeout_ms=5000)
    print(f"Indexed under {finder.base_path}")

    result = finder.search("main")
    if result:
        print(f"Showing {len(result)} of {result.total_matched} matches")
    for item, score in zip(result.items, result.scores):
        print(f"{item.relative_path}: {score.total}")
```

## Building wheels

```bash
cd packages/fff-python
uv run maturin build --release
```

The produced wheel is `abi3` compatible with Python 3.10+.
