import curses
import os
import subprocess
import time
from datetime import date, datetime

from macbook81_fixit import catalog
from macbook81_fixit.age import computer_status
from macbook81_fixit.deps import missing
from macbook81_fixit.execute import execute
from macbook81_fixit.firmware import state as firmware_state
from macbook81_fixit.plan import plan_apply, plan_remove
from macbook81_fixit.run import live_run
from macbook81_fixit.status import scan

ORDER = ("keyboard", "audio", "speaker", "sleep", "webcam")
TOKEN = "initcall_blacklist=dw_pci_driver_init"
SLEEP_TOKEN = "mem_sleep_default=s2idle"

HELP = (
    "j/k move   space mark   a apply   x remove   s scan   q quit",
    "u authenticates as root, then reads the boot image. That is the file this machine starts from.",
)


def run(stdscr, probe, log):
    curses.curs_set(0)
    stdscr.keypad(True)
    stdscr.timeout(400)
    _colors()
    app = _App(stdscr, probe, log)
    app.loop()


class _App:
    def __init__(self, stdscr, probe, log):
        self.stdscr = stdscr
        self.probe = probe
        self.log = log
        self.rows = []
        self.cursor = 0
        self.marked = set()
        self.message = ""
        self.auth_line = ""
        self.age_at = 0
        self.age_label = ""
        self.rescan()

    def rescan(self):
        kept = kept_notice(self.auth_line, scan_notice(True))
        self._show_scanning()
        self.rows = scan(self.probe)
        self.deps = missing(self.probe)
        self._refresh_age(force=True)
        self.auth_line = kept

    def _notice(self, text):
        self.message = ""
        shown = notice_line(text)
        if shown:
            self.auth_line = shown

    def _show_scanning(self):
        self.auth_line = scan_notice(True)
        if self.rows:
            self.draw()
            return
        self.stdscr.erase()
        paint_first_scan(self.stdscr)

    def loop(self):
        self.stdscr.timeout(5000)
        dirty = True
        while True:
            if dirty:
                self.draw()
                dirty = False
            key = self.stdscr.getch()
            if key == -1:
                before = self.age_label
                self._refresh_age()
                dirty = self.age_label != before
                continue
            if key == curses.KEY_RESIZE:
                dirty = True
                continue
            self.auth_line = ""
            dirty = True
            if key in (ord("q"), ord("Q")):
                return
            if key in (curses.KEY_UP, ord("k")):
                self.cursor = max(0, self.cursor - 1)
            elif key in (curses.KEY_DOWN, ord("j")):
                self.cursor = min(len(self.rows) - 1, self.cursor + 1)
            elif key == ord(" "):
                name = self.rows[self.cursor][0]
                if name in self.marked:
                    self.marked.remove(name)
                else:
                    self.marked.add(name)
            elif key in (ord("a"), ord("A")):
                self._act("apply")
            elif key in (ord("x"), ord("X")):
                self._act("remove")
            elif key in (ord("u"), ord("U")):
                self._read_boot_image()
            elif key in (ord("s"), ord("S")):
                self.rescan()
            elif key in (ord("d"), ord("D")) and self.deps:
                self._install_deps()

    def draw(self):
        self.stdscr.erase()
        height, width = self.stdscr.getmaxyx()
        state = boot_image_state(self.probe)
        _frame(self.stdscr, state)
        min_width, min_height = screen_min()
        if height < min_height or width < min_width:
            top, left = content_origin()
            self.stdscr.addnstr(
                top,
                left,
                f"Terminal too small. Need {min_width} columns and {min_height} rows.",
                content_span(width),
            )
            self.stdscr.refresh()
            return
        y = _banner(self.stdscr, width, self.probe.kernel_release(), self.age_label)
        _top, left = content_origin()
        span = content_span(width)
        field, hint_row = prompt_rows(height)
        if self.deps:
            self.stdscr.addnstr(y, left, "missing: " + ", ".join(self.deps) + "   [d] install", span)
            y += 1
        header = f"{'':3} {'Patch':<22} {'Status':<12} {'License':<18} Version"
        self.stdscr.addnstr(y, left, header, span, _pair(4))
        y = first_catalog_row(bool(self.deps))
        for index, (name, title, report) in enumerate(self.rows):
            if y >= field:
                break
            line = row_text(name, title, report.status, name in self.marked)
            attr = _pair(_status_color(report.status))
            if index == self.cursor:
                attr |= curses.A_REVERSE
            self.stdscr.addnstr(y, left, line, span, attr)
            y += 1
        y += 1
        name, title, report = self.rows[self.cursor]
        floor = field
        if y < floor:
            self.stdscr.addnstr(y, left, title, span, curses.A_BOLD)
            y += 1
        for text in (license_line(name), report.detail, report.note, self._extra(), self._boot_note()):
            if not text or y >= floor:
                break
            self.stdscr.addnstr(y, left, text, span)
            y += 1
        status = _status_line(state)
        self.stdscr.addnstr(status_row(height), left, status, span, _pair(_COLOR[frame_style(state)[1]]) | curses.A_BOLD)
        help_a, help_b = help_rows(height)
        self.stdscr.addnstr(help_a, left, HELP[0], span, _pair(4))
        self.stdscr.addnstr(help_b, left, HELP[1], span, _pair(4))
        self.stdscr.addnstr(footer_row(height), left, footer_line(), span, _pair(4))
        if self.auth_line:
            self.stdscr.addnstr(field, left, self.auth_line, span, _pair(3) | curses.A_BOLD)
            self.stdscr.addnstr(hint_row, left, " " * span, span)
        self.stdscr.refresh()

    def _boot_note(self):
        name = self.rows[self.cursor][0]
        if name not in ("keyboard", "sleep"):
            return ""
        return (
            "Keyboard and sleep live in the boot image. "
            "Press u to authenticate as root and read it. A change there waits for a reboot."
        )

    def _extra(self):
        if self.rows[self.cursor][0] != "webcam":
            return ""
        return "Apple camera package in cache: " + firmware_state(self.probe.home())

    def _refresh_age(self, force=False):
        now = time.monotonic()
        if not force and now - self.age_at < 30:
            return
        self.age_at = now
        fn = getattr(self.probe, "laptop_age", None)
        if not fn:
            self.age_label = ""
            return
        state = fn(date.today())
        self.age_label = computer_status(state)

    def _act(self, mode):
        names = [name for name in ORDER if name in self.marked]
        if not names:
            self._notice("nothing marked")
            return
        steps = plan_apply(names, self.probe) if mode == "apply" else plan_remove(names, self.probe)
        if steps and all(step.kind == "skip" for step in steps):
            self._notice(steps[0].detail)
            return
        if any(step.sudo for step in steps) and not self._ensure_root():
            return
        curses.def_prog_mode()
        curses.endwin()
        try:
            self._confirm_and_run(mode, names, steps)
        finally:
            curses.reset_prog_mode()
        self.rescan()
        self.marked.clear()

    def _confirm_and_run(self, mode, names, steps):
        print()
        print(f"{mode}: {', '.join(names)}")
        rebuilds = needs_reboot(steps)
        if rebuilds:
            print("The boot image will be rebuilt once, at the end.")
            print("That change does nothing until you reboot.")
            print("You can reboot by hand, or this screen can reboot for you at the end.")
        else:
            print("This change does not need a reboot.")
        for step in steps:
            label = " ".join(step.argv) or step.detail
            print(f"  {label}")
        answer = input("Proceed? [y/N] ")
        if answer.strip().lower() != "y":
            self._notice("cancelled")
            return
        result = execute(steps, live_run, self.log)
        if not result.ok:
            print(result.detail)
            self._notice(result.detail or "stopped")
            input("Press Enter to return.")
            return
        if not rebuilds:
            print("Done. No reboot is needed for this change.")
            self._notice("done")
            input("Press Enter to return.")
            return
        print()
        print("The boot image was rebuilt.")
        print("Reboot by hand when you are ready, then run this again.")
        choice = input("Reboot now? [y/N] ")
        if choice.strip().lower() != "y":
            print("Left running. Reboot by hand.")
            self._notice("done. reboot by hand when you are ready")
            input("Press Enter to return.")
            return
        import subprocess
        rc = subprocess.run(["sudo", "systemctl", "reboot"]).returncode
        if rc != 0:
            print("Reboot did not start. Reboot by hand.")
            self._notice("reboot did not start. reboot by hand")
            input("Press Enter to return.")
            return
        self._notice("rebooting")

    def _read_boot_image(self):
        if not self._ensure_root():
            return
        if hasattr(self.probe, "_uki_cache"):
            del self.probe._uki_cache
        self.rescan()

    def _install_deps(self):
        if not self._ensure_root():
            return
        curses.def_prog_mode()
        curses.endwin()
        try:
            print("Install: " + " ".join(self.deps))
            answer = input("sudo pacman -S --needed these packages? [y/N] ")
            if answer.strip().lower() == "y":
                rc = live_run(_dep_step(self.deps))
                self.log.record("deps", " ".join(self.deps) if rc == 0 else "failed")
                self._notice("dependencies installed" if rc == 0 else "dependency install failed")
            else:
                self._notice("cancelled")
        finally:
            curses.reset_prog_mode()
        self.rescan()

    def _ensure_root(self):
        if _root_cached():
            return True
        self.message = ""
        self.auth_line = ""
        secret = self._ask_secret()
        if not secret:
            self._notice("root authentication cancelled")
            return False
        self._show_auth("checking")
        result = cache_root(secret, _sudo_stdin)
        if result == "ok":
            self._show_auth("accepted")
            return True
        self._show_auth("rejected")
        return False

    def _show_auth(self, phase):
        self.auth_line = auth_notice(phase)
        self.draw()
        self.stdscr.refresh()

    def _ask_secret(self):
        self.stdscr.timeout(-1)
        try:
            curses.curs_set(1)
        except curses.error:
            pass
        try:
            return collect_secret(self._next_key, self._paint_secret)
        finally:
            try:
                curses.curs_set(0)
            except curses.error:
                pass
            self.stdscr.timeout(5000)

    def _next_key(self):
        getwch = getattr(self.stdscr, "get_wch", None)
        if getwch:
            try:
                return getwch()
            except curses.error:
                return 27
        return self.stdscr.getch()

    def _paint_secret(self, count):
        self.draw()
        height, width = self.stdscr.getmaxyx()
        field, hint_row = prompt_rows(height)
        _top, left = content_origin()
        span = content_span(width)
        prompt = "Root password: " + ("*" * count)
        hint = "Enter submits. Esc cancels. This authenticates as root."
        self.stdscr.addnstr(field, left, prompt, span, _pair(3) | curses.A_BOLD)
        self.stdscr.addnstr(hint_row, left, hint, span, _pair(3))
        self.stdscr.refresh()


