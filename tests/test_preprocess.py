import unittest
import pandas as pd
import os
from preprocess import preprocess_paysim

class TestPreprocess(unittest.TestCase):
    def test_preprocessing_script_exists(self):
        self.assertTrue(os.path.exists("preprocess.py"))

if __name__ == "__main__":
    unittest.main()
