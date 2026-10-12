import glob
import re

ESP_CANDIDATES = ("/efi", "/boot", "/boot/efi", "/limine")
_ASSIGN = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$")
_NAME = re.compile(r"^[a-z0-9]+$")


def config_paths():
    paths = sorted(glob.glob("/usr/share/limine-entry-tool.d/*.conf"))
    paths.append("/etc/limine-entry-tool.conf")
    paths.extend(sorted(glob.glob("/etc/limine-entry-tool.d/*.conf")))
    paths.append("/etc/default/limine")
    return paths


def loader_path(text):
    for line in text.splitlines():
        if "Loader:" not in line or ".efi" not in line:
            continue
        tail = line.split("└─")[-1].strip()
        if tail.endswith(".efi") and "EFI/Linux/" in tail and tail.startswith("/"):
            return tail
    return ""


def paths_to_try(constructed, loader):
    paths = []
    if constructed:
        paths.append(constructed)
    if loader and loader not in paths:
        paths.append(loader)
    return paths


def package_name(pacman_code, pacman_text, pkgbase):
    if pacman_code == 0:
        name = pacman_text.strip().splitlines()[-1].strip() if pacman_text.strip() else ""
        if name and "/" not in name:
            return name
    return pkgbase.strip()


def resolve_boot_image(configs, package, machine_id, mounts):
    custom = _assigned(configs, "CUSTOM_UKI_NAME")
    configured = _assigned(configs, "ESP_PATH")
    prefix = custom if custom and _NAME.fullmatch(custom) else machine_id.strip()
    esp = configured.strip() if configured and configured.strip() else _esp(mounts)
    if not package or not prefix or not esp:
        return ""
    return f"{esp.rstrip('/')}/EFI/Linux/{prefix}_{package}.efi"


def _assigned(configs, key):
    found = None
    for text in configs:
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            match = _ASSIGN.match(line)
            if match and match.group(1) == key:
                found = _unquote(match.group(2))
    return found


def _unquote(value):
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1].strip()
    return value.strip()


def _esp(mounts):
    for path in ESP_CANDIDATES:
        if mounts.get(path) == "vfat":
            return path
    return ""
