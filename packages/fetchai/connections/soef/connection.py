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

"""Extension to the Simple OEF and OEF Python SDK."""

import asyncio
import logging
from asyncio import CancelledError
from typing import Dict, List, Optional, Set, Tuple, cast
from urllib import parse

from defusedxml import ElementTree as ET

import requests

from aea.configurations.base import ConnectionConfig, PublicId
from aea.connections.base import Connection
from aea.helpers.search.models import (
    Constraint,
    ConstraintTypes,
    Description,
    Location,
    Query,
)
from aea.mail.base import Address, Envelope

from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.oef_search.serialization import OefSearchSerializer

logger = logging.getLogger("aea.packages.fetchai.connections.oef")

TARGET = 0
MESSAGE_ID = 1
RESPONSE_TARGET = MESSAGE_ID
RESPONSE_MESSAGE_ID = MESSAGE_ID + 1
STUB_MESSAGE_ID = 0
STUB_DIALOGUE_ID = 0
DEFAULT_OEF = "default_oef"
PUBLIC_ID = PublicId.from_str("fetchai/soef:0.1.0")


class SOEFChannel:
    """The OEFChannel connects the OEF Agent with the connection."""

    def __init__(
        self,
        address: Address,
        api_key: str,
        soef_addr: str,
        soef_port: int,
        excluded_protocols: Set[PublicId],
        restricted_to_protocols: Set[PublicId],
    ):
        """
        Initialize.

        :param address: the address of the agent.
        :param api_key: the SOEF API key.
        :param soef_addr: the SOEF IP address.
        :param soef_port: the SOEF port.
        :param excluded_protocols: the protocol ids excluded
        :param restricted_to_protocols: the protocol ids restricted to
        """
        self.address = address
        self.api_key = api_key
        self.soef_addr = soef_addr
        self.soef_port = soef_port
        self.base_url = "http://{}:{}".format(soef_addr, soef_port)
        self.excluded_protocols = excluded_protocols
        self.restricted_to_protocols = restricted_to_protocols
        self.search_id = 0
        self.search_id_to_dialogue_reference = {}  # type: Dict[int, Tuple[str, str]]
        self.service_name_to_page_address = {}  # type: Dict[str, str]
        self.in_queue = None  # type: Optional[asyncio.Queue]

    def send(self, envelope: Envelope) -> None:
        """
        Send message handler.

        :param envelope: the message.
        :return: None
        """
        if self.excluded_protocols is not None:
            if envelope.protocol_id in self.excluded_protocols:
                logger.error(
                    "This envelope cannot be sent with the soef connection: protocol_id={}".format(
                        envelope.protocol_id
                    )
                )
                raise ValueError("Cannot send message.")
        if envelope.protocol_id in self.restricted_to_protocols:
            self.send_soef_message(envelope)
        else:
            raise ValueError(
                "Cannot send message, invalid protocol: {}".format(envelope.protocol_id)
            )

    def send_soef_message(self, envelope: Envelope) -> None:
        """
        Send soef message handler.

        :param envelope: the message.
        :return: None
        """
        oef_message = OefSearchSerializer().decode(envelope.message)
        oef_message = cast(OefSearchMessage, oef_message)
        if oef_message.performative == OefSearchMessage.Performative.REGISTER_SERVICE:
            service_description = oef_message.service_description
            self.register_service(service_description)
        elif (
            oef_message.performative == OefSearchMessage.Performative.UNREGISTER_SERVICE
        ):
            service_name = oef_message.service_description.values["service_name"]
            self._try_unregister_service(service_name)
        elif oef_message.performative == OefSearchMessage.Performative.SEARCH_SERVICES:
            query = oef_message.query
            dialogue_reference = oef_message.dialogue_reference[0]
            self.search_id += 1
            self.search_id_to_dialogue_reference[self.search_id] = (
                dialogue_reference,
                str(self.search_id),
            )
            self.search_services(self.search_id, query)
        else:
            raise ValueError("OEF request not recognized.")

    def register_service(self, service_description: Description) -> None:
        """
        Register a service on the SOEF.

        :param service_name: the name of the service
        :param service_location: the location of the service
        """
        if self._is_compatible_description(service_description):
            service_name = service_description.values["service_name"]
            service_location = service_description.values["location"]
            # TODO: atm agent == service; there is only one service registrable per agent
            if service_name in self.service_name_to_page_address:
                unique_page_address = self.service_name_to_page_address[
                    service_name
                ]  # type: Optional[str]
            else:
                unique_page_address = self._register_service(service_name)
            if unique_page_address is not None:
                self._set_location(service_location, unique_page_address)
        else:
            logger.warning(
                "Service description incompatible with SOEF: values={}".format(
                    service_description.values
                )
            )

    @staticmethod
    def _is_compatible_description(service_description: Description) -> bool:
        """
        Check if a description is compatible with the soef.

        :param service_description: the service description
        :return: bool
        """
        is_compatible = (
            type(service_description.values.get("service_name", None)) == str
            and type(service_description.values.get("location", None)) == Location
        )
        return is_compatible

    def _register_service(self, service_name: str) -> Optional[str]:
        """
        Register a service.

        :param service_name: the service name
        :return: the unique page address
        """
        logger.debug("Applying to SOEF lobby with address={}".format(self.address))
        url = parse.urljoin(self.base_url, "register")
        params = {
            "api_key": self.api_key,
            "chain_identifier": "fetchai",
            "address": self.address,
            "declared_name": service_name,
        }
        try:
            response = requests.get(url=url, params=params)
            logger.debug("Response: {}".format(response.text))
            root = ET.fromstring(response.text)
            logger.debug("Root tag: {}".format(root.tag))
            unique_page_address = ""
            unique_token = ""  # nosec
            for child in root:
                logger.debug(
                    "Child tag={}, child attrib={}, child text={}".format(
                        child.tag, child.attrib, child.text
                    )
                )
                if "page_address" == child.tag and child.text is not None:
                    unique_page_address = child.text
                if "token" == child.tag and child.text is not None:
                    unique_token = child.text
            if len(unique_page_address) > 0 and len(unique_token) > 0:
                logger.debug("Registering service {}".format(service_name))
                url = parse.urljoin(self.base_url, unique_page_address)
                params = {"token": unique_token, "command": "acknowledge"}
                response = requests.get(url=url, params=params)
                if "<response><success>1</success></response>" in response.text:
                    logger.debug("Service registration SUCCESS")
                    self.service_name_to_page_address[
                        service_name
                    ] = unique_page_address
                    return unique_page_address
                else:
                    raise ValueError(
                        "Service registration error - acknowledge not accepted"
                    )
            else:
                raise ValueError(
                    "Service registration error - page address or token not received"
                )
        except Exception as e:
            logger.error("Exception when interacting with SOEF: {}".format(e))
            return None

    def _set_location(
        self, service_location: Location, unique_page_address: str
    ) -> None:
        """
        Set the location.

        :param service_location: the service location
        :param unique_page_address: the page address where the service is registered
        """
        try:
            latitude = service_location.latitude
            longitude = service_location.longitude

            logger.debug(
                "Registering position lat={}, long={}".format(latitude, longitude)
            )
            url = parse.urljoin(self.base_url, unique_page_address)
            params = {
                "longitude": str(longitude),
                "latitude": str(latitude),
                "command": "set_position",
            }
            response = requests.get(url=url, params=params)
            if "<response><success>1</success></response>" in response.text:
                logger.debug("Location registration SUCCESS")
            else:
                raise ValueError("Location registration error.")
        except Exception as e:
            logger.error("Exception when interacting with SOEF: {}".format(e))

    def _try_unregister_service(self, service_name: str):
        # TODO: add keep alive background tasks which ping the SOEF until the service is deregistered
        if service_name in self.service_name_to_page_address.keys():
            unique_page_address = self.service_name_to_page_address[service_name]
            url = parse.urljoin(self.base_url, unique_page_address)
            params = {"command": "unregister"}
            try:
                response = requests.get(url=url, params=params)
                if "<response><message>Goodbye!</message></response>" in response.text:
                    logger.info("Successfully unregistered from the s-oef.")
            except Exception as e:
                logger.error(
                    "Something went wrong cannot unregister the service! {}".format(e)
                )
        else:
            logger.error(
                "The service is not registered to the simple OEF. Cannot unregister."
            )

    def disconnect(self):
        for key in self.service_name_to_page_address.keys():
            self._try_unregister_service(key)

    def search_services(self, search_id: int, query: Query) -> None:
        """
        Search services on the SOEF.

        :param search_id: the message id
        :param oef_query: the oef query
        """
        if self._is_compatible_query(query):
            constraints = [cast(Constraint, c) for c in query.constraints]
            constraint_distance = [
                c
                for c in constraints
                if c.constraint_type.type == ConstraintTypes.DISTANCE
            ][0]
            constraint_name = [
                c
                for c in constraints
                if c.constraint_type.type == ConstraintTypes.EQUAL
            ][0]
            service_location, radius = constraint_distance.constraint_type.value
            service_name = constraint_name.constraint_type.value
            # TODO: atm agent == service; there is only one service registrable per agent
            if service_name in self.service_name_to_page_address:
                unique_page_address = self.service_name_to_page_address[
                    service_name
                ]  # type: Optional[str]
            else:
                # if we are not yet registered with our service we first need to register it
                unique_page_address = self._register_service(service_name)
                if unique_page_address is not None:
                    self._set_location(service_location, unique_page_address)
            if unique_page_address is not None:
                self._search_range(unique_page_address, radius, service_name)
        else:
            logger.warning(
                "Service query incompatible with SOEF: constraints={}".format(
                    query.constraints
                )
            )

    @staticmethod
    def _is_compatible_query(query: Query) -> bool:
        """
        Check if a query is compatible with the soef.

        :return: bool
        """
        is_compatible = True
        is_compatible = is_compatible and len(query.constraints) == 2
        constraint_one = query.constraints[0]
        constraint_two = query.constraints[1]
        is_compatible = (
            is_compatible
            and type(constraint_one) == Constraint
            and type(constraint_two) == Constraint
        )
        if is_compatible:
            constraint_one = cast(Constraint, constraint_one)
            constraint_two = cast(Constraint, constraint_two)
            is_compatible = is_compatible and (
                set([constraint_one.attribute_name, constraint_two.attribute_name])
                == set(["location", "service_name"])
                and set(
                    [
                        constraint_one.constraint_type.type,
                        constraint_two.constraint_type.type,
                    ]
                )
                == set([ConstraintTypes.EQUAL, ConstraintTypes.DISTANCE])
            )
        return is_compatible

    def _search_range(
        self, unique_page_address: str, radius: float, service_name: str
    ) -> None:
        """
        Search services on the SOEF.
        """
        assert self.in_queue is not None, "Inqueue not set!"
        try:
            logger.debug(
                "Searching in radius={} of service={}".format(radius, service_name)
            )
            url = parse.urljoin(self.base_url, unique_page_address)
            params = {
                "range_in_km": str(radius),
                "command": "find_around_me",
            }
            response = requests.get(url=url, params=params)
            root = ET.fromstring(response.text)
            agents = {
                "fetchai": {},
                "cosmos": {},
                "ethereum": {},
            }  # type: Dict[str, Dict[str, str]]
            agents_l = []  # type: List[str]
            for agent in root.findall(path=".//agent"):
                chain_identifier = ""
                for identities in agent.findall("identities"):
                    for identity in identities.findall("identity"):
                        for (
                            chain_identifier_key,
                            chain_identifier_name,
                        ) in identity.items():
                            if chain_identifier_key == "chain_identifier":
                                chain_identifier = chain_identifier_name
                                agent_address = identity.text
                agent_distance = agent.find("range_in_km").text
                if chain_identifier in agents:
                    agents[chain_identifier][agent_address] = agent_distance
                    agents_l.append(agent_address)
            if root.tag == "response":
                logger.debug("Search SUCCESS")
                message = OefSearchMessage(
                    performative=OefSearchMessage.Performative.SEARCH_RESULT,
                    agents=tuple(agents_l),
                )
                envelope = Envelope(
                    to=self.address,
                    sender="simple_oef",
                    protocol_id=OefSearchMessage.protocol_id,
                    message=OefSearchSerializer().encode(message),
                )
                self.in_queue.put_nowait(envelope)
            else:
                raise ValueError("Location registration error.")
        except Exception as e:
            logger.error("Exception when interacting with SOEF: {}".format(e))

        # command=find_around_me&range_in_km=20


