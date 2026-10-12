# Sources

The known versions, gists, forks, and public conversations for this model's Linux quirks. Grouped by issue area. This is the source list for the patch pre-check. It is not the pre-check.

A newer commit in one of these trees is not a reason to move a pin. Do not install a listed file just because it is listed. Do not remove a foreign file.

The installer pins are the commits in `catalog.py`. They are not branch tips. A release tag is not a pin unless `catalog.py` says so.

Each entry names the repository, the commit or the file, and what this program did not take.

## Pins

These are the commits the installer checks out.

| Area | Repository | Commit |
| --- | --- | --- |
| Keyboard | `brontsor/macbook81-spi-pio` | `930eceb20dd27aa8367048c114f2535f2ff04281` |
| Sleep | `brontsor/macbook81-s2idle-default` | `adbc9f4f0de885ce47d29a6b44e56831be07558a` |
| Audio driver | `brontsor/macbook81-cs4208` | `b90beed8c1dd0af2e588fe73b064f276d00d6a66` |
| Speaker profile | `brontsor/macbook81-audio-profile` | `10794e14e9cf9cfb82ccfe81983dd0c6095629da` |
| Webcam driver | `patjak/facetimehd` | `54fb8f25fcf76d4d5af682875f044dc0b6fa0b65` |
| Webcam firmware script | `patjak/facetimehd-firmware` | `60ee21228d9ca00a7bd84fdaefaff00a81f1db91` |

`macbook81-cs4208` tag `v0.1.1` is a README correction. It is not the installer pin. The pin is the build-failure fix: a missing wget is not a missing tarball, and DONE is printed only when `dkms status` says installed for the running kernel. The webcam short name `0.7.2` is the tag on that commit. `dkms.conf` at that tag still says `0.7.0.1`. The installer sets the package version to the tag in the clone. It does not commit that edit upstream.

Bluetooth and Wi-Fi have no pin. This program does not install either.

## Keyboard

The running fix is one kernel parameter, `initcall_blacklist=dw_pci_driver_init`. `dw_dmac_pci` is built in, so a `modprobe` blacklist does nothing. The parameter is written to `/etc/limine-entry-tool.d/macbook81-spi-pio.conf` and rebuilt into the UKI with `limine-mkinitcpio`. This program does not run `limine-update`.

