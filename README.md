# macbook81-fixit

Installer for the MacBook (Retina, 12-inch, Early 2015), model `MacBook8,1`,
on Omarchy.

Clone this repository and run it. Do not run it as root. It asks for sudo
when a step needs it. It does not reboot.

```bash
git clone https://github.com/brontsor/macbook81-fixit.git
cd macbook81-fixit
python3 -m macbook81_fixit
```

`python3 -m macbook81_fixit --check` prints the live status and writes
nothing. That includes no download.

The program matches `product_name` `MacBook8,1` only. `product_family`
`Crb` is normal on this model and is not a match. Any other product is
refused, and nothing is written.

## Patches

| Patch | Source | License |
|---|---|---|
| Keyboard and trackpad | [macbook81-spi-pio](https://github.com/brontsor/macbook81-spi-pio) | MIT |
| Audio driver | [macbook81-cs4208](https://github.com/brontsor/macbook81-cs4208) | GPL-2.0-or-later |
| Speaker profile | [macbook81-audio-profile](https://github.com/brontsor/macbook81-audio-profile) | MIT |
| Sleep default | [macbook81-s2idle-default](https://github.com/brontsor/macbook81-s2idle-default) | MIT |
| Webcam | [patjak/facetimehd](https://github.com/patjak/facetimehd) tag `0.7.2` | GPL-2.0-only |

Each clone is pinned to a reviewed commit. The program does not track a
branch tip.

Not included: Bluetooth, Wi-Fi, deep sleep, hibernate, `macbook12-spi-driver`,
`macbook12-audio`.

The sleep row is the default that avoids the deep-sleep wedge. It is not a
sleep fix. A lid close has hung in s2idle.

The speaker profile names the nodes Headphones, Internal Microphone, and
Speaker (Raw). The equalizer coefficients come from a published macOS layout.
They were not measured on this machine.

The headphone jack watcher is part of the audio driver, not its own row.
It moves the playing stream. It does not restart WirePlumber.

## Webcam firmware

The firmware is not in git. This program downloads the macOS 10.12.6 camera
package from Apple, using the byte ranges in
[patjak/facetimehd-firmware](https://github.com/patjak/facetimehd-firmware).
The download starts in the background when the firmware is missing. Install
still runs that upstream script, which checks the hashes. Do not commit the
package or the extracted files.

While these repositories are private, `git clone` fails for a stranger.
`gh auth login` as someone who can see them lets this program fall back to
`gh repo clone`. Once they are public, plain git is enough.

## What installed means

Status comes from the live machine, not from a log. A file on disk whose
boot image or running check does not match is `partial`. The boot image is
a Limine UKI. Reading it needs sudo. Press `u` in the screen to authenticate
and rescan. The program rebuilds that image once, with `limine-mkinitcpio`,
after the selected writes. It does not run `limine-update`.

## Keys

`j`/`k` move. Space marks. `a` applies. `x` removes. `i` shows the license.
`u` reads the boot image. `s` scans again. `q` quits.

## For agents

Read `AGENTS.md` before changing this tree.

## License

MIT. See `LICENSE`. The patches keep their own licenses.
