import os
import subprocess

from macbook81_fixit import catalog


def cache_dir(home):
    return os.path.join(home, ".cache", "macbook81-fixit", "camera")


def start(home):
    dest = cache_dir(home)
    os.makedirs(dest, exist_ok=True)
    procs = []
    for index, rng in enumerate(catalog.APPLE_RANGES):
        path = os.path.join(dest, f"range-{index}")
        if os.path.isfile(path) and os.path.getsize(path) > 0:
            continue
        procs.append(subprocess.Popen(
            ["curl", "-fsSL", "--retry", "2", "-r", rng, "-o", path, catalog.APPLE_CAMERA_URL],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ))
    return procs


def state(home):
    dest = cache_dir(home)
    present = 0
    for index in range(len(catalog.APPLE_RANGES)):
        path = os.path.join(dest, f"range-{index}")
        if os.path.isfile(path) and os.path.getsize(path) > 0:
            present += 1
    if present == len(catalog.APPLE_RANGES):
        return "cached"
    if present:
        return "downloading"
    return "not-downloaded"
