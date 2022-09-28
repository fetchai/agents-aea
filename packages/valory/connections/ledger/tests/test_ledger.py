# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

"""This module contains the tests of the ledger connection module."""

# pylint: skip-file

import asyncio
import logging
import time
from asyncio import Task
from threading import Thread
from typing import Any, Callable, Dict, FrozenSet, Tuple, Type, cast
from unittest import mock

import pytest
from aea_ledger_ethereum import EthereumCrypto

from aea.common import Address
from aea.configurations.base import ConnectionConfig
from aea.connections.base import ConnectionStates
from aea.crypto.base import LedgerApi
from aea.exceptions import AEAEnforceError
from aea.helpers.async_utils import AsyncState
from aea.mail.base import Envelope
from aea.multiplexer import Multiplexer
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue, DialogueLabel, Dialogues

from packages.valory.connections.ledger.base import RequestDispatcher
from packages.valory.connections.ledger.connection import LedgerConnection
from packages.valory.connections.ledger.tests.conftest import make_ledger_api_connection
from packages.valory.protocols.ledger_api import LedgerApiMessage
from packages.valory.protocols.ledger_api.custom_types import Kwargs


SOME_SKILL_ID = "some/skill:0.1.0"
NON_BLOCKING_TIME = 1
BLOCKING_TIME = 100
TOLERANCE = 1
WAIT_TIME_AMONG_TASKS = 0.1


def dummy_task_wrapper(waiting_time: float, result_message: LedgerApiMessage) -> Task:
    """Create a dummy task that simply waits for a given `waiting_time` and returns a given `result_message`."""

    async def dummy_task(*_: Any) -> LedgerApiMessage:
        """Wait for the given `waiting_time` and return the given `result_message`."""
        await asyncio.sleep(waiting_time)
        return result_message

    task = asyncio.create_task(dummy_task())
    return task


class TestLedgerConnection:
    """Test `LedgerConnection` class."""

    @pytest.mark.asyncio
    async def test_not_hanging(self) -> None:
        """Test that the connection does not hang and that the tasks cannot get blocked."""
        # create configurations for the test, re bocking and non-blocking tasks' waiting times
        assert (
            NON_BLOCKING_TIME + TOLERANCE + WAIT_TIME_AMONG_TASKS < BLOCKING_TIME
        ), "`NON_BLOCKING_TIME + TOLERANCE + WAIT_TIME_AMONG_TASKS` should be less than the `BLOCKING_TIME`."

        # setup a dummy ledger connection
        ledger_connection = LedgerConnection(
            configuration=ConnectionConfig("ledger", "valory", "0.19.0"),
            data_dir="test_data_dir",
        )

        # connect() is called by the multiplexer
        await ledger_connection.connect()

        # once a connection is ready, `receive()` is called by the multiplexer
        receive_task = asyncio.ensure_future(ledger_connection.receive())

        # create a blocking task lasting `BLOCKING_TIME` secs
        blocking_task = dummy_task_wrapper(
            BLOCKING_TIME,
            LedgerApiMessage(
                LedgerApiMessage.Performative.ERROR, _body={"data": b"blocking_task"}  # type: ignore
            ),
        )
        blocking_dummy_envelope = Envelope(
            to="test_blocking_to",
            sender="test_blocking_sender",
            message=LedgerApiMessage(LedgerApiMessage.Performative.ERROR),  # type: ignore
        )
        with mock.patch.object(
            LedgerConnection, "_schedule_request", return_value=blocking_task
        ):
            await ledger_connection.send(blocking_dummy_envelope)

        # create a non-blocking task lasting `NON_BLOCKING_TIME` secs, after `WAIT_TIME_AMONG_TASKS`
        await asyncio.sleep(WAIT_TIME_AMONG_TASKS)
        normal_task = dummy_task_wrapper(
            NON_BLOCKING_TIME,
            LedgerApiMessage(LedgerApiMessage.Performative.ERROR, _body={"data": b"normal_task"}),  # type: ignore
        )
        normal_dummy_envelope = Envelope(
            to="test_normal_to",
            sender="test_normal_sender",
            message=LedgerApiMessage(LedgerApiMessage.Performative.ERROR),  # type: ignore
        )
        with mock.patch.object(
            LedgerConnection, "_schedule_request", return_value=normal_task
        ):
            await ledger_connection.send(normal_dummy_envelope)

        # sleep for `NON_BLOCKING_TIME + TOLERANCE`
        await asyncio.sleep(NON_BLOCKING_TIME + TOLERANCE)

        # the normal task should be finished
        assert normal_task.done(), "Normal task should be done at this point."

        # the `receive_task` should be done, and not await for the `blocking_task`
        assert receive_task.done(), "Receive task is blocked by blocking task!"

        # the blocking task should not be done
        assert not blocking_task.done(), "Blocking task should be still running."
        # cancel remaining task before ending test
        blocking_task.cancel()


