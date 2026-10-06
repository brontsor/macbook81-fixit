class Report:
    def __init__(self, status, detail="", note=""):
        self.status = status
        self.detail = detail
        self.note = note


DROPIN = "/etc/limine-entry-tool.d/macbook81-spi-pio.conf"
TOKEN = "initcall_blacklist=dw_pci_driver_init"
SLEEP_LIMINE = "/etc/limine-entry-tool.d/macbook81-s2idle.conf"
SLEEP_SYSTEMD = "/etc/systemd/sleep.conf.d/macbook81-s2idle.conf"
SLEEP_TOKEN = "mem_sleep_default=s2idle"
JACK = "/usr/local/bin/mb81-jack-switch"
JACK_UNIT = "mb81-jack-switch.service"
FIRMWARE = "/usr/lib/firmware/facetimehd/firmware.bin"
SETFILE = "/usr/lib/firmware/facetimehd/1675_01XX.dat"
VIDEO = "/dev/video0"
PW_NAME = "51-macbook81-speaker.conf"
WP_NAME = "51-mb81-rawpcm-speaker.conf"

SLEEP_NOTE = (
    "This avoids the deep-sleep wedge. It is not a sleep fix. "
    "A lid close has hung in s2idle."
)
EQ_NOTE = (
    "EQ coefficients are from a published macOS layout. "
    "Not measured on this machine."
)
WEBCAM_NOTE = (
    "Upstream patjak/facetimehd tag 0.7.2. "
    "Firmware is downloaded from Apple and is not in git."
)


def _dkms_installed(text, package, version, kernel):
    prefix = f"{package}/{version},"
    for line in text.splitlines():
        status = line.split(":")[-1]
        if line.startswith(prefix) and kernel in line and "installed" in status:
            return True
    return False


def _obsolete_spi_note(probe):
    text = probe.dkms_status()
    kernel = probe.kernel_release()
    installed = broken = added = False
    for line in text.splitlines():
        if not line.startswith("macbook12-spi-driver/"):
            continue
        tail = line.split(":")[-1].strip().lower()
        if kernel in line and tail.startswith("installed"):
            installed = True
        elif tail.startswith("broken"):
            broken = True
        elif tail.startswith("added"):
            added = True
    if not (installed or broken or added):
        return ""
    path = ""
    fn = getattr(probe, "module_path", None)
    if fn:
        path = fn("applespi") or ""
    if installed:
        return (
            "macbook12-spi-driver is installed for this kernel. "
            "It is not the keyboard fix. This program will not remove it."
        )
    if broken:
        return (
            "macbook12-spi-driver is broken in DKMS. "
            "It is not the keyboard fix. This program will not remove it."
        )
    loaded = "The running driver is in-tree applespi. " if path and "updates/dkms" not in path else ""
    return (
        "macbook12-spi-driver is only registered with DKMS, not installed. "
        + loaded
        + "The fix is the boot-image parameter. This leftover is not that fix. "
        "This program will not remove it."
    )


def _restarts_wireplumber(text):
    for line in text.splitlines():
        code = line.split("#", 1)[0].lower()
        if "restart" in code and "wireplumber" in code:
            return True
    return False


def _profile_paths(probe):
    home = probe.home()
    pw = f"{home}/.config/pipewire/pipewire.conf.d/{PW_NAME}"
    wp = f"{home}/.config/wireplumber/wireplumber.conf.d/{WP_NAME}"
    return pw, wp


def keyboard_status(probe):
    note = _obsolete_spi_note(probe)
    present = probe.exists(DROPIN)
    in_uki = probe.uki_has(TOKEN)
    err = _uki_error(probe)
    text = probe.read(DROPIN) or ""
    if sets_mem_sleep(text):
        extra = "This drop-in also sets mem_sleep_default. It will not be replaced."
        note = (note + " " + extra).strip() if note else extra
    if present and in_uki:
        return Report("installed", TOKEN, note)
    if present and err:
        extra = ""
        if _cmdline_has(probe, TOKEN):
            extra = " The running command line has the token."
        return Report("partial", err.rstrip(".") + "." + extra, note)
    if present and not in_uki:
        return Report(
            "partial",
            f"the drop-in is on disk but the boot image does not contain {TOKEN}",
            note,
        )
    return Report("not-installed", "", note)


def audio_status(probe):
    dkms = probe.dkms_status()
    if any(line.startswith("macbook12-audio") for line in dkms.splitlines()):
        return Report(
            "blocked",
            "macbook12-audio is installed. It ships the same three modules. "
            "This program will not install over it.",
        )
    kernel = probe.kernel_release()
    dkms_ok = _dkms_installed(dkms, "macbook81-cs4208", "0.1", kernel)
    module_ok = probe.module_has("MB81 HP PREPARE")
    jack = probe.read(JACK)
    unit_ok = probe.user_unit_enabled(JACK_UNIT)
    restart = _restarts_wireplumber(jack or "")
    if dkms_ok and module_ok and jack is not None and unit_ok and not restart:
        return Report("installed", "macbook81-cs4208/0.1 and mb81-jack-switch")
    if restart:
        return Report(
            "partial",
            "mb81-jack-switch restarts WirePlumber. That is not the headphone fix.",
        )
    if dkms_ok or jack is not None or unit_ok:
        return Report("partial", "the driver or the jack watcher is only partly installed")
    return Report("not-installed")


