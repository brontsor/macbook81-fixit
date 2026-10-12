import os
import shutil
import subprocess

from macbook81_fixit.bootimage import (
    ESP_CANDIDATES,
    config_paths,
    loader_path,
    package_name,
    paths_to_try,
    resolve_boot_image,
)


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

    def out_of_tree(self, name):
        return "O" in _read(f"/sys/module/{name}/taint")

    def forget_boot_image(self):
        if hasattr(self, "_uki_cache"):
            del self._uki_cache

    def module_path(self, name):
        code, out = _run(["modinfo", "-n", name])
        return out.strip() if code == 0 else ""

    def laptop_age(self, today):
        from macbook81_fixit.age import computer_line, manufacture_date

        serial = self._product_serial()
        if serial is None:
            return "password"
        built = manufacture_date(serial)
        if not built:
            return "unknown"
        return computer_line(built, today) or "unknown"

    def _product_serial(self):
        path = "/sys/class/dmi/id/product_serial"
        text = _read(path).strip()
        if _usable_serial(text):
            return text
        if os.path.exists(path) and not os.access(path, os.R_OK):
            if _run(["sudo", "-n", "true"])[0] != 0:
                return None
            code, out = _run(["sudo", "-n", "cat", path])
            text = out.strip() if code == 0 else ""
            return text if _usable_serial(text) else ""
        return ""

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
            self._uki_cache = self._read_boot_image()
        return self._uki_cache

    def _read_boot_image(self):
        paths = paths_to_try(self._constructed_image(), self._loader_image())
        if not paths:
            return "", "boot image missing: unresolved"
        for path in paths:
            text, err = _read_image(path)
            if not err:
                return text, ""
            if "not readable" in err:
                return text, err
        return "", f"boot image missing: {paths[0]}"

    def _constructed_image(self):
        release = self.kernel_release()
        builtin = f"/usr/lib/modules/{release}/modules.builtin"
        code, out = _run(["pacman", "-Qqo", builtin])
        package = package_name(code, out, _read(f"/usr/lib/modules/{release}/pkgbase"))
        configs = []
        for path in config_paths():
            text = self.read(path)
            if text:
                configs.append(text)
        return resolve_boot_image(
            configs,
            package,
            _read("/etc/machine-id"),
            self._esp_mounts(),
        )

    def _esp_mounts(self):
        mounts = {}
        for path in ESP_CANDIDATES:
            code, out = _run(["findmnt", "-no", "FSTYPE", path])
            if code == 0 and out.strip():
                mounts[path] = out.strip()
        return mounts

    def _loader_image(self):
        _code, out = _run(["bootctl", "status"])
        return loader_path(out)

    def pacman_version(self, package):
        code, out = _run(["pacman", "-Q", package])
        if code != 0:
            return ""
        parts = out.split()
        return parts[1] if len(parts) > 1 else ""


def _usable_serial(text):
    lowered = text.strip().lower()
    if not lowered:
        return False
    return lowered not in {
        "none",
        "not specified",
        "default string",
        "to be filled by o.e.m.",
        "system serial number",
    }


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


def _read_image(path):
    if not path:
        return "", "boot image missing: unresolved"
    if os.path.isfile(path) and os.access(path, os.R_OK):
        return _run(["strings", path])[1], ""
    if _run(["sudo", "-n", "true"])[0] != 0:
        return "", "the boot image is not readable without a password"
    if _run(["sudo", "-n", "test", "-f", path])[0] != 0:
        return "", f"boot image missing: {path}"
    code, out = _run(["sudo", "-n", "strings", path])
    if code == 0:
        return out, ""
    return "", "the boot image is not readable without a password"
