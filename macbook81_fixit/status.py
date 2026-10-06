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
    note = ""
    if any(line.startswith("macbook12-spi-driver") for line in probe.dkms_status().splitlines()):
        note = "macbook12-spi-driver is present and unrelated. This program will not remove it."
    present = probe.exists(DROPIN)
    in_uki = probe.uki_has(TOKEN)
    err = _uki_error(probe)
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
            f"the drop-in is on disk but the UKI does not contain {TOKEN}",
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
