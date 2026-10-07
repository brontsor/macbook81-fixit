import locale
import sys

from macbook81_fixit import catalog
from macbook81_fixit.deps import missing
from macbook81_fixit.firmware import start as start_firmware
from macbook81_fixit.gate import host_verdict
from macbook81_fixit.log import ActionLog
from macbook81_fixit.probe import SystemProbe
from macbook81_fixit.status import FIRMWARE, scan


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    probe = SystemProbe()
    verdict = host_verdict(probe)
    if not verdict.ok:
        print(verdict.reason)
        print("Nothing was written.")
        return 1
    if "--check" in argv or not sys.stdout.isatty():
        print(format_check(probe))
        return 0
    log = ActionLog(f"{probe.home()}/.local/state/macbook81-fixit/actions.log")
    if not probe.exists(FIRMWARE):
        start_firmware(probe.home())
        log.record("prefetch", "Apple camera ranges")
    try:
        locale.setlocale(locale.LC_CTYPE, "")
    except locale.Error:
        pass
    import curses
    from macbook81_fixit.tui import run
    curses.wrapper(lambda stdscr: run(stdscr, probe, log))
    return 0


def format_check(probe):
    lines = [
        f"product_name {probe.product_name()}",
        f"kernel {probe.kernel_release()}",
    ]
    absent = missing(probe)
    lines.append("dependencies: " + ("ok" if not absent else "missing " + ", ".join(absent)))
    lines.append("")
    for key, title, report in scan(probe):
        lines.append(f"{title:<24} {report.status:<14} {catalog.SHORT[key]}")
        if report.detail:
            lines.append(f"  {report.detail}")
        if report.note:
            lines.append(f"  {report.note}")
    lines.append("")
    lines.append("Nothing was written.")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
