class Result:
    def __init__(self, ok, detail="", rebuilt=False):
        self.ok = ok
        self.detail = detail
        self.rebuilt = rebuilt


STILL_PLAYING = (
    "WirePlumber was not restarted. Something is still playing. "
    "Quit it and restart WirePlumber, or run this again."
)


def execute(steps, run, log=None):
    rebuilt = False
    note = ""
    for step in steps:
        if step.kind == "wait":
            if log is not None:
                log.record("wait", step.detail)
            return Result(False, step.detail, rebuilt)
        if step.kind == "skip":
            if log is not None:
                log.record("skip", step.detail)
            continue
        rc = run(step)
        if step.argv[:1] == ["limine-mkinitcpio"] and rc == 0:
            rebuilt = True
        if step.kind == "wireplumber" and rc == 2:
            if log is not None:
                log.record("wait", STILL_PLAYING)
            if rebuilt:
                note = STILL_PLAYING
                continue
            return Result(False, STILL_PLAYING, False)
        if log is not None:
            log.record("run" if rc == 0 else "fail", " ".join(step.argv) or step.detail)
        if rc != 0:
            detail = step.detail if step.kind == "confirm-dkms" else (" ".join(step.argv) or step.detail)
            return Result(False, detail, rebuilt)
    return Result(True, note, rebuilt)