def license_line(name):
    license_name, url = catalog.LICENSE.get(name, ("unknown", ""))
    if url:
        return f"{license_name}  {url}"
    return license_name


def cache_root(password, run):
    if not password:
        return "cancelled"
    argv = ["sudo", "-S", "-p", "", "-v"]
    rc = run(argv, password + "\n")
    return "ok" if rc == 0 else "rejected"


def collect_secret(getch, draw):
    chars = []
    while True:
        draw(len(chars))
        key = getch()
        if key in (10, 13, 343, "\n", "\r"):
            secret = "".join(chars)
            chars.clear()
            return secret
        if key in (27, "\x1b"):
            chars.clear()
            return None
        if key in (8, 127, 263, "\b", "\x7f"):
            if chars:
                chars.pop()
            continue
        if isinstance(key, str) and key.isprintable():
            chars.append(key)
        elif isinstance(key, int) and 32 <= key <= 126:
            chars.append(chr(key))


def _root_cached():
    return subprocess.run(["sudo", "-n", "true"], capture_output=True).returncode == 0


def _sudo_stdin(argv, text):
    try:
        proc = subprocess.run(argv, input=text, text=True, capture_output=True, timeout=15)
    except subprocess.TimeoutExpired:
        return 1
    return proc.returncode


def row_text(name, title, status, marked):
    mark = "[x]" if marked else "[ ]"
    license_name = catalog.LICENSE.get(name, ("", ""))[0]
    return f"{mark} {title:<22} {status:<12} {license_name:<18} {catalog.SHORT[name]}"


