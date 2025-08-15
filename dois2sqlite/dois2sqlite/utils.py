import os


def get_cpu_count() -> int | None:
    return os.cpu_count() or 1
