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

"""This module contains the tests for the OEF protocol."""
# from enum import Enum
# import base64
# import json
from unittest import mock

from aea.protocols.oef.message import OEFMessage
from aea.protocols.oef.models import DataModel, Attribute, Query, Constraint
from oef.query import Eq


def test_oef_type_string_value():
    """Test the string value of the type."""
    assert str(OEFMessage.Type.REGISTER_SERVICE) == "register_service"
    assert str(OEFMessage.Type.UNREGISTER_SERVICE) == "unregister_service"
    assert str(OEFMessage.Type.SEARCH_SERVICES) == "search_services"
    assert str(OEFMessage.Type.SEARCH_AGENTS) == "search_agents"
    assert str(OEFMessage.Type.OEF_ERROR) == "oef_error"
    assert str(OEFMessage.Type.DIALOGUE_ERROR) == "dialogue_error"
    assert str(OEFMessage.Type.SEARCH_RESULT) == "search_result"


def test_oef_message_consistency():
    """Tests the consistency of an OEFMessage."""
    foo_datamodel = DataModel("foo", [Attribute("bar", int, True, "A bar attribute.")])
    msg = OEFMessage(
        oef_type=OEFMessage.Type.SEARCH_AGENTS,
        id=2,
        query=Query([Constraint("bar", Eq(1))], model=foo_datamodel)
    )
    assert msg.check_consistency()
    with mock.patch("aea.protocols.oef.message.OEFMessage.Type") as mock_type_enum:
        mock_type_enum.SEARCH_AGENTS.value = "unknown"
        assert not msg.check_consistency()

# def test_oef_message_OEF_ERROR():
#     """Tests the OEF_ERROR msg."""
#     foo_datamodel = DataModel("boo", [Attribute("far", int, False, "A far attribute.")])
#     msg = OEFMessage(oef_type = OEFMessage.Type.OEF_ERROR,
#                     id = 23,
#                     query = Query([], model=foo_datamodel)
#     )
#     with mock.patch("aea.protocols.oef.message.OEFMessage.OEF_ERROR_Operation") as mock_type_enum:
#         mock_type_enum.register_service = 0
#         assert not msg.check_consistency()

# def test_oef_message_OEF_DIALOGUE_ERROR():
#     """Tests the OEF_DIALOGUE_ERROR msg"""
#     foo_datamodel = DataModel("foo", [Attribute("bar", int, True, "A bar attribute.")])
#     msg = OEFMessage(
#         oef_type=OEFMessage.Type.DIALOGUE_ERROR,
#         id=2,
#         query=Query([Constraint("bar", Eq(1))],
#         model=foo_datamodel)
#     )
#     assert msg.check_consistency()
