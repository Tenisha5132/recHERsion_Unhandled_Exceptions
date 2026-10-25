import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.extraction import parse_cycle_length


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


class TestCycleLengthExtraction(unittest.TestCase):
    def check(self, text, expected_cycle, expected_gaps):
        cycle, gaps = parse_cycle_length(text)
        self.assertEqual(cycle, expected_cycle, f"cycle for {text!r}")
        self.assertEqual(gaps, expected_gaps, f"gaps for {text!r}")

    def test_50_days_apart(self):
        self.check("My periods are 50 days apart", 50, [50])

    def test_every_45_days(self):
        self.check("They come every 45 days", 45, [45])

    def test_cycles_of_40_to_55_days(self):
        self.check("cycles of 40-55 days", 47.5, [40, 55])

    def test_periods_came_after_three_gaps(self):
        self.check("periods came after 45, 52 and 48 days", 48, [45, 52, 48])

    def test_gap_about_six_weeks(self):
        self.check("gap between periods is about 6 weeks", 42, [42])

    def test_no_period_for_four_months_is_unknown(self):
        self.check("haven't had a period for 4 months", None, [])

    def test_cycle_is_28_days(self):
        self.check("my cycle is 28 days", 28, [28])

    def test_cycle_length_35_days(self):
        self.check("cycle length 35 days", 35, [35])

    def test_periods_every_three_weeks(self):
        self.check("periods every 3 weeks", 21, [21])

    def test_gaps_list(self):
        self.check("gaps of 30, 36 and 42 days", 36, [30, 36, 42])

    def test_cycles_range_with_to(self):
        self.check("cycles 21 to 40 days", 30.5, [21, 40])

    def test_period_duration_is_not_cycle_length(self):
        self.check("my period lasts 7 days", None, [])

    def test_en_dash_range(self):
        self.check("cycles of 40–55 days", 47.5, [40, 55])

    def test_week_range(self):
        self.check("cycles of 2-3 weeks", 17.5, [14, 21])

    def test_no_cycle_information(self):
        self.check("No cycle information mentioned", None, [])


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestCycleLengthExtraction)
    runner = unittest.TextTestRunner(verbosity=0, resultclass=VerboseResult)
    result = runner.run(suite)
    print(f"\n{result.testsRun - len(result.failures) - len(result.errors)}/{result.testsRun} passed")
    sys.exit(0 if result.wasSuccessful() else 1)
