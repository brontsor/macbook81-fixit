# macbook81-fixit

Python 3, standard library, curses. No pip package. The owner runs it.
It asks for sudo. It does not reboot.

- Match `product_name` `MacBook8,1` only. Do not match on `Crb`.
- A refused host writes nothing. `--check` writes nothing, including no
  firmware download.
- Status comes from the live system. The action log is not the status.
- Do not read a serial, a board serial, or a battery date.
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
- Do not push or flip a repository public unless asked.