class TestRequestDispatcher:
    """Test `RequestDispatcher` class."""

    dispatcher: RequestDispatcher
    loop: asyncio.AbstractEventLoop

    def setup(self) -> None:
        """Setup test vars."""
        logger = logging.getLogger(type(self).__class__.__name__)
        state = AsyncState(ConnectionStates.connected)
        self.loop = asyncio.get_event_loop()
        self.dispatcher = DummyRequestDispatcher(
            logger=logger, connection_state=state, loop=self.loop
        )

    def dummy_func(self, sleep: float) -> bool:
        """A dummy function that sleeps and returns True."""
        time.sleep(sleep)
        return True

    async def dummy_async_func(self, sleep: float) -> bool:
        """A dummy async function that sleeps and returns True."""
        await asyncio.sleep(sleep)
        return True

    @pytest.mark.asyncio
    async def test_wait_for_happy_path(self) -> None:
        """Tests that wait_for works when timeout is bigger than execution time of callable."""
        should_finish_in = 0.5
        tolerance = 0.5
        timeout = should_finish_in + tolerance

        return_value = await self.dispatcher.wait_for(
            lambda: self.dummy_func(should_finish_in), timeout=timeout
        )
        assert return_value, "dummy_func() should've returned True"

    @pytest.mark.asyncio
    async def test_wait_for_raise_excp(self) -> None:
        """Tests that wait_for works when timeout is less than execution time of callable."""
        timeout = 0.25
        timeout_increase = 0.5
        should_finish_in = timeout + timeout_increase

        with pytest.raises(asyncio.TimeoutError):
            await self.dispatcher.wait_for(
                lambda: self.dummy_func(should_finish_in), timeout=timeout
            )

    @pytest.mark.asyncio
    async def test_wait_for_coroutine(self) -> None:
        """Tests that an error is thrown when a coroutine is passed."""
        should_finish_in = 0.0  # this value is irrelevant to the result of the test
        with pytest.raises(AEAEnforceError):
            await self.dispatcher.wait_for(self.dummy_async_func, should_finish_in)


class DummyLedgerApiMessage(LedgerApiMessage):
    """Implement a dummy `LedgerApiMessage`, which contains performatives for the normal and blocking tasks."""

    class Performative(Message.Performative):
        """Performatives for the ledger_api protocol."""

        NORMAL = "normal"
        BLOCKING = "blocking"
        GET_NORMAL = "get_normal"
        GET_BLOCKING = "get_blocking"

    def __init__(
        self,
        performative: Performative,
        dialogue_reference: Tuple[str, str] = ("", ""),
        message_id: int = 1,
        target: int = 0,
        **kwargs: Any,
    ):
        """Initialise an instance of `DummyLedgerApiMessage`."""
        Message.__init__(
            self,
            dialogue_reference=dialogue_reference,
            message_id=message_id,
            target=target,
            performative=DummyLedgerApiMessage.Performative(performative),
            **kwargs,
        )

    def _is_consistent(self) -> bool:
        """Dummy consistency checks."""


class DummyLedgerApiDialogue(Dialogue):
    """Implement a dummy `LedgerApiDialogue`."""

    INITIAL_PERFORMATIVES: FrozenSet[Message.Performative] = frozenset(
        {
            DummyLedgerApiMessage.Performative.GET_NORMAL,
            DummyLedgerApiMessage.Performative.GET_BLOCKING,
        }
    )
    TERMINAL_PERFORMATIVES: FrozenSet[Message.Performative] = frozenset(
        {
            DummyLedgerApiMessage.Performative.NORMAL,
            DummyLedgerApiMessage.Performative.BLOCKING,
        }
    )
    VALID_REPLIES: Dict[Message.Performative, FrozenSet[Message.Performative]] = {
        DummyLedgerApiMessage.Performative.GET_NORMAL: frozenset(
            {DummyLedgerApiMessage.Performative.NORMAL}
        ),
        DummyLedgerApiMessage.Performative.GET_BLOCKING: frozenset(
            {DummyLedgerApiMessage.Performative.BLOCKING}
        ),
    }

    class Role(Dialogue.Role):
        """This class defines the agent's role in a ledger_api dialogue."""

        AGENT = "agent"

    class EndState(Dialogue.EndState):
        """This class defines the end states of a ledger_api dialogue."""

        SUCCESSFUL = 0

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: Dialogue.Role,
        message_class: Type[DummyLedgerApiMessage] = DummyLedgerApiMessage,
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for
        :param message_class: the message class used
        """
        Dialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            message_class=message_class,
            self_address=self_address,
            role=role,
        )


class DummyLedgerApiDialogues(Dialogues):
    """Implement a dummy `LedgerApiDialogues`."""

    END_STATES = frozenset({DummyLedgerApiDialogue.EndState.SUCCESSFUL})

    def __init__(self, self_address: Address, **kwargs: Any) -> None:
        """Initialize dialogues."""

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> Dialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message"""
            return DummyLedgerApiDialogue.Role.AGENT

        Dialogues.__init__(
            self,
            self_address=self_address,
            end_states=cast(FrozenSet[Dialogue.EndState], self.END_STATES),
            role_from_first_message=role_from_first_message,
            message_class=DummyLedgerApiMessage,
            dialogue_class=DummyLedgerApiDialogue,
        )


