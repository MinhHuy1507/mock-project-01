import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.commons.transformations import (
    split_customers_name,
    split_customers_address,
    rename_columns,
    add_columns,
)


# Before these transformations, i do validate and just transform valid records. No need to worry about None. But still test
class TransformationsTest(unittest.TestCase):
    def test_split_customers_name(self):
        df = pd.DataFrame(
            {"name": ["Huy Ngo", None, "Huy", "Huy Ngo Minh", " Huy Ngo Minh"]}
        )
        config = [{"from": "name", "to": ["first_name", "last_name"]}]
        context = {"df": df}

        split_customers_name(context, config)

        self.assertEqual(df.loc[0, "first_name"], "Huy")
        self.assertEqual(df.loc[0, "last_name"], "Ngo")

        self.assertIsNone(df.loc[1, "first_name"])
        self.assertIsNone(df.loc[1, "last_name"])

        self.assertEqual(df.loc[2, "first_name"], "Huy")
        self.assertIsNone(df.loc[2, "last_name"])

        self.assertEqual(df.loc[3, "first_name"], "Huy")
        self.assertEqual(df.loc[3, "last_name"], "Ngo Minh")

        self.assertEqual(df.loc[4, "first_name"], "Huy")
        self.assertEqual(df.loc[4, "last_name"], "Ngo Minh")

    def test_split_customers_address(self):
        df = pd.DataFrame(
            {
                "address": [
                    None,
                    "123 Nguyen Ai Quoc, Ho Chi Minh",
                    "123 Nguyen Ai Quoc",
                    " 123 Nguyen Ai Quoc, Ho Chi Minh",
                    ",123 Nguyen Ai Quoc, Ho Chi Minh",
                    ",123 Nguyen Ai Quoc, Ho Chi Minh,",
                ]
            }
        )
        config = [{"from": "address", "to": ["address", "address_province"]}]
        context = {"df": df}

        split_customers_address(context, config)

        self.assertIsNone(df.loc[0, "address"])
        self.assertIsNone(df.loc[0, "address_province"])

        self.assertEqual(df.loc[1, "address"], "123 Nguyen Ai Quoc, Ho Chi Minh")
        self.assertEqual(df.loc[1, "address_province"], "Ho Chi Minh")

        self.assertEqual(df.loc[2, "address"], "123 Nguyen Ai Quoc")
        self.assertIsNone(df.loc[2, "address_province"])

        self.assertEqual(df.loc[3, "address"], "123 Nguyen Ai Quoc, Ho Chi Minh")
        self.assertEqual(df.loc[3, "address_province"], "Ho Chi Minh")

        self.assertEqual(df.loc[4, "address"], "123 Nguyen Ai Quoc, Ho Chi Minh")
        self.assertEqual(df.loc[4, "address_province"], "Ho Chi Minh")

        self.assertEqual(df.loc[5, "address"], "123 Nguyen Ai Quoc, Ho Chi Minh")
        self.assertEqual(df.loc[5, "address_province"], "Ho Chi Minh")

    def test_rename_columns(self):
        df = pd.DataFrame({"id": [None, "CUST_001"], "other_col": [1, 2]})
        config = [{"from": "id", "to": "customer_id"}]
        context = {"df": df}

        rename_columns(context, config)

        self.assertIn("customer_id", df.columns)
        self.assertNotIn("id", df.columns)
        self.assertIn("other_col", df.columns)

        self.assertTrue(pd.isna(df.loc[0, "customer_id"]))
        self.assertEqual(df.loc[1, "customer_id"], "CUST_001")
        self.assertEqual(df.loc[1, "other_col"], 2)

    def test_add_columns(self):
        df = pd.DataFrame({"customer_id": ["CUST_001", "CUST_002"]})
        config = [{"name": "process_date"}, {"name": "source_file"}]
        context = {"df": df, "file_path": "test_path.csv"}

        add_columns(context, config)

        self.assertIn("process_date", df.columns)
        self.assertIn("source_file", df.columns)

        self.assertEqual(df["source_file"].tolist(), ["test_path.csv", "test_path.csv"])
        self.assertEqual(len(df["process_date"].unique()), 1)
        self.assertFalse(pd.isna(df.loc[0, "process_date"]))


if __name__ == "__main__":
    unittest.main()