class SOEFConnection(Connection):
    """The SOEFConnection connects the Simple OEF to the mailbox."""

    def __init__(
        self,
        api_key: str,
        soef_addr: str = "127.0.0.1",
        soef_port: int = 10001,
        **kwargs
    ):
        """
        Initialize.

        :param api_key: the SOEF API key
        :param soef_addr: the SOEF IP address.
        :param soef_port: the SOEF port.
        :param kwargs: the keyword arguments (check the parent constructor)
        """
        if kwargs.get("configuration") is None and kwargs.get("connection_id") is None:
            kwargs["connection_id"] = PUBLIC_ID
        if (
            kwargs.get("configuration") is None
            and kwargs.get("excluded_protocols") is None
        ):
            kwargs["excluded_protocols"] = []
        if (
            kwargs.get("configuration") is None
            and kwargs.get("restricted_to_protocols") is None
        ):
            kwargs["restricted_to_protocols"] = [
                PublicId.from_str("fetchai/oef_search:0.1.0")
            ]
        super().__init__(**kwargs)
        self.api_key = api_key
        self.soef_addr = soef_addr
        self.soef_port = soef_port
        self.in_queue = None  # type: Optional[asyncio.Queue]
        self.channel = SOEFChannel(
            self.address,
            self.api_key,
            self.soef_addr,
            self.soef_port,
            self.excluded_protocols,
            self.restricted_to_protocols,
        )

    async def connect(self) -> None:
        """
        Connect to the channel.

        :return: None
        :raises Exception if the connection to the OEF fails.
        """
        if self.connection_status.is_connected:
            return
        try:
            self.connection_status.is_connecting = True
            self.in_queue = asyncio.Queue()
            self.channel.in_queue = self.in_queue
            self.connection_status.is_connecting = False
            self.connection_status.is_connected = True
        except (CancelledError, Exception) as e:  # pragma: no cover
            self.connection_status.is_connected = False
            raise e

    async def disconnect(self) -> None:
        """
        Disconnect from the channel.

        :return: None
        """
        assert (
            self.connection_status.is_connected or self.connection_status.is_connecting
        ), "Call connect before disconnect."
        assert self.in_queue is not None
        self.channel.disconnect()
        self.channel.in_queue = None
        self.connection_status.is_connected = False
        self.connection_status.is_connecting = False
        await self.in_queue.put(None)

    async def receive(self, *args, **kwargs) -> Optional["Envelope"]:
        """
        Receive an envelope. Blocking.

        :return: the envelope received, or None.
        """
        try:
            assert self.in_queue is not None
            envelope = await self.in_queue.get()
            if envelope is None:
                logger.debug("Received None.")
                return None
            logger.debug("Received envelope: {}".format(envelope))
            return envelope
        except CancelledError:
            logger.debug("Receive cancelled.")
            return None
        except Exception as e:
            logger.exception(e)
            return None

    async def send(self, envelope: "Envelope") -> None:
        """
        Send an envelope.

        :param envelope: the envelope to send.
        :return: None
        """
        if self.connection_status.is_connected:
            self.channel.send(envelope)

    @classmethod
    def from_config(
        cls, address: Address, configuration: ConnectionConfig
    ) -> "Connection":
        """
        Get the OEF connection from the connection configuration.
        :param address: the address of the agent.
        :param configuration: the connection configuration object.
        :return: the connection object
        """
        api_key = cast(str, configuration.config.get("api_key"))
        soef_addr = cast(str, configuration.config.get("soef_addr"))
        soef_port = cast(int, configuration.config.get("soef_port"))
        return SOEFConnection(
            api_key, soef_addr, soef_port, address=address, configuration=configuration,
        )
