"""Cross-platform exclusive advisory lock for append-only JSONL stores.

POSIX uses ``fcntl.flock``. Windows has no ``fcntl``, so it uses
``msvcrt.locking`` on a single sentinel byte far beyond any realistic file
size. Windows byte-range locks are mandatory, so locking real data bytes would
make unlocked readers (``read_text``) fail with ``PermissionError``; locking a
sentinel past EOF keeps the data readable while still serialising writers that
take this lock.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import IO, Any, Iterator

try:  # pragma: no cover - exercised per platform
    import fcntl as _fcntl
except ImportError:  # pragma: no cover - Windows
    _fcntl = None

try:  # pragma: no cover - exercised per platform
    import msvcrt as _msvcrt
except ImportError:  # pragma: no cover - POSIX
    _msvcrt = None

# Offset of the Windows sentinel byte. Kept below 2**31 so it is valid for
# 32-bit offsets as well.
_WINDOWS_LOCK_OFFSET = 0x7FFFFFF0


def _windows_lock(fd: int, mode: int) -> None:
    previous = os.lseek(fd, 0, os.SEEK_CUR)
    try:
        os.lseek(fd, _WINDOWS_LOCK_OFFSET, os.SEEK_SET)
        while True:
            try:
                # LK_LOCK retries for ~10 seconds before raising; loop so the
                # call blocks like flock(LOCK_EX) does on POSIX.
                _msvcrt.locking(fd, mode, 1)
                return
            except OSError:
                if mode == _msvcrt.LK_UNLCK:
                    raise
    finally:
        os.lseek(fd, previous, os.SEEK_SET)


@contextmanager
def exclusive_lock(handle: IO[Any]) -> Iterator[None]:
    """Hold an exclusive lock on ``handle`` for the duration of the block.

    Buffered writes are flushed before the lock is released so that other
    writers never observe a partially written row.
    """
    fd = handle.fileno()
    if _fcntl is not None:
        _fcntl.flock(fd, _fcntl.LOCK_EX)
        try:
            yield
        finally:
            handle.flush()
            _fcntl.flock(fd, _fcntl.LOCK_UN)
        return
    if _msvcrt is not None:
        _windows_lock(fd, _msvcrt.LK_LOCK)
        try:
            yield
        finally:
            handle.flush()
            _windows_lock(fd, _msvcrt.LK_UNLCK)
        return
    # No locking primitive available: fall back to unlocked access.
    yield
