import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import tracker


class TestTracker(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / 'test.db'
        self.patch = mock.patch.object(tracker, 'DB_PATH', self.db_path)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def test_save_and_read_entry(self):
        tracker.save_entry('anon-1', 'my period is late', {'symptoms': ['late period']})
        entries = tracker.get_entries('anon-1')
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['raw_text'], 'my period is late')

    def test_entries_are_scoped_to_anonymous_id(self):
        tracker.save_entry('anon-1', 'first', {})
        tracker.save_entry('anon-2', 'second', {})
        self.assertEqual(len(tracker.get_entries('anon-1')), 1)
        self.assertEqual(tracker.get_entries('anon-1')[0]['raw_text'], 'first')

    def test_delete_entries_removes_only_matching_rows(self):
        tracker.save_entry('anon-1', 'keep me elsewhere', {})
        tracker.save_entry('anon-2', 'remove me', {})
        removed = tracker.delete_entries('anon-2')
        self.assertEqual(removed, 1)
        self.assertEqual(tracker.get_entries('anon-2'), [])
        self.assertEqual(len(tracker.get_entries('anon-1')), 1)

    def test_recent_entries_limit_is_applied(self):
        for index in range(7):
            tracker.save_entry('anon-1', f'entry {index}', {})
        self.assertEqual(len(tracker.get_recent_entries('anon-1', limit=5)), 5)


if __name__ == '__main__':
    unittest.main(verbosity=2)
