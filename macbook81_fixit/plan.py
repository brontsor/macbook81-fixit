from macbook81_fixit import catalog
from macbook81_fixit.status import (
    DROPIN,
    JACK,
    JACK_UNIT,
    SLEEP_LIMINE,
    SLEEP_SYSTEMD,
    foreign_detail,
    sets_mem_sleep,
)


class Step:
    def __init__(self, argv, sudo=False, env=None, kind="run", detail="", cwd=None):
        self.argv = list(argv)
        self.sudo = sudo
        self.env = {} if env is None else env
        self.kind = kind
        self.detail = detail
        self.cwd = cwd


BOOT = {"keyboard", "sleep", "audio", "webcam"}


def _src(probe, name):
    return f"{probe.home()}/.local/share/macbook81-fixit/src/{name}"


def _pin(probe, name):
    dest = _src(probe, name)
    url = catalog.REPO[name]
    commit = catalog.PIN[name]
    return [
        Step(["git", "clone", url, dest], detail=commit),
        Step(["git", "-C", dest, "checkout", "--detach", commit]),
    ]


def plan_apply(selected, probe):
    steps = []
    tail = []
    boot_write = False
    for name in selected:
        if name == "speaker":
            dest = _src(probe, "speaker")
            steps.extend(_pin(probe, "speaker"))
            steps.append(Step(["bash", "apply.sh"], cwd=dest))
            tail = _wireplumber_tail(probe)
        else:
            chunk = _apply_one(name, probe)
            steps.extend(chunk)
            if name in BOOT and _wrote(chunk):
                boot_write = True
    if boot_write:
        steps.append(Step(["limine-mkinitcpio"], sudo=True, detail="one boot image rebuild"))
    steps.extend(tail)
    return steps


def plan_remove(selected, probe):
    steps = []
    tail = []
    boot_write = False
    for name in selected:
        if name == "speaker":
            dest = _src(probe, "speaker")
            steps.append(Step(["bash", "revert.sh"], cwd=dest))
            tail = _wireplumber_tail(probe)
        else:
            chunk = _remove_one(name, probe)
            steps.extend(chunk)
            if name in BOOT and _wrote(chunk):
                boot_write = True
    if boot_write:
        steps.append(Step(["limine-mkinitcpio"], sudo=True, detail="one boot image rebuild"))
    steps.extend(tail)
    return steps


def _wrote(steps):
    return any(step.kind != "skip" and step.argv for step in steps)


def _wireplumber_tail(probe):
    if probe.playing():
        return [Step([], kind="wait", detail="WirePlumber restart waits until nothing is playing")]
    return [Step(["systemctl", "--user", "restart", "wireplumber"])]


def _apply_one(name, probe):
    if name == "keyboard":
        text = _read(probe, DROPIN)
        if sets_mem_sleep(text):
            return [Step(
                [],
                kind="skip",
                detail=(
                    DROPIN
                    + " also sets mem_sleep_default. "
                    "It will not be replaced."
                ),
            )]
        dest = _src(probe, "keyboard")
        steps = _pin(probe, "keyboard")
        steps.append(Step(
            ["install", "-D", "-m", "644", f"{dest}/macbook81-spi-pio.conf", DROPIN],
            sudo=True,
        ))
        early = "/etc/mkinitcpio.conf.d/macbook_spi_modules.conf"
        if not probe.exists(early):
            steps.append(Step(
                ["install", "-D", "-m", "644", "/dev/stdin", early],
                sudo=True,
                kind="write",
                detail="MODULES=(applespi spi_pxa2xx_platform spi_pxa2xx_pci)\n",
            ))
        return steps
    if name == "sleep":
        foreign = _foreign(probe)
        if foreign:
            return [Step([], kind="skip", detail=foreign_detail(foreign))]
        dest = _src(probe, "sleep")
        steps = _pin(probe, "sleep")
        steps.append(Step(
            ["install", "-D", "-m", "644", f"{dest}/macbook81-s2idle.conf", SLEEP_LIMINE],
            sudo=True,
        ))
        steps.append(Step(
            ["install", "-D", "-m", "644", f"{dest}/macbook81-s2idle-sleep.conf", SLEEP_SYSTEMD],
            sudo=True,
        ))
        return steps
    if name == "audio":
        dest = _src(probe, "audio")
        steps = _pin(probe, "audio")
        steps.append(Step(
            ["bash", "install.sh"],
            sudo=True,
            cwd=dest,
            env={"MB81_SKIP_INITRAMFS": "1"},
        ))
        return steps
    if name == "webcam":
        dest = _src(probe, "webcam")
        fw = _src(probe, "firmware")
        steps = _pin(probe, "webcam")
        steps.append(Step(
            [],
            kind="edit",
            cwd=dest,
            detail="set PACKAGE_VERSION to 0.7.2",
        ))
        steps.append(Step(["dkms", "add", dest], sudo=True))
        steps.append(Step(
            ["dkms", "install", "-m", "facetimehd", "-v", "0.7.2", "-k", probe.kernel_release()],
            sudo=True,
        ))
        steps.extend(_pin(probe, "firmware"))
        steps.append(Step(
            ["bash", "facetimehd-firmware-install.sh"],
            sudo=True,
            cwd=fw,
            detail=catalog.APPLE_CAMERA_URL,
        ))
        steps.append(Step(["modprobe", "facetimehd"], sudo=True))
        return steps
    raise ValueError(name)


def _remove_one(name, probe):
    if name == "keyboard":
        text = _read(probe, DROPIN)
        if sets_mem_sleep(text):
            return [Step(
                [],
                kind="skip",
                detail=DROPIN + " also sets mem_sleep_default. It was not removed.",
            )]
        return [Step(["rm", "-f", DROPIN], sudo=True)]
    if name == "sleep":
        return [
            Step(["rm", "-f", SLEEP_LIMINE], sudo=True),
            Step(["rm", "-f", SLEEP_SYSTEMD], sudo=True),
        ]
    if name == "audio":
        dest = _src(probe, "audio")
        return [
            Step(["bash", "install.sh", "-r"], sudo=True, cwd=dest, env={"MB81_SKIP_INITRAMFS": "1"}),
            Step(["rm", "-f", "/usr/src/macbook81-cs4208-0.1"], sudo=True),
            Step(["rm", "-f", JACK], sudo=True),
            Step(["rm", "-f", f"/etc/systemd/user/{JACK_UNIT}"], sudo=True),
        ]
    if name == "speaker":
        raise ValueError("speaker remove is handled by plan_remove")
    if name == "webcam":
        return [
            Step(["dkms", "remove", "-m", "facetimehd", "-v", "0.7.2", "--all"], sudo=True),
            Step(["rm", "-rf", "/usr/src/facetimehd-0.7.2"], sudo=True),
            Step(["rm", "-rf", "/usr/lib/firmware/facetimehd"], sudo=True),
        ]
    raise ValueError(name)


def _read(probe, path):
    read = getattr(probe, "read", None)
    if not read:
        return ""
    return read(path) or ""


def _foreign(probe):
    fn = getattr(probe, "foreign_sleep", None)
    return list(fn()) if fn else []
