"""Downloaded clones and the camera ranges. Not the installed packages."""

import os
import shutil


def clone_root(home):
    return os.path.join(home, ".local", "share", "macbook81-fixit", "src")


def camera_root(home):
    return os.path.join(home, ".cache", "macbook81-fixit", "camera")


def listing(home):
    found = []
    clones = clone_root(home)
    if os.path.isdir(clones):
        names = sorted(name for name in os.listdir(clones) if os.path.isdir(os.path.join(clones, name)))
        if names:
            found.append((clones, "clones: " + ", ".join(names)))
    camera = camera_root(home)
    if os.path.isdir(camera) and os.listdir(camera):
        found.append((camera, "camera ranges"))
    if not found:
        return "nothing cached", []
    text = "; ".join(note for _path, note in found)
    return text, [path for path, _note in found]


def purge(paths):
    removed = []
    failed = []
    for path in paths:
        if not os.path.lexists(path):
            failed.append(f"{path}: not found")
            continue
        try:
            if os.path.islink(path) or os.path.isfile(path):
                os.remove(path)
            else:
                shutil.rmtree(path)
        except OSError as err:
            failed.append(f"{path}: {err.strerror or err}")
            continue
        removed.append(path)
    return removed, failed