class DummyRequestDispatcher(RequestDispatcher):
    """Implement a dummy request dispatcher."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the dispatcher."""
        super().__init__(*args, **kwargs)
        self.block = True
        self._ledger_api_dialogues = DummyLedgerApiDialogues(
            LedgerConnection.connection_id.__str__()
        )

    @staticmethod
    def get_normal(
        _api: LedgerApi,
        message: DummyLedgerApiMessage,
        dialogue: DummyLedgerApiDialogue,
    ) -> DummyLedgerApiMessage:
        """
        Send the request 'get_normal'.

        :param _api: the API object.
        :param message: the Ledger API message
        :param dialogue: the Ledger API dialogue
        :return: response Ledger API message
        """
        time.sleep(NON_BLOCKING_TIME)

        return cast(
            DummyLedgerApiMessage,
            dialogue.reply(
                performative=DummyLedgerApiMessage.Performative.NORMAL,  # type: ignore
                target_message=message,
                data=b"normal_task",
                ledger_id=message.ledger_id,
            ),
        )

    def get_blocking(
        self,
        _api: LedgerApi,
        message: DummyLedgerApiMessage,
        dialogue: DummyLedgerApiDialogue,
    ) -> DummyLedgerApiMessage:
        """
        Send the request 'get_blocking'.

        :param _api: the API object.
        :param message: the Ledger API message
        :param dialogue: the Ledger API dialogue
        :return: response Ledger API message
        """
        while self.block:
            time.sleep(0.05)

        return cast(
            DummyLedgerApiMessage,
            dialogue.reply(
                performative=DummyLedgerApiMessage.Performative.BLOCKING,  # type: ignore
                target_message=message,
                data=b"blocking_task",
                ledger_id=message.ledger_id,
            ),
        )

    @property
    def dialogues(self) -> Dialogues:
        """Dummy dialogues property."""
        return self._ledger_api_dialogues

    def get_error_message(
        self, exception: Exception, api: LedgerApi, message: Message, dialogue: Dialogue
    ) -> Message:
        """Dummy `get_error_message`."""

    def get_ledger_id(self, message: Message) -> str:
        """Dummy `get_ledger_id`."""
        if not isinstance(message, DummyLedgerApiMessage):  # pragma: nocover
            raise ValueError("argument is not a `DummyLedgerApiMessage` instance.")
        return message.ledger_id


class LedgerConnectionWithDummyDispatcher(LedgerConnection):
    """An extended `LedgerConnection` which utilizes the `DummyDispatcher`."""

    async def connect(self) -> None:
        """Set up the connection."""
        if self.is_connected:  # pragma: nocover
            return

        self.state = ConnectionStates.connecting

        self._ledger_dispatcher = DummyRequestDispatcher(  # type: ignore
            logger=self.logger,
            connection_state=self._state,
            loop=self.loop,
            api_configs=self.api_configs,
            retry_attempts=self.request_retry_attempts,
            retry_timeout=self.request_retry_timeout,
        )

        self._response_envelopes = asyncio.Queue()
        self.state = ConnectionStates.connected


