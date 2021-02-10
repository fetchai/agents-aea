#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Patch of 'fnctl' to make it compatible with Windows."""

import os
from typing import IO


# needs win32all to work on Windows
if os.name == "nt":  # pragma: nocover  # cause platform dependent!
    import pywintypes  # pylint: disable=import-error
    import win32con  # pylint: disable=import-error
    import win32file  # pylint: disable=import-error

    LOCK_EX = win32con.LOCKFILE_EXCLUSIVE_LOCK
    LOCK_SH = 0  # the default
    LOCK_NB = win32con.LOCKFILE_FAIL_IMMEDIATELY
    __overlapped = pywintypes.OVERLAPPED()

    def lock(file: IO, flags: int) -> None:
        """Lock a file with flags."""
        hfile = win32file._get_osfhandle(  # pylint: disable=protected-access
            file.fileno()
        )
        win32file.LockFileEx(hfile, flags, 0, 0xFFFF0000, __overlapped)

    def unlock(file: IO) -> None:
        """Unlock a file."""
        hfile = win32file._get_osfhandle(  # pylint: disable=protected-access
            file.fileno()
        )
        win32file.UnlockFileEx(hfile, 0, 0xFFFF0000, __overlapped)


elif os.name == "posix":  # pragma: nocover  # cause platform dependent!
    import fcntl
    from fcntl import LOCK_EX, LOCK_NB, LOCK_SH  # noqa # pylint: disable=unused-import

    def lock(file: IO, flags: int) -> None:
        """Lock a file with flags."""
        fcntl.flock(file.fileno(), flags)

    def unlock(file: IO) -> None:
        """Unlock a file."""
        fcntl.flock(file.fileno(), fcntl.LOCK_UN)


else:  # pragma: nocover
    raise RuntimeError("This module only works for nt and posix platforms")
