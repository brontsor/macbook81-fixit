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
            self.assertEqual(purge(paths), (paths, []))
            self.assertFalse(os.path.exists(clone))
            self.assertFalse(os.path.exists(camera))
            late = os.path.join(home, ".local", "share", "macbook81-fixit", "src", "late")
            os.makedirs(late)
            self.assertTrue(os.path.exists(late))

    def test_a_symlink_cache_is_not_followed(self):
        with tempfile.TemporaryDirectory() as home:
            target = os.path.join(home, "real")
            link = os.path.join(home, "link")
            os.makedirs(target)
            open(os.path.join(target, "keep"), "w").close()
            os.symlink(target, link)
            removed, failed = purge([link])
            self.assertEqual(failed, [])
            self.assertEqual(removed, [link])
            self.assertTrue(os.path.exists(os.path.join(target, "keep")))

    def test_a_purge_failure_is_reported(self):
        removed, failed = purge(["/proc/does-not-exist-macbook81"])
        self.assertEqual(removed, [])
        self.assertEqual(len(failed), 1)

    def test_an_empty_cache_says_so(self):
        with tempfile.TemporaryDirectory() as home:
            text, paths = listing(home)
            self.assertIn("nothing cached", text)
            self.assertEqual(paths, [])
            self.assertEqual(purge([]), ([], []))
