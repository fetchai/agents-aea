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
import os
import re
import urllib
from asyncio import CancelledError
from concurrent.futures._base import CancelledError as ConcurrentCancelledError
from concurrent.futures.thread import ThreadPoolExecutor
from contextlib import suppress
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union, cast
from urllib import parse
from uuid import uuid4

from defusedxml import ElementTree  # pylint: disable=wrong-import-order

from aea.common import Address, JSONLike
from aea.configurations.base import PublicId
from aea.connections.base import Connection, ConnectionStates
from aea.exceptions import enforce
from aea.helpers import http_requests as requests
from aea.helpers.search.models import (
    Constraint,
    ConstraintTypes,
    Description,
    Location,
    Query,
)
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue

from packages.fetchai.protocols.oef_search.custom_types import (
    AgentsInfo,
    OefErrorOperation,
)
from packages.fetchai.protocols.oef_search.dialogues import (
    OefSearchDialogue as BaseOefSearchDialogue,
)
from packages.fetchai.protocols.oef_search.dialogues import (
    OefSearchDialogues as BaseOefSearchDialogues,
)
from packages.fetchai.protocols.oef_search.message import OefSearchMessage


_default_logger = logging.getLogger("aea.packages.fetchai.connections.soef")

PUBLIC_ID = PublicId.from_str("fetchai/soef:0.26.0")

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


class ModelNames(Enum):
    """Enum of supported data models."""

    LOCATION_AGENT = "location_agent"
    SET_SERVICE_KEY = "set_service_key"
    REMOVE_SERVICE_KEY = "remove_service_key"
    PERSONALITY_AGENT = "personality_agent"
    SEARCH_MODEL = "search_model"
    PING = "ping"
    GENERIC_COMMAND = "generic_command"


class SOEFException(Exception):
    """SOEF channel expected exception."""

    @classmethod
    def warning(
        cls, msg: str, logger: logging.Logger = _default_logger
    ) -> "SOEFException":  # pragma: no cover
        """Construct exception and write log."""
        logger.warning(msg)
        return cls(msg)

    @classmethod
    def debug(
        cls, msg: str, logger: logging.Logger = _default_logger
    ) -> "SOEFException":  # pragma: no cover
        """Construct exception and write log."""
        logger.debug(msg)
        return cls(msg)

    @classmethod
    def error(
        cls, msg: str, logger: logging.Logger = _default_logger
    ) -> "SOEFException":  # pragma: no cover
        """Construct exception and write log."""
        logger.error(msg)
        return cls(msg)

    @classmethod
    def exception(
        cls, msg: str, logger: logging.Logger = _default_logger
    ) -> "SOEFException":  # pragma: no cover
        """Construct exception and write log."""
        logger.exception(msg)
        return cls(msg)


OefSearchDialogue = BaseOefSearchDialogue


class BaseHandledException(Exception):
    """Base Exception class."""

    MSG: str

    def __init__(self, exc: Union[Exception, str]) -> None:
        """Init exception with message or exception instance."""
        super().__init__()
        self.exc = exc

    def __repr__(self) -> str:
        """Get exception representation."""
        return self.MSG.format(str(self.exc))

    def __str__(self) -> str:
        """Get exception str representation."""
        return self.__repr__()


class SOEFNetworkConnectionError(BaseHandledException):
    """Exception class for network connection errors."""

    MSG = "<SOEF Network Connection Error: {}. Check internet connection!>"


class SOEFServerBadResponseError(BaseHandledException):
    """Exception class for bad server responses."""

    MSG = "<SOEF Server Bad Response Error: {}.>"


class OefSearchDialogues(BaseOefSearchDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self) -> None:
        """Initialize dialogues."""

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            # The soef connection maintains the dialogue on behalf of the node
            return OefSearchDialogue.Role.OEF_NODE

        BaseOefSearchDialogues.__init__(
            self,
            self_address=str(SOEFConnection.connection_id.to_any()),
            role_from_first_message=role_from_first_message,
            dialogue_class=OefSearchDialogue,
        )


