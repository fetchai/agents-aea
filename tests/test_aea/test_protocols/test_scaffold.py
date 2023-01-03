# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2022 Fetch.AI Limited
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

"""This module contains the tests for the Scaffold protocol."""

import pytest

from aea.protocols.scaffold.message import MyScaffoldMessage


def test_scaffold_message():
    """Testing the creation of a scaffold message."""
    with pytest.raises(NotImplementedError):
        msg = MyScaffoldMessage(performative="")
        assert not msg._check_consistency(), "Not Implemented Error"
