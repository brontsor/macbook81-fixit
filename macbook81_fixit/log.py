import os
from datetime import datetime


class ActionLog:
    def __init__(self, path):
        self.path = path

    def record(self, action, detail):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        stamp = datetime.now().isoformat(timespec="seconds")
        line = f"{stamp} {action} {detail}\n"
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(line)
