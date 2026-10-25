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

    def test_database_uses_wal_and_has_lookup_index(self):
        tracker.init_db()
        with tracker.db_connection() as conn:
            self.assertEqual(conn.execute('PRAGMA journal_mode').fetchone()[0].lower(), 'wal')
            self.assertEqual(conn.execute('PRAGMA busy_timeout').fetchone()[0], 10000)
            indexes = {row['name'] for row in conn.execute('PRAGMA index_list(entries)')}
        self.assertIn('idx_entries_anon_created', indexes)

    def test_lookup_uses_the_anonymous_index(self):
        tracker.init_db()
        with tracker.db_connection() as conn:
            plan = ' '.join(
                row['detail'] for row in conn.execute(
                    'EXPLAIN QUERY PLAN SELECT * FROM entries '
                    'WHERE anonymous_user_id=? ORDER BY created_at DESC LIMIT 5',
                    ('anon-1',),
                )
            )
        self.assertIn('idx_entries_anon_created', plan)


if __name__ == '__main__':
    unittest.main(verbosity=2)
