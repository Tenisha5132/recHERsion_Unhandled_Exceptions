import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app
from health import health_snapshot


class TestHealthEndpoint(unittest.TestCase):
    def test_route_exists(self):
        paths = {route.path for route in app.routes}
        self.assertIn('/healthz', paths)

    def test_snapshot_has_operational_fields_and_no_secrets(self):
        data = health_snapshot()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['app'], 'recHERsion')
        self.assertIn('version', data)
        self.assertIn(data['retrieval']['backend'], ('bm25', 'embedding'))
        self.assertIn('chunks', data['retrieval'])
        self.assertIn(data['llm']['mode'], ('rules', 'llm'))
        self.assertNotIn('key', {str(key).lower() for key in data['llm']})
        self.assertNotIn('secret', str(data).lower())


if __name__ == '__main__':
    unittest.main(verbosity=2)
