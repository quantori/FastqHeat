import os


def get_cpu_cores_count() -> int:
    try:
        return len(os.sched_getaffinity(0))
    except AttributeError:
        # sched_getaffinity is not available on this OS, fall back to cpu_count
        if (cpu_count := os.cpu_count()) is not None:
            return cpu_count
        else:
            return 4
