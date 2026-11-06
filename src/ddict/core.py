"""Infer column types and summarise a dataframe into a citable data dictionary."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import pandas as pd

MAX_CATEGORICAL_UNIQUE = 20
CATEGORICAL_RATIO = 0.5
PARSE_THRESHOLD = 0.9
TOP_VALUES = 3


@dataclass
class ColumnProfile:
    name: str
    type: str
    non_null: int
    missing: int
    missing_pct: float
    unique: int
    stats: dict = field(default_factory=dict)


@dataclass
class DatasetProfile:
    source: str
    rows: int
    columns: int
    duplicate_rows: int
    column_profiles: list[ColumnProfile] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "rows": self.rows,
            "columns": self.columns,
            "duplicate_rows": self.duplicate_rows,
            "column_profiles": [asdict(c) for c in self.column_profiles],
        }

    def to_markdown(self, title: str | None = None) -> str:
        heading = title or self.source
        lines = [
            f"# Data dictionary: {heading}",
            "",
            f"{self.rows} rows x {self.columns} columns - "
            f"{self.duplicate_rows} duplicate row(s)",
            "",
            "| Column | Type | Non-null | Missing | Unique | Summary |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for col in self.column_profiles:
            summary = _summary(col).replace("|", "\\|")
            lines.append(
                f"| {col.name} | {col.type} | {col.non_null} | "
                f"{col.missing} ({col.missing_pct:g}%) | {col.unique} | {summary} |"
            )
        return "\n".join(lines) + "\n"

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


def _is_text(series: pd.Series) -> bool:
    return series.dtype == object or isinstance(series.dtype, pd.StringDtype)


def infer_type(series: pd.Series) -> str:
    """Best-effort type label: empty, boolean, integer, float, datetime, categorical, text."""
    non_null = series.dropna()
    if non_null.empty:
        return "empty"
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_numeric_dtype(series):
        values = non_null.astype("float64")
        return "integer" if (values % 1 == 0).all() else "float"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if _is_text(series):
        cleaned = non_null.astype("string").str.replace(",", "", regex=False).str.strip()
        numbers = pd.to_numeric(cleaned, errors="coerce")
        if numbers.notna().mean() >= PARSE_THRESHOLD:
            return "integer" if (numbers.dropna() % 1 == 0).all() else "float"
        dates = pd.to_datetime(non_null.astype("string"), errors="coerce", format="mixed")
        if dates.notna().mean() >= PARSE_THRESHOLD:
            return "datetime"
        unique = non_null.nunique()
        if unique <= MAX_CATEGORICAL_UNIQUE and unique / len(non_null) <= CATEGORICAL_RATIO:
            return "categorical"
        return "text"
    return "other"


def _numeric_stats(series: pd.Series) -> dict:
    values = pd.to_numeric(series, errors="coerce").dropna()
    return {
        "min": _number(values.min()),
        "max": _number(values.max()),
        "mean": _number(values.mean()),
        "median": _number(values.median()),
    }


def _number(value) -> float | int | None:
    if pd.isna(value):
        return None
    return int(value) if float(value).is_integer() else round(float(value), 3)


def _summarise_column(name: str, series: pd.Series) -> ColumnProfile:
    col_type = infer_type(series)
    non_null = int(series.notna().sum())
    missing = int(series.isna().sum())
    total = len(series)
    missing_pct = round(100 * missing / total, 1) if total else 0.0
    stats: dict = {}

    if col_type in {"integer", "float"}:
        stats = _numeric_stats(series)
    elif col_type == "datetime":
        dates = pd.to_datetime(series.dropna().astype("string"), errors="coerce", format="mixed")
        stats = {
            "min": dates.min().date().isoformat() if not dates.empty else None,
            "max": dates.max().date().isoformat() if not dates.empty else None,
        }
    elif col_type == "categorical":
        counts = series.dropna().astype("string").value_counts().head(TOP_VALUES)
        stats = {"top": {str(k): int(v) for k, v in counts.items()}}
    elif col_type == "text":
        lengths = series.dropna().astype("string").str.len()
        stats = {
            "min_length": int(lengths.min()) if not lengths.empty else 0,
            "max_length": int(lengths.max()) if not lengths.empty else 0,
            "examples": [str(v) for v in series.dropna().astype("string").unique()[:TOP_VALUES]],
        }

    return ColumnProfile(
        name=name,
        type=col_type,
        non_null=non_null,
        missing=missing,
        missing_pct=missing_pct,
        unique=int(series.nunique(dropna=True)),
        stats=stats,
    )


def _summary(col: ColumnProfile) -> str:
    stats = col.stats
    if col.type in {"integer", "float"} and stats.get("median") is not None:
        return f"{stats['min']:g} to {stats['max']:g} (median {stats['median']:g})"
    if col.type == "datetime" and stats.get("min"):
        return f"{stats['min']} to {stats['max']}"
    if col.type == "categorical" and stats.get("top"):
        return ", ".join(f"{value} ({count})" for value, count in stats["top"].items())
    if col.type == "text" and stats.get("examples"):
        return f"{stats['min_length']}-{stats['max_length']} chars, e.g. {stats['examples'][0]}"
    if col.type == "empty":
        return "no values"
    return ""


def profile_frame(df: pd.DataFrame, source: str = "<dataframe>") -> DatasetProfile:
    """Profile every column and count duplicate rows."""
    return DatasetProfile(
        source=source,
        rows=len(df),
        columns=len(df.columns),
        duplicate_rows=int(df.duplicated().sum()),
        column_profiles=[
            _summarise_column(str(name), df[name]) for name in df.columns
        ],
    )


def profile_file(path: str | Path) -> DatasetProfile:
    """Read a CSV or Excel file and profile it."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(path)
    elif suffix in {".xlsx", ".xlsm", ".xls"}:
        try:
            df = pd.read_excel(path)
        except ImportError as exc:
            raise RuntimeError(
                'Excel support needs openpyxl: pip install "research-data-dictionary[excel]"'
            ) from exc
    elif suffix == ".parquet":
        try:
            df = pd.read_parquet(path)
        except ImportError as exc:
            raise RuntimeError(
                'Parquet support needs pyarrow: pip install "research-data-dictionary[parquet]"'
            ) from exc
    else:
        raise ValueError(
            f"unsupported file type: {path.suffix or '<none>'} (use .csv, .xlsx or .parquet)"
        )
    return profile_frame(df, source=path.name)
