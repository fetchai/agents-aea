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

"""This module contains the tests of the soef connection module."""

import logging
import time
from threading import Thread

from aea.configurations.base import ProtocolId
from aea.crypto.fetchai import FetchAICrypto
from aea.helpers.search.models import (
    Attribute,
    Constraint,
    ConstraintType,
    DataModel,
    Description,
    Location,
    Query,
)
from aea.mail.base import Envelope
from aea.multiplexer import Multiplexer

from packages.fetchai.connections.soef.connection import SOEFConnection
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.oef_search.serialization import OefSearchSerializer

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)


def test_soef():

    # First run OEF in a separate terminal: python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
    crypto = FetchAICrypto()

    # create the connection and multiplexer objects
    soef_connection = SOEFConnection(
        api_key="TwiCIriSl0mLahw17pyqoA",
        soef_addr="soef.fetch.ai",
        soef_port=9002,
        address=crypto.address,
    )
    multiplexer = Multiplexer([soef_connection])
    try:
        # Set the multiplexer running in a different thread
        t = Thread(target=multiplexer.connect)
        t.start()

        time.sleep(3.0)

        # register a service with location
        attr_service_name = Attribute(
            "service_name", str, True, "The name of the service."
        )
        attr_location = Attribute(
            "location", Location, True, "The location where the service is provided."
        )
        service_location_model = DataModel(
            "location_service",
            [attr_service_name, attr_location],
            "A data model to describe location of a service.",
        )
        service_name = "train"
        service_location = Location(52.2057092, 2.1183431)
        service_instance = {"service_name": service_name, "location": service_location}
        service_description = Description(
            service_instance, data_model=service_location_model
        )
        message = OefSearchMessage(
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            service_description=service_description,
        )
        message_b = OefSearchSerializer().encode(message)
        envelope = Envelope(
            to="soef",
            sender=crypto.address,
            protocol_id=ProtocolId.from_str("fetchai/oef_search:0.1.0"),
            message=message_b,
        )
        logger.info(
            "Registering service={} at location=({},{}) by agent={}".format(
                service_name,
                service_location.latitude,
                service_location.longitude,
                crypto.address,
            )
        )
        multiplexer.put(envelope)

        # find agents near the previously registered service
        radius = 0.1
        matches_my_service_name = Constraint(
            "service_name", ConstraintType("==", service_name)
        )
        close_to_my_service = Constraint(
            "location", ConstraintType("distance", (service_location, radius))
        )
        closeness_query = Query(
            [matches_my_service_name, close_to_my_service], model=service_location_model
        )
        message = OefSearchMessage(
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            query=closeness_query,
        )
        message_b = OefSearchSerializer().encode(message)
        envelope = Envelope(
            to="soef",
            sender=crypto.address,
            protocol_id=ProtocolId.from_str("fetchai/oef_search:0.1.0"),
            message=message_b,
        )
        logger.info(
            "Searching for agents in radius={} of service={} at location=({},{})".format(
                radius,
                service_name,
                service_location.latitude,
                service_location.longitude,
            )
        )
        multiplexer.put(envelope)
        time.sleep(4.0)

        # check for search results
        envelope = multiplexer.get()
        message = OefSearchSerializer().decode(envelope.message)
        assert len(message.agents) >= 0

    finally:
        # Shut down the multiplexer
        multiplexer.disconnect()
        t.join()