def needs_reboot(steps):
    return any(step.argv[:1] == ["limine-mkinitcpio"] for step in steps)


def boot_image_state(probe):
    err = ""
    fn = getattr(probe, "uki_error", None)
    if fn:
        err = fn() or ""
    if "not readable" in err:
        return "locked"
    if "missing" in err.lower():
        return "missing"
    has = getattr(probe, "uki_has", None)
    if not has:
        return "incomplete"
    if has(TOKEN) and has(SLEEP_TOKEN):
        return "ready"
    return "incomplete"


def _status_line(state):
    return {
        "locked": "Not authenticated as root. Press u to read the boot image.",
        "missing": "Authenticated as root. Boot image missing.",
        "ready": "Authenticated as root. Boot image read.",
        "incomplete": "Authenticated as root. Boot image read, a setting is missing.",
    }[state]


def border_edge(columns, char):
    return char * columns


def title_line(version, built):
    return f"MacBook8,1 fixit version {version} built on {built}"


_STAMP = None


def release_stamp(read=None):
    global _STAMP
    if read is None and _STAMP is not None:
        return _STAMP
    if read is None:
        read = _read_git_stamp
    version, built = read()
    version = version.strip().lstrip("v") or "0.1.0"
    text = built.strip()
    if not text:
        stamped = (version, "unknown")
    else:
        parsed = datetime.strptime(text, "%Y-%m-%d %H:%M:%S %z").astimezone()
        zone = parsed.tzname() or ""
        stamp = f"{parsed.day} {parsed.strftime('%B')} {parsed.year}, {parsed.strftime('%H:%M')}"
        if zone:
            stamp = f"{stamp} {zone}"
        stamped = (version, stamp)
    if read is _read_git_stamp:
        _STAMP = stamped
    return stamped


