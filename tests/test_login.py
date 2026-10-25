import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import _clean_display_name, app


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


class TestLoginProfile(unittest.TestCase):
    def test_name_is_trimmed_and_spacing_is_clean(self):
        self.assertEqual(_clean_display_name('  Asha   Rao  '), 'Asha Rao')

    def test_html_markers_are_removed(self):
        self.assertEqual(_clean_display_name('<script>x</script>'), 'scriptx/script')

    def test_name_is_limited(self):
        self.assertEqual(len(_clean_display_name('x' * 80)), 40)

    def test_login_and_logout_routes_exist(self):
        paths = {route.path for route in app.routes}
        self.assertIn('/login', paths)
        self.assertIn('/logout', paths)

    def test_login_template_exists(self):
        self.assertTrue((Path(__file__).resolve().parents[1] / 'templates' / 'login.html').exists())


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestLoginProfile)
    runner = unittest.TextTestRunner(verbosity=0, resultclass=VerboseResult)
    result = runner.run(suite)
    print(f"\n{result.testsRun - len(result.failures) - len(result.errors)}/{result.testsRun} passed")
    sys.exit(0 if result.wasSuccessful() else 1)
