# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""Constants, utility functions and base classes for ACN p2p_libp2p tests"""


import functools
import inspect
import itertools
import tempfile
from typing import Any, Callable, Type
from unittest import mock

from packages.fetchai.protocols.default.message import DefaultMessage


TIMEOUT = 20
TEMP_LIBP2P_TEST_DIR = tempfile.mkdtemp()
ports = itertools.count(10234)

MockDefaultMessageProtocol = mock.Mock()
MockDefaultMessageProtocol.protocol_id = DefaultMessage.protocol_id
MockDefaultMessageProtocol.protocol_specification_id = (
    DefaultMessage.protocol_specification_id
)


def libp2p_log_on_failure(fn: Callable) -> Callable:
    """Decorate a method running a libp2p node to print its logs in case test fails."""

    @functools.wraps(fn)
    def wrapper(self, *args: Any, **kwargs: Any) -> None:  # type: ignore
        try:
            return fn(self, *args, **kwargs)
        except Exception:
            for log_file in getattr(self, "log_files", []):
                print(f"libp2p log file ======================= {log_file}")
                try:
                    with open(log_file, "r") as f:
                        print(f.read())
                except FileNotFoundError:
                    print("FileNotFoundError")
                print("=======================================")
            raise

    return wrapper


def libp2p_log_on_failure_all(cls: Type) -> Type:
    """Decorate every method of a class with `libp2p_log_on_failure`."""

    for name, fn in inspect.getmembers(cls, inspect.isfunction):
        setattr(cls, name, libp2p_log_on_failure(fn))

    return cls
