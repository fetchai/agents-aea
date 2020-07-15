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
"""This test module contains the tests for the OEF serializer."""

from aea.helpers.search.models import (
    Attribute,
    Constraint,
    ConstraintType,
    DataModel,
    Description,
    Location,
    Query,
)

from packages.fetchai.connections.oef.object_translator import OEFObjectTranslator
from packages.fetchai.protocols.oef_search.message import OefSearchMessage


def test_oef_serialization_description():
    """Testing the serialization of the OEF."""
    foo_datamodel = DataModel(
        "foo",
        [
            Attribute("bar", int, True, "A bar attribute."),
            Attribute("location", Location, True, "A location attribute."),
        ],
    )
    desc = Description(
        {"bar": 1, "location": Location(10.0, 10.0)}, data_model=foo_datamodel
    )
    msg = OefSearchMessage(
        performative=OefSearchMessage.Performative.REGISTER_SERVICE,
        dialogue_reference=(str(1), ""),
        service_description=desc,
    )
    msg_bytes = OefSearchMessage.serializer.encode(msg)
    assert len(msg_bytes) > 0
    recovered_msg = OefSearchMessage.serializer.decode(msg_bytes)
    assert recovered_msg == msg


def test_oef_object_transator():
    """Test oef description and description tranlations."""
    foo_datamodel = DataModel(
        "foo",
        [
            Attribute("bar", int, True, "A bar attribute."),
            Attribute("location", Location, True, "A location attribute."),
        ],
    )
    desc = Description(
        {"bar": 1, "location": Location(10.0, 10.0)}, data_model=foo_datamodel
    )
    oef_desc = OEFObjectTranslator.to_oef_description(desc)
    new_desc = OEFObjectTranslator.from_oef_description(oef_desc)
    assert desc.values["location"] == new_desc.values["location"]


def test_oef_serialization_query():
    """Testing the serialization of the OEF."""
    query = Query([Constraint("foo", ConstraintType("==", "bar"))], model=None)
    msg = OefSearchMessage(
        performative=OefSearchMessage.Performative.SEARCH_SERVICES,
        dialogue_reference=(str(1), ""),
        query=query,
    )
    msg_bytes = OefSearchMessage.serializer.encode(msg)
    assert len(msg_bytes) > 0
    recovered_msg = OefSearchMessage.serializer.decode(msg_bytes)
    assert recovered_msg == msg
