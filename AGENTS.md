# macbook81-fixit

Python 3, standard library, curses. No pip package. The owner runs it.
It asks for sudo. After a boot-image rebuild it offers a reboot, and
reboots only if you say yes.

- Match `product_name` `MacBook8,1` only. Do not match on `Crb`.
- A refused host writes nothing. `--check` writes nothing, including no
  firmware download.
- Status comes from the live system. The action log is not the status.
- The screen may read the serial to show computer age and the manufacture date. Do not log either, print the serial, or put the date or the serial in `--check`. Do not read a board serial or a battery date.
- `macbook12-spi-driver` at DKMS `added` is not installed. Say so.
  Do not call it the keyboard fix. Do not remove it unless asked.
- Pins live in `catalog.py`. Do not float them to a branch tip. `SOURCES.md` lists the versions, gists, and forks. It is not the patch pre-check. Do not install a listed file just because it is listed.
- One `limine-mkinitcpio` after the writes. Never `limine-update`.
- The boot image path follows the running kernel package, the way `limine-mkinitcpio` names it. Do not hardcode a filename.
- Do not write `/sys/power/mem_sleep`.
- Do not restart WirePlumber while something is playing. The equalizer's
  own stream is not that something. Recheck at the last step, not when
  the list is built. Quitting the player when the warning appears is in
  time. A boot-image rebuild still asks to reboot if that step finds
  something playing. Do not leave that warning as the notice for a
  rebuild that already ran.
- A row whose files are gone, while this boot still has the effect, is
  not-rebooted. It is not not-installed, and it is not partial. The same
  word applies the other way. The audio package on disk, with the loaded
  module still in-tree, is not-rebooted. `dkms status` and a patch string
  in the file `modinfo` would load describe the next boot. Installed means
  the running module is the patched one. Speaker names left behind are
  not-restarted. Restart means the WirePlumber process, not the machine.
- Keyboard and sleep say partial* before the boot image is read. The star
  means that check is waiting on the root password. A mismatch after the
  image is read stays partial, with no star. Do not treat partial* as an
  incomplete install.
- Do not install beside `macbook12-audio`. Do not remove
  `macbook12-spi-driver`.
- Do not vendor the Apple camera package or the extracted firmware.
- The webcam `dkms.conf` at tag `0.7.2` says `0.7.0.1`. Set it to `0.7.2`
  in the clone. Do not commit that edit upstream.
- Do not install the sleep default beside another one. That includes `mem_sleep_default=` in another Limine file, an uncommented `MemorySleepMode=` or `HibernateMode=` in systemd, and the gist hooks `macbook81-applespi` and `macbook81-spi-detach`. A comment in the stock `sleep.conf` is not one of those.
- Do not replace or remove `macbook81-spi-pio.conf` when that file also sets `mem_sleep_default`. That is the open Omarchy pull request, not our keyboard file.
- Do not push or flip a repository public unless asked.
- Changes: the README holds only the latest. That is the unreleased list and the current tag. Older tags are in `CHANGELOG.md`, newest first. When tagging, move the unreleased notes under that version in the README, and move the previous tag from the README into `CHANGELOG.md`, before the tag. Do not describe a change that is not in the tag. Do not put a serial or a manufacture date in the notes. Do not add a changelog to another repository unless that repository has a substantive change.
- The title version is the tag only when this checkout is that release. `git describe --tags --abbrev=0` is not that check. A pull does not fetch a new tag. If the local tag is absent, ask the remote which tag points at this commit. Do not fall back to `0.1.0`.
