import unittest

from macbook81_fixit.status import (
    audio_status,
    keyboard_status,
    sleep_status,
    speaker_status,
    webcam_status,
)

DROPIN = "/etc/limine-entry-tool.d/macbook81-spi-pio.conf"
TOKEN = "initcall_blacklist=dw_pci_driver_init"
SLEEP_LIMINE = "/etc/limine-entry-tool.d/macbook81-s2idle.conf"
SLEEP_SYSTEMD = "/etc/systemd/sleep.conf.d/macbook81-s2idle.conf"
JACK = "/usr/local/bin/mb81-jack-switch"
PW = "/home/owner/.config/pipewire/pipewire.conf.d/51-macbook81-speaker.conf"
WP = "/home/owner/.config/wireplumber/wireplumber.conf.d/51-mb81-rawpcm-speaker.conf"
FIRMWARE = "/usr/lib/firmware/facetimehd/firmware.bin"
SETFILE = "/usr/lib/firmware/facetimehd/1675_01XX.dat"
VIDEO = "/dev/video0"


class Fake:
    def __init__(self):
        self.files = {}
        self.uki = ""
        self.dkms = ""
        self.kernel = "7.2.5-4-omarchy"
        self.module_needles = set()
        self.enabled = set()
        self.nicks = ""
        self.mem_sleep = "s2idle [deep]"
        self._home = "/home/owner"

    def read(self, path):
        return self.files.get(path)

    def exists(self, path):
        return path in self.files

    def uki_has(self, token):
        return token in self.uki

    def dkms_status(self):
        return self.dkms

    def kernel_release(self):
        return self.kernel

    def module_has(self, needle):
        return needle in self.module_needles

    def user_unit_enabled(self, name):
        return name in self.enabled

    def node_text(self):
        return self.nicks

    def mem_sleep_text(self):
        return self.mem_sleep

    def home(self):
        return self._home


class TestKeyboardStatus(unittest.TestCase):
    def test_dropin_without_uki_token_is_partial(self):
        probe = Fake()
        probe.files[DROPIN] = "token\n"
        report = keyboard_status(probe)
        self.assertEqual(report.status, "partial")
        self.assertIn(TOKEN, report.detail)

    def test_dropin_and_uki_token_is_installed(self):
        probe = Fake()
        probe.files[DROPIN] = "token\n"
        probe.uki = "quiet initcall_blacklist=dw_pci_driver_init"
        report = keyboard_status(probe)
        self.assertEqual(report.status, "installed")


class TestAudioStatus(unittest.TestCase):
    def test_macbook12_audio_blocks_the_row(self):
        probe = Fake()
        probe.dkms = "macbook12-audio/0.1, 7.2.5-4-omarchy, x86_64: installed\n"
        report = audio_status(probe)
        self.assertEqual(report.status, "blocked")
        self.assertIn("macbook12-audio", report.detail)

    def test_comment_about_not_restarting_is_not_a_restart(self):
        probe = _audio_ready()
        probe.files[JACK] = "# It does not restart WirePlumber.\nmove-sink-input\n"
        report = audio_status(probe)
        self.assertEqual(report.status, "installed")

    def test_a_restart_command_is_not_installed(self):
        probe = _audio_ready()
        probe.files[JACK] = "systemctl --user restart wireplumber\n"
        report = audio_status(probe)
        self.assertNotEqual(report.status, "installed")


class TestSpeakerStatus(unittest.TestCase):
    def test_files_with_old_nick_are_partial(self):
        probe = Fake()
        probe.files[PW] = "eq\n"
        probe.files[WP] = "names\n"
        probe.nicks = "CS4208 Analog"
        report = speaker_status(probe)
        self.assertEqual(report.status, "partial")
        self.assertIn("CS4208 Analog", report.detail)

    def test_installed_names_the_three_nicks_and_says_eq_was_not_measured(self):
        probe = Fake()
        probe.files[PW] = "eq\n"
        probe.files[WP] = "names\n"
        probe.nicks = "Headphones\nInternal Microphone\nSpeaker (Raw)\n"
        report = speaker_status(probe)
        self.assertEqual(report.status, "installed")
        self.assertIn("not measured", report.note.lower())


class TestSleepStatus(unittest.TestCase):
    def test_limine_file_alone_is_not_installed(self):
        probe = Fake()
        probe.files[SLEEP_LIMINE] = "mem_sleep_default=s2idle\n"
        probe.uki = "mem_sleep_default=s2idle"
        probe.mem_sleep = "[s2idle] deep"
        report = sleep_status(probe)
        self.assertNotEqual(report.status, "installed")

    def test_both_files_uki_and_bracket_are_installed_and_not_called_a_fix(self):
        probe = Fake()
        probe.files[SLEEP_LIMINE] = "mem_sleep_default=s2idle\n"
        probe.files[SLEEP_SYSTEMD] = "[Sleep]\nMemorySleepMode=s2idle\n"
        probe.uki = "mem_sleep_default=s2idle"
        probe.mem_sleep = "[s2idle] deep"
        report = sleep_status(probe)
        self.assertEqual(report.status, "installed")
        self.assertIn("not a sleep fix", report.note.lower())


class TestWebcamStatus(unittest.TestCase):
    def test_dkms_without_firmware_is_not_installed(self):
        probe = Fake()
        probe.dkms = "facetimehd/0.7.2, 7.2.5-4-omarchy, x86_64: installed\n"
        probe.files[VIDEO] = ""
        report = webcam_status(probe)
        self.assertNotEqual(report.status, "installed")
        self.assertIn("firmware", report.detail.lower())

    def test_dkms_firmware_setfile_and_video_node_are_installed(self):
        probe = Fake()
        probe.dkms = "facetimehd/0.7.2, 7.2.5-4-omarchy, x86_64: installed\n"
        probe.files[FIRMWARE] = "bin"
        probe.files[SETFILE] = "dat"
        probe.files[VIDEO] = ""
        report = webcam_status(probe)
        self.assertEqual(report.status, "installed")
        self.assertIn("patjak/facetimehd", report.note)


def _audio_ready():
    probe = Fake()
    probe.dkms = "macbook81-cs4208/0.1, 7.2.5-4-omarchy, x86_64: installed\n"
    probe.module_needles.add("MB81 HP PREPARE")
    probe.files[JACK] = "move-sink-input\n"
    probe.enabled.add("mb81-jack-switch.service")
    return probe
