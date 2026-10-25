import sys
import tempfile
import unittest
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sounds import SAMPLE_RATE, SOUND_PROFILES, sound_cards, write_sound


class VerboseResult(unittest.TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        print(f"PASS {test._testMethodName}")


class TestSoundLibrary(unittest.TestCase):
    def test_catalog_has_fifteen_sounds(self):
        self.assertEqual(len(SOUND_PROFILES), 15)

    def test_slugs_are_unique(self):
        slugs = [profile['slug'] for profile in SOUND_PROFILES]
        self.assertEqual(len(slugs), len(set(slugs)))

    def test_categories_cover_calm_focus_and_sleep(self):
        categories = {profile['category'] for profile in SOUND_PROFILES}
        self.assertIn('Calm', categories)
        self.assertIn('Focus', categories)
        self.assertIn('Sleep', categories)
        self.assertIn('Nature', categories)

    def test_required_metadata_is_present(self):
        for profile in SOUND_PROFILES:
            for key in ('slug', 'title', 'category', 'icon', 'description', 'kind', 'frequencies'):
                self.assertTrue(profile.get(key), f"{profile.get('slug')} missing {key}")

    def test_sound_cards_have_urls(self):
        for card in sound_cards():
            self.assertEqual(card['url'], f"/static/sounds/{card['slug']}.wav")

    def test_short_wave_file_is_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            profile = dict(SOUND_PROFILES[0], duration=0.5)
            path = write_sound(profile, directory)
            with wave.open(str(path), 'rb') as handle:
                self.assertEqual(handle.getnchannels(), 1)
                self.assertEqual(handle.getsampwidth(), 2)
                self.assertEqual(handle.getframerate(), SAMPLE_RATE)
                self.assertEqual(handle.getnframes(), int(0.5 * SAMPLE_RATE))

    def test_every_render_kind_produces_audio(self):
        kinds = {profile['kind'] for profile in SOUND_PROFILES}
        with tempfile.TemporaryDirectory() as directory:
            for kind in kinds:
                profile = next(item for item in SOUND_PROFILES if item['kind'] == kind)
                profile = dict(profile, duration=0.25)
                path = write_sound(profile, directory)
                self.assertGreater(path.stat().st_size, 44)


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestSoundLibrary)
    runner = unittest.TextTestRunner(verbosity=0, resultclass=VerboseResult)
    result = runner.run(suite)
    print(f"\n{result.testsRun - len(result.failures) - len(result.errors)}/{result.testsRun} passed")
    sys.exit(0 if result.wasSuccessful() else 1)
