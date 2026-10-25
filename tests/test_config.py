import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import env_float


class TestEnvironmentFloats(unittest.TestCase):
    def test_invalid_value_uses_default(self):
        with mock.patch.dict(os.environ, {'TEST_FLOAT': 'not-a-number'}):
            self.assertEqual(env_float('TEST_FLOAT', 0.30), 0.30)

    def test_empty_value_uses_default(self):
        with mock.patch.dict(os.environ, {'TEST_FLOAT': '   '}):
            self.assertEqual(env_float('TEST_FLOAT', 10.0), 10.0)

    def test_value_is_clamped_to_range(self):
        with mock.patch.dict(os.environ, {'TEST_FLOAT': '999'}):
            self.assertEqual(env_float('TEST_FLOAT', 0.3, maximum=1.0), 1.0)
        with mock.patch.dict(os.environ, {'TEST_FLOAT': '-4'}):
            self.assertEqual(env_float('TEST_FLOAT', 0.3, minimum=0.0), 0.0)

    def test_valid_value_is_used(self):
        with mock.patch.dict(os.environ, {'TEST_FLOAT': '2.5'}):
            self.assertEqual(env_float('TEST_FLOAT', 10.0), 2.5)


if __name__ == '__main__':
    unittest.main(verbosity=2)
