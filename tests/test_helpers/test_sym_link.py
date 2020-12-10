# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
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
"""This module contains the tests for the sym link module."""

import os
import shutil
import tempfile
from pathlib import Path

from aea.helpers.sym_link import create_symlink


def test_create_symlink():
    """Test create_symlink method."""
    t = Path(tempfile.mkdtemp())
    cwd = os.getcwd()
    os.chdir(t)
    try:
        link = Path(os.path.join(t, "here"))
        target = Path(os.path.join(t, "test", "nested"))
        os.makedirs(target)
        create_symlink(link, target, t)
        assert os.path.islink(link)
        assert os.readlink("here") == os.path.join("test", "nested")
    finally:
        os.chdir(cwd)
        shutil.rmtree(t)
