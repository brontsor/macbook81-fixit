COMMANDS = (
    ("git", "git"),
    ("dkms", "dkms"),
    ("limine-mkinitcpio", "limine-mkinitcpio-hook"),
    ("wget", "wget"),
    ("curl", "curl"),
    ("gcc", "base-devel"),
    ("make", "base-devel"),
)


def missing(probe):
    pkgs = []
    for command, package in COMMANDS:
        if not probe.has_command(command):
            pkgs.append(package)
    version = probe.pacman_version("linux-omarchy-headers")
    kernel = probe.kernel_release()
    if not version or not kernel.startswith(version):
        pkgs.append("linux-omarchy-headers")
    ordered = []
    for package in pkgs:
        if package not in ordered:
            ordered.append(package)
    return ordered
