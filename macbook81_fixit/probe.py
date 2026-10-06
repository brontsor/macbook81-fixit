import os
import shutil
import subprocess

UKI = "/boot/EFI/Linux/omarchy_linux-omarchy.efi"


class SystemProbe:
    def product_name(self):
        return _read("/sys/class/dmi/id/product_name").strip()

    def product_family(self):
        return _read("/sys/class/dmi/id/product_family").strip()

    def os_id(self):
        for line in _read("/etc/os-release").splitlines():
            if line.startswith("ID="):
                return line.split("=", 1)[1].strip().strip('"')
        return ""

    def kernel_release(self):
        return os.uname().release

    def home(self):
        return os.path.expanduser("~")

    def has_command(self, name):
        return shutil.which(name) is not None

    def read(self, path):
        if not os.path.isfile(path):
            return None
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                return fh.read()
        except OSError:
            return None

    def exists(self, path):
        return os.path.exists(path)

    def dkms_status(self):
        return _run(["dkms", "status"])[1]

    def module_has(self, needle):
        code, path = _run(["modinfo", "-n", "snd_hda_codec_cs420x"])
        path = path.strip()
        if code != 0 or "updates/dkms/" not in path:
            return False
        if path.endswith(".zst"):
            data = subprocess.run(["zstdcat", path], capture_output=True).stdout
        else:
            with open(path, "rb") as fh:
                data = fh.read()
        return needle.encode() in data

    def user_unit_enabled(self, name):
        code, out = _run(["systemctl", "--user", "is-enabled", name])
        return code == 0 and out.strip() == "enabled"

    def node_text(self):
        code, out = _run(["wpctl", "status"])
        if code == 0 and out:
            return out
        return _run(["pactl", "list", "sinks"])[1]

    def mem_sleep_text(self):
        return _read("/sys/power/mem_sleep")

    def playing(self):
        _code, out = _run(["pactl", "list", "sink-inputs"])
        for block in out.split("Sink Input #")[1:]:
            if 'media.name = "MacBook Speaker (EQ) output"' in block:
                continue
            if "Corked: no" in block:
                return True
        return False

    def uki_has(self, token):
        text, _err = self._uki_state()
        return token in text

    def uki_error(self):
        _text, err = self._uki_state()
        return err

    def cmdline_has(self, token):
        return token in _read("/proc/cmdline")

    def foreign_sleep(self):
        from macbook81_fixit.status import GIST_HOOKS, foreign_from_listing

        entries = []
        for directory in ("/etc/limine-entry-tool.d", "/etc/systemd/sleep.conf.d"):
            try:
                names = sorted(os.listdir(directory))
            except OSError:
                continue
            for name in names:
                path = os.path.join(directory, name)
                entries.append((path, self.read(path)))
        entries.append(("/etc/default/limine", self.read("/etc/default/limine")))
        entries.append(("/etc/systemd/sleep.conf", self.read("/etc/systemd/sleep.conf")))
        for path in sorted(GIST_HOOKS):
            if self.exists(path):
                entries.append((path, None))
        return foreign_from_listing(entries)

    def _uki_state(self):
        if not hasattr(self, "_uki_cache"):
            self._uki_cache = _uki_state()
        return self._uki_cache

    def pacman_version(self, package):
        code, out = _run(["pacman", "-Q", package])
        if code != 0:
            return ""
        parts = out.split()
        return parts[1] if len(parts) > 1 else ""


def _read(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def _run(argv):
    try:
        proc = subprocess.run(argv, capture_output=True, text=True)
    except OSError as exc:
        return 127, str(exc)
    return proc.returncode, proc.stdout + proc.stderr


def _uki_state():
    if os.path.isfile(UKI) and os.access(UKI, os.R_OK):
        return _run(["strings", UKI])[1], ""
    if _run(["sudo", "-n", "true"])[0] != 0:
        return "", "the UKI is not readable without sudo"
    if _run(["sudo", "-n", "test", "-f", UKI])[0] != 0:
        return "", f"UKI missing: {UKI}"
    code, out = _run(["sudo", "-n", "strings", UKI])
    if code == 0:
        return out, ""
    return "", "the UKI is not readable without sudo"
