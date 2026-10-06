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
