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
- Pins live in `catalog.py`. Do not float them to a branch tip.
- One `limine-mkinitcpio` after the writes. Never `limine-update`.
- Do not write `/sys/power/mem_sleep`.
- Do not restart WirePlumber while something is playing. The equalizer's
  own stream is not that something.
- Do not install beside `macbook12-audio`. Do not remove
  `macbook12-spi-driver`.
- Do not vendor the Apple camera package or the extracted firmware.
- The webcam `dkms.conf` at tag `0.7.2` says `0.7.0.1`. Set it to `0.7.2`
  in the clone. Do not commit that edit upstream.
- Do not install the sleep default beside another one. That includes `mem_sleep_default=` in another Limine file, an uncommented `MemorySleepMode=` or `HibernateMode=` in systemd, and the gist hooks `macbook81-applespi` and `macbook81-spi-detach`. A comment in the stock `sleep.conf` is not one of those.
- Do not replace or remove `macbook81-spi-pio.conf` when that file also sets `mem_sleep_default`. That is the open Omarchy pull request, not our keyboard file.
- Do not push or flip a repository public unless asked.
