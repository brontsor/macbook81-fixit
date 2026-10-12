import unittest

from macbook81_fixit.execute import execute
from macbook81_fixit.plan import Step


class TestExecute(unittest.TestCase):
    def test_a_failed_write_does_not_rebuild_the_uki(self):
        steps = [
            Step(["install", "-D", "-m", "644", "src", "/etc/limine-entry-tool.d/x.conf"], sudo=True),
            Step(["limine-mkinitcpio"], sudo=True),
        ]
        ran = []

        def run(step):
            ran.append(step.argv)
            return 1 if step.argv[0] == "install" else 0

        result = execute(steps, run, log=None)
        self.assertEqual(ran, [["install", "-D", "-m", "644", "src", "/etc/limine-entry-tool.d/x.conf"]])
        self.assertFalse(result.ok)
        self.assertNotIn("limine-mkinitcpio", " ".join(" ".join(argv) for argv in ran))

    def test_a_failed_dkms_confirm_does_not_rebuild_the_uki(self):
        steps = [
            Step(["bash", "install.sh"], sudo=True),
            Step(
                ["macbook81-cs4208/0.1"],
                kind="confirm-dkms",
                detail="macbook81-cs4208/0.1 is not installed for the running kernel",
            ),
            Step(["limine-mkinitcpio"], sudo=True),
        ]
        ran = []

        def run(step):
            ran.append(step.kind)
            return 1 if step.kind == "confirm-dkms" else 0

        result = execute(steps, run, log=None)
        self.assertFalse(result.ok)
        self.assertEqual(result.detail, "macbook81-cs4208/0.1 is not installed for the running kernel")
        self.assertEqual(ran, ["run", "confirm-dkms"])

    def test_a_player_still_open_after_the_rebuild_does_not_hide_the_reboot(self):
        from macbook81_fixit.plan import Step

        steps = [
            Step(["limine-mkinitcpio"], sudo=True),
            Step(["systemctl", "--user", "restart", "wireplumber"], kind="wireplumber"),
        ]

        def run(step):
            return 2 if step.kind == "wireplumber" else 0

        result = execute(steps, run, log=None)
        self.assertTrue(result.rebuilt)
        self.assertTrue(result.ok)
        self.assertIn("still playing", result.detail)

    def test_a_player_quit_before_the_step_restarts_wireplumber(self):
        from macbook81_fixit.plan import Step

        steps = [
            Step(["limine-mkinitcpio"], sudo=True),
            Step(["systemctl", "--user", "restart", "wireplumber"], kind="wireplumber"),
        ]
        ran = []

        def run(step):
            ran.append(step.kind)
            return 0

        result = execute(steps, run, log=None)
        self.assertTrue(result.ok)
        self.assertTrue(result.rebuilt)
        self.assertEqual(result.detail, "")
        self.assertEqual(ran, ["run", "wireplumber"])