def _read_git_stamp():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def one(args):
        result = subprocess.run(args, cwd=root, capture_output=True, text=True)
        if result.returncode != 0:
            return ""
        return result.stdout

    return (
        one(["git", "describe", "--tags", "--abbrev=0"]) or "0.1.0",
        one(["git", "log", "-1", "--format=%ci"]),
    )


def banner_lines(kernel, age, version=None, built=None):
    if version is None or built is None:
        version, built = release_stamp()
    return (
        title_line(version, built),
        "MacBook (Retina, 12-inch, Early 2015)",
        age,
        f"Omarchy  {kernel}",
    )


def description_message(text):
    return ""


def notice_line(text):
    if text in ("", "scanned", "authenticated as root", "root password rejected"):
        return ""
    return text


def kept_notice(previous, scanning):
    if not previous or previous == scanning:
        return ""
    return previous


def paint_first_scan(stdscr):
    text = scan_notice(True)
    _height, width = stdscr.getmaxyx()
    top, left = content_origin()
    stdscr.erase()
    stdscr.addnstr(top, left, text, content_span(width))
    stdscr.refresh()


def scan_notice(running):
    if running:
        return "Scanning."
    return ""


def footer_line():
    return (
        "dm the author @bronson on X. "
        "Distributed under MIT license. No warranty, caveat emptor."
    )


def screen_min():
    return 76, 24


def first_catalog_row(deps):
    y = content_origin()[0] + len(banner_lines("k", "age")) + 1
    if deps:
        y += 1
    return y + 1


def content_origin():
    return 2, 2


def content_span(width):
    return max(0, width - 4)


def footer_row(height):
    return height - 3


def help_rows(height):
    return height - 5, height - 4


def status_row(height):
    return height - 6


def prompt_rows(height):
    return height - 9, height - 8


def auth_notice(phase):
    return {
        "checking": "Password received. Wait a moment.",
        "accepted": "Root password accepted.",
        "rejected": "Root password rejected.",
    }[phase]


def frame_style(state):
    if state == "locked":
        return ("█", "red")
    return ("█", "green")


_COLOR = {"red": 3, "green": 1, "yellow": 2, "cyan": 4}


def _frame(stdscr, state):
    height, width = stdscr.getmaxyx()
    if height < 2 or width < 2:
        return
    char, color = frame_style(state)
    attr = _pair(_COLOR[color]) | curses.A_BOLD
    _hline(stdscr, 0, width, char, attr)
    _hline(stdscr, height - 1, width, char, attr)
    for y in range(1, height - 1):
        stdscr.addch(y, 0, char, attr)
        try:
            stdscr.addch(y, width - 1, char, attr)
        except curses.error:
            pass


def _hline(stdscr, y, width, char, attr):
    if width < 1:
        return
    if width > 1:
        stdscr.addnstr(y, 0, border_edge(width - 1, char), width - 1, attr)
    try:
        stdscr.addch(y, width - 1, char, attr)
    except curses.error:
        pass


def _dep_step(packages):
    from macbook81_fixit.plan import Step
    return Step(["pacman", "-S", "--needed", *packages], sudo=True)


def _colors():
    if not curses.has_colors():
        return
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)
    curses.init_pair(2, curses.COLOR_YELLOW, -1)
    curses.init_pair(3, curses.COLOR_RED, -1)
    curses.init_pair(4, curses.COLOR_CYAN, -1)


def _pair(number):
    if not curses.has_colors():
        return curses.A_NORMAL
    return curses.color_pair(number)


def _status_color(status):
    return {"installed": 1, "partial": 2, "blocked": 3}.get(status, 0)


def _banner(stdscr, width, kernel, age):
    top, left = content_origin()
    lines = banner_lines(kernel, age)
    span = content_span(width)
    for offset, text in enumerate(lines):
        row = top + offset
        attr = _pair(4)
        if offset == 0:
            attr |= curses.A_BOLD
        stdscr.addnstr(row, left, text, span, attr)
    return top + len(lines) + 1
