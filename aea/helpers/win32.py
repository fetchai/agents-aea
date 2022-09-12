# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2020 Fetch.AI Limited
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
"""Helpers for Windows."""
import ctypes
import logging
import platform


_default_logger = logging.getLogger(__name__)


def enable_ctrl_c_support() -> None:  # pragma: no cover
    """Enable ctrl+c support for aea.cli command to be tested on windows platform."""
    if platform.system() != "Windows":
        return

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore

    if not kernel32.SetConsoleCtrlHandler(None, False):
        _default_logger.debug(f"SetConsoleCtrlHandler Error: {ctypes.get_last_error()}")  # type: ignore
