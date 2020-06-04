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

from packages.fetchai.protocols.oef_search.message import OefSearchMessage


def test_oef_type_string_value():
    """Test the string value of the type."""
    assert (
        str(OefSearchMessage.Performative.REGISTER_SERVICE) == "register_service"
    ), "The string representation must be register_service"
    assert (
        str(OefSearchMessage.Performative.UNREGISTER_SERVICE) == "unregister_service"
    ), "The string representation must be unregister_service"
    assert (
        str(OefSearchMessage.Performative.SEARCH_SERVICES) == "search_services"
    ), "The string representation must be search_services"
    assert (
        str(OefSearchMessage.Performative.OEF_ERROR) == "oef_error"
    ), "The string representation must be oef_error"
    assert (
        str(OefSearchMessage.Performative.SEARCH_RESULT) == "search_result"
    ), "The string representation must be search_result"


def test_oef_error_operation():
    """Test the string value of the error operation."""
    assert (
        str(OefSearchMessage.OefErrorOperation.REGISTER_SERVICE) == "0"
    ), "The string representation must be 0"
    assert (
        str(OefSearchMessage.OefErrorOperation.UNREGISTER_SERVICE) == "1"
    ), "The string representation must be 1"
    assert (
        str(OefSearchMessage.OefErrorOperation.SEARCH_SERVICES) == "2"
    ), "The string representation must be 2"
    assert (
        str(OefSearchMessage.OefErrorOperation.SEND_MESSAGE) == "3"
    ), "The string representation must be 3"
    assert (
        str(OefSearchMessage.OefErrorOperation.OTHER) == "10000"
    ), "The string representation must be 10000"


def test_oef_message_consistency():
    """Tests the consistency of an OefSearchMessage."""

    attribute_foo = Attribute("foo", int, True, "a foo attribute.")
    attribute_bar = Attribute("bar", str, True, "a bar attribute.")
    data_model_foobar = DataModel(
        "foobar", [attribute_foo, attribute_bar], "A foobar data model."
    )
    description_foobar = Description(
        {"foo": 1, "bar": "baz"}, data_model=data_model_foobar
    )
    msg = OefSearchMessage(
        performative=OefSearchMessage.Performative.REGISTER_SERVICE,
        message_id=1,
        service_description=description_foobar,
    )

    with mock.patch.object(OefSearchMessage.Performative, "__eq__", return_value=False):
        assert not msg._is_consistent()


def test_oef_message_oef_error():
    """Tests the OEF_ERROR type of message."""
    msg = OefSearchMessage(
        performative=OefSearchMessage.Performative.OEF_ERROR,
        message_id=1,
        oef_error_operation=OefSearchMessage.OefErrorOperation.SEARCH_SERVICES,
    )
    assert OefSearchMessage(
        performative=OefSearchMessage.Performative.OEF_ERROR,
        message_id=1,
        oef_error_operation=OefSearchMessage.OefErrorOperation.SEARCH_SERVICES,
    ), "Expects an oef message Error!"
    msg_bytes = OefSearchMessage.serializer.encode(msg)
    assert len(msg_bytes) > 0, "Expects the length of bytes not to be Empty"
    deserialized_msg = OefSearchMessage.serializer.decode(msg_bytes)
    assert msg == deserialized_msg, "Expected the deserialized_msg to me equals to msg"
