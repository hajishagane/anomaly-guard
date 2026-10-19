import unittest
import os
import pandas as pd
from features import FEATURE_NAMES

class TestTrain(unittest.TestCase):
    def test_feature_names_defined(self):
        self.assertEqual(len(FEATURE_NAMES), 6)

if __name__ == "__main__":
    unittest.main()
