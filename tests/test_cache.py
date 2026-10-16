import os
import tempfile
import unittest

from macbook81_fixit.cache import listing, purge


class TestCache(unittest.TestCase):
    def test_the_listing_names_what_is_cached(self):
        with tempfile.TemporaryDirectory() as home:
            clone = os.path.join(home, ".local", "share", "macbook81-fixit", "src", "audio")
            camera = os.path.join(home, ".cache", "macbook81-fixit", "camera")
            os.makedirs(clone)
            os.makedirs(camera)
            open(os.path.join(camera, "range-0"), "w").close()
            text, paths = listing(home)
            self.assertIn("audio", text)
            self.assertIn("camera", text)
            self.assertEqual(len(paths), 2)
            self.assertEqual(purge(home), paths)
            self.assertFalse(os.path.exists(clone))
            self.assertFalse(os.path.exists(camera))

    def test_an_empty_cache_says_so(self):
        with tempfile.TemporaryDirectory() as home:
            text, paths = listing(home)
            self.assertIn("nothing cached", text)
            self.assertEqual(paths, [])
            self.assertEqual(purge(home), [])
