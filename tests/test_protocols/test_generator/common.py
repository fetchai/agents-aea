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
"""This module contains utility code for the test_generator modules."""
import os

from tests.conftest import ROOT_DIR


T_PROTOCOL_NAME = "t_protocol"
PATH_TO_T_PROTOCOL_SPECIFICATION = os.path.join(
    ROOT_DIR, "tests", "data", "sample_specification.yaml"
)
PATH_TO_T_PROTOCOL = os.path.join(
    ROOT_DIR, "tests", "data", "generator", T_PROTOCOL_NAME
)


def black_is_not_installed(*args, **kwargs):
    """Check black is not installed."""
    return not args[0] == "black"