class TestLedgerConnectionWithMultiplexer:
    """Test `LedgerConnection` class, using the multiplexer."""

    running_loop: asyncio.AbstractEventLoop
    thread_loop: Thread
    multiplexer: Multiplexer
    ledger_connection: LedgerConnectionWithDummyDispatcher
    make_ledger_connection_callable: Callable = make_ledger_api_connection
    ledger_api_dialogues: DummyLedgerApiDialogues

    @classmethod
    def setup(cls) -> None:
        """Setup the test class."""
        # set up a multiplexer with the required ledger connection
        cls.running_loop = asyncio.new_event_loop()
        cls.thread_loop = Thread(target=cls.running_loop.run_forever)
        cls.thread_loop.start()
        cls.multiplexer = Multiplexer(
            [
                LedgerConnectionWithDummyDispatcher(
                    configuration=ConnectionConfig("ledger", "valory", "0.19.0"),
                    data_dir="test_data_dir",
                )
            ],
            loop=cls.running_loop,
        )
        cls.multiplexer.connect()
        # the ledger connection's connect() is called by the multiplexer
        # once a connection is ready, `receive()` is called by the multiplexer
        cls.ledger_connection = cast(
            LedgerConnectionWithDummyDispatcher, cls.multiplexer.connections[0]
        )
        assert cls.ledger_connection._ledger_dispatcher is not None
        cls.ledger_api_dialogues = cast(
            DummyLedgerApiDialogues,
            cls.ledger_connection._ledger_dispatcher._ledger_api_dialogues,
        )

    @classmethod
    def teardown(cls) -> None:
        """Tear down the multiplexer."""
        cls.ledger_connection._ledger_dispatcher.block = False  # type: ignore
        if cls.multiplexer.is_connected:
            cls.multiplexer.disconnect()
        cls.running_loop.call_soon_threadsafe(cls.running_loop.stop)
        cls.thread_loop.join()

    def create_ledger_dialogues(
        self, blocking: bool = True
    ) -> Tuple[DummyLedgerApiMessage, DummyLedgerApiDialogues]:
        """Create a dialogue."""
        if blocking:
            performative = DummyLedgerApiMessage.Performative.GET_BLOCKING
            _callable = "get_blocking"
        else:
            performative = DummyLedgerApiMessage.Performative.GET_NORMAL
            _callable = "get_normal"

        return cast(
            Tuple[DummyLedgerApiMessage, DummyLedgerApiDialogues],
            self.ledger_api_dialogues.create(
                counterparty=str(self.ledger_connection.connection_id),
                performative=performative,  # type: ignore
                ledger_id=EthereumCrypto.identifier,
                callable=_callable,
                args=(),
                kwargs=Kwargs({}),
            ),
        )

    @staticmethod
    def create_envelope(request: DummyLedgerApiMessage) -> Envelope:
        """Create a dummy envelope."""
        return Envelope(
            to=request.to,
            sender=request.sender,
            message=request,
        )

    @pytest.mark.asyncio
    async def test_not_hanging_with_multiplexer(self) -> None:
        """Test that the connection does not hang and that the tasks cannot get blocked, using the multiplexer."""
        # create configurations for the test, re bocking and non-blocking tasks' waiting times
        assert (
            NON_BLOCKING_TIME + TOLERANCE + WAIT_TIME_AMONG_TASKS < BLOCKING_TIME
        ), "`NON_BLOCKING_TIME + TOLERANCE + WAIT_TIME_AMONG_TASKS` should be less than the `blocking_time`."
        assert self.ledger_connection._ledger_dispatcher.block  # type: ignore

        # create a blocking task lasting `BLOCKING_TIME` secs
        request, _ = self.create_ledger_dialogues()
        request._sender = SOME_SKILL_ID
        blocking_dummy_envelope = TestLedgerConnectionWithMultiplexer.create_envelope(
            request
        )
        self.multiplexer.put(blocking_dummy_envelope)

        # create a non-blocking task lasting `NON_BLOCKING_TIME` secs, after `WAIT_TIME_AMONG_TASKS`
        await asyncio.sleep(WAIT_TIME_AMONG_TASKS)

        request, _ = self.create_ledger_dialogues(blocking=False)
        request._sender = SOME_SKILL_ID
        normal_dummy_envelope = TestLedgerConnectionWithMultiplexer.create_envelope(
            request
        )
        self.multiplexer.put(normal_dummy_envelope)

        # the response envelopes of the ledger connection should be empty
        assert (
            self.ledger_connection.response_envelopes.empty()
        ), "The response envelopes of the ledger connection should be empty."
        # `receive()` should not be done,
        # and multiplexer's `_receiving_loop` should be still running and have an empty `in_queue`
        assert (
            len(self.multiplexer.in_queue.queue) == 0
        ), "The multiplexer's `in_queue` should not contain anything."

        # sleep for `NON_BLOCKING_TIME + TOLERANCE`
        await asyncio.sleep(NON_BLOCKING_TIME + TOLERANCE)

        # `receive()` should be done,
        # and multiplexer's `_receiving_loop` should have put the `normal_dummy_envelope` in the `in_queue`
        envelope = self.multiplexer.get(block=True)
        assert envelope is not None
        message = envelope.message
        assert isinstance(message, DummyLedgerApiMessage)
        assert (
            message.data == b"normal_task"
        ), "Normal task should be the first item in the multiplexer's `in_queue`."
        assert self.ledger_connection._ledger_dispatcher.block  # type: ignore
