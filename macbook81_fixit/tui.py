import curses

from macbook81_fixit import catalog
from macbook81_fixit.deps import missing
from macbook81_fixit.execute import execute
from macbook81_fixit.firmware import state as firmware_state
from macbook81_fixit.plan import plan_apply, plan_remove
from macbook81_fixit.run import live_run
from macbook81_fixit.status import scan

ORDER = ("keyboard", "audio", "speaker", "sleep", "webcam")


def run(stdscr, probe, log):
    curses.curs_set(0)
    stdscr.keypad(True)
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
        self.rescan()

    def rescan(self):
        self.rows = scan(self.probe)
        self.deps = missing(self.probe)

    def loop(self):
        while True:
            self.draw()
            key = self.stdscr.getch()
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
                self._read_uki()
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
        if height < 16 or width < 60:
            self.stdscr.addnstr(0, 0, "Terminal too small. Need 60x16.", width - 1)
            self.stdscr.refresh()
            return
        y = _banner(self.stdscr, width, self.probe.kernel_release())
        if self.deps:
            self.stdscr.addnstr(y, 2, "missing: " + ", ".join(self.deps) + "   [d] install", width - 3)
            y += 1
        self.stdscr.addnstr(y, 2, f"{'':3} {'Patch':<24} {'Status':<14} Version", width - 3, _pair(4))
        y += 1
        for index, (name, title, report) in enumerate(self.rows):
            mark = "[x]" if name in self.marked else "[ ]"
            line = f"{mark} {title:<24} {report.status:<14} {catalog.SHORT[name]}"
            attr = _pair(_status_color(report.status))
            if index == self.cursor:
                attr |= curses.A_REVERSE
            self.stdscr.addnstr(y, 2, line, width - 3, attr)
            y += 1
        y += 1
        _name, title, report = self.rows[self.cursor]
        self.stdscr.addnstr(y, 2, title, width - 3, curses.A_BOLD)
        y += 1
        for text in (report.detail, report.note, self._extra()):
            if not text:
                continue
            self.stdscr.addnstr(y, 2, text, width - 3)
            y += 1
        license_name, license_url = catalog.LICENSE.get(self.rows[self.cursor][0], ("", ""))
        if license_name:
            self.stdscr.addnstr(y, 2, f"License: {license_name}  {license_url}", width - 3)
            y += 1
        if self.message:
            self.stdscr.addnstr(height - 2, 2, self.message, width - 3)
        help_line = "j/k move  space mark  a apply  x remove  u uki  i license  s scan  q quit"
        self.stdscr.addnstr(height - 1, 2, help_line, width - 3, _pair(4))
        self.stdscr.refresh()

    def _extra(self):
        if self.rows[self.cursor][0] != "webcam":
            return ""
        return "Apple camera package in cache: " + firmware_state(self.probe.home())

    def _act(self, mode):
        names = [name for name in ORDER if name in self.marked]
        if not names:
            self.message = "nothing marked"
            return
        steps = plan_apply(names, self.probe) if mode == "apply" else plan_remove(names, self.probe)
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
        print("This program does not reboot.")
        if any(step.argv[:1] == ["limine-mkinitcpio"] for step in steps):
            print("The UKI will be rebuilt once, at the end.")
        for step in steps:
            label = " ".join(step.argv) or step.detail
            print(f"  {label}")
        answer = input("Proceed? [y/N] ")
        if answer.strip().lower() != "y":
            self.message = "cancelled"
            return
        result = execute(steps, live_run, self.log)
        if result.ok:
            print("Done. Reboot when you are ready, then run this again to rescan.")
            self.message = "done. reboot when you are ready"
        else:
            print(result.detail)
            self.message = result.detail or "stopped"
        input("Press Enter to return.")

    def _read_uki(self):
        import subprocess
        curses.def_prog_mode()
        curses.endwin()
        try:
            print("Reading the boot image needs sudo.")
            rc = subprocess.run(["sudo", "-v"]).returncode
            self.message = "boot image read" if rc == 0 else "sudo cancelled"
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
    inner = min(width - 2, 62)
    edge = "+" + "-" * (inner - 2) + "+"
    stdscr.addnstr(0, 1, edge, width - 2, _pair(4) | curses.A_BOLD)
    stdscr.addnstr(1, 1, "|  MACBOOK81 FIXIT", width - 2, _pair(4) | curses.A_BOLD)
    stdscr.addnstr(2, 1, "|  MacBook (Retina, 12-inch, Early 2015)", width - 2, _pair(4))
    stdscr.addnstr(3, 1, f"|  Omarchy  {kernel}", width - 2, _pair(4))
    stdscr.addnstr(4, 1, edge, width - 2, _pair(4))
    return 6
