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
"""This module contains some constants for the p2p libp2p connection."""
import os
import platform


LIBP2P_NODE_MODULE_NAME = "libp2p_node"

LIBP2P_NODE_MODULE = str(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), LIBP2P_NODE_MODULE_NAME)
)

if platform.system() == "Windows":  # pragma: nocover
    LIBP2P_NODE_MODULE_NAME += ".exe"

LIBP2P_NODE_DEPS_DOWNLOAD_TIMEOUT = 660  # time to download ~66Mb
