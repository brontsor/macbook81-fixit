import unittest

from macbook81_fixit.plan import Step
from macbook81_fixit.tui import (
    HELP,
    auth_notice,
    banner_lines,
    boot_image_state,
    border_edge,
    cache_root,
    collect_secret,
    frame_style,
    license_line,
    needs_reboot,
    prompt_rows,
    row_text,
)


class Probe:
    def __init__(self, err="", uki=""):
        self.err = err
        self.uki = uki

    def uki_error(self):
        return self.err

    def uki_has(self, token):
        return token in self.uki


class TestScreen(unittest.TestCase):
    def test_the_license_link_follows_the_selected_row(self):
        audio = license_line("audio")
        keyboard = license_line("keyboard")
        self.assertIn("https://github.com/brontsor/macbook81-cs4208", audio)
        self.assertIn("https://github.com/brontsor/macbook81-spi-pio", keyboard)
        self.assertNotEqual(audio, keyboard)
        self.assertNotIn("i license", " ".join(HELP))

    def test_row_shows_the_license_type(self):
        line = row_text("audio", "Audio driver", "installed", False)
        self.assertIn("GPL-2.0-or-later", line)
        self.assertIn("Audio driver", line)
        self.assertNotIn("uki", line.lower())

    def test_the_border_covers_every_column(self):
        self.assertEqual(len(border_edge(80, "X")), 80)
        self.assertEqual(border_edge(80, "X"), "X" * 80)
        self.assertEqual(len(border_edge(1, "+")), 1)

    def test_computer_age_sits_under_the_model_name(self):
        lines = banner_lines("7.2.5-4-omarchy", "Computer age  11 years, 6 months    made 19 March 2015")
        self.assertEqual(lines[1], "MacBook (Retina, 12-inch, Early 2015)")
        self.assertEqual(lines[2], "Computer age  11 years, 6 months    made 19 March 2015")
        self.assertNotIn("Omarchy", lines[2])

    def test_the_password_prompt_does_not_cover_the_age_line(self):
        age_row = 1 + banner_lines("k", "Computer age  needs a root password (press u)").index(
            "Computer age  needs a root password (press u)"
        )
        for height in (22, 32):
            field, hint = prompt_rows(height)
            self.assertNotIn(age_row, (field, hint))
            self.assertGreater(field, age_row)
            self.assertLess(max(field, hint), height - 4)
            self.assertGreaterEqual((height - 4) - min(field, hint), 3)

    def test_a_rejected_password_is_not_drawn_as_accepted(self):
        self.assertIn("Wait", auth_notice("checking"))
        self.assertIn("accepted", auth_notice("accepted"))
        rejected = auth_notice("rejected")
        self.assertIn("rejected", rejected)
        self.assertNotIn("accepted", rejected)
        self.assertNotIn("Wait", rejected)

    def test_the_border_is_a_red_x_until_root_then_a_green_plus(self):
        self.assertEqual(frame_style("locked"), ("X", "red"))
        self.assertEqual(frame_style("ready"), ("+", "green"))
        self.assertEqual(frame_style("incomplete"), ("+", "green"))
        self.assertEqual(frame_style("missing"), ("+", "green"))

    def test_u_means_authenticate_as_root(self):
        text = " ".join(HELP)
        self.assertIn("root", text)
        self.assertIn("boot image", text)
        self.assertNotIn("uki", text.lower())

    def test_locked_boot_image_is_not_called_missing(self):
        state = boot_image_state(Probe("the UKI is not readable without sudo"))
        self.assertEqual(state, "locked")

    def test_the_root_password_stays_on_stdin_and_off_the_command(self):
        seen = {}

        def run(argv, text):
            seen["argv"] = list(argv)
            seen["text"] = text
            return 0

        self.assertEqual(cache_root("secret", run), "ok")
        self.assertEqual(seen["argv"], ["sudo", "-S", "-p", "", "-v"])
        self.assertNotIn("secret", seen["argv"])
        self.assertEqual(seen["text"], "secret\n")
        self.assertEqual(cache_root("", lambda argv, text: 0), "cancelled")
        self.assertEqual(cache_root(None, lambda argv, text: 0), "cancelled")
        self.assertEqual(cache_root("nope", lambda argv, text: 1), "rejected")

    def test_escape_cancels_the_password_and_backspace_edits_it(self):
        lengths = []
        keys = iter([ord("a"), ord("b"), 127, ord("c"), 10])
        self.assertEqual(collect_secret(lambda: next(keys), lengths.append), "ac")
        self.assertEqual(lengths, [0, 1, 2, 1, 2])
        keys = iter([ord("x"), 27])
        self.assertIsNone(collect_secret(lambda: next(keys), lambda n: None))

    def test_a_boot_image_rebuild_is_what_asks_for_a_reboot(self):
        steps = [Step(["limine-mkinitcpio"], sudo=True)]
        self.assertTrue(needs_reboot(steps))
        self.assertFalse(needs_reboot([Step(["bash", "apply.sh"])]))
