import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.commons.validations import ValidationError, validate_file


class ValidationTests(unittest.TestCase):
    def test_validate_file_accepts_missing_suffix_in_config(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as tmp:
            tmp.write("id\n1\n")
            temp_path = tmp.name

        try:
            context = {"file_path": temp_path, "config": {}}
            validate_file(context)
            self.assertIn("df", context)
            self.assertEqual(context["df"].shape[0], 1)
        finally:
            os.remove(temp_path)

    def test_validate_file_rejects_missing_file(self):
        missing_path = os.path.join(tempfile.gettempdir(), "missing_file.csv")
        context = {"file_path": missing_path, "config": {"suffix": ".csv"}}

        with self.assertRaises(ValidationError):
            validate_file(context)


if __name__ == "__main__":
    unittest.main()
