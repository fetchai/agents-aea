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
# from unittest import mock

from aea.protocols.oef.message import OEFMessage
from aea.protocols.oef.models import DataModel, Attribute, Query, Constraint, ConstraintType, Description
from aea.protocols.oef.serialization import OEFSerializer


def test_oef_type_string_value():
    """Test the string value of the type."""
    assert str(OEFMessage.Type.REGISTER_SERVICE) == "register_service",\
        "The string representation must be register_service"
    assert str(OEFMessage.Type.UNREGISTER_SERVICE) == "unregister_service",\
        "The string representation must be unregister_service"
    assert str(OEFMessage.Type.REGISTER_AGENT) == "register_agent",\
        "The string representation must be register_agent"
    assert str(OEFMessage.Type.UNREGISTER_AGENT) == "unregister_agent",\
        "The string representation must be unregister_agent"
    assert str(OEFMessage.Type.SEARCH_SERVICES) == "search_services",\
        "The string representation must be search_services"
    assert str(OEFMessage.Type.SEARCH_AGENTS) == "search_agents",\
        "The string representation must be search_agents"
    assert str(OEFMessage.Type.OEF_ERROR) == "oef_error",\
        "The string representation must be oef_error"
    assert str(OEFMessage.Type.DIALOGUE_ERROR) == "dialogue_error",\
        "The string representation must be dialogue_error"
    assert str(OEFMessage.Type.SEARCH_RESULT) == "search_result",\
        "The string representation must be search_result"


def test_oef_message_consistency():
    """Tests the consistency of an OEFMessage."""
    foo_datamodel = DataModel("foo", [Attribute("bar", int,
                                                True, "A bar attribute.")])
    msg = OEFMessage(
        type=OEFMessage.Type.SEARCH_AGENTS,
        id=2,
        query=Query([Constraint("bar", ConstraintType("==", 1))], model=foo_datamodel)
    )
    assert msg.check_consistency(), "We expect the consistency to return TRUE"

    attribute_foo = Attribute("foo", int, True, "a foo attribute.")
    attribute_bar = Attribute("bar", str, True, "a bar attribute.")
    data_model_foobar = DataModel("foobar", [attribute_foo, attribute_bar], "A foobar data model.")
    description_foobar = Description({"foo": 1, "bar": "baz"}, data_model=data_model_foobar)
    msg = OEFMessage(type=OEFMessage.Type.REGISTER_AGENT,
                     id=0,
                     agent_description=description_foobar,
                     agent_id="address")
    assert msg.check_consistency()

    msg = OEFMessage(type=OEFMessage.Type.UNREGISTER_AGENT,
                     id=0,
                     agent_description=description_foobar,
                     agent_id="address")

    assert msg.check_consistency()


def test_oef_message_oef_error():
    """Tests the OEF_ERROR type of message."""
    msg = OEFMessage(type=OEFMessage.Type.OEF_ERROR, id=0,
                     operation=OEFMessage.OEFErrorOperation.SEARCH_AGENTS)
    assert OEFMessage(type=OEFMessage.Type.OEF_ERROR, id=0,
                      operation=OEFMessage.OEFErrorOperation.SEARCH_AGENTS),\
        "Expects an oef message Error!"
    msg_bytes = OEFSerializer().encode(msg)
    assert len(msg_bytes) > 0,\
        "Expects the length of bytes not to be Empty"
    deserialized_msg = OEFSerializer().decode(msg_bytes)
    assert msg == deserialized_msg,\
        "Expected the deserialized_msg to me equals to msg"


def test_oef_message_dialoge_error():
    """Tests the OEFMEssage of type DialogueError."""
    assert OEFMessage(type=OEFMessage.Type.DIALOGUE_ERROR,
                      id=0,
                      dialogue_id=1,
                      origin="myKey"),\
        "Could not create the message of type DialogueError"
