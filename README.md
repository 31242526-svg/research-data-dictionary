# research-data-dictionary

[![CI](https://github.com/31242526-svg/research-data-dictionary/actions/workflows/ci.yml/badge.svg)](https://github.com/31242526-svg/research-data-dictionary/actions/workflows/ci.yml)

Turn a CSV or Excel file into a data dictionary your methods section can cite.

Most datasets arrive without one. Then a reviewer asks "what is `score`, and why are 14% of
`age` missing?" — and someone rebuilds the table by hand. This tool produces it from the
file itself: inferred types, missingness, ranges, top categories and example values.

## Quick start

```bash
pip install -e ".[dev]"
ddict examples/participants.csv -o dictionary.md --json dictionary.json
```

Excel files work too — install the extra once:

```bash
pip install -e ".[excel]"
ddict participants.xlsx -o dictionary.md
```

```
dictionary.md written: 7 rows, 6 columns
dictionary.json written
```

## Output

`dictionary.md`:

| Column | Type | Non-null | Missing | Unique | Summary |
| --- | --- | --- | --- | --- | --- |
| participant_id | integer | 7 | 0 (0%) | 6 | 1 to 6 (median 3) |
| age | integer | 6 | 1 (14.3%) | 5 | 21 to 45 (median 22.5) |
| score | float | 7 | 0 (0%) | 5 | 64 to 91 (median 88.5) |
| city | categorical | 7 | 0 (0%) | 3 | Pune (4), Mumbai (2), Nashik (1) |
| joined | datetime | 7 | 0 (0%) | 6 | 2024-01-12 to 2024-03-21 |
| notes | text | 4 | 3 (42.9%) | 4 | 8-16 chars, e.g. baseline |

`dictionary.json` carries the same information in a machine-readable shape:

```json
{
  "source": "participants.csv",
  "rows": 7,
  "columns": 6,
  "duplicate_rows": 1,
  "column_profiles": [
    {"name": "score", "type": "float", "non_null": 7, "missing": 0,
     "missing_pct": 0.0, "unique": 5,
     "stats": {"min": 64, "max": 91, "mean": 82.643, "median": 88.5}}
  ]
}
```

## How types are inferred

| Label | Rule |
| --- | --- |
| `empty` | every value is missing |
| `integer` / `float` | numeric dtype, or text where at least 90% parses as numbers |
| `datetime` | at least 90% of non-null values parse as dates, or real date cells from Excel |
| `categorical` | text with at most 20 distinct values and at most 50% distinct |
| `text` | everything else |

The rules are deliberately conservative: a column is only called numeric or datetime when
the parse rate is high, so mixed-unit columns (`12 kg`, `3 cm`) stay `text` instead of
silently losing values.

## Limitations

- `.xlsx` and `.xlsm` input needs the `excel` extra (`openpyxl`); legacy `.xls` also needs
  `xlrd`.
- Parquet, SPSS and Stata files are not read yet.
- No semantic typing: a column of years is `integer`, not `year`.
- Inference is heuristic. Check the table before quoting it in a paper; the JSON output is
  there so you can diff versions of a dataset as it changes.
- Duplicate counting is exact-match across all columns.

## Tests

```bash
pytest
```

MIT licensed.
