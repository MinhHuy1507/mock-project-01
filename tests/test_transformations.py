import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.commons.transformations import split_customers_name


class TransformationsTest(unittest.TestCase):
    def test_split_customers_name_handles_missing_values(self):
        df = pd.DataFrame({"name": ["Huy Ngo", None]})
        config = [{"from": "name", "to": ["first_name", "last_name"]}]

        split_customers_name(df, config)

        self.assertEqual(df.loc[0, "first_name"], "Huy")
        self.assertEqual(df.loc[0, "last_name"], "Ngo")
        self.assertIsNone(df.loc[1, "first_name"])
        self.assertIsNone(df.loc[1, "last_name"])


if __name__ == "__main__":
    unittest.main()
