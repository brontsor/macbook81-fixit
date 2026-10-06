import curses
import time
from datetime import date

from macbook81_fixit import catalog
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
    "j/k move   space mark   a apply   x remove   i license   s scan   q quit",
    "u reads the boot image. That is the file this machine starts from.",
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
        self.tick = 0
        self.age_at = 0
        self.age_label = ""
        self.rescan()

    def rescan(self):
        if hasattr(self.probe, "_uki_cache"):
            pass
        self.rows = scan(self.probe)
        self.deps = missing(self.probe)
        self._refresh_age(force=True)

    def loop(self):
        while True:
            self.tick += 1
            self.draw()
            key = self.stdscr.getch()
            if key == -1:
                self._refresh_age()
                continue
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
                self.message = "scanned"
            elif key in (ord("i"), ord("I")):
                self._license()
            elif key in (ord("d"), ord("D")) and self.deps:
                self._install_deps()

    def draw(self):
        self.stdscr.erase()
        height, width = self.stdscr.getmaxyx()
        state = boot_image_state(self.probe)
        _frame(self.stdscr, state, self.tick)
        if height < 22 or width < 76:
            self.stdscr.addnstr(2, 2, "Terminal too small. Need 76 columns and 22 rows.", max(0, width - 4))
            self.stdscr.refresh()
            return
        y = _banner(self.stdscr, width, self.probe.kernel_release())
        if self.deps:
            self.stdscr.addnstr(y, 2, "missing: " + ", ".join(self.deps) + "   [d] install", width - 4)
            y += 1
        header = f"{'':3} {'Patch':<22} {'Status':<12} {'License':<18} Version"
        self.stdscr.addnstr(y, 2, header, width - 4, _pair(4))
        y += 1
        for index, (name, title, report) in enumerate(self.rows):
            line = row_text(name, title, report.status, name in self.marked)
            attr = _pair(_status_color(report.status))
            if index == self.cursor:
                attr |= curses.A_REVERSE
            self.stdscr.addnstr(y, 2, line, width - 4, attr)
            y += 1
        y += 1
        _name, title, report = self.rows[self.cursor]
        floor = height - 5
        if y < floor:
            self.stdscr.addnstr(y, 2, title, width - 4, curses.A_BOLD)
            y += 1
        for text in (report.detail, report.note, self._extra(), self._boot_note()):
            if not text or y >= floor:
                break
            self.stdscr.addnstr(y, 2, text, width - 4)
            y += 1
        status = _status_line(state, self.age_label)
        self.stdscr.addnstr(height - 4, 2, status, width - 4, _pair(_frame_color(state)) | curses.A_BOLD)
        self.stdscr.addnstr(height - 3, 2, HELP[0], width - 4, _pair(4))
        self.stdscr.addnstr(height - 2, 2, HELP[1], width - 4, _pair(4))
        if self.message and y < height - 4:
            self.stdscr.addnstr(y, 2, self.message, width - 4)
        self.stdscr.refresh()

    def _boot_note(self):
        name = self.rows[self.cursor][0]
        if name not in ("keyboard", "sleep"):
            return ""
        return (
            "Keyboard and sleep live in the boot image. "
            "Press u to read it. A change there waits for a reboot."
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
        if state == "password":
            self.age_label = "Age needs a password (u)"
        elif state == "unknown":
            self.age_label = "Age unknown"
        else:
            self.age_label = "Age " + state

    def _act(self, mode):
        names = [name for name in ORDER if name in self.marked]
        if not names:
            self.message = "nothing marked"
            return
        steps = plan_apply(names, self.probe) if mode == "apply" else plan_remove(names, self.probe)
        if steps and all(step.kind == "skip" for step in steps):
            self.message = steps[0].detail
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
            self.message = "cancelled"
            return
        result = execute(steps, live_run, self.log)
        if not result.ok:
            print(result.detail)
            self.message = result.detail or "stopped"
            input("Press Enter to return.")
            return
        if not rebuilds:
            print("Done. No reboot is needed for this change.")
            self.message = "done"
            input("Press Enter to return.")
            return
        print()
        print("The boot image was rebuilt.")
        print("Reboot by hand when you are ready, then run this again.")
        choice = input("Reboot now? [y/N] ")
        if choice.strip().lower() != "y":
            print("Left running. Reboot by hand.")
            self.message = "done. reboot by hand when you are ready"
            input("Press Enter to return.")
            return
        import subprocess
        rc = subprocess.run(["sudo", "systemctl", "reboot"]).returncode
        if rc != 0:
            print("Reboot did not start. Reboot by hand.")
            self.message = "reboot did not start. reboot by hand"
            input("Press Enter to return.")
            return
        self.message = "rebooting"

    def _read_boot_image(self):
        import subprocess
        curses.def_prog_mode()
        curses.endwin()
        try:
            print("Reading the boot image needs your password.")
            print("The boot image is the file this machine starts from.")
            rc = subprocess.run(["sudo", "-v"]).returncode
            self.message = "boot image read" if rc == 0 else "password cancelled"
        finally:
            curses.reset_prog_mode()
        if hasattr(self.probe, "_uki_cache"):
            del self.probe._uki_cache
        self.rescan()

    def _license(self):
        name = self.rows[self.cursor][0]
        license_name, license_url = catalog.LICENSE.get(name, ("unknown", ""))
        self.message = f"{license_name}  {license_url}"

    def _install_deps(self):
        curses.def_prog_mode()
        curses.endwin()
        try:
            print("Install: " + " ".join(self.deps))
            answer = input("sudo pacman -S --needed these packages? [y/N] ")
            if answer.strip().lower() == "y":
                rc = live_run(_dep_step(self.deps))
                self.log.record("deps", " ".join(self.deps) if rc == 0 else "failed")
                self.message = "dependencies installed" if rc == 0 else "dependency install failed"
            else:
                self.message = "cancelled"
        finally:
            curses.reset_prog_mode()
        self.rescan()


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


def _status_line(state, age):
    boot = {
        "locked": "Boot image locked — press u",
        "missing": "Boot image missing",
        "ready": "Boot image read",
        "incomplete": "Boot image read — a setting is missing",
    }[state]
    if age:
        return boot + "    " + age
    return boot


def _frame(stdscr, state, tick):
    height, width = stdscr.getmaxyx()
    if height < 2 or width < 2:
        return
    char = _frame_char(state, tick)
    attr = _pair(_frame_color(state)) | curses.A_BOLD
    edge = char * (width - 1)
    stdscr.addnstr(0, 0, edge, width - 1, attr)
    try:
        stdscr.addnstr(height - 1, 0, edge, width - 1, attr)
    except curses.error:
        pass
    for y in range(1, height - 1):
        stdscr.addch(y, 0, char, attr)
        try:
            stdscr.addch(y, width - 1, char, attr)
        except curses.error:
            pass
    if state == "locked":
        for x in (0, max(0, width - 2)):
            try:
                stdscr.addch(0, x, "?", attr)
                stdscr.addch(height - 2, x, "?", attr)
            except curses.error:
                pass


def _frame_char(state, tick):
    if state == "locked":
        return ".~-+"[tick % 4]
    return {"ready": "#", "incomplete": "+", "missing": "x"}.get(state, "#")


def _frame_color(state):
    return {"locked": 2, "ready": 1, "incomplete": 2, "missing": 3}.get(state, 4)


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


def _banner(stdscr, width, kernel):
    stdscr.addnstr(1, 2, "MACBOOK81 FIXIT", width - 4, _pair(4) | curses.A_BOLD)
    stdscr.addnstr(2, 2, "MacBook (Retina, 12-inch, Early 2015)", width - 4, _pair(4))
    stdscr.addnstr(3, 2, f"Omarchy  {kernel}", width - 4, _pair(4))
    return 5
