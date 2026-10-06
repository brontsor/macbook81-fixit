class Result:
    def __init__(self, ok, detail=""):
        self.ok = ok
        self.detail = detail


def execute(steps, run, log=None):
    for step in steps:
        if step.kind == "wait":
            if log is not None:
                log.record("wait", step.detail)
            return Result(False, step.detail)
        rc = run(step)
        if log is not None:
            log.record("run" if rc == 0 else "fail", " ".join(step.argv) or step.detail)
        if rc != 0:
            return Result(False, " ".join(step.argv) or step.detail)
    return Result(True, "")
