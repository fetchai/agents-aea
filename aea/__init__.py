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

"""Contains the AEA package."""

import inspect
import os

from packaging.version import Version

import aea.crypto  # triggers registry population
from aea.__version__ import (
    __author__,
    __copyright__,
    __description__,
    __license__,
    __title__,
    __url__,
    __version__,
)
from aea.crypto.plugin import load_all_plugins


AEA_DIR = os.path.dirname(inspect.getfile(inspect.currentframe()))  # type: ignore

load_all_plugins()


def get_current_aea_version() -> Version:
    """Get current version."""
    return Version(__version__)
