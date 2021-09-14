# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2021 Fetch.AI Limited
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
"""This module contains utility methods for ipfs helpers."""
import contextlib
import os
import sys
from typing import Generator


@contextlib.contextmanager
def _protobuf_python_implementation() -> Generator:
    """
    Makes a context manager to force usage of the python implementation of the protobuf modules.

    By default cpp version of the protobuf library is loaded.
    This library does not provide all the needed tools to customize fields serialization order.
    Python verrsion allows to use internal methods of the protobuf objects to serialize.
    Custom serializations is required cause ipfs uses own version to serialize data to calculate data hash.
    # noqa: DAR301
    """
    PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION = "PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"
    # unload modules
    saved_mods = {}
    for mod_name, mod in list(sys.modules.items()):
        if mod_name.startswith("google.protobuf"):
            saved_mods[mod_name] = mod
            del sys.modules[mod_name]

    prev_os_env = os.environ.get(PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION)
    os.environ[PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION] = "python"

    yield

    if prev_os_env is None:  # pragma: nocover
        del os.environ[PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION]
    else:  # pragma: nocover
        os.environ[PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION] = prev_os_env

    for mod_name in list(sys.modules.keys()):
        if mod_name.startswith("google.protobuf"):
            del sys.modules[mod_name]

    for mod_name, mod in saved_mods.items():
        sys.modules[mod_name] = mod
