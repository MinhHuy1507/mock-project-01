import os
import sys
import tempfile
import unittest
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.local.pandas.commons.validations import (
    ValidationError,
    validate_file,
    validate_schema,
    validate_not_null,
    validate_unique,
    validate_format,
    validate_range,
    validate_datatype,
)


class TestRCVToL0Validations(unittest.TestCase):
    def test_validate_file_not_found(self):
        context = {
            "file_path": "invalid_path/customers.csv",
            "config": {"suffix": ".csv"},
        }
        with self.assertRaisesRegex(ValidationError, "File not found"):
            validate_file(context)

    def test_validate_file_invalid_suffix(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as tmp:
            temp_path = tmp.name

        context = {"file_path": temp_path, "config": {"suffix": ".csv"}}
        try:
            with self.assertRaisesRegex(ValidationError, "Invalid file format"):
                validate_file(context)
        finally:
            os.remove(temp_path)

    def test_validate_file_empty(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as tmp:
            temp_path = tmp.name

        context = {"file_path": temp_path, "config": {"suffix": ".csv"}}
        try:
            with self.assertRaisesRegex(ValidationError, "File empty"):
                validate_file(context)
        finally:
            os.remove(temp_path)

    def test_validate_schema_missing_columns(self):
        df = pd.DataFrame({"id": [1]})
        config = {"columns": [{"name": "id"}, {"name": "name"}]}
        context = {"df": df, "config": config}

        with self.assertRaisesRegex(
            ValidationError, "Schema drift detected.*Missing columns"
        ):
            validate_schema(context)

    def test_validate_schema_unexpected_columns(self):
        df = pd.DataFrame({"id": [1], "age": [20]})
        config = {"columns": [{"name": "id"}]}
        context = {"df": df, "config": config}

        with self.assertRaisesRegex(
            ValidationError, "Schema drift detected.*Unexpected columns"
        ):
            validate_schema(context)

    def test_validate_schema_both(self):
        df = pd.DataFrame({"id": [1], "age": [20]})
        config = {"columns": [{"name": "id"}, {"name": "name"}]}
        context = {"df": df, "config": config}

        with self.assertRaises(ValidationError) as context_manager:
            validate_schema(context)

        error_msg = str(context_manager.exception)
        self.assertIn("Missing columns", error_msg)
        self.assertIn("Unexpected columns", error_msg)


class TestL0ToL1Validations(unittest.TestCase):

    def test_validate_not_null(self):
        df = pd.DataFrame({"id": [1, None, 3]})
        mask = validate_not_null(df, "id")
        self.assertListEqual(mask.tolist(), [True, False, True])

    def test_validate_unique(self):
        df = pd.DataFrame({"id": [1, None, 1, 3, None]})
        mask = validate_unique(df, "id")
        self.assertListEqual(mask.tolist(), [False, True, False, True, True])

    def test_validate_range(self):
        df = pd.DataFrame({"kpi": [-1, 0, 100, 50, None]})
        mask = validate_range(df, "kpi", min=0, max=100)
        self.assertListEqual(mask.tolist(), [False, True, True, True, True])

    def test_validate_format(self):
        df = pd.DataFrame({"birthdate": [None, "2005-07-15", "2005/07/15"]})
        mask = validate_format(df, "birthdate", format="yyyy-MM-dd")
        self.assertListEqual(mask.tolist(), [True, True, False])

    def test_validate_datatype(self):
        df = pd.DataFrame({"kpi": [90, 90.1, None, "String"]})
        mask = validate_datatype(df, "kpi", col_type="decimal")
        self.assertListEqual(mask.tolist(), [True, True, True, False])


if __name__ == "__main__":
    unittest.main()
