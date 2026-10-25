import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import MAX_MESSAGE_CHARS
from validation import validate_message


class TestMessageValidation(unittest.TestCase):
    def test_empty_message_is_rejected(self):
        text, error, status = validate_message('   ')
        self.assertEqual(text, '')
        self.assertEqual(status, 400)
        self.assertTrue(error)

    def test_none_message_is_rejected(self):
        text, error, status = validate_message(None)
        self.assertEqual(text, '')
        self.assertEqual(status, 400)

    def test_valid_message_is_trimmed(self):
        text, error, status = validate_message('  I have a cold  ')
        self.assertEqual(text, 'I have a cold')
        self.assertEqual(error, '')
        self.assertEqual(status, 0)

    def test_long_message_is_rejected(self):
        text, error, status = validate_message('x' * (MAX_MESSAGE_CHARS + 1))
        self.assertEqual(len(text), MAX_MESSAGE_CHARS + 1)
        self.assertEqual(status, 413)
        self.assertIn(str(MAX_MESSAGE_CHARS), error)


if __name__ == '__main__':
    unittest.main(verbosity=2)