class SOEFChannel:
    """The OEFChannel connects the OEF Agent with the connection."""

    DEFAULT_CHAIN_IDENTIFIER = "fetchai_v2_testnet_stable"

    SUPPORTED_CHAIN_IDENTIFIERS = [
        re.compile("ethereum"),
        re.compile("^fetchai(_[a-z0-9_]*)?$"),
    ]

    DEFAULT_PERSONALITY_PIECES = ["architecture,agentframework"]
    NONE_UNIQUE_PAGE_ADDRESS = ""

    PING_PERIOD = 30 * 60  # 30 minutes
    FIND_AROUND_ME_REQUEST_DELAY = 2  # seconds

    def __init__(
        self,
        address: Address,
        api_key: str,
        is_https: bool,
        soef_addr: str,
        soef_port: int,
        data_dir: str,
        chain_identifier: Optional[str] = None,
        token_storage_path: Optional[str] = None,
        logger: logging.Logger = _default_logger,
        connection_check_timeout: float = 15.0,
        connection_check_max_retries: int = 3,
    ):
        """
        Initialize.

        :param address: the address of the agent.
        :param api_key: the SOEF API key.
        :param is_https: whether htts or http is used.
        :param soef_addr: the SOEF IP address.
        :param soef_port: the SOEF port.
        :param data_dir: the data directory.
        :param chain_identifier: supported chain id.
        :param token_storage_path: storage path for the SOEF token.
        :param logger: the logger.
        :param connection_check_timeout: timeout to check network connection on connect.
        :param connection_check_max_retries: maximum retries when performing connection check.
        """
        if chain_identifier is not None and not any(
            regex.match(chain_identifier) for regex in self.SUPPORTED_CHAIN_IDENTIFIERS
        ):
            raise ValueError(
                f"Unsupported chain_identifier. Valid identifier regular expressions are {', '.join([reg.pattern for reg in self.SUPPORTED_CHAIN_IDENTIFIERS])}"
            )

        self.address = address
        self.api_key = api_key
        self.is_https = is_https
        self.soef_addr = soef_addr
        self.soef_port = soef_port
        self.base_url = (
            f"https://{soef_addr}:{soef_port}"
            if self.is_https
            else f"http://{soef_addr}:{soef_port}"
        )
        self.oef_search_dialogues = OefSearchDialogues()
        self.connection_check_timeout = connection_check_timeout
        self.connection_check_max_retries = connection_check_max_retries

        self._token_storage_path = token_storage_path
        if self._token_storage_path is not None:
            if not Path(self._token_storage_path).is_absolute():
                self._token_storage_path = os.path.join(
                    data_dir, self._token_storage_path
                )
            Path(self._token_storage_path).touch()
        self.declared_name = uuid4().hex
        self._unique_page_address = None  # type: Optional[str]
        self.agent_location = None  # type: Optional[Location]
        self.in_queue = None  # type: Optional[asyncio.Queue]
        self._executor_pool: Optional[ThreadPoolExecutor] = None
        self.chain_identifier: str = chain_identifier or self.DEFAULT_CHAIN_IDENTIFIER
        self._loop = None  # type: Optional[asyncio.AbstractEventLoop]
        self._ping_periodic_task: Optional[asyncio.Task] = None
        self._find_around_me_queue: Optional[asyncio.Queue] = None
        self._find_around_me_processor_task: Optional[asyncio.Task] = None
        self.logger = logger
        self._unregister_lock: Optional[asyncio.Lock] = None

    @property
    def unique_page_address(self) -> Optional[str]:
        """Get unique page address."""
        if self._unique_page_address is None:
            # check if we have it in storage
            self._unique_page_address = self._get_unique_page_address_from_storage()
        return self._unique_page_address

    @unique_page_address.setter
    def unique_page_address(self, unique_page_address: Optional[str]) -> None:
        """Set the unique page address."""
        self._unique_page_address = unique_page_address
        self._set_unique_page_address_to_storage(unique_page_address)

    def _get_unique_page_address_from_storage(self) -> Optional[str]:
        """Get the unique page address from storage."""
        if self._token_storage_path is None:
            return None
        with open(self._token_storage_path, "r") as f:
            result = f.read().strip()
        unique_page_address = (
            result if result != self.NONE_UNIQUE_PAGE_ADDRESS else None
        )
        return unique_page_address

    def _set_unique_page_address_to_storage(
        self, unique_page_address: Optional[str]
    ) -> None:
        """Set the unique page address to storage."""
        if self._token_storage_path is None:
            return
        if unique_page_address is None:
            unique_page_address = self.NONE_UNIQUE_PAGE_ADDRESS
        with open(self._token_storage_path, "w") as f:
            f.write(unique_page_address)

    async def _find_around_me_processor(self) -> None:
        """Process find me around requests in background task."""
        while self._find_around_me_queue is not None:
            try:
                task = await self._find_around_me_queue.get()
                oef_message, oef_search_dialogue, radius, params = task
            except (
                asyncio.CancelledError,
                CancelledError,
                GeneratorExit,
            ):  # pylint: disable=try-except-raise  # pragma: nocover
                return
            except Exception:  # pragma: nocover
                self.logger.exception(
                    "Error on reading messages queue for find around me!"
                )
                raise

            try:
                await self._find_around_me_handle_request(
                    oef_message, oef_search_dialogue, radius, params
                )
                await asyncio.sleep(self.FIND_AROUND_ME_REQUEST_DELAY)
            except (
                asyncio.CancelledError,
                CancelledError,
                GeneratorExit,
            ):  # pylint: disable=try-except-raise
                return
            except SOEFException:  # pragma: nocover
                await self._send_error_response(
                    oef_message,
                    oef_search_dialogue,
                    oef_error_operation=OefSearchMessage.OefErrorOperation.OTHER,
                )
            except Exception as e:  # pylint: disable=broad-except  # pragma: nocover
                self.logger.exception(
                    f"Exception occurred in  _find_around_me_processor: {e}"
                )
                await self._send_error_response(
                    oef_message,
                    oef_search_dialogue,
                    oef_error_operation=OefSearchMessage.OefErrorOperation.OTHER,
                )
            finally:
                self.logger.debug("_find_around_me_processor exited")

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        """Get event loop."""
        if self._loop is None:
            raise ValueError("Loop not set!")  # pragma: nocover
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

    async def send(self, envelope: Envelope) -> None:
        """
        Send message handler.

        :param envelope: the envelope.
        """
        await self.process_envelope(envelope)

    async def _request_text(self, *args: Any, **kwargs: Any) -> str:
        """Perform and http request and return text of response."""

        def _do_request() -> requests.Response:
            return requests.request(*args, **kwargs)

        try:
            response = await self.loop.run_in_executor(self._executor_pool, _do_request)
        except requests.ConnectionError as e:
            raise SOEFNetworkConnectionError(e) from e

        if response.status_code < 200 or response.status_code >= 300:
            raise SOEFServerBadResponseError(
                f"Bad server response: code {response.status_code} when 2XX expected. Request data: ({args}, {kwargs}) Response content: `{response.text}`"
            )
        if not response.text:
            raise SOEFServerBadResponseError(
                f"Bad server response: empty response. Request data: ({args}, {kwargs})"
            )

        return response.text

    async def process_envelope(self, envelope: Envelope) -> None:
        """
        Process envelope.

        :param envelope: the envelope.
        """
        enforce(
            isinstance(envelope.message, OefSearchMessage),
            "Message not of type OefSearchMessage",
        )
        oef_message = cast(OefSearchMessage, envelope.message)
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
                # first time registration or we previously unregistered
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
        except (asyncio.CancelledError, ConcurrentCancelledError):  # pragma: nocover
            pass
        except Exception as e:  # pylint: disable=broad-except # pragma: nocover
            if "<reason>Forbidden</reason><detail>already in lobby" in str(e):
                raise ValueError(
                    "Could not register with SOEF. Agent address already registered from elsewhere."
                )
            self.logger.exception(f"Exception during envelope processing: {e}")
            await self._send_error_response(
                oef_message,
                oef_search_dialogue,
                oef_error_operation=oef_error_operation,
            )

    async def register_service(
        self, oef_message: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Register a service on the SOEF.

        :param oef_message: OefSearchMessage
        :param oef_search_dialogue: OefSearchDialogue
        """
        service_description = oef_message.service_description

        data_model_handlers = {
            "location_agent": self._register_location_handler,
            "personality_agent": self._set_personality_piece_handler,
            "set_service_key": self._set_service_key_handler,
            "ping": self._ping_handler,
            "generic_command": self._generic_command_handler,
        }  # type: Dict[str, Callable]
        data_model_name = service_description.data_model.name

        if data_model_name not in data_model_handlers:
            raise SOEFException.error(
                f'Data model name: {data_model_name} is not supported for `register`. Valid models for performative {oef_message.performative} are: {", ".join(data_model_handlers.keys())}'
            )

        handler = data_model_handlers[data_model_name]
        await handler(service_description, oef_message, oef_search_dialogue)

    async def _ping_handler(
        self,
        service_description: Description,
        oef_message: OefSearchMessage,
        oef_search_dialogue: OefSearchDialogue,
    ) -> None:
        """
        Perform ping command.

        :param service_description: Service description
        :param oef_message: the oef message.
        :param oef_search_dialogue: the oef search dialogue
        """
        self._check_data_model(service_description, ModelNames.PING.value)
        await self._ping_command()
        await self._send_success_response(oef_message, oef_search_dialogue)

    async def _generic_command_handler(
        self,
        service_description: Description,
        oef_message: OefSearchMessage,
        oef_search_dialogue: OefSearchDialogue,
    ) -> None:
        """
        Perform ping command.

        :param service_description: Service description
        :param oef_message: the oef message.
        :param oef_search_dialogue: the oef search dialogue
        """
        if not self.in_queue:  # pragma: no cover
            """not connected."""
            return

        self._check_data_model(service_description, ModelNames.GENERIC_COMMAND.value)
        command = service_description.values.get("command", None)
        params = service_description.values.get("parameters", {})

        if params:
            params = urllib.parse.parse_qs(params)

        parsed_text = await self._generic_oef_command(command, params)
        content = ElementTree.tostring(parsed_text)
        agents_info: JSONLike = {
            "response": {"content": content},
            "command": service_description.values,
        }
        await self._send_success_response(oef_message, oef_search_dialogue, agents_info)

    async def _ping_command(self) -> None:
        """Perform ping on registered agent."""
        await self._generic_oef_command("ping", {}, check_success=False)

    async def _ping_periodic(self, period: float = 30 * 60) -> None:
        """
        Send ping command every `period`.

        :param period: period of ping in seconds
        """
        with suppress(asyncio.CancelledError):
            while self.unique_page_address:
                try:
                    await self._ping_command()
                except (
                    asyncio.CancelledError,
                    ConcurrentCancelledError,
                ):  # pragma: nocover  # pylint: disable=try-except-raise
                    raise
                except Exception:  # pylint: disable=broad-except  # pragma: nocover
                    self.logger.exception("Error on periodic ping command!")
                await asyncio.sleep(period)

    async def _set_service_key_handler(
        self,
        service_description: Description,
        oef_message: OefSearchMessage,
        oef_search_dialogue: OefSearchDialogue,
    ) -> None:
        """
        Set service key from service description.

        :param service_description: Service description
        :param oef_message: the oef message.
        :param oef_search_dialogue: the oef search dialogue
        """
        self._check_data_model(service_description, ModelNames.SET_SERVICE_KEY.value)

        key = service_description.values.get("key", None)
        value = service_description.values.get("value", NOT_SPECIFIED)

        if key is None or value is NOT_SPECIFIED:  # pragma: nocover
            raise SOEFException.error("Bad values provided!")

        await self._set_service_key(key, value)
        await self._send_success_response(oef_message, oef_search_dialogue)

    @staticmethod
    def _parse_soef_response(
        response_text: str, check_success: bool = True
    ) -> ElementTree:
        try:
            root = ElementTree.fromstring(response_text)
        except ElementTree.ParseError as e:  # pragma: nocover
            raise SOEFServerBadResponseError(
                f"Failed to parse xml from the response: Error {e}. Text: {response_text}"
            ) from e

        if root.tag != "response":
            raise SOEFServerBadResponseError(
                "Not a valid response. Expected `root.tag = response`, received `root.tag = {root.tag}`"
            )
        if check_success:
            el = root.find("./success")
            if el is None:
                raise SOEFServerBadResponseError(
                    "Bad response, no success value present. Found = {response_text}."
                )
            if str(el.text).strip() != "1":
                raise SOEFServerBadResponseError(  # pragma: nocover
                    "Request was not successful. Found = {response_text}"
                )
        return root

    async def _generic_oef_command(
        self,
        command: str,
        params: Optional[Dict[str, Union[str, List[str]]]] = None,
        unique_page_address: Optional[str] = None,
        check_success: bool = True,
    ) -> ElementTree:
        """
        Set service key from service description.

        :param command: the command
        :param params: the parameters of the command
        :param unique_page_address: the unique page address
        :param check_success: whether or not to check for success

        :return: parsed xml ElementTree
        """
        params = params or {}
        self.logger.debug(f"Perform `{command}` with {params}")
        url = parse.urljoin(
            self.base_url, unique_page_address or self.unique_page_address
        )

        response_text = ""
        try:
            response_text = await self._request_text(
                "get", url=url, params={"command": command, **params}
            )
            parsed_text = self._parse_soef_response(response_text, check_success)
            self.logger.debug(f"`{command}` SUCCESS!")
            return parsed_text
        except (
            asyncio.CancelledError,
            ConcurrentCancelledError,
        ):  # pragma: nocover  # pylint: disable=try-except-raise
            raise
        except Exception as e:
            raise SOEFException.error(
                f"Command: `{command}` Params: `{params}` Response: `{response_text}` Exception: {[e]}"
            ) from e

    async def _set_service_key(self, key: str, value: Union[str, int, float]) -> None:
        """
        Perform set service key command.

        :param key: key to set
        :param value: value to set
        """
        await self._generic_oef_command(
            "set_service_key", {"key": key, "value": str(value)}
        )

    async def _remove_service_key_handler(
        self,
        service_description: Description,
        oef_message: OefSearchMessage,
        oef_search_dialogue: OefSearchDialogue,
    ) -> None:
        """
        Remove service key from service description.

        :param service_description: Service description
        :param oef_message: the oef message.
        :param oef_search_dialogue: the oef search dialogue
        """
        self._check_data_model(service_description, ModelNames.REMOVE_SERVICE_KEY.value)
        key = service_description.values.get("key", None)

        if key is None:  # pragma: nocover
            raise SOEFException.error("Bad values provided!")

        await self._remove_service_key(key)
        await self._send_success_response(oef_message, oef_search_dialogue)

    async def _remove_service_key(self, key: str) -> None:
        """
        Perform remove service key command.

        :param key: key to remove
        """
        await self._generic_oef_command("remove_service_key", {"key": key})

    async def _register_location_handler(
        self,
        service_description: Description,
        oef_message: OefSearchMessage,
        oef_search_dialogue: OefSearchDialogue,
    ) -> None:
        """
        Register service with location.

        :param service_description: Service description
        :param oef_message: the oef message.
        :param oef_search_dialogue: the oef search dialogue
        """
        self._check_data_model(service_description, ModelNames.LOCATION_AGENT.value)

        agent_location = service_description.values.get("location", None)

        if agent_location is None or not isinstance(
            agent_location, Location
        ):  # pragma: nocover
            raise SOEFException.debug("Bad location provided.")

        disclosure_accuracy = service_description.values.get(
            "disclosure_accuracy", None
        )

        if disclosure_accuracy not in [
            None,
            "none",
            "low",
            "medium",
            "high",
            "maximum",
        ]:
            raise SOEFException.debug("Bad disclosure_accuracy.")  # pragma: nocover

        await self._set_location(agent_location, disclosure_accuracy)
        await self._send_success_response(oef_message, oef_search_dialogue)

    async def _send_success_response(
        self,
        oef_message: OefSearchMessage,
        oef_search_dialogue: OefSearchDialogue,
        agents_info: Optional[JSONLike] = None,
    ) -> None:
        """
        Send success message in response to the given dialogue and message.

        :param oef_search_dialogue: the oef search dialogue
        :param oef_message: the oef message
        :param agents_info: the agents info json
        """
        if self.in_queue is None:
            raise ValueError("Inqueue not set!")  # pragma: nocover
        if agents_info is None:
            agents_info = {}
        message = oef_search_dialogue.reply(
            performative=OefSearchMessage.Performative.SUCCESS,
            target_message=oef_message,
            agents_info=AgentsInfo(cast(Dict[str, Any], agents_info)),
        )
        envelope = Envelope(to=message.to, sender=message.sender, message=message)
        await self.in_queue.put(envelope)

    @staticmethod
    def _check_data_model(
        service_description: Description, data_model_name: str
    ) -> None:
        """
        Check data model corresponds.

        Raise exception if not.

        :param service_description: Service description
        :param data_model_name: data model name expected.
        """
        if service_description.data_model.name != data_model_name:  # pragma: nocover
            raise SOEFException.error(
                f"Bad service description! expected {data_model_name} but go {service_description.data_model.name}"
            )

    async def _set_location(
        self, agent_location: Location, disclosure_accuracy: Optional[str] = None
    ) -> None:
        """
        Set the location.

        :param agent_location: the agent location
        :param disclosure_accuracy: the accuracy of the agent location disclosure
        """
        latitude = agent_location.latitude
        longitude = agent_location.longitude
        params: Dict[str, Union[str, List[str]]] = {
            "longitude": str(longitude),
            "latitude": str(latitude),
        }
        await self._generic_oef_command("set_position", params)
        if disclosure_accuracy:
            params = {"accuracy": disclosure_accuracy}
            await self._generic_oef_command(
                "set_find_position_disclosure_accuracy", params,
            )

        self.agent_location = agent_location

    async def _set_personality_piece_handler(
        self,
        service_description: Description,
        oef_message: OefSearchMessage,
        oef_search_dialogue: OefSearchDialogue,
    ) -> None:
        """
        Set the personality piece.

        :param service_description: the service description.
        :param oef_message: the oef message.
        :param oef_search_dialogue: the oef search dialogue
        """
        self._check_data_model(service_description, ModelNames.PERSONALITY_AGENT.value)
        piece = service_description.values.get("piece", None)
        value = service_description.values.get("value", None)

        if not (isinstance(piece, str) and isinstance(value, str)):  # pragma: nocover
            raise SOEFException.debug("Personality piece bad values provided.")

        await self._set_personality_piece(piece, value)
        await self._send_success_response(oef_message, oef_search_dialogue)

    async def _set_personality_piece(self, piece: str, value: str) -> None:
        """
        Set the personality piece.

        :param piece: the piece to be set
        :param value: the value to be set
        """
        params: Dict[str, Union[str, List[str]]] = {
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
        """
        self.logger.debug("Applying to SOEF lobby with address={}".format(self.address))
        url = parse.urljoin(self.base_url, "register")
        params: Dict[str, Union[str, List[str]]] = {
            "api_key": self.api_key,
            "chain_identifier": self.chain_identifier,
            "address": self.address,
            "declared_name": self.declared_name,
        }
        response_text = await self._request_text("get", url=url, params=params)
        root = self._parse_soef_response(response_text, check_success=False)

        self.logger.debug("Root tag: {}".format(root.tag))
        unique_page_address = ""
        unique_token = ""  # nosec
        for child in root:
            self.logger.debug(
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
                f"Agent registration error - page address or token not received. Response text: {response_text}"
            )
        self.logger.debug("Registering agent")
        params = {"token": unique_token}
        await self._generic_oef_command(
            "acknowledge", params, unique_page_address=unique_page_address
        )
        self.unique_page_address = unique_page_address

        await self._set_personality_piece("architecture", "agentframework")

        self.start_periodic_ping_task()

    def start_periodic_ping_task(self) -> None:
        """Start the periodic ping task."""
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
        """
        if self.in_queue is None:
            raise ValueError("Inqueue not set!")  # pragma: nocover
        message = oef_search_dialogue.reply(
            performative=OefSearchMessage.Performative.OEF_ERROR,
            target_message=oef_search_message,
            oef_error_operation=oef_error_operation,
        )
        envelope = Envelope(to=message.to, sender=message.sender, message=message,)
        await self.in_queue.put(envelope)

    async def unregister_service(
        self, oef_message: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Unregister a service on the SOEF.

        :param oef_message: OefSearchMessage
        :param oef_search_dialogue: OefSearchDialogue
        """
        service_description = oef_message.service_description

        data_model_handlers = {
            "location_agent": self._unregister_agent,
            "remove_service_key": self._remove_service_key_handler,
        }  # type: Dict[str, Callable]
        data_model_name = service_description.data_model.name

        if data_model_name not in data_model_handlers:  # pragma: nocover
            raise SOEFException.error(
                f'Data model name: {data_model_name} is not supported for `unregister`. Valid models for performative {oef_message.performative} are: {", ".join(data_model_handlers.keys())}'
            )

        handler = data_model_handlers[data_model_name]
        if data_model_name == "location_agent":
            await handler(oef_message, oef_search_dialogue)
        else:
            await handler(service_description, oef_message, oef_search_dialogue)

    async def _unregister_agent(
        self,
        oef_message: Optional[OefSearchMessage] = None,
        oef_search_dialogue: Optional[OefSearchDialogue] = None,
    ) -> None:
        """
        Unregister a location agent from the SOEF.

        :param oef_message: OefSearchMessage
        :param oef_search_dialogue: OefSearchDialogue
        """
        if not self._unregister_lock:
            raise ValueError(  # pragma: nocover
                "unregistered lock is not set, please call connect!"
            )

        async with self._unregister_lock:
            if self.unique_page_address is None:  # pragma: nocover
                self.logger.debug(
                    "The service is not registered to the simple OEF. Cannot unregister."
                )
                return

            task = asyncio.ensure_future(
                self._generic_oef_command("unregister", check_success=False)
            )

            try:
                response = await asyncio.shield(task)
            finally:
                response = await task
                if (
                    "<response><message>Goodbye!</message></response>" not in response
                ):  # pragma: nocover
                    self.logger.debug(f"No Goodbye response. Response={response}")
                self.unique_page_address = None
                await self._stop_periodic_ping_task()
        if oef_message is not None and oef_search_dialogue is not None:
            await self._send_success_response(oef_message, oef_search_dialogue)

    async def _stop_periodic_ping_task(self) -> None:
        """Cancel periodic ping task."""
        if self._ping_periodic_task and not self._ping_periodic_task.done():
            self._ping_periodic_task.cancel()
            self._ping_periodic_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._ping_periodic_task
            self._ping_periodic_task = None

    async def _check_server_reachable(self) -> None:
        """Check network connection is ok."""
        try:
            await asyncio.wait_for(
                self._request_text(
                    "get", self.base_url, timeout=self.connection_check_timeout
                ),
                timeout=self.connection_check_timeout,
            )
        except asyncio.TimeoutError:
            raise SOEFNetworkConnectionError(
                f"Server can not be reached within timeout={self.connection_check_timeout}!"
            )

    async def connect(self) -> None:
        """Connect channel set queues and executor pool."""
        self._loop = asyncio.get_event_loop()

        reachable_check_count = 0
        while reachable_check_count < self.connection_check_max_retries:
            reachable_check_count += 1
            try:
                await self._check_server_reachable()
                reachable_check_count = self.connection_check_max_retries
            except Exception as e:  # pylint: disable=broad-except # pragma: nocover
                if reachable_check_count == self.connection_check_max_retries:
                    raise e
                self.logger.debug(f"Exception during SOEF reachability check: {e}.")

        self.in_queue = asyncio.Queue()
        self._find_around_me_queue = asyncio.Queue()
        self._unregister_lock = asyncio.Lock()
        self._executor_pool = ThreadPoolExecutor(max_workers=10)
        self._find_around_me_processor_task = self._loop.create_task(
            self._find_around_me_processor()
        )
        # make sure we first unregister, in case of improper previous termination
        try:
            await self._unregister_agent()
        except Exception as e:  # pylint: disable=broad-except # pragma: nocover
            if "<reason>Bad Request</reason><detail>agent lookup failed" not in str(e):
                # i.e. we're not trying to unregister and already unregistered agent
                raise e
            self.logger.debug("Unregister on SOEF failed. Agent not registered.")
            self.unique_page_address = None

    async def disconnect(self) -> None:
        """Disconnect unregisters any potential services still registered."""
        await self._stop_periodic_ping_task()

        if self.in_queue is None:
            raise ValueError("Queue is not set, use connect first!")  # pragma: nocover

        if self._find_around_me_processor_task:
            if not self._find_around_me_processor_task.done():
                self._find_around_me_processor_task.cancel()
            await self._find_around_me_processor_task

        try:
            await self._unregister_agent()
        except Exception as e:  # pylint: disable=broad-except # pragma: nocover
            self.logger.exception(str(e))

        await self.in_queue.put(None)
        self._find_around_me_queue = None

    async def search_services(
        self, oef_message: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Search services on the SOEF.

        :param oef_message: OefSearchMessage
        :param oef_search_dialogue: OefSearchDialogue
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
        Add find agent task to queue to process in dedicated loop respectful to timeouts.

        :param oef_message: OefSearchMessage
        :param oef_search_dialogue: OefSearchDialogue
        :param radius: the radius in which to search
        :param params: the parameters for the query
        """
        if not self._find_around_me_queue:
            raise ValueError("SOEFChannel not started.")  # pragma: nocover
        await self._find_around_me_queue.put(
            (oef_message, oef_search_dialogue, radius, params)
        )

    async def _find_around_me_handle_request(
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
        """
        if self.in_queue is None:
            raise ValueError("Inqueue not set!")  # pragma: nocover
        self.logger.debug("Searching in radius={} of myself".format(radius))

        root = await self._generic_oef_command(
            "find_around_me", {"range_in_km": [str(radius)], **params}
        )
        agents = {}  # type: Dict[str, Dict[str, Union[str, Dict[str, str]]]]
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

                            range_in_km = agent.find("range_in_km").text
                            agents[agent_address] = {
                                "chain_identifier": chain_identifier,
                                "address": agent_address,
                                "range_in_km": range_in_km,
                                **agent.attrib,
                            }
                            location = agent.find("./location")
                            if location:
                                agents[agent_address]["location"] = {
                                    **location.attrib,
                                    "longitude": location.find("longitude").text,
                                    "latitude": location.find("latitude").text,
                                }

        message = oef_search_dialogue.reply(
            performative=OefSearchMessage.Performative.SEARCH_RESULT,
            target_message=oef_message,
            agents=tuple(agents.keys()),
            agents_info=AgentsInfo(agents),
        )
        envelope = Envelope(to=message.to, sender=message.sender, message=message,)
        await self.in_queue.put(envelope)


class SOEFConnection(Connection):
    """The SOEFConnection connects the Simple OEF to the mailbox."""

    connection_id = PUBLIC_ID
    DEFAULT_CONNECTION_CHECK_TIMEOUT: float = 15.0
    DEFAULT_CONNECTION_CHECK_MAX_RETRIES: int = 3

    def __init__(self, **kwargs: Any) -> None:
        """Initialize."""
        if kwargs.get("configuration") is None:  # pragma: nocover
            kwargs["excluded_protocols"] = kwargs.get("excluded_protocols") or []
            kwargs["restricted_to_protocols"] = kwargs.get("excluded_protocols") or [
                OefSearchMessage.protocol_id
            ]

        super().__init__(**kwargs)
        api_key = cast(str, self.configuration.config.get("api_key"))
        connection_check_timeout = cast(
            float,
            self.configuration.config.get(
                "connection_check_timeout", self.DEFAULT_CONNECTION_CHECK_TIMEOUT
            ),
        )
        connection_check_max_retries = cast(
            int,
            self.configuration.config.get(
                "connection_check_max_retries",
                self.DEFAULT_CONNECTION_CHECK_MAX_RETRIES,
            ),
        )
        is_https = cast(bool, self.configuration.config.get("is_https", True))
        soef_addr = cast(str, self.configuration.config.get("soef_addr"))
        soef_port = cast(int, self.configuration.config.get("soef_port"))
        chain_identifier = cast(str, self.configuration.config.get("chain_identifier"))
        token_storage_path = cast(
            Optional[str], self.configuration.config.get("token_storage_path")
        )
        not_none_params = {
            "api_key": api_key,
            "soef_addr": soef_addr,
            "soef_port": soef_port,
        }
        for param_name, param_value in not_none_params.items():  # pragma: nocover
            if param_value is None:
                raise ValueError(f"{param_name} must be set!")
        self.api_key = api_key
        self.is_https = is_https
        self.soef_addr = soef_addr
        self.soef_port = soef_port
        self.channel = SOEFChannel(
            self.address,
            self.api_key,
            self.is_https,
            self.soef_addr,
            self.soef_port,
            data_dir=self.data_dir,
            chain_identifier=chain_identifier,
            token_storage_path=token_storage_path,
            connection_check_timeout=connection_check_timeout,
            connection_check_max_retries=connection_check_max_retries,
        )

    async def connect(self) -> None:
        """
        Connect to the channel.

        :raises Exception if the connection to the OEF fails.
        """
        if self.is_connected:  # pragma: nocover
            return

        with self._connect_context():
            await self.channel.connect()

    @property
    def in_queue(self) -> Optional[asyncio.Queue]:
        """Return in_queue of the channel."""
        return self.channel.in_queue

    async def disconnect(self) -> None:
        """Disconnect from the channel."""
        if self.is_disconnected:  # pragma: nocover
            return
        if self.in_queue is None:
            raise ValueError("In queue not set.")  # pragma: nocover
        self.state = ConnectionStates.disconnecting
        await self.channel.disconnect()
        self.state = ConnectionStates.disconnected

    async def receive(self, *args: Any, **kwargs: Any) -> Optional["Envelope"]:
        """
        Receive an envelope. Blocking.

        :param args: positional arguments
        :param kwargs: keyword arguments
        :return: the envelope received, or None.
        """
        try:
            if self.in_queue is None:
                raise ValueError("In queue not set.")  # pragma: nocover
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
        """
        if self.is_connected:
            await self.channel.send(envelope)
