import tempfile
import unittest
from pathlib import Path

from macbook81_fixit.catalog import package_version
from macbook81_fixit.version import read_version, write_version
from macbook81_fixit.tui import read_build_stamp, release_stamp, row_text


class TestFixedVersion(unittest.TestCase):
    def test_the_build_stamp_is_the_version_the_title_shows(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "VERSION"
            write_version("v0.1.4", path)
            self.assertEqual(read_version(path), "0.1.4")
            version, built = release_stamp(lambda: read_build_stamp(
                lambda args: "2026-10-16 12:00:00 -0500\n" if args[:3] == ["git", "log", "-1"] else "",
                version_text=path.read_text(),
            ))
        self.assertEqual(version, "0.1.4")
        self.assertEqual(built, "16 October 2026, 12:00 CDT")

    def test_the_title_does_not_ask_git_for_a_tag(self):
        calls = []

        def run(args):
            calls.append(args)
            if args[:3] == ["git", "log", "-1"]:
                return "2026-10-16 12:00:00 -0500\n"
            return "v9.9.9\n"

        version, _built = release_stamp(lambda: read_build_stamp(run, version_text="0.1.4\n"))
        self.assertEqual(version, "0.1.4")
        joined = " ".join(" ".join(args) for args in calls)
        self.assertNotIn("describe", joined)
        self.assertNotIn("ls-remote", joined)

    def test_a_tagged_pin_shows_the_version_number(self):
        self.assertEqual(package_version("webcam"), "0.7.2")
        line = row_text("webcam", "Webcam", "installed", False)
        self.assertTrue(line.endswith("0.7.2"))
        self.assertNotIn("v0.7.2", line)

    def test_an_untagged_pin_is_not_labeled_with_another_release(self):
        self.assertEqual(package_version("audio"), "37ef61a")
        self.assertEqual(package_version("keyboard"), "930eceb")
        line = row_text("audio", "Audio driver", "installed", False)
        self.assertTrue(line.endswith("37ef61a"))
        self.assertNotIn("0.1.2", line)
        self.assertNotIn("0.1.0", line)