- `brontsor/macbook81-spi-pio` at the pin above. The file is the Limine drop-in. Did not take a second early-load file. Omarchy already loads `applespi`, `spi_pxa2xx_platform`, and `spi_pxa2xx_pci`. Later models want `intel_lpss_pci`. This model wants `spi_pxa2xx_pci`. Did not take that other module list.
- [omacom/omarchy#1954](https://github.com/omacom/omarchy/issues/1954). The keyboard timeout thread. The parameter was confirmed there.
- [omacom/omarchy#9735](https://github.com/omacom/omarchy/pull/9735). Still open when this list was written. The installer reads that pull request as both `initcall_blacklist=dw_pci_driver_init` and `mem_sleep_default=s2idle` on one line, in the same file name we use for the keyboard. If that file also sets `mem_sleep_default`, this program will not replace it, and will not install its sleep default beside it. The hibernate hooks are not in that pull request.
- [matthiasjg gist](https://gist.github.com/matthiasjg/78aaf7802146f0b89be3da9e4feb111f). Keyboard, s2idle, and hibernate, tested on Omarchy 4.0.0, kernel 7.1.8. The keyboard half is the same parameter. It writes `/etc/limine-entry-tool.d/macbook81-spi-fix.conf` with both tokens on one line. Did not take the hibernate hooks, the suspend detach hook, the rebind units, or that combined file. Those files are `macbook81-applespi`, `macbook81-spi-detach`, `macbook81-applespi-rebind.service`, and `macbook81-applespi-ensure.service`. If any of them is installed, the sleep row stays blocked. This program will not remove them.
- [openwebcraft writeup](https://openwebcraft.com/archive/2026/omarchy-4-on-12-macbook8-1). Same DMA diagnosis and the same parameter. It cites #1954, #2099, and later #9735. Did not take its `limine-update` instruction. #2099 is cited there as the same timeout. This list does not summarize that issue.
- [roydq gist](https://gist.github.com/roydq/e99fdb263c8fd3360012612af8288466). Keyboard, sleep, and speakers, tested on Omarchy 4.0.4, kernel 7.2.5-3. The keyboard half puts the same parameter in `/etc/default/limine` and runs `limine-update`. Did not take `limine-update`. The speakers section is not a source for our profile. Read it before treating it as one.
- [omacom/omarchy#9831](https://github.com/omacom/omarchy/issues/9831). `macbook12-spi-driver-dkms` cannot build on a kernel that already ships `applespi`. The package is obsolete. A DKMS `added` line is not an install. Did not take the package. Will not remove it if it is present. Will not call it the keyboard fix.
- [PIO series, v16 5/7](https://lore.kernel.org/linux-spi/20260720162117.32304-6-fourdollars@debian.org/). Shih-Yuan Lee. This is the real fix: force PIO in the SPI driver, not in `applespi`. It is not in `7.2.5-4-omarchy`. Did not ship the quirk. The command-line parameter stays until that series is in the kernel we boot.
- An earlier applespi-side patch, also Shih-Yuan Lee, 2026-07-11, "Input: applespi - force PIO mode on MacBook8,1". [v3](https://lkml.rescloud.iu.edu/hypermail/linux/kernel/2607.1/08131.html) links [bugzilla 108331](https://bugzilla.kernel.org/show_bug.cgi?id=108331). That is a different approach from the SPI-driver series. Did not take it.
- A CachyOS thread with the same DMA diagnosis was named while gathering this list. No URL was found. Do not invent one.

## Speakers

The driver and the profile are two packages. The driver does not install the profile.

- `brontsor/macbook81-cs4208` at the pin above. Fork of `omnidecker/macbook8.1-speaker-driver` at `e4134fb272ba3be29aa71ad7aa6eae8b0ebddf1a`, which forks `thomas-shirley/macbook8.1-speaker-driver`. Credits `davidjo/snd_hda_macbookpro` and `leifliddy/macbook12-audio-driver`. `leifliddy` does not support MacBook8,1. Package name `macbook81-cs4208`, version `0.1`. Did not take the `macbook12-audio` package name. Will not install over `macbook12-audio`. Will not remove it.
- Upstream at that commit still calls jack switching wonky, and ships a unit so a headphone pull does not leave silence. This fork's reconnect change is on top of that import. A headphone open must not write its stream onto the speaker converter, `0x0a`. The prepare widget is `0x02` only. Did not take a GPIO4 or GPIO5 change. Did not take 48 kHz or 24-bit. The speakers stay at 44.1 kHz, 16-bit.
- `brontsor/macbook81-audio-profile` at the pin above. Two user files, not a system package. `51-macbook81-speaker.conf` is the PipeWire filter. The coefficients are copied from `thomas-shirley` `51-macbook81-speaker.conf`, layout100. They were not measured on this machine. Do not call them tuned. `51-mb81-rawpcm-speaker.conf` is the WirePlumber rename: Headphones, Internal Microphone, Speaker (Raw). Did not take a measured layout. Did not copy these files back into the driver installer.

## Jack

The jack switch lives in the driver repository, not in the profile.

- `mb81-jack-switch.sh` in `brontsor/macbook81-cs4208`. On plug, it moves the stream that is already playing to the headphone PCM `alsa_output.pci-0000_00_1b.0.playback.0.0` and sets that as the default. On unplug, it moves that same stream back to `input.MacBook_Speaker`. Plug in again and the same stream follows. It does not restart WirePlumber. It does not write coefficients. It does not touch GPIO.
- Restarting WirePlumber is the old workaround. It is not the headphone fix. If the installed script still restarts WirePlumber, the audio row is partial.
- The card is raw-PCM. There is no ACP jack route to take.
- `resume_recover.sh` reloads the card after resume and starts the jack switch if it is down. That is a workaround for the resume path. It is not the reconnect fix.

## Sleep

The running choice is s2idle. It is not a sleep fix. A lid close has hung in s2idle. Deep sleep resumes the machine and wedges SPI with `-110` until reboot. Hibernate is not installed.

- `brontsor/macbook81-s2idle-default` at the pin above. Two files. The Limine drop-in sets `mem_sleep_default=s2idle`. The systemd drop-in sets `MemorySleepMode=s2idle`. The token is the same one the gist uses. The choice was a listen on this model, not that script. Did not take the gist's hibernate hooks, the suspend detach hook, or putting the sleep token on the keyboard line.
- The same foreign files listed under Keyboard block this row. So does an uncommented `MemorySleepMode=` or `HibernateMode=` in systemd, and `mem_sleep_default=` in another Limine file, including `/etc/default/limine`. A comment in the stock `sleep.conf` is not one of those. Did not take writing `/sys/power/mem_sleep` as the install. The live write is a probe. It does not survive reboot.

## Camera

- `patjak/facetimehd` at the pin above, tag `0.7.2`. The upstream README still points at the `bcwc_pcie` wiki. That is the old repository name. Did not vendor the driver.
- `patjak/facetimehd-firmware` at the pin above. The script is `facetimehd-firmware-install.sh`. It downloads one Apple combo image and extracts two files, `firmware.bin` and `1675_01XX.dat`. The image URL and the byte ranges are in `catalog.py`. They must match that script. Did not reimplement the offsets. Did not vendor the Apple package. Did not commit the extracted files. The package is not redistributed.

The image, as named by that script and by `catalog.py`:

`https://download.info.apple.com/Mac_OS_X/031-34089-20160809-3ca52e36-2d5f-11e6-a93f-c5e6bfb90746/com_apple_macbookpro_13_2.pkg`

## Bluetooth

Not installed. The controller is a UART `BCM2E7C` behind an SSDC mux. A USB `BCM4350C5` is not this controller. There is no `.hcd` for it. Do not rename a USB Bluetooth firmware file onto `brcm/BCM.hcd`.

- [jaderfeijo gist](https://gist.github.com/jaderfeijo/7429e3ed5d1fd446ed8f8431880ecacf). Serdev swap, an `hci_bcm` baud quirk, and a 500 ms `btbcm` reset delay. The controller runs its ROM firmware. No pin. Did not install it. The local test tree was removed. Do not rebuild it on a kernel update.
- [`leifliddy/macbook12-bluetooth-driver`](https://github.com/leifliddy/macbook12-bluetooth-driver), [issue 34](https://github.com/leifliddy/macbook12-bluetooth-driver/issues/34). The same `-EBUSY` on kernel 7.x, before `hci_uart` loads. Not re-tested here. Did not take that driver.
- [Lukas Wunner, 2017](https://www.spinics.net/lists/linux-bluetooth/msg73527.html). The SSDC mux and GPIO 36. [linux-serial discussion](https://www.spinics.net/lists/linux-serial/msg28691.html) of the ACPI tables. [bugzilla 110901](https://bugzilla.kernel.org/show_bug.cgi?id=110901) is the older controller report. Did not take a DSDT override. Did not take driving the mux GPIO low. Did not take `rmmod 8250_lpss`.

## Wi-Fi

Not changed. The radio is in-tree `brcmfmac` on `14e4:43a3`, firmware request `brcm/brcmfmac4350c2-pcie`. The loaded firmware is the 2015 Broadcom file. There is no matching CLM blob. Do not rename another chip's blob onto this device.

- Did not take `pcie_aspm=off`. That was a probe failure on another distribution. This chip probes.
- Did not take a BSSID lock as a fix.
- A local holder can keep NetworkManager off the device and send `WPA-PSK` alone. It is unpublished. It is not the fix. The menu bar cannot see that connection. The correct change is still in the NetworkManager path: stop the supplicant from advertising `FT-PSK` and `WPA-PSK-SHA256`, which this firmware rejects. Not started. No public patch is adopted here.
- There is no newer `brcmfmac4350c2` firmware in the notes to load. Did not take a macOS Wi-Fi kext as firmware.
