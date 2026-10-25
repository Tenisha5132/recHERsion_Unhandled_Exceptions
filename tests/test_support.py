import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from support import build_support


class VerboseResult(unittest.TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        print(f"PASS {test._testMethodName}")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        print(f"FAIL {test._testMethodName}")

    def addError(self, test, err):
        super().addError(test, err)
        print(f"ERROR {test._testMethodName}")


class TestSupportResources(unittest.TestCase):
    def support(self, theme, age=None):
        res = {}
        if age is not None:
            res = {'extraction': {'extracted': {'age': age}}}
        return build_support(theme, res)

    def labels(self, theme, age=None):
        return [o['label'] for o in self.support(theme, age)['options']]

    def test_urgent_has_emergency_and_specialist(self):
        labels = self.labels('urgent')
        self.assertIn('Call 112 for emergency help', labels)
        self.assertIn('Nearby emergency hospital', labels)
        self.assertIn('Nearby gynaecologist', labels)

    def test_distress_has_counselling_and_global_fallback(self):
        labels = self.labels('distress')
        self.assertIn('Call Tele-MANAS', labels)
        self.assertIn('Nearby counsellor or therapist', labels)
        self.assertIn('Find a helpline outside India', labels)

    def test_discuss_has_doctor_options(self):
        labels = self.labels('discuss')
        self.assertIn('Nearby gynaecologist', labels)
        self.assertIn('Nearby general doctor', labels)
        self.assertIn('Government hospital gynaecology', labels)

    def test_low_has_mental_health_options(self):
        labels = self.labels('low')
        self.assertIn('Call Tele-MANAS', labels)
        self.assertIn('Nearby psychiatrist', labels)

    def test_mild_has_gp_and_pharmacy(self):
        labels = self.labels('mild')
        self.assertIn('Nearby general doctor', labels)
        self.assertIn('Nearby pharmacy', labels)

    def test_neutral_has_general_choices(self):
        labels = self.labels('neutral')
        self.assertIn('Nearby general doctor', labels)
        self.assertIn('Nearby gynaecologist', labels)
        self.assertIn('Nearby counsellor or therapist', labels)

    def test_minor_gets_adolescent_options(self):
        labels = self.labels('discuss', age=14)
        self.assertIn('Adolescent-friendly health clinic', labels)
        self.assertIn('Counsellor for teenagers', labels)

    def test_adult_does_not_get_adolescent_options(self):
        labels = self.labels('discuss', age=30)
        self.assertNotIn('Adolescent-friendly health clinic', labels)

    def test_map_urls_are_valid(self):
        for theme in ['urgent', 'distress', 'discuss', 'low', 'mild', 'neutral']:
            for option in self.support(theme)['options']:
                if option['kind'] == 'maps':
                    self.assertTrue(option['url'].startswith('https://www.google.com/maps/search/?api=1&query='))
                    self.assertTrue(option['maps_query'])

    def test_no_todo_or_snake_case_in_user_text(self):
        for theme in ['urgent', 'distress', 'discuss', 'low', 'mild', 'neutral']:
            payload = self.support(theme, age=14)
            text = json.dumps(payload, ensure_ascii=False)
            self.assertNotIn('TODO_VERIFY', text)
            for value in [payload['title'], payload['note'], payload['location_note']]:
                self.assertIsNone(re.search(r'\b[a-z]+(?:_[a-z]+)+\b', value), value)
            for option in payload['options']:
                for value in [option['label'], option['description']]:
                    self.assertIsNone(re.search(r'\b[a-z]+(?:_[a-z]+)+\b', value), value)


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestSupportResources)
    runner = unittest.TextTestRunner(verbosity=0, resultclass=VerboseResult)
    result = runner.run(suite)
    print(f"\n{result.testsRun - len(result.failures) - len(result.errors)}/{result.testsRun} passed")
    sys.exit(0 if result.wasSuccessful() else 1)
