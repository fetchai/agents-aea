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
import copy
import logging
from asyncio import CancelledError
from concurrent.futures.thread import ThreadPoolExecutor
from contextlib import suppress
from typing import Callable, Dict, List, Optional, Set, Union, cast
from urllib import parse
from uuid import uuid4

from defusedxml import ElementTree as ET  # pylint: disable=wrong-import-order

import requests

from aea.configurations.base import PublicId
from aea.connections.base import Connection
from aea.helpers.dialogue.base import Dialogue as BaseDialogue
from aea.helpers.dialogue.base import DialogueLabel as BaseDialogueLabel
from aea.helpers.search.models import (
    Constraint,
    ConstraintTypes,
    Description,
    Location,
    Query,
)
from aea.mail.base import Address, Envelope
from aea.protocols.base import Message

from packages.fetchai.protocols.oef_search.custom_types import OefErrorOperation
from packages.fetchai.protocols.oef_search.dialogues import OefSearchDialogue
from packages.fetchai.protocols.oef_search.dialogues import (
    OefSearchDialogues as BaseOefSearchDialogues,
)
from packages.fetchai.protocols.oef_search.message import OefSearchMessage

logger = logging.getLogger("aea.packages.fetchai.connections.oef")

PUBLIC_ID = PublicId.from_str("fetchai/soef:0.5.0")

NOT_SPECIFIED = object()

PERSONALITY_PIECES_KEYS = [
    "genus",
    "classification",
    "architecture",
    "dynamics.moving",
    "dynamics.heading",
    "dynamics.position",
    "action.buyer",
    "action.seller",
]


class ModelNames:
    """Enum of supported data models."""

    location_agent = "location_agent"
    set_service_key = "set_service_key"
    remove_service_key = "remove_service_key"
    personality_agent = "personality_agent"
    search_model = "search_model"
    ping = "ping"


class SOEFException(Exception):
    """Soef chanlle expected  exception."""

    @classmethod
    def warning(cls, msg: str) -> "SOEFException":  # pragma: no cover
        """Construct exception and write log."""
        logger.warning(msg)
        return cls(msg)

    @classmethod
    def debug(cls, msg: str) -> "SOEFException":  # pragma: no cover
        """Construct exception and write log."""
        logger.debug(msg)
        return cls(msg)

    @classmethod
    def error(cls, msg: str) -> "SOEFException":  # pragma: no cover
        """Construct exception and write log."""
        logger.error(msg)
        return cls(msg)

    @classmethod
    def exception(cls, msg: str) -> "SOEFException":  # pragma: no cover
        """Construct exception and write log."""
        logger.exception(msg)
        return cls(msg)


