import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import build_api_payload
from agents.router import RouterAgent
from orchestrator import Orchestrator
from retriever import retriever

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / 'templates'


class TestScopeRouting(unittest.TestCase):
    def setUp(self):
        self.router = RouterAgent()

    def category(self, text):
        with mock.patch('agents.router.is_available', return_value=False):
            return self.router.run({'message': text})['category']

    def test_cold_is_general_health(self):
        self.assertEqual(self.category('I have a cold'), 'general_health')

    def test_sore_throat_is_general_health(self):
        self.assertEqual(self.category('I have a cold and a sore throat'), 'general_health')

    def test_headache_is_general_health(self):
        self.assertEqual(self.category('I have a bad headache'), 'general_health')

    def test_period_gap_is_womens_health(self):
        self.assertEqual(self.category('my periods are 50 days apart'), 'womens_health')

    def test_urgent_still_wins(self):
        self.assertEqual(self.category('I am soaking a pad every hour and feel faint'), 'urgent')

    def test_distress_still_wins(self):
        self.assertEqual(self.category('I want to die'), 'distress')

    def test_general_knowledge_is_off_topic(self):
        self.assertEqual(self.category('what is the capital of France'), 'off_topic')


class TestRelevantRetrieval(unittest.TestCase):
    def test_cold_returns_no_kb_chunks(self):
        self.assertEqual(retriever.query('I have a cold', top_k=3), [])

    def test_combined_cold_returns_no_kb_chunks(self):
        self.assertEqual(retriever.query('I have a cold and a sore throat', top_k=3), [])

    def test_period_question_still_returns_chunks(self):
        chunks = retriever.query('my periods are 50 days apart', top_k=3)
        self.assertTrue(chunks)
        self.assertTrue(all(c['score'] >= 0.30 for c in chunks))


class TestGeneralPipeline(unittest.TestCase):
    def setUp(self):
        self.orch = Orchestrator()

    def run_message(self, text):
        with mock.patch('agents.router.is_available', return_value=False), \
             mock.patch('agents.general.is_available', return_value=False):
            return self.orch.run(text, anon_id='test-general-route')

    def test_cold_skips_period_pipeline(self):
        res = self.run_message('I have a cold')
        self.assertEqual(res['route']['category'], 'general_health')
        self.assertIn('general', res)
        self.assertNotIn('retriever', res)
        self.assertNotIn('insight', res)
        self.assertNotIn('remedy', res)

    def test_cold_payload_has_no_period_sources(self):
        payload = build_api_payload(self.run_message('I have a cold'), 'I have a cold')
        self.assertTrue(payload['general']['reply'])
        self.assertEqual(payload['general']['scope'], 'general_health')
        self.assertEqual(payload['insight']['citations'], [])
        self.assertEqual(payload['remedy']['advice'], [])
        self.assertEqual(payload['remedy']['citations'], [])
        labels = [item['label'] for item in payload['support']['options']]
        self.assertIn('Nearby pharmacy', labels)
        self.assertNotIn('Nearby gynaecologist', labels)

    def test_off_topic_has_no_support_or_citations(self):
        payload = build_api_payload(
            self.run_message('what is the capital of France'),
            'what is the capital of France'
        )
        self.assertEqual(payload['general']['scope'], 'off_topic')
        self.assertIsNone(payload['support'])
        self.assertEqual(payload['remedy']['citations'], [])

    def test_general_uses_llm_when_configured(self):
        with mock.patch('agents.router.is_available', return_value=False), \
             mock.patch('agents.general.is_available', return_value=True), \
             mock.patch('agents.general.chat', return_value='Rest, drink fluids, and see a pharmacist or GP if symptoms worsen.'):
            res = self.orch.run('I have a cold', anon_id='test-general-llm')
        self.assertEqual(res['general']['mode'], 'llm')
        self.assertIn('fluids', res['general']['reply'])

    def test_general_falls_back_when_llm_fails(self):
        with mock.patch('agents.router.is_available', return_value=False), \
             mock.patch('agents.general.is_available', return_value=True), \
             mock.patch('agents.general.chat', return_value=None):
            res = self.orch.run('I have a cold', anon_id='test-general-fallback')
        self.assertEqual(res['general']['mode'], 'fallback')
        self.assertTrue(res['general']['reply'])

    def test_chat_disclaimer_removed(self):
        text = (TEMPLATES / 'mood_ui.html').read_text()
        self.assertNotIn('Screening support only. Not a diagnosis.', text)
        self.assertNotIn("Screening support, not a diagnosis.", text)
        self.assertIn('general: { reply:', text)


if __name__ == '__main__':
    unittest.main(verbosity=2)
