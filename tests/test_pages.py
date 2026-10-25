import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app, robots, templates

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

    def test_custom_404_template_is_registered(self):
        from starlette.exceptions import HTTPException as StarletteHTTPException
        self.assertIn(StarletteHTTPException, app.exception_handlers)
        self.assertIn('This page is not here', (TEMPLATES / '404.html').read_text())

    def test_generic_error_template_is_registered(self):
        self.assertIn(Exception, app.exception_handlers)
        self.assertIn('Something went wrong', (TEMPLATES / '500.html').read_text())

    def test_robots_file_disallows_crawling(self):
        self.assertIn('/robots.txt', {route.path for route in app.routes})
        response = asyncio.run(robots())
        self.assertIn(b'Disallow: /', response.body)

    def test_generated_sound_route_exists(self):
        paths = {route.path for route in app.routes}
        self.assertIn('/media/sounds/{slug}.wav', paths)

    def test_page_templates_compile(self):
        for name in ['mood_ui.html', 'sounds.html', 'support.html', 'timeline.html', 'privacy.html', 'login.html', '404.html', '500.html']:
            templates.env.get_template(name)

    def test_pages_share_navigation(self):
        for name in ['mood_ui.html', 'sounds.html', 'support.html', 'timeline.html', 'privacy.html', 'login.html', '404.html', '500.html']:
            text = (TEMPLATES / name).read_text()
            self.assertIn('_nav.html', text, name)

    def test_pages_have_skip_link_target(self):
        nav = (TEMPLATES / '_nav.html').read_text()
        self.assertIn('class="skip-link"', nav)
        self.assertIn('href="#main"', nav)
        for name in ['mood_ui.html', 'sounds.html', 'support.html', 'timeline.html', 'privacy.html', 'login.html', '500.html']:
            self.assertIn('id="main"', (TEMPLATES / name).read_text(), name)

    def test_navigation_links_all_primary_pages(self):
        text = (TEMPLATES / '_nav.html').read_text()
        for path in ['href="/"', 'href="/sounds"', 'href="/timeline"', 'href="/support"', 'href="/privacy"']:
            self.assertIn(path, text)

    def test_sound_page_contains_player_and_upload_controls(self):
        text = (TEMPLATES / 'sounds.html').read_text()
        for marker in ['id="audio"', 'id="sleepTimer"', 'id="musicUpload"', 'id="trackList"', 'data-src=']:
            self.assertIn(marker, text)

    def test_chat_input_has_length_limit_and_hint(self):
        text = (TEMPLATES / 'mood_ui.html').read_text()
        self.assertIn('maxlength="{{ max_message_chars }}"', text)
        self.assertIn('id="msgHelp"', text)
        legacy = (TEMPLATES / 'index.html').read_text()
        self.assertIn('maxlength="2000"', legacy)

    def test_support_page_contains_emergency_and_map_actions(self):
        text = (TEMPLATES / 'support.html').read_text()
        for marker in ['{{ item.label }}', 'id="locateSupport"', 'data-map-query', 'Call emergency services']:
            self.assertIn(marker, text)

    def test_journal_page_has_empty_state_and_actions(self):
        text = (TEMPLATES / 'timeline.html').read_text()
        for marker in ['Your journal is quiet', 'Download doctor summary', 'Download JSON copy', 'Delete my data']:
            self.assertIn(marker, text)


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestSitePages)
    runner = unittest.TextTestRunner(verbosity=0, resultclass=VerboseResult)
    result = runner.run(suite)
    print(f"\n{result.testsRun - len(result.failures) - len(result.errors)}/{result.testsRun} passed")
    sys.exit(0 if result.wasSuccessful() else 1)