class OefSearchDialogues(BaseOefSearchDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        BaseOefSearchDialogues.__init__(self, SOEFConnection.connection_id.latest)

    @staticmethod
    def role_from_first_message(message: Message) -> BaseDialogue.Role:
        """
        Infer the role of the agent from an incoming/outgoing first message.

        :param message: an incoming/outgoing first message
        :return: The role of the agent
        """
        return OefSearchDialogue.Role.OEF_NODE

    def create_dialogue(
        self, dialogue_label: BaseDialogueLabel, role: BaseDialogue.Role,
    ) -> OefSearchDialogue:
        """
        Create an instance of fipa dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param role: the role of the agent this dialogue is maintained for

        :return: the created dialogue
        """
        dialogue = OefSearchDialogue(
            dialogue_label=dialogue_label,
            agent_address=SOEFConnection.connection_id.latest,
            role=role,
        )
        return dialogue


class SOEFChannel:
    """The OEFChannel connects the OEF Agent with the connection."""

    DEFAULT_CHAIN_IDENTIFIER = "fetchai_cosmos"

    SUPPORTED_CHAIN_IDENTIFIERS = [
        "fetchai",
        "fetchai_cosmos",
        "ethereum",
    ]

    DEFAULT_PERSONALITY_PIECES = ["architecture,agentframework"]

    PING_PERIOD = 30 * 60  # 30 minutes

    def __init__(
        self,
        address: Address,
        api_key: str,
        soef_addr: str,
        soef_port: int,
        excluded_protocols: Set[PublicId],
        restricted_to_protocols: Set[PublicId],
        chain_identifier: Optional[str] = None,
    ):
        """
        Initialize.

        :param address: the address of the agent.
        :param api_key: the SOEF API key.
        :param soef_addr: the SOEF IP address.
        :param soef_port: the SOEF port.
        :param excluded_protocols: the protocol ids excluded
        :param restricted_to_protocols: the protocol ids restricted to
        :param chain_identifier: supported chain id
        """
        if (
            chain_identifier is not None
            and chain_identifier not in self.SUPPORTED_CHAIN_IDENTIFIERS
        ):
            raise ValueError(
                f"Unsupported chain_identifier. Valida are {', '.join(self.SUPPORTED_CHAIN_IDENTIFIERS)}"
            )

        self.address = address
        self.api_key = api_key
        self.soef_addr = soef_addr
        self.soef_port = soef_port
        self.base_url = "http://{}:{}".format(soef_addr, soef_port)
        self.excluded_protocols = excluded_protocols
        self.restricted_to_protocols = restricted_to_protocols
        self.oef_search_dialogues = OefSearchDialogues()
        self.oef_msg_id = 0
        self.oef_msg_id_to_dialogue = {}  # type: Dict[int, OefSearchDialogue]

        self.declared_name = uuid4().hex
        self.unique_page_address = None  # type: Optional[str]
        self.agent_location = None  # type: Optional[Location]
        self.in_queue = None  # type: Optional[asyncio.Queue]
        self._executor_pool: Optional[ThreadPoolExecutor] = None
        self.chain_identifier: str = chain_identifier or self.DEFAULT_CHAIN_IDENTIFIER
        self._loop = None  # type: Optional[asyncio.AbstractEventLoop]
        self._ping_periodic_task: Optional[asyncio.Task] = None

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        """Get event loop."""
        assert self._loop is not None, "Loop not set!"
        return self._loop

    @staticmethod
    def _is_compatible_query(query: Query) -> bool:
        """
        Check if a query is compatible with the soef.

        Each query must contain a distance constraint type.

        :param query: search query to check
        :return: bool
        """
        constraints = [c for c in query.constraints if isinstance(c, Constraint)]
        if len(constraints) == 0:  # pragma: nocover
            return False

        if ConstraintTypes.DISTANCE not in [
            c.constraint_type.type for c in constraints
        ]:  # pragma: nocover
            return False

        return True

    def _construct_personality_filter_params(
        self, equality_constraints: List[Constraint],
    ) -> Dict[str, List[str]]:
        """
        Construct a dictionary of personality filters.

        :param equality_constraints: list of equality constraints
        :return: bool
        """
        filters = copy.copy(self.DEFAULT_PERSONALITY_PIECES)

        for constraint in equality_constraints:
            if constraint.attribute_name not in PERSONALITY_PIECES_KEYS:
                continue
            filters.append(
                constraint.attribute_name + "," + constraint.constraint_type.value
            )
        if not filters:  # pragma: nocover
            return {}
        return {"ppfilter": filters}

    @staticmethod
    def _construct_service_key_filter_params(
        equality_constraints: List[Constraint],
    ) -> Dict[str, List[str]]:
        """
        Construct a dictionary of service keys filters.

        We assume each equality constraint which is not a personality piece relates to a service key!

        :param equality_constraints: list of equality constraints

        :return: bool
        """
        filters = []

        for constraint in equality_constraints:
            if constraint.attribute_name in PERSONALITY_PIECES_KEYS:
                continue
            filters.append(
                constraint.attribute_name + "," + constraint.constraint_type.value
            )
        if not filters:  # pragma: nocover
            return {}
        return {"skfilter": filters}

    def _check_protocol_valid(self, envelope: Envelope) -> None:
        """
        Check protocol is supported and raises ValueError if not.

        :param envelope: envelope to check protocol of
        :return: None
        """
        is_in_excluded = envelope.protocol_id in (self.excluded_protocols or [])
        is_in_restricted = not self.restricted_to_protocols or envelope.protocol_id in (
            self.restricted_to_protocols or []
        )

        if is_in_excluded or not is_in_restricted:
            logger.error(
                "This envelope cannot be sent with the soef connection: protocol_id={}".format(
                    envelope.protocol_id
                )
            )
            raise ValueError(
                "Cannot send message, invalid protocol: {}".format(envelope.protocol_id)
            )

    async def send(self, envelope: Envelope) -> None:
        """
        Send message handler.

        :param envelope: the envelope.
        :return: None
        """
        self._check_protocol_valid(envelope)
        await self.process_envelope(envelope)

    async def _request_text(self, *args, **kwargs) -> str:
        """Perform and http request and return text of response."""
        # pydocstyle fix. cause black reformat.
        def _do_request():
            return requests.request(*args, **kwargs).text

        return await self.loop.run_in_executor(self._executor_pool, _do_request)

    async def process_envelope(self, envelope: Envelope) -> None:
        """
        Process envelope.

        :param envelope: the envelope.
        :return: None
        """
        assert isinstance(envelope.message, OefSearchMessage), ValueError(
            "Message not of type OefSearchMessage"
        )
        oef_message = cast(OefSearchMessage, envelope.message)
        oef_message = copy.deepcopy(
            oef_message
        )  # TODO: fix; need to copy atm to avoid overwriting "is_incoming"
        oef_message.is_incoming = True  # TODO: fix; should be done by framework
        oef_message.counterparty = (
            envelope.sender
        )  # TODO: fix; should be done by framework
        oef_search_dialogue = cast(
            OefSearchDialogue, self.oef_search_dialogues.update(oef_message)
        )
        if oef_search_dialogue is None:  # pragma: nocover
            raise ValueError(
                "Could not create dialogue for message={}".format(oef_message)
            )

        err_ops = OefSearchMessage.OefErrorOperation
        oef_error_operation = err_ops.OTHER

        try:
            if self.unique_page_address is None:  # pragma: nocover
                await self._register_agent()

            handlers_and_errors = {
                OefSearchMessage.Performative.REGISTER_SERVICE: (
                    self.register_service,
                    err_ops.REGISTER_SERVICE,
                ),
                OefSearchMessage.Performative.UNREGISTER_SERVICE: (
                    self.unregister_service,
                    err_ops.UNREGISTER_SERVICE,
                ),
                OefSearchMessage.Performative.SEARCH_SERVICES: (
                    self.search_services,
                    err_ops.SEARCH_SERVICES,
                ),
            }

            if oef_message.performative not in handlers_and_errors:
                raise ValueError("OEF request not recognized.")  # pragma: nocover

            handler, oef_error_operation = handlers_and_errors[oef_message.performative]
            await handler(oef_message, oef_search_dialogue)

        except SOEFException:
            await self._send_error_response(
                oef_message,
                oef_search_dialogue,
                oef_error_operation=oef_error_operation,
            )
        except Exception:  # pylint: disable=broad-except # pragma: nocover
            logger.exception("Exception during envelope processing")
            await self._send_error_response(
                oef_message,
                oef_search_dialogue,
                oef_error_operation=oef_error_operation,
            )
            raise

    async def register_service(
        self, oef_message: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Register a service on the SOEF.

        :param oef_message: OefSearchMessage
        :param oef_search_dialogue: OefSearchDialogue
        :return: None
        """
        service_description = oef_message.service_description

        data_model_handlers = {
            "location_agent": self._register_location_handler,
            "personality_agent": self._set_personality_piece_handler,
            "set_service_key": self._set_service_key_handler,
            "ping": self._ping_handler,
        }  # type: Dict[str, Callable]
        data_model_name = service_description.data_model.name

        if data_model_name not in data_model_handlers:
            raise SOEFException.error(
                f'Data model name: {data_model_name} is not supported. Valid models are: {", ".join(data_model_handlers.keys())}'
            )

        handler = data_model_handlers[data_model_name]
        await handler(service_description)

    async def _ping_handler(self, service_description: Description) -> None:
        """
        Perform ping command.

        :param service_description: Service description

        :return None
        """
        self._check_data_model(service_description, ModelNames.ping)
        await self._ping_command()

    async def _ping_command(self) -> None:
        """Perform ping on registered agent."""
        await self._generic_oef_command("ping", {})

    async def _ping_periodic(self, period: float = 30 * 60) -> None:
        """
        Send ping command every `period`.

        :param period: period of ping in secinds

        :return: None
        """
        with suppress(asyncio.CancelledError):
            while True:
                try:
                    await self._ping_command()
                except asyncio.CancelledError:  # pylint: disable=try-except-raise
                    raise
                except Exception:  # pylint: disable=broad-except
                    logger.exception("Error on periodic ping command!")
                await asyncio.sleep(period)

    async def _set_service_key_handler(self, service_description: Description) -> None:
        """
        Set service key from service description.

        :param service_description: Service description
        :return None
        """
        self._check_data_model(service_description, ModelNames.set_service_key)

        key = service_description.values.get("key", None)
        value = service_description.values.get("value", NOT_SPECIFIED)

        if key is None or value is NOT_SPECIFIED:  # pragma: nocover
            raise SOEFException.error("Bad values provided!")

        await self._set_service_key(key, value)

    async def _generic_oef_command(
        self, command, params=None, unique_page_address=None, check_success=True
    ) -> str:
        """
        Set service key from service description.

        :param service_description: Service description
        :return: response text
        """
        params = params or {}
        logger.debug(f"Perform `{command}` with {params}")
        url = parse.urljoin(
            self.base_url, unique_page_address or self.unique_page_address
        )
        response_text = await self._request_text(
            "get", url=url, params={"command": command, **params}
        )
        try:
            root = ET.fromstring(response_text)
            assert root.tag == "response"
            if check_success:
                el = root.find("./success")
                assert el is not None, "No success element"
                assert str(el.text).strip() == "1", "Success is not 1"
            logger.debug(f"`{command}` SUCCESS!")
            return response_text
        except Exception as e:
            raise SOEFException.error(f"`{command}` error: {response_text}: {[e]}")

    async def _set_service_key(self, key: str, value: Union[str, int, float]) -> None:
        """
        Perform set service key command.

        :param key: key to set
        :param value: value to set
        :return None:
        """
        await self._generic_oef_command("set_service_key", {"key": key, "value": value})

    async def _remove_service_key_handler(
        self, service_description: Description
    ) -> None:
        """
        Remove service key from service description.

        :param service_description: Service description
        :return None
        """
        self._check_data_model(service_description, ModelNames.remove_service_key)
        key = service_description.values.get("key", None)

        if key is None:  # pragma: nocover
            raise SOEFException.error("Bad values provided!")

        await self._remove_service_key(key)

    async def _remove_service_key(self, key: str) -> None:
        """
        Perform remove service key command.

        :param key: key to remove
        :return None:
        """
        await self._generic_oef_command("remove_service_key", {"key": key})

    async def _register_location_handler(
        self, service_description: Description
    ) -> None:
        """
        Register service with location.

        :param service_description: Service description
        :return None
        """
        self._check_data_model(service_description, ModelNames.location_agent)

        agent_location = service_description.values.get("location", None)
        if agent_location is None or not isinstance(
            agent_location, Location
        ):  # pragma: nocover
            raise SOEFException.debug("Bad location provided.")
        await self._set_location(agent_location)

    @staticmethod
    def _check_data_model(
        service_description: Description, data_model_name: str
    ) -> None:
        """
        Check data model corresponds.

        Raise exception if not.

        :param service_description: Service description
        :param data_model_name: data model name expected.
        :return None
        """
        if service_description.data_model.name != data_model_name:  # pragma: nocover
            raise SOEFException.error(
                f"Bad service description! expected {data_model_name} but go {service_description.data_model.name}"
            )

    async def _set_location(self, agent_location: Location) -> None:
        """
        Set the location.

        :param service_location: the service location
        """
        latitude = agent_location.latitude
        longitude = agent_location.longitude
        params = {
            "longitude": str(longitude),
            "latitude": str(latitude),
        }
        await self._generic_oef_command("set_position", params)
        self.agent_location = agent_location

    async def _set_personality_piece_handler(
        self, service_description: Description
    ) -> None:
        """
        Set the personality piece.

        :param piece: the piece to be set
        :param value: the value to be set
        """
        self._check_data_model(service_description, ModelNames.personality_agent)
        piece = service_description.values.get("piece", None)
        value = service_description.values.get("value", None)

        if not (isinstance(piece, str) and isinstance(value, str)):  # pragma: nocover
            raise SOEFException.debug("Personality piece bad values provided.")

        await self._set_personality_piece(piece, value)

    async def _set_personality_piece(self, piece: str, value: str):
        """
        Set the personality piece.

        :param piece: the piece to be set
        :param value: the value to be set
        """
        params = {
            "piece": piece,
            "value": value,
        }
        await self._generic_oef_command("set_personality_piece", params)

    async def _register_agent(self) -> None:
        """
        Register an agent on the SOEF.

        Includes the following steps:
        - apply to lobby to receive unique page address and token
        - acknowledge registration
        - set default personality piece for agent framework
        - initiate ping task

        :return: None
        """
        logger.debug("Applying to SOEF lobby with address={}".format(self.address))
        url = parse.urljoin(self.base_url, "register")
        params = {
            "api_key": self.api_key,
            "chain_identifier": self.chain_identifier,
            "address": self.address,
            "declared_name": self.declared_name,
        }
        response_text = await self._request_text("get", url=url, params=params)
        root = ET.fromstring(response_text)
        logger.debug("Root tag: {}".format(root.tag))
        unique_page_address = ""
        unique_token = ""  # nosec
        for child in root:
            logger.debug(
                "Child tag={}, child attrib={}, child text={}".format(
                    child.tag, child.attrib, child.text
                )
            )
            if child.tag == "page_address" and child.text is not None:
                unique_page_address = child.text
            if child.tag == "token" and child.text is not None:
                unique_token = child.text
        if not (len(unique_page_address) > 0 and len(unique_token) > 0):
            raise SOEFException.error(
                "Agent registration error - page address or token not received"
            )
        logger.debug("Registering agent")
        params = {"token": unique_token}
        await self._generic_oef_command(
            "acknowledge", params, unique_page_address=unique_page_address
        )
        self.unique_page_address = unique_page_address

        await self._set_personality_piece("architecture", "agentframework")

        if self._loop and not self._ping_periodic_task:
            self._ping_periodic_task = self._loop.create_task(
                self._ping_periodic(self.PING_PERIOD)
            )

    async def _send_error_response(
        self,
        oef_search_message: OefSearchMessage,
        oef_search_dialogue: OefSearchDialogue,
        oef_error_operation: OefErrorOperation = OefSearchMessage.OefErrorOperation.OTHER,
    ) -> None:
        """
        Send an error response back.

        :param oef_search_message: the oef search message
        :param oef_search_dialogue: the oef search dialogue
        :param oef_error_operation: the error code to send back
        :return: None
        """
        assert self.in_queue is not None, "Inqueue not set!"
        message = OefSearchMessage(
            performative=OefSearchMessage.Performative.OEF_ERROR,
            oef_error_operation=oef_error_operation,
            dialogue_reference=oef_search_dialogue.dialogue_label.dialogue_reference,
            target=oef_search_message.message_id,
            message_id=oef_search_message.message_id + 1,
        )
        message.counterparty = oef_search_message.counterparty
        oef_search_dialogue.update(message)
        message = copy.deepcopy(
            message
        )  # TODO: fix; need to copy atm to avoid overwriting "is_incoming"
        envelope = Envelope(
            to=message.counterparty,
            sender=SOEFConnection.connection_id.latest,
            protocol_id=message.protocol_id,
            message=message,
        )
        await self.in_queue.put(envelope)

    async def unregister_service(
        self, oef_message: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Unregister a service on the SOEF.

        :param oef_message: OefSearchMessage
        :param oef_search_dialogue: OefSearchDialogue
        :return: None
        """
        service_description = oef_message.service_description

        data_model_handlers = {
            "location_agent": self._unregister_agent,
            "remove_service_key": self._remove_service_key_handler,
        }  # type: Dict[str, Callable]
        data_model_name = service_description.data_model.name

        if data_model_name not in data_model_handlers:
            raise SOEFException.error(
                f'Data model name: {data_model_name} is not supported. Valid models are: {", ".join(data_model_handlers.keys())}'
            )

        handler = data_model_handlers[data_model_name]
        if data_model_name == "location_agent":
            await handler()
        else:
            await handler(service_description)

    async def _unregister_agent(self) -> None:
        """
        Unnregister a service_name from the SOEF.

        :return: None
        """
        await self._stop_periodic_ping_task()
        if self.unique_page_address is None:  # pragma: nocover
            logger.debug(
                "The service is not registered to the simple OEF. Cannot unregister."
            )
            return

        response = await self._generic_oef_command("unregister", check_success=False)
        assert "<response><message>Goodbye!</message></response>" in response
        self.unique_page_address = None

    async def _stop_periodic_ping_task(self) -> None:
        """Cancel periodic ping task."""
        if self._ping_periodic_task and not self._ping_periodic_task.done():
            self._ping_periodic_task.cancel()
            self._ping_periodic_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._ping_periodic_task
            self._ping_periodic_task = None

    async def connect(self) -> None:
        """Connect channel set queues and executor pool."""
        self._loop = asyncio.get_event_loop()
        self.in_queue = asyncio.Queue()
        self._executor_pool = ThreadPoolExecutor(max_workers=10)

    async def disconnect(self) -> None:
        """
        Disconnect unregisters any potential services still registered.

        :return: None
        """
        await self._stop_periodic_ping_task()

        assert self.in_queue, ValueError("Queue is not set, use connect first!")
        await self._unregister_agent()
        await self.in_queue.put(None)

    async def search_services(
        self, oef_message: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Search services on the SOEF.

        :param oef_message: OefSearchMessage
        :param oef_search_dialogue: OefSearchDialogue
        :return: None
        """
        query = oef_message.query

        if not self._is_compatible_query(query):
            raise SOEFException.warning(
                "Service query incompatible with SOEF: constraints={}".format(
                    query.constraints
                )
            )

        constraints = [cast(Constraint, c) for c in query.constraints]
        constraint_distance = [
            c for c in constraints if c.constraint_type.type == ConstraintTypes.DISTANCE
        ][0]
        service_location, radius = constraint_distance.constraint_type.value

        equality_constraints = [
            c for c in constraints if c.constraint_type.type == ConstraintTypes.EQUAL
        ]

        params = {}

        params.update(self._construct_personality_filter_params(equality_constraints))

        params.update(self._construct_service_key_filter_params(equality_constraints))

        if self.agent_location is None or self.agent_location != service_location:
            # we update the location to match the query.
            await self._set_location(service_location)  # pragma: nocover
        await self._find_around_me(oef_message, oef_search_dialogue, radius, params)

    async def _find_around_me(
        self,
        oef_message: OefSearchMessage,
        oef_search_dialogue: OefSearchDialogue,
        radius: float,
        params: Dict[str, List[str]],
    ) -> None:
        """
        Find agents around me.

        :param oef_message: OefSearchMessage
        :param oef_search_dialogue: OefSearchDialogue
        :param radius: the radius in which to search
        :param params: the parameters for the query
        :return: None
        """
        assert self.in_queue is not None, "Inqueue not set!"
        logger.debug("Searching in radius={} of myself".format(radius))

        response_text = await self._generic_oef_command(
            "find_around_me", {"range_in_km": [str(radius)], **params}
        )
        root = ET.fromstring(response_text)
        agents = {
            key: {} for key in self.SUPPORTED_CHAIN_IDENTIFIERS
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

        message = OefSearchMessage(
            performative=OefSearchMessage.Performative.SEARCH_RESULT,
            dialogue_reference=oef_search_dialogue.dialogue_label.dialogue_reference,
            agents=tuple(agents_l),
            target=oef_message.message_id,
            message_id=oef_message.message_id + 1,
        )
        message.counterparty = oef_message.counterparty
        oef_search_dialogue.update(message)
        message = copy.deepcopy(
            message
        )  # TODO: fix; need to copy atm to avoid overwriting "is_incoming"
        envelope = Envelope(
            to=message.counterparty,
            sender=SOEFConnection.connection_id.latest,
            protocol_id=message.protocol_id,
            message=message,
        )
        await self.in_queue.put(envelope)


class SOEFConnection(Connection):
    """The SOEFConnection connects the Simple OEF to the mailbox."""

    connection_id = PUBLIC_ID

    def __init__(self, **kwargs):
        """Initialize."""
        if kwargs.get("configuration") is None:  # pragma: nocover
            kwargs["excluded_protocols"] = kwargs.get("excluded_protocols") or []
            kwargs["restricted_to_protocols"] = kwargs.get("excluded_protocols") or [
                PublicId.from_str("fetchai/oef_search:0.3.0")
            ]

        super().__init__(**kwargs)
        api_key = cast(str, self.configuration.config.get("api_key"))
        soef_addr = cast(str, self.configuration.config.get("soef_addr"))
        soef_port = cast(int, self.configuration.config.get("soef_port"))
        chain_identifier = cast(str, self.configuration.config.get("chain_identifier"))
        assert (
            api_key is not None and soef_addr is not None and soef_port is not None
        ), "api_key, soef_addr and soef_port must be set!"

        self.api_key = api_key
        self.soef_addr = soef_addr
        self.soef_port = soef_port
        self.channel = SOEFChannel(
            self.address,
            self.api_key,
            self.soef_addr,
            self.soef_port,
            self.excluded_protocols,
            self.restricted_to_protocols,
            chain_identifier=chain_identifier,
        )

    async def connect(self) -> None:
        """
        Connect to the channel.

        :return: None
        :raises Exception if the connection to the OEF fails.
        """
        if self.connection_status.is_connected:  # pragma: no cover
            return
        try:
            self.connection_status.is_connecting = True
            await self.channel.connect()
            self.connection_status.is_connecting = False
            self.connection_status.is_connected = True
        except (CancelledError, Exception) as e:  # pragma: no cover
            self.connection_status.is_connected = False
            raise e

    @property
    def in_queue(self) -> Optional[asyncio.Queue]:
        """Return in_queue of the channel."""
        return self.channel.in_queue

    async def disconnect(self) -> None:
        """
        Disconnect from the channel.

        :return: None
        """
        assert (
            self.connection_status.is_connected or self.connection_status.is_connecting
        ), "Call connect before disconnect."
        assert self.in_queue is not None
        await self.channel.disconnect()
        self.connection_status.is_connected = False
        self.connection_status.is_connecting = False

    async def receive(self, *args, **kwargs) -> Optional["Envelope"]:
        """
        Receive an envelope. Blocking.

        :return: the envelope received, or None.
        """
        try:
            assert self.in_queue is not None
            envelope = await self.in_queue.get()
            if envelope is None:  # pragma: nocover
                self.logger.debug("Received None.")
                return None
            self.logger.debug("Received envelope: {}".format(envelope))
            return envelope
        except CancelledError:
            self.logger.debug("Receive cancelled.")
            return None
        except Exception as e:  # pragma: nocover # pylint: disable=broad-except
            self.logger.exception(e)
            return None

    async def send(self, envelope: "Envelope") -> None:
        """
        Send an envelope.

        :param envelope: the envelope to send.
        :return: None
        """
        if self.connection_status.is_connected:
            await self.channel.send(envelope)
