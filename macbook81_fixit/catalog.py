# Reviewed commits. Do not float these to a branch tip.

PIN = {
    "keyboard": "930eceb20dd27aa8367048c114f2535f2ff04281",
    "sleep": "adbc9f4f0de885ce47d29a6b44e56831be07558a",
    "audio": "3dcc9ef23e852a17a872587bcd1ade2a25c1d064",
    "speaker": "10794e14e9cf9cfb82ccfe81983dd0c6095629da",
    "webcam": "54fb8f25fcf76d4d5af682875f044dc0b6fa0b65",
    "firmware": "60ee21228d9ca00a7bd84fdaefaff00a81f1db91",
}

REPO = {
    "keyboard": "https://github.com/brontsor/macbook81-spi-pio.git",
    "sleep": "https://github.com/brontsor/macbook81-s2idle-default.git",
    "audio": "https://github.com/brontsor/macbook81-cs4208.git",
    "speaker": "https://github.com/brontsor/macbook81-audio-profile.git",
    "webcam": "https://github.com/patjak/facetimehd.git",
    "firmware": "https://github.com/patjak/facetimehd-firmware.git",
}

LICENSE = {
    "keyboard": ("MIT", "https://github.com/brontsor/macbook81-spi-pio/blob/master/LICENSE"),
    "sleep": ("MIT", "https://github.com/brontsor/macbook81-s2idle-default/blob/master/LICENSE"),
    "audio": ("GPL-2.0-or-later", "https://github.com/brontsor/macbook81-cs4208/blob/master/LICENSE"),
    "speaker": ("MIT", "https://github.com/brontsor/macbook81-audio-profile/blob/master/LICENSE"),
    "webcam": ("GPL-2.0-only", "https://github.com/patjak/facetimehd/blob/master/LICENSE"),
}

# patjak/facetimehd-firmware facetimehd-firmware-install.sh, the 10.12.6 combo.
# The installer fetches three byte ranges. It does not download the whole image.
APPLE_CAMERA_URL = (
    "https://updates.cdn-apple.com/2019/cert/"
    "041-90765-20191011-837e856d-b522-4865-b64c-641048ed77c4/"
    "macOSUpdCombo10.12.6.dmg"
)
APPLE_RANGES = (
    "699186570-703316225",
    "703316242-707986973",
    "430282546-439105037",
)

SHORT = {
    "keyboard": "930eceb",
    "sleep": "adbc9f4",
    "audio": "3dcc9ef",
    "speaker": "10794e1",
    "webcam": "0.7.2",
}
