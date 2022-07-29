import logging
import os
from enum import Enum

logger = logging.getLogger("fastqheat.utility")


class BaseEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


def get_cpu_cores_count() -> int:
    try:
        return len(os.sched_getaffinity(0))
    except AttributeError:
        # sched_getaffinity is not available on this OS, fall back to core_count
        if (core_count := os.cpu_count()) is not None:
            return core_count
        else:
            # For now we only use it to pass to fasterq-dump and to pigz external utilities.
            # pigz uses 8 threads by default. fasterq-dump uses 6, so 4 feels like a safe option
            return 4
