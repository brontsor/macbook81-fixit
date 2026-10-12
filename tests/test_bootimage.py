import unittest

from macbook81_fixit.bootimage import loader_path, package_name, paths_to_try, resolve_boot_image


class BootImageTests(unittest.TestCase):
    def test_edge_kernel_is_not_named_as_the_stable_image(self):
        path = resolve_boot_image(
            [
                'CUSTOM_UKI_NAME="omarchy"\n',
                'ESP_PATH="/boot"\n',
            ],
            "linux-omarchy-bore",
            "abc123",
            {"/boot": "vfat"},
        )
        self.assertEqual(path, "/boot/EFI/Linux/omarchy_linux-omarchy-bore.efi")

    def test_stable_kernel_keeps_the_name_this_machine_boots(self):
        path = resolve_boot_image(
            [
                'CUSTOM_UKI_NAME="omarchy"\n',
                'ESP_PATH="/boot"\n',
            ],
            "linux-omarchy",
            "abc123",
            {"/boot": "vfat"},
        )
        self.assertEqual(path, "/boot/EFI/Linux/omarchy_linux-omarchy.efi")

    def test_a_dev_package_is_used_as_given(self):
        path = resolve_boot_image(
            ['CUSTOM_UKI_NAME="omarchy"\n', 'ESP_PATH="/boot"\n'],
            "linux-omarchy-dev",
            "abc123",
            {"/boot": "vfat"},
        )
        self.assertEqual(path, "/boot/EFI/Linux/omarchy_linux-omarchy-dev.efi")

    def test_later_config_wins_and_an_invalid_name_uses_the_machine_id(self):
        path = resolve_boot_image(
            [
                'CUSTOM_UKI_NAME="omarchy"\n',
                'CUSTOM_UKI_NAME="Not A Name"\nESP_PATH="/efi"\n',
            ],
            "linux-omarchy",
            "deadbeef",
            {"/boot": "vfat"},
        )
        self.assertEqual(path, "/efi/EFI/Linux/deadbeef_linux-omarchy.efi")

    def test_cmdline_append_is_not_a_uki_name(self):
        path = resolve_boot_image(
            [
                'KERNEL_CMDLINE[default]+=" quiet"\n',
                'ESP_PATH="/boot"\n',
            ],
            "linux-omarchy-bore",
            "abc123",
            {"/boot": "vfat"},
        )
        self.assertEqual(path, "/boot/EFI/Linux/abc123_linux-omarchy-bore.efi")

    def test_missing_esp_uses_the_vfat_mount_limine_searches(self):
        path = resolve_boot_image(
            ['CUSTOM_UKI_NAME="omarchy"\n'],
            "linux-omarchy",
            "abc123",
            {"/efi": "vfat", "/boot": "vfat"},
        )
        self.assertEqual(path, "/efi/EFI/Linux/omarchy_linux-omarchy.efi")

    def test_bootctl_loader_line_is_the_file_this_boot_started(self):
        text = "         Loader: └─/boot/EFI/Linux/omarchy_linux-omarchy-bore.efi\n"
        self.assertEqual(
            loader_path(text),
            "/boot/EFI/Linux/omarchy_linux-omarchy-bore.efi",
        )

    def test_a_missing_constructed_image_still_tries_the_loader(self):
        self.assertEqual(
            paths_to_try(
                "/boot/EFI/Linux/omarchy_linux-omarchy.efi",
                "/boot/EFI/Linux/omarchy_linux-omarchy-bore.efi",
            ),
            [
                "/boot/EFI/Linux/omarchy_linux-omarchy.efi",
                "/boot/EFI/Linux/omarchy_linux-omarchy-bore.efi",
            ],
        )

    def test_package_query_wins_and_a_failed_query_uses_pkgbase(self):
        self.assertEqual(package_name(0, "linux-omarchy-bore\n", "linux-omarchy"), "linux-omarchy-bore")
        self.assertEqual(package_name(1, "", "linux-omarchy-dev"), "linux-omarchy-dev")
