from __future__ import annotations

import concurrent.futures
from typing import Callable, TypeVar

T = TypeVar("T")


def run_with_timeout(func: Callable[[], T], timeout_seconds: float) -> T:
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(func)
        try:
            return future.result(timeout=timeout_seconds)
        except concurrent.futures.TimeoutError as exc:
            raise TimeoutError(
                f"Operation timed out after {timeout_seconds}s"
            ) from exc
