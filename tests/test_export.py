import asyncio
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from starlette.requests import Request

from app import _export_payload, app, export_data


def _request():
    scope = {
        'type': 'http',
        'http_version': '1.1',
        'method': 'GET',
        'scheme': 'http',
        'path': '/export.json',
        'raw_path': b'/export.json',
        'query_string': b'',
        'headers': [],
        'client': ('127.0.0.1', 1234),
        'server': ('testserver', 80),
    }
    return Request(scope)


class TestJournalExport(unittest.TestCase):
    def test_export_payload_contains_version_and_entries(self):
        entries = [{'id': 1, 'raw_text': 'my period is late', 'extracted_json': '{}'}]
        with mock.patch('app.get_entries', return_value=entries) as get_entries:
            payload = _export_payload('anon-1')
        self.assertEqual(payload['app'], 'recHERsion')
        self.assertIn('version', payload)
        self.assertIn('exported_at', payload)
        self.assertEqual(payload['entries'], entries)
        get_entries.assert_called_once_with('anon-1', limit=100)

    def test_export_route_is_registered(self):
        self.assertIn('/export.json', {route.path for route in app.routes})

    def test_export_response_is_a_json_download(self):
        entries = [{'id': 1, 'raw_text': 'my period is late', 'extracted_json': '{}'}]
        with mock.patch('app.get_entries', return_value=entries):
            response = asyncio.run(export_data(_request()))
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response.headers['content-disposition'])
        self.assertIn('rechersion-journal.json', response.headers['content-disposition'])
        body = json.loads(response.body)
        self.assertEqual(body['entries'], entries)


if __name__ == '__main__':
    unittest.main(verbosity=2)