def speaker_status(probe):
    pw, wp = _profile_paths(probe)
    files = probe.exists(pw) and probe.exists(wp)
    nicks = probe.node_text()
    named = all(name in nicks for name in ("Headphones", "Internal Microphone", "Speaker (Raw)"))
    if files and named:
        return Report("installed", "Headphones, Internal Microphone, Speaker (Raw)", EQ_NOTE)
    if files and "CS4208 Analog" in nicks:
        return Report(
            "partial",
            "the files are on disk but a node is still named CS4208 Analog",
            EQ_NOTE,
        )
    if files or named:
        return Report("partial", "the speaker profile is only partly applied", EQ_NOTE)
    return Report("not-installed", "", EQ_NOTE)


def sleep_status(probe):
    foreign = _foreign_sleep(probe)
    if foreign:
        return Report("blocked", foreign_detail(foreign), SLEEP_NOTE)
    limine = probe.exists(SLEEP_LIMINE)
    systemd = probe.exists(SLEEP_SYSTEMD)
    uki = probe.uki_has(SLEEP_TOKEN)
    err = _uki_error(probe)
    bracket = "[s2idle]" in probe.mem_sleep_text()
    if limine and systemd and uki and bracket:
        return Report("installed", SLEEP_TOKEN, SLEEP_NOTE)
    if (limine or systemd) and err and not uki:
        extra = ""
        if _cmdline_has(probe, SLEEP_TOKEN):
            extra = " The running command line has the token."
        return Report("partial", err.rstrip(".") + "." + extra, SLEEP_NOTE)
    if limine or systemd or uki:
        return Report("partial", "the s2idle default is only partly installed", SLEEP_NOTE)
    return Report("not-installed", "", SLEEP_NOTE)


def _foreign_sleep(probe):
    fn = getattr(probe, "foreign_sleep", None)
    return list(fn()) if fn else []


def foreign_detail(paths):
    path = paths[0]
    name = path.rsplit("/", 1)[-1]
    if name == "macbook81-spi-pio.conf":
        lead = (
            "omacom/omarchy#9735 already sets mem_sleep_default=s2idle in "
            + path
            + "."
        )
    elif name == "macbook81-spi-fix.conf":
        lead = (
            path
            + " is the matthiasjg gist. It sets mem_sleep_default=s2idle and "
            "installs hibernate hooks this program does not."
        )
    elif name == "macbook81-applespi":
        lead = "The gist suspend hook is installed at " + path + "."
    elif name == "macbook81-spi-detach":
        lead = "The gist hibernate detach hook is installed at " + path + "."
    elif name == "10-macbook-hibernate.conf":
        lead = path + " sets a hibernate mode. This program does not install hibernate."
    elif path == "/etc/default/limine":
        lead = "/etc/default/limine already sets mem_sleep_default."
    else:
        lead = path + " is already a sleep workaround."
    more = ""
    if len(paths) > 1:
        more = " Also present: " + ", ".join(paths[1:]) + "."
    return lead + more + " This program will not install its sleep default beside that."


OUR_SLEEP = {
    "/etc/limine-entry-tool.d/macbook81-s2idle.conf",
    "/etc/systemd/sleep.conf.d/macbook81-s2idle.conf",
}
GIST_HOOKS = {
    "/usr/lib/systemd/system-sleep/macbook81-applespi",
    "/etc/initcpio/hooks/macbook81-spi-detach",
    "/etc/systemd/system/macbook81-applespi-rebind.service",
    "/etc/systemd/system/macbook81-applespi-ensure.service",
}


def foreign_from_listing(entries):
    found = []
    for path, text in entries:
        if path in OUR_SLEEP:
            continue
        if path in GIST_HOOKS:
            found.append(path)
            continue
        if text and _sets_foreign_sleep(path, text):
            found.append(path)
    return found


def _sets_foreign_sleep(path, text):
    active = _active(text)
    if path == "/etc/default/limine" or path.startswith("/etc/limine-entry-tool.d/"):
        return "mem_sleep_default=" in active
    if path == "/etc/systemd/sleep.conf" or path.startswith("/etc/systemd/sleep.conf.d/"):
        return "MemorySleepMode=" in active or "HibernateMode=" in active
    return False


def sets_mem_sleep(text):
    return "mem_sleep_default=" in _active(text or "")


def _active(text):
    lines = []
    for line in text.splitlines():
        code = line.split("#", 1)[0].strip()
        if code:
            lines.append(code)
    return "\n".join(lines)


def _uki_error(probe):
    fn = getattr(probe, "uki_error", None)
    return fn() if fn else ""


def _cmdline_has(probe, token):
    fn = getattr(probe, "cmdline_has", None)
    return fn(token) if fn else False


def webcam_status(probe):
    kernel = probe.kernel_release()
    dkms_ok = _dkms_installed(probe.dkms_status(), "facetimehd", "0.7.2", kernel)
    firmware = probe.exists(FIRMWARE) and probe.exists(SETFILE)
    video = probe.exists(VIDEO)
    if dkms_ok and firmware and video:
        return Report("installed", "facetimehd/0.7.2", WEBCAM_NOTE)
    if not firmware:
        return Report(
            "partial" if dkms_ok or video else "not-installed",
            "firmware is missing. A kext without it is not a working camera.",
            WEBCAM_NOTE,
        )
    return Report("partial", "the webcam is only partly installed", WEBCAM_NOTE)


def scan(probe):
    return [
        ("keyboard", "Keyboard and trackpad", keyboard_status(probe)),
        ("audio", "Audio driver", audio_status(probe)),
        ("speaker", "Speaker profile", speaker_status(probe)),
        ("sleep", "Sleep default", sleep_status(probe)),
        ("webcam", "Webcam", webcam_status(probe)),
    ]
