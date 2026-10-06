class Verdict:
    def __init__(self, ok, reason=""):
        self.ok = ok
        self.reason = reason


def host_verdict(probe):
    name = probe.product_name()
    if name != "MacBook8,1":
        return Verdict(
            False,
            f"product_name is {name}. This program only runs on MacBook8,1.",
        )
    os_id = probe.os_id()
    if os_id != "omarchy":
        return Verdict(False, f"os-release ID is {os_id}. This program only runs on Omarchy.")
    if not probe.has_command("limine-mkinitcpio"):
        return Verdict(
            False,
            "limine-mkinitcpio is not installed. This program will not write a command line it cannot rebuild.",
        )
    return Verdict(True, "")
