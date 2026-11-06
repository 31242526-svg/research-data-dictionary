import json
from pathlib import Path

import pandas as pd
import pytest

from ddict import profile_file, profile_frame
from ddict.core import infer_type

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def test_integer_and_float_detection():
    assert infer_type(pd.Series([1, 2, 3])) == "integer"
    assert infer_type(pd.Series([1.5, 2.5, 3.0])) == "float"


def test_numeric_text_is_detected():
    assert infer_type(pd.Series(["1", "2", "3"])) == "integer"


def test_dates_are_detected():
    assert infer_type(pd.Series(["2024-01-01", "2024-02-01"])) == "datetime"


def test_categorical_versus_free_text():
    assert infer_type(pd.Series(["Pune", "Pune", "Mumbai", "Pune"])) == "categorical"
    notes = pd.Series([f"note {i} about the visit" for i in range(10)])
    assert infer_type(notes) == "text"


def test_missing_values_are_counted():
    frame = pd.DataFrame({"x": [1.0, None, 3.0, 4.0]})
    column = profile_frame(frame).column_profiles[0]
    assert column.missing == 1
    assert column.missing_pct == 25.0


def test_duplicate_rows_are_counted():
    frame = pd.DataFrame({"x": [1, 1, 2]})
    assert profile_frame(frame).duplicate_rows == 1


def test_markdown_table_contains_types_and_top_values():
    frame = pd.DataFrame({"city": ["Pune", "Pune", "Mumbai", "Pune"], "age": [21, 22, None, 24]})
    markdown = profile_frame(frame).to_markdown()
    assert "# Data dictionary" in markdown
    assert "| Column | Type | Non-null | Missing | Unique | Summary |" in markdown
    assert "Pune (3)" in markdown
    assert "integer" in markdown


def test_json_output_is_parsable():
    frame = pd.DataFrame({"x": [1, 2]})
    data = json.loads(profile_frame(frame).to_json())
    assert data["rows"] == 2
    assert data["column_profiles"][0]["type"] == "integer"


def test_empty_column_is_labelled():
    frame = pd.DataFrame({"x": [None, None], "y": [1, 2]})
    profile = profile_frame(frame)
    assert profile.column_profiles[0].type == "empty"


def test_text_statistics_include_lengths_and_examples():
    frame = pd.DataFrame({"notes": ["short note", "a much longer note here", "short note"]})
    column = profile_frame(frame).column_profiles[0]
    if column.type == "text":
        assert column.stats["min_length"] == 10
        assert "short note" in column.stats["examples"]


def test_excel_matches_the_csv_profile(tmp_path):
    frame = pd.read_csv(EXAMPLES / "participants.csv")
    workbook = tmp_path / "participants.xlsx"
    frame.to_excel(workbook, index=False)

    from_csv = profile_file(EXAMPLES / "participants.csv")
    from_xlsx = profile_file(workbook)

    assert from_xlsx.rows == from_csv.rows
    assert from_xlsx.duplicate_rows == from_csv.duplicate_rows
    assert [c.type for c in from_xlsx.column_profiles] == [
        c.type for c in from_csv.column_profiles
    ]


def test_real_excel_dates_are_detected(tmp_path):
    frame = pd.DataFrame({"when": pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"])})
    workbook = tmp_path / "dates.xlsx"
    frame.to_excel(workbook, index=False)

    assert profile_file(workbook).column_profiles[0].type == "datetime"


def test_unsupported_file_type_is_rejected(tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text("a,b\n1,2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported file type"):
        profile_file(path)


def test_parquet_matches_the_csv_profile(tmp_path):
    frame = pd.read_csv(EXAMPLES / "participants.csv")
    path = tmp_path / "participants.parquet"
    frame.to_parquet(path)

    from_csv = profile_file(EXAMPLES / "participants.csv")
    from_parquet = profile_file(path)

    assert from_parquet.rows == from_csv.rows
    assert from_parquet.duplicate_rows == from_csv.duplicate_rows
    assert [c.type for c in from_parquet.column_profiles] == [
        c.type for c in from_csv.column_profiles
    ]
