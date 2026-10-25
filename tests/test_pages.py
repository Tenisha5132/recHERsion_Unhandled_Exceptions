import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app, templates

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / 'templates'


class VerboseResult(unittest.TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        print(f"PASS {test._testMethodName}")


class TestSitePages(unittest.TestCase):
    def test_primary_routes_exist(self):
        paths = {route.path for route in app.routes}
        for path in ['/', '/sounds', '/support', '/timeline', '/privacy', '/login', '/logout']:
            self.assertIn(path, paths)

    def test_generated_sound_route_exists(self):
        paths = {route.path for route in app.routes}
        self.assertIn('/media/sounds/{slug}.wav', paths)

    def test_page_templates_compile(self):
        for name in ['mood_ui.html', 'sounds.html', 'support.html', 'timeline.html', 'privacy.html', 'login.html']:
            templates.env.get_template(name)

    def test_pages_share_navigation(self):
        for name in ['mood_ui.html', 'sounds.html', 'support.html', 'timeline.html', 'privacy.html', 'login.html']:
            text = (TEMPLATES / name).read_text()
            self.assertIn('_nav.html', text, name)

    def test_navigation_links_all_primary_pages(self):
        text = (TEMPLATES / '_nav.html').read_text()
        for path in ['href="/"', 'href="/sounds"', 'href="/timeline"', 'href="/support"', 'href="/privacy"']:
            self.assertIn(path, text)

    def test_sound_page_contains_player_and_upload_controls(self):
        text = (TEMPLATES / 'sounds.html').read_text()
        for marker in ['id="audio"', 'id="sleepTimer"', 'id="musicUpload"', 'id="trackList"', 'data-src=']:
            self.assertIn(marker, text)

    def test_support_page_contains_emergency_and_map_actions(self):
        text = (TEMPLATES / 'support.html').read_text()
        for marker in ['{{ item.label }}', 'id="locateSupport"', 'data-map-query', 'Call emergency services']:
            self.assertIn(marker, text)

    def test_journal_page_has_empty_state_and_actions(self):
        text = (TEMPLATES / 'timeline.html').read_text()
        for marker in ['Your journal is quiet', 'Download doctor summary', 'Delete my data']:
            self.assertIn(marker, text)


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestSitePages)
    runner = unittest.TextTestRunner(verbosity=0, resultclass=VerboseResult)
    result = runner.run(suite)
    print(f"\n{result.testsRun - len(result.failures) - len(result.errors)}/{result.testsRun} passed")
    sys.exit(0 if result.wasSuccessful() else 1)
