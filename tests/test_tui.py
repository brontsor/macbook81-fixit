import unittest

from macbook81_fixit.plan import Step
from macbook81_fixit.tui import boot_image_state, needs_reboot, row_text


class Probe:
    def __init__(self, err="", uki=""):
        self.err = err
        self.uki = uki

    def uki_error(self):
        return self.err

    def uki_has(self, token):
        return token in self.uki


class TestScreen(unittest.TestCase):
    def test_row_shows_the_license_type(self):
        line = row_text("audio", "Audio driver", "installed", False)
        self.assertIn("GPL-2.0-or-later", line)
        self.assertIn("Audio driver", line)
        self.assertNotIn("uki", line.lower())

    def test_locked_boot_image_is_not_called_missing(self):
        state = boot_image_state(Probe("the UKI is not readable without sudo"))
        self.assertEqual(state, "locked")

    def test_a_boot_image_rebuild_is_what_asks_for_a_reboot(self):
        steps = [Step(["limine-mkinitcpio"], sudo=True)]
        self.assertTrue(needs_reboot(steps))
        self.assertFalse(needs_reboot([Step(["bash", "apply.sh"])]))
