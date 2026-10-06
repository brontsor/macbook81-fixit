import os
import shutil
import subprocess


def live_run(step):
    if step.kind == "edit":
        return _edit_version(step.cwd)
    if step.kind == "write":
        return _write_root(step.argv[-1], step.detail)
    if step.argv[:2] == ["git", "clone"]:
        return _clone(step.argv[2], step.argv[3])
    argv = list(step.argv)
    if step.sudo:
        prefix = ["sudo"]
        if step.env:
            prefix += ["env", *[f"{key}={value}" for key, value in step.env.items()]]
        argv = prefix + argv
        return _dkms_rc(step.argv, subprocess.run(argv, cwd=step.cwd).returncode)
    env = os.environ.copy()
    env.update(step.env)
    return _dkms_rc(step.argv, subprocess.run(argv, cwd=step.cwd, env=env).returncode)


def _dkms_rc(argv, rc):
    if rc == 0 or argv[:1] != ["dkms"]:
        return rc
    text = subprocess.run(["dkms", "status"], capture_output=True, text=True).stdout
    if "facetimehd/0.7.2" in text and "installed" in text:
        print("facetimehd/0.7.2 is already installed")
        return 0
    return rc


def _clone(url, dest):
    if os.path.isdir(os.path.join(dest, ".git")):
        return 0
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    rc = subprocess.run(["git", "clone", url, dest]).returncode
    if rc == 0:
        return 0
    if shutil.which("gh") and url.startswith("https://github.com/"):
        slug = url.removeprefix("https://github.com/").removesuffix(".git")
        print(f"git clone failed. Trying gh repo clone {slug}")
        return subprocess.run(["gh", "repo", "clone", slug, dest]).returncode
    return rc


def _edit_version(cwd):
    path = os.path.join(cwd, "dkms.conf")
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    updated = text.replace("PACKAGE_VERSION=0.7.0.1", "PACKAGE_VERSION=0.7.2")
    if "PACKAGE_VERSION=0.7.2" not in updated:
        print(f"unexpected PACKAGE_VERSION in {path}")
        return 1
    if updated != text:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(updated)
    return 0


def _write_root(path, content):
    parent = os.path.dirname(path)
    if subprocess.run(["sudo", "mkdir", "-p", parent]).returncode != 0:
        return 1
    proc = subprocess.run(["sudo", "tee", path], input=content.encode(), stdout=subprocess.DEVNULL)
    if proc.returncode != 0:
        return proc.returncode
    return subprocess.run(["sudo", "chmod", "644", path]).returncode
