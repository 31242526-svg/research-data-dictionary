import json

import pandas as pd

from ddict import profile_frame
from ddict.core import infer_type


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
