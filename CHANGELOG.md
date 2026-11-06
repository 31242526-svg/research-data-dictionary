# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-11-06

### Added

- Excel input: `.xlsx`, `.xlsm` and `.xls` through `pandas.read_excel`, with `openpyxl`
  available as the `excel` extra. Real Excel date cells are detected as `datetime`. (#2)
- Parquet input through `pandas.read_parquet`, with `pyarrow` available as the `parquet`
  extra. (#5)
- `--title` on the CLI to name the Markdown heading after the study instead of the file.
  The JSON output keeps `source` as the file name. (#6)

### Changed

- Unsupported file extensions now fail with a message that names the supported types,
  instead of raising a `ValueError` from pandas.
- A missing optional dependency reports how to install it, e.g.
  `pip install "research-data-dictionary[parquet]"`.

## [0.1.0] - 2026-10-31

### Added

- Initial release: profiled CSV columns into `empty`, `boolean`, `integer`, `float`,
  `datetime`, `categorical` or `text`.
- Markdown table and JSON output, including missingness, ranges, top categories, example
  values and duplicate row count.
- `ddict` CLI with `-o/--output` and `--json`.
- CI on Python 3.10, 3.12 and 3.13, ruff lint, and a CLI smoke test.

[0.2.0]: https://github.com/31242526-svg/research-data-dictionary/releases/tag/v0.2.0
[0.1.0]: https://github.com/31242526-svg/research-data-dictionary/releases/tag/v0.1.0
