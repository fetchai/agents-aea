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
from unittest import mock


from aea.helpers.search.models import (
    Attribute,
    DataModel,
    Description,
)

from packages.fetchai.protocols.oef.message import OEFMessage
from packages.fetchai.protocols.oef.serialization import OEFSerializer


def test_oef_type_string_value():
    """Test the string value of the type."""
    assert (
        str(OEFMessage.Type.REGISTER_SERVICE) == "register_service"
    ), "The string representation must be register_service"
    assert (
        str(OEFMessage.Type.UNREGISTER_SERVICE) == "unregister_service"
    ), "The string representation must be unregister_service"
    assert (
        str(OEFMessage.Type.REGISTER_AGENT) == "register_agent"
    ), "The string representation must be register_agent"
    assert (
        str(OEFMessage.Type.UNREGISTER_AGENT) == "unregister_agent"
    ), "The string representation must be unregister_agent"
    assert (
        str(OEFMessage.Type.SEARCH_SERVICES) == "search_services"
    ), "The string representation must be search_services"
    assert (
        str(OEFMessage.Type.SEARCH_AGENTS) == "search_agents"
    ), "The string representation must be search_agents"
    assert (
        str(OEFMessage.Type.OEF_ERROR) == "oef_error"
    ), "The string representation must be oef_error"
    assert (
        str(OEFMessage.Type.DIALOGUE_ERROR) == "dialogue_error"
    ), "The string representation must be dialogue_error"
    assert (
        str(OEFMessage.Type.SEARCH_RESULT) == "search_result"
    ), "The string representation must be search_result"


def test_oef_error_operation():
    """Test the string value of the error operation."""
    assert (
        str(OEFMessage.OEFErrorOperation.REGISTER_SERVICE) == "0"
    ), "The string representation must be 0"
    assert (
        str(OEFMessage.OEFErrorOperation.UNREGISTER_SERVICE) == "1"
    ), "The string representation must be 1"
    assert (
        str(OEFMessage.OEFErrorOperation.SEARCH_SERVICES) == "2"
    ), "The string representation must be 2"
    assert (
        str(OEFMessage.OEFErrorOperation.SEARCH_SERVICES_WIDE) == "3"
    ), "The string representation must be 3"
    assert (
        str(OEFMessage.OEFErrorOperation.SEARCH_AGENTS) == "4"
    ), "The string representation must be 4"
    assert (
        str(OEFMessage.OEFErrorOperation.SEND_MESSAGE) == "5"
    ), "The string representation must be 5"
    assert (
        str(OEFMessage.OEFErrorOperation.REGISTER_AGENT) == "6"
    ), "The string representation must be 6"
    assert (
        str(OEFMessage.OEFErrorOperation.UNREGISTER_AGENT) == "7"
    ), "The string representation must be 7"
    assert (
        str(OEFMessage.OEFErrorOperation.OTHER) == "10000"
    ), "The string representation must be 10000"


def test_oef_message_consistency():
    """Tests the consistency of an OEFMessage."""

    attribute_foo = Attribute("foo", int, True, "a foo attribute.")
    attribute_bar = Attribute("bar", str, True, "a bar attribute.")
    data_model_foobar = DataModel(
        "foobar", [attribute_foo, attribute_bar], "A foobar data model."
    )
    description_foobar = Description(
        {"foo": 1, "bar": "baz"}, data_model=data_model_foobar
    )
    msg = OEFMessage(
        type=OEFMessage.Type.REGISTER_AGENT,
        id=0,
        agent_description=description_foobar,
        agent_id="address",
    )

    with mock.patch.object(OEFMessage.Type, "__eq__", return_value=False):
        assert not msg._check_consistency()


def test_oef_message_oef_error():
    """Tests the OEF_ERROR type of message."""
    msg = OEFMessage(
        type=OEFMessage.Type.OEF_ERROR,
        id=0,
        operation=OEFMessage.OEFErrorOperation.SEARCH_AGENTS,
    )
    assert OEFMessage(
        type=OEFMessage.Type.OEF_ERROR,
        id=0,
        operation=OEFMessage.OEFErrorOperation.SEARCH_AGENTS,
    ), "Expects an oef message Error!"
    msg_bytes = OEFSerializer().encode(msg)
    assert len(msg_bytes) > 0, "Expects the length of bytes not to be Empty"
    deserialized_msg = OEFSerializer().decode(msg_bytes)
    assert msg == deserialized_msg, "Expected the deserialized_msg to me equals to msg"


def test_oef_message_dialoge_error():
    """Tests the OEFMEssage of type DialogueError."""
    assert OEFMessage(
        type=OEFMessage.Type.DIALOGUE_ERROR, id=0, dialogue_id=1, origin="myKey"
    ), "Could not create the message of type DialogueError"
