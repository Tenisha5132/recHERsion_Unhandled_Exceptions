import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import llm_client


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode('utf-8')


class TestLlmClient(unittest.TestCase):
    def test_not_available_without_key_or_base_url(self):
        with mock.patch.object(llm_client, 'LLM_API_KEY', ''), \
             mock.patch.object(llm_client, 'LLM_BASE_URL', ''):
            self.assertFalse(llm_client.is_available())
            self.assertIsNone(llm_client.chat([{'role': 'user', 'content': 'hello'}]))

    def test_default_endpoint(self):
        with mock.patch.object(llm_client, 'LLM_BASE_URL', ''):
            self.assertEqual(
                llm_client._endpoint(),
                'https://api.openai.com/v1/chat/completions'
            )

    def test_explicit_chat_completions_endpoint_is_not_duplicated(self):
        with mock.patch.object(llm_client, 'LLM_BASE_URL', 'http://localhost:11434/v1/chat/completions'):
            self.assertEqual(
                llm_client._endpoint(),
                'http://localhost:11434/v1/chat/completions'
            )

    def test_chat_sends_auth_and_parses_content(self):
        with mock.patch.object(llm_client, 'LLM_API_KEY', 'secret'), \
             mock.patch.object(llm_client, 'LLM_BASE_URL', 'http://model.local/v1'), \
             mock.patch.object(llm_client, 'LLM_MODEL', 'test-model'), \
             mock.patch.object(llm_client.request, 'urlopen', return_value=FakeResponse({
                 'choices': [{'message': {'content': '  rest and fluids  '}}]
             })) as opened:
            result = llm_client.chat([{'role': 'user', 'content': 'cold'}])
        self.assertEqual(result, 'rest and fluids')
        req = opened.call_args.args[0]
        self.assertEqual(req.full_url, 'http://model.local/v1/chat/completions')
        self.assertEqual(req.get_header('Authorization'), 'Bearer secret')

    def test_chat_returns_none_on_provider_error(self):
        with mock.patch.object(llm_client, 'LLM_API_KEY', 'secret'), \
             mock.patch.object(llm_client.request, 'urlopen', side_effect=OSError('down')):
            self.assertIsNone(llm_client.chat([{'role': 'user', 'content': 'cold'}]))

    def test_chat_json_accepts_fenced_json(self):
        with mock.patch.object(llm_client, 'chat', return_value='```json\n{"category":"general_health"}\n```'):
            self.assertEqual(
                llm_client.chat_json([{'role': 'user', 'content': 'cold'}]),
                {'category': 'general_health'}
            )

    def test_chat_json_rejects_non_json(self):
        with mock.patch.object(llm_client, 'chat', return_value='not json'):
            self.assertIsNone(llm_client.chat_json([{'role': 'user', 'content': 'cold'}]))

    def test_chat_json_rejects_non_object(self):
        with mock.patch.object(llm_client, 'chat', return_value='["general_health"]'):
            self.assertIsNone(llm_client.chat_json([{'role': 'user', 'content': 'cold'}]))


if __name__ == '__main__':
    unittest.main(verbosity=2)
