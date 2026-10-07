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
    content_origin,
    frame_style,
    license_line,
    needs_reboot,
    prompt_rows,
    row_text,
    title_line,
    release_stamp,
    description_message,
    footer_line,
    status_row,
    scan_notice,
    notice_line,
    kept_notice,
    paint_first_scan,
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

    def test_the_top_line_names_the_version_and_when_it_was_built(self):
        line = title_line("0.1.0", "6 October 2026, 17:47 CDT")
        self.assertEqual(
            line,
            "MacBook8,1 fixit version 0.1.0 built on 6 October 2026, 17:47 CDT",
        )
        lines = banner_lines(
            "7.2.5-4-omarchy",
            "Computer age",
            "0.1.0",
            "6 October 2026, 17:47 CDT",
        )
        self.assertEqual(lines[0], line)
        self.assertNotIn("MACBOOK81", lines[0])

    def test_the_stamp_uses_the_tag_and_the_commit_time(self):
        version, built = release_stamp(lambda: ("v0.1.0\n", "2026-10-06 17:32:13 -0500\n"))
        self.assertEqual(version, "0.1.0")
        self.assertEqual(built, "6 October 2026, 17:32 CDT")
        self.assertNotIn("-0500", built)

    def test_the_description_does_not_repeat_root_authentication(self):
        self.assertEqual(description_message("authenticated as root"), "")
        self.assertEqual(description_message("scanned"), "")
        self.assertEqual(description_message(""), "")
        self.assertEqual(scan_notice(True), "Scanning.")
        self.assertEqual(scan_notice(False), "")

    def test_action_results_stay_off_the_package_description(self):
        for text in (
            "nothing marked",
            "cancelled",
            "done",
            "stopped",
            "done. reboot by hand when you are ready",
            "reboot did not start. reboot by hand",
            "rebooting",
            "dependencies installed",
            "dependency install failed",
            "root authentication cancelled",
            "root password rejected",
            "already installed, skipped",
        ):
            self.assertEqual(description_message(text), "", text)
        self.assertEqual(notice_line("nothing marked"), "nothing marked")
        self.assertEqual(notice_line("done"), "done")
        self.assertEqual(notice_line("root password rejected"), "")
        self.assertEqual(notice_line("scanned"), "")
        self.assertEqual(notice_line(""), "")
        self.assertEqual(kept_notice("done", "Scanning."), "done")
        self.assertEqual(kept_notice("Scanning.", "Scanning."), "")
        self.assertEqual(kept_notice("", "Scanning."), "")

    def test_the_first_scan_line_passes_a_length(self):
        seen = {}

        class Screen:
            def erase(self):
                pass

            def refresh(self):
                pass

            def getmaxyx(self):
                return (24, 80)

            def addnstr(self, y, x, text, n, attr=0):
                if not isinstance(n, int):
                    raise TypeError("'str' object cannot be interpreted as an integer")
                seen["call"] = (y, x, text, n)

        paint_first_scan(Screen())
        self.assertEqual(seen["call"][:2], (2, 2))
        self.assertEqual(seen["call"][2], "Scanning.")
        self.assertIsInstance(seen["call"][3], int)
        self.assertGreater(seen["call"][3], 0)

    def test_the_last_line_names_the_author_and_the_license(self):
        self.assertEqual(
            footer_line(),
            "dm the author @bronson on X. Distributed under MIT license. No warranty, caveat emptor.",
        )
        self.assertEqual(status_row(32), 26)
        self.assertEqual(status_row(22), 16)
        self.assertEqual(prompt_rows(32), (23, 24))
        self.assertEqual(prompt_rows(22), (13, 14))

    def test_computer_age_sits_under_the_model_name(self):
        lines = banner_lines("7.2.5-4-omarchy", "Computer age  11 years, 6 months    made 19 March 2015")
        self.assertEqual(lines[1], "MacBook (Retina, 12-inch, Early 2015)")
        self.assertEqual(lines[2], "Computer age  11 years, 6 months    made 19 March 2015")
        self.assertNotIn("Omarchy", lines[2])

    def test_the_password_prompt_does_not_cover_the_age_line(self):
        age_text = "Computer age  needs a root password (press u)"
        age_row = content_origin()[0] + banner_lines("k", age_text).index(age_text)
        for height in (22, 32):
            field, hint = prompt_rows(height)
            self.assertNotIn(age_row, (field, hint))
            self.assertGreater(field, age_row)
            self.assertLess(max(field, hint), status_row(height))
            self.assertGreaterEqual(status_row(height) - min(field, hint), 3)

    def test_a_rejected_password_is_not_drawn_as_accepted(self):
        self.assertIn("Wait", auth_notice("checking"))
        self.assertIn("accepted", auth_notice("accepted"))
        rejected = auth_notice("rejected")
        self.assertIn("rejected", rejected)
        self.assertNotIn("accepted", rejected)
        self.assertNotIn("Wait", rejected)

    def test_the_border_is_a_red_block_until_root_then_a_green_block(self):
        self.assertEqual(frame_style("locked"), ("█", "red"))
        self.assertEqual(frame_style("ready"), ("█", "green"))
        self.assertEqual(frame_style("incomplete"), ("█", "green"))
        self.assertEqual(frame_style("missing"), ("█", "green"))
        self.assertEqual(frame_style("locked")[0], frame_style("ready")[0])

    def test_package_rows_stay_above_the_password_line(self):
        from macbook81_fixit.status import Report
        from macbook81_fixit.tui import _App, first_catalog_row, screen_min

        self.assertEqual(screen_min(), (76, 24))
        field, _hint = prompt_rows(24)
        start = first_catalog_row(True)
        painted = [start + index for index in range(5)]
        self.assertTrue(all(row < field for row in painted), (painted, field))
        short_field, _short_hint = prompt_rows(22)
        self.assertGreaterEqual(first_catalog_row(True) + 4, short_field)

        class Screen:
            def __init__(self, height):
                self.height = height
                self.calls = []

            def getmaxyx(self):
                return self.height, 80

            def erase(self):
                pass

            def refresh(self):
                pass

            def addnstr(self, y, x, text, n, attr=0):
                self.calls.append((y, text))

            def addch(self, y, x, char, attr=0):
                pass

        def paint(height):
            import curses
            saved = curses.has_colors
            curses.has_colors = lambda: False
            try:
                screen = Screen(height)
                app = _App.__new__(_App)
                app.stdscr = screen
                app.probe = Probe()
                app.probe.kernel_release = lambda: "7.2.5-4-omarchy"
                app.rows = [
                    (name, name, Report("installed", "detail"))
                    for name in ("keyboard", "audio", "speaker", "sleep", "webcam")
                ]
                app.cursor = 0
                app.marked = set()
                app.deps = ["git"]
                app.age_label = "Computer age  needs a root password (press u)"
                app.auth_line = "Root password accepted."
                app.draw()
                return screen.calls
            finally:
                curses.has_colors = saved

        short = paint(22)
        self.assertIn((2, "Terminal too small. Need 76 columns and 24 rows."), short)
        self.assertFalse(any(text.startswith("[") for _y, text in short))
        full = paint(24)
        package_rows = [y for y, text in full if text.startswith("[")]
        self.assertEqual(len(package_rows), 5)
        self.assertTrue(all(y < prompt_rows(24)[0] for y in package_rows), package_rows)

    def test_text_stays_one_line_inside_the_border(self):
        from macbook81_fixit.tui import content_origin, footer_row, help_rows

        self.assertEqual(content_origin(), (2, 2))
        for height in (22, 32):
            top, left = content_origin()
            self.assertEqual(footer_row(height), height - 3)
            self.assertEqual(help_rows(height), (height - 5, height - 4))
            self.assertEqual(status_row(height), height - 6)
            self.assertEqual(prompt_rows(height), (height - 9, height - 8))
            rows = (
                top,
                *prompt_rows(height),
                status_row(height),
                *help_rows(height),
                footer_row(height),
            )
            self.assertTrue(all(row > 1 and row < height - 2 for row in rows), rows)
            self.assertGreater(left, 0)

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
