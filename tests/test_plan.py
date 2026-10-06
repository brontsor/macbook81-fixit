import unittest

from macbook81_fixit.plan import plan_apply
from macbook81_fixit.status import DROPIN
from macbook81_fixit import catalog


class Fake:
    def __init__(self):
        self._playing = False
        self.files = {}
        self.foreign = []

    def home(self):
        return "/home/owner"

    def foreign_sleep(self):
        return getattr(self, "foreign", [])

    def playing(self):
        return self._playing

    def exists(self, path):
        return path in self.files

    def read(self, path):
        return self.files.get(path)

    def kernel_release(self):
        return "7.2.5-4-omarchy"


class TestPlan(unittest.TestCase):
    def test_keyboard_and_sleep_rebuild_the_uki_once_and_do_not_write_mem_sleep(self):
        steps = plan_apply(["keyboard", "sleep"], Fake())
        rebuilds = [step for step in steps if step.argv[:1] == ["limine-mkinitcpio"]]
        blob = " ".join(" ".join(step.argv) for step in steps)
        self.assertEqual(len(rebuilds), 1)
        self.assertNotIn("limine-update", blob)
        self.assertNotIn("/sys/power/mem_sleep", blob)

    def test_speaker_apply_waits_instead_of_restarting_wireplumber_while_playing(self):
        probe = Fake()
        probe._playing = True
        steps = plan_apply(["speaker"], probe)
        blob = " ".join(" ".join(step.argv) for step in steps)
        self.assertNotIn("restart", blob)
        self.assertTrue(any(step.kind == "wait" for step in steps))

    def test_audio_apply_skips_its_own_rebuild_and_does_not_copy_the_profile(self):
        steps = plan_apply(["audio"], Fake())
        self.assertTrue(any(step.env.get("MB81_SKIP_INITRAMFS") == "1" for step in steps))
        blob = " ".join(" ".join(step.argv) for step in steps)
        self.assertNotIn("51-macbook81-speaker.conf", blob)
        self.assertNotIn("51-mb81-rawpcm-speaker.conf", blob)

    def test_webcam_apply_uses_the_upstream_firmware_script(self):
        steps = plan_apply(["webcam"], Fake())
        blob = " ".join(" ".join(step.argv) + " " + step.detail for step in steps)
        self.assertIn("facetimehd-firmware-install.sh", blob)
        self.assertNotIn("--osx-10.11.5", blob)
        self.assertIn("0.7.2", blob)

    def test_clones_are_pinned_commits(self):
        steps = plan_apply(["keyboard", "audio", "speaker", "sleep"], Fake())
        blob = " ".join(" ".join(step.argv) for step in steps)
        self.assertIn(catalog.PIN["keyboard"], blob)
        self.assertIn(catalog.PIN["audio"], blob)
        self.assertIn(catalog.PIN["speaker"], blob)
        self.assertIn(catalog.PIN["sleep"], blob)

    def test_a_foreign_sleep_workaround_is_not_installed_over(self):
        probe = Fake()
        probe.foreign = ["/etc/limine-entry-tool.d/macbook81-spi-pio.conf"]
        steps = plan_apply(["sleep"], probe)
        blob = " ".join(" ".join(step.argv) for step in steps)
        self.assertNotIn("macbook81-s2idle.conf", blob)
        self.assertNotIn("limine-mkinitcpio", blob)
        self.assertTrue(any(step.kind == "skip" for step in steps))

    def test_keyboard_apply_does_not_replace_a_dropin_that_also_sets_sleep(self):
        probe = Fake()
        probe.files["/etc/mkinitcpio.conf.d/macbook_spi_modules.conf"] = "MODULES=(applespi spi_pxa2xx_platform spi_pxa2xx_pci)\n"
        probe.files[DROPIN] = (
            'KERNEL_CMDLINE[default]+=" initcall_blacklist=dw_pci_driver_init'
            ' mem_sleep_default=s2idle"\n'
        )
        steps = plan_apply(["keyboard"], probe)
        blob = " ".join(" ".join(step.argv) for step in steps)
        self.assertNotIn(DROPIN, blob)
        self.assertNotIn("limine-mkinitcpio", blob)

    def test_firmware_url_is_the_apple_10126_combo(self):
        self.assertEqual(
            catalog.APPLE_CAMERA_URL,
            "https://updates.cdn-apple.com/2019/cert/041-90765-20191011-837e856d-b522-4865-b64c-641048ed77c4/macOSUpdCombo10.12.6.dmg",
        )
