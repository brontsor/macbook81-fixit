# macbook81-fixit

Installer for a MacBook (Retina, 12-inch, Early 2015) running Omarchy.

A fresh install on this machine leaves the built-in keyboard, trackpad, speakers, and webcam unusable or unnamed. This program checks the computer and installs the fixes we use for those. It does not cover Bluetooth or Wi-Fi.

You run it as yourself, not as root. It asks for your password when a step needs one. It will not reboot the machine.

## Run it

```bash
git clone https://github.com/brontsor/macbook81-fixit.git
cd macbook81-fixit
python3 -m macbook81_fixit
```

To see what is already in place, and change nothing:

```bash
python3 -m macbook81_fixit --check
```

## The screen

The first screen is a scan. Each row is one fix, with a status.

- `j` and `k`, or the arrow keys, move through the list
- Space marks a row
- `a` installs the marked rows
- `x` removes the marked rows
- `u` reads the boot image
- `q` quits

The boot image is the file this machine starts from. The keyboard and sleep settings live in it. Reading it asks for your password. The border is yellow and moving until that read succeeds.

Each row has a license column. `i` shows the license link.

It asks before it writes. If a change rebuilt the boot image, it tells you to reboot by hand, and asks if it should reboot now. It reboots only if you say yes. Then run it again and look at the scan.

## What it installs

### Keyboard and trackpad

On a stock boot the built-in keyboard and trackpad time out. This installs the workaround already used on other Omarchy machines of this model.

[macbook81-spi-pio](https://github.com/brontsor/macbook81-spi-pio)

### Speakers and headphones

Stock Linux sees the audio chip and does not play the internal speakers. This installs our driver. Plugging or unplugging headphones moves whatever is playing. You do not have to pick the output from a menu.

[macbook81-cs4208](https://github.com/brontsor/macbook81-cs4208)

### Speaker names and equalizer

Separate from the driver. Without it, the headphones and the microphone are both named "CS4208 Analog". This names them Headphones, Internal Microphone, and Speaker (Raw), and adds the equalizer we use with the speakers. The equalizer came from a published macOS layout. We did not measure it on this machine.

[macbook81-audio-profile](https://github.com/brontsor/macbook81-audio-profile)

### Sleep default

Deep sleep on this machine can resume with a dead keyboard. This makes light sleep the default, so a normal suspend does not do that. It does not fix deep sleep. Closing the lid has also hung once, in light sleep. The screen says so.

[macbook81-s2idle-default](https://github.com/brontsor/macbook81-s2idle-default)

If the machine already has another sleep workaround, this row says blocked and the program will not install ours beside it. It also will not overwrite a keyboard drop-in that already carries the sleep setting. That is the shape in [omacom/omarchy#9735](https://github.com/omacom/omarchy/pull/9735), which is still open: the keyboard parameter and `mem_sleep_default=s2idle` on one line, in the same file we use for the keyboard. The hibernate hooks and the suspend detach hook are not in that pull request. They are in the [gist it cites](https://gist.github.com/matthiasjg/78aaf7802146f0b89be3da9e4feb111f). Those are a later sleep and hibernate patch, not this one. If they are already installed, this row stays blocked.

### Webcam

The FaceTime camera is not a USB webcam. This installs patjak's driver and downloads the firmware from Apple. The firmware is not in our repositories.

[patjak/facetimehd](https://github.com/patjak/facetimehd)

Bluetooth, Wi-Fi, deep sleep, and hibernate are not in this package.

## Details

### Which machine

It runs only when the product name is `MacBook8,1`. These machines report a family of `Crb`. That string is normal, and the program does not use it. On any other product it prints what it read and exits. It does not write anything.

### Status

The status on each row is read from the machine, not from a log.

| Status | Meaning |
|---|---|
| installed | The live check matches |
| partial | A file is present, but the boot image or the running check does not match yet |
| not-installed | Not present |
| blocked | Something else is in the way. The program will not install over it |

Two boot fixes, the keyboard and the sleep default, live in the boot image. Reading that image needs your password. If a row says the image is not readable, press `u`, enter the password, and it scans again. `s` scans again without that.

### Reboot and the boot image

This machine boots a Limine UKI, which is the boot image. If an install changes a boot file, the program rebuilds that image once, with `limine-mkinitcpio`, after the other writes. It does not run `limine-update`. It then asks if you want to reboot. It reboots only if you say yes. You can always reboot by hand instead.

### Webcam firmware

The download starts in the background when the firmware is missing. Install then runs patjak's own script, which fetches the macOS 10.12.6 camera package from Apple and checks the hashes. Do not commit that package, or the files extracted from it.

[patjak/facetimehd-firmware](https://github.com/patjak/facetimehd-firmware)

### Private repositories

Until these repositories are public, a plain `git clone` fails for anyone who cannot see them. If you can, `gh auth login` is enough. The program tries `gh repo clone` when `git clone` fails.

Each fix is pinned to a reviewed commit. The program does not follow a branch tip.

### License

This installer is MIT. See `LICENSE`. The audio driver and the webcam driver are GPL. Press `i` on a row for that row's license link.

### For agents

Read `AGENTS.md` before changing this tree.
