"""The version fixed into this tree. The screen reads it. It does not ask git."""

import sys
from pathlib import Path


def version_path():
    return Path(__file__).with_name("VERSION")


def read_version(path=None):
    path = Path(path) if path else version_path()
    try:
        text = path.read_text()
    except OSError:
        return ""
    return text.strip().lstrip("v")


def write_version(version, path):
    number = version.strip().lstrip("v")
    Path(path).write_text(number + "\n")


def main(argv):
    if len(argv) != 2:
        print("usage: python3 -m macbook81_fixit.version 0.1.4")
        return 1
    write_version(argv[1], version_path())
    print(read_version())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
