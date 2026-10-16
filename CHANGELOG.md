# Changelog

Older releases of macbook81-fixit. The latest changes stay in the README. When a new version is tagged, the previous one moves here. Newest first.

## [v0.1.3](https://github.com/brontsor/macbook81-fixit/releases/tag/v0.1.3)

- The boot image name follows the running kernel package. Stable, Edge, and dev do not share one filename. If that file is missing, the screen reads the file this boot started from.
- A row whose files are gone, while this boot still has the effect, says not-rebooted. It does not say not-installed. The same word applies the other way: the audio package can be on disk while the loaded driver is still the in-tree one. That is not installed. Installed means the running module is the patched one. Speaker names left behind say not-restarted. Restart means the WirePlumber process, not the machine. not-restarted fits the status column, so the license column does not shift.
- Keyboard and sleep say partial* only while the boot image is not readable. The star means that check is waiting on the root password. Press u. A missing image, and a mismatch after the image is read, stay partial with no star.
- Quitting a player when the WirePlumber warning appears is in time. The check is at the last step. A boot-image rebuild still asks to reboot if that step finds something playing. The warning does not stay on the screen as the result of the rebuild.
- The audio pin is `37ef61a`. A failed DKMS install is not applied. `added` is not installed. The boot image is not rebuilt until that confirm succeeds.
- `SOURCES.md` lists the versions, gists, and forks. It is not the patch pre-check.
- Tested on 12 October 2026 on a scratch MacBook (Retina, 12-inch, Early 2015), product name MacBook8,1, running the Omarchy Edge channel, kernel `7.2.8-5-omarchy-bore`.
- The README image is still the previous authenticated screen. It does not show partial* or the wider status column. The manufacture date is covered.

## [v0.1.2](https://github.com/brontsor/macbook81-fixit/releases/tag/v0.1.2)

- A scan says Scanning while it runs. It does not leave "scanned" under the package description.
- Apply, remove, and the other action results use the notice row above the status band. The next key clears them.
- The first paint no longer crashes. `addnstr` was called without a length.
- The border is a solid block, red until root authentication, then green. Text starts one cell inside the frame.
- The screen needs 76 columns and 24 rows. A shorter window does not draw a package row on the password line.
- The opening lists what a fresh Omarchy install leaves broken, and what this program does about each item.
- Older releases are in CHANGELOG.md. This file keeps the latest only.
- The README image is still the previous authenticated screen. It does not show the block border. The manufacture date is covered.

## [v0.1.1](https://github.com/brontsor/macbook81-fixit/releases/tag/v0.1.1)

- The top line is MacBook8,1 fixit, the version, and the commit time.
- The extra "authenticated as root" line under the package description is gone. The boot-image line at the bottom is that indicator.
- The last line names the author and the MIT license.
- The README image is the previous authenticated screen. The manufacture date is covered. It does not show this title.

## [v0.1.0](https://github.com/brontsor/macbook81-fixit/releases/tag/v0.1.0)

First public release. Checks the machine and installs the keyboard, speaker, sleep, and webcam fixes. Does not cover Bluetooth or Wi-Fi.
