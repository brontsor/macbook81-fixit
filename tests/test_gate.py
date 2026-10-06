import unittest

from macbook81_fixit.gate import host_verdict


class FakeHost:
    def __init__(self, product_name="MacBook8,1", family="Crb", os_id="omarchy",
                 has_limine=True):
        self._product_name = product_name
        self._family = family
        self._os_id = os_id
        self._has_limine = has_limine

    def product_name(self):
        return self._product_name

    def product_family(self):
        return self._family

    def os_id(self):
        return self._os_id

    def has_command(self, name):
        return name == "limine-mkinitcpio" and self._has_limine


class TestHostGate(unittest.TestCase):
    def test_refuses_other_product_and_names_what_was_read(self):
        verdict = host_verdict(FakeHost(product_name="MacBookPro11,1"))
        self.assertFalse(verdict.ok)
        self.assertIn("MacBookPro11,1", verdict.reason)
        self.assertNotIn("family", verdict.reason.lower())

    def test_refuses_a_non_omarchy_install(self):
        verdict = host_verdict(FakeHost(os_id="arch"))
        self.assertFalse(verdict.ok)
        self.assertIn("arch", verdict.reason)

    def test_accepts_macbook81_when_family_is_crb(self):
        verdict = host_verdict(FakeHost(family="Crb"))
        self.assertTrue(verdict.ok)

    def test_refuses_when_the_uki_rebuild_command_is_missing(self):
        verdict = host_verdict(FakeHost(has_limine=False))
        self.assertFalse(verdict.ok)
        self.assertIn("limine-mkinitcpio", verdict.reason)
        self.assertNotIn("limine-update", verdict.reason)
