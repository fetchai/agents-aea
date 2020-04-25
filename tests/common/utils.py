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
"""This module contains some utils for testing purposes."""

import time
from contextlib import contextmanager
from typing import Callable, Tuple, Type, Union


from aea.aea import AEA
from aea.configurations.base import ProtocolId
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.skills.base import Behaviour, Handler


DEFAULT_SLEEP = 0.0001
DEFAULT_TIMEOUT = 3


class TimeItResult:
    """Class to store execution time for timeit_context."""

    def __init__(self):
        """Init with time passed = -1."""
        self.time_passed = -1


@contextmanager
def timeit_context():
    """
    Context manager to measure execution time of code in context.

    :return TimeItResult

    example:
    with timeit_context() as result:
        do_long_code()
    print("Long code takes ", result.time_passed)
    """
    result = TimeItResult()
    started_time = time.time()
    try:
        yield result
    finally:
        result.time_passed = time.time() - started_time


class AeaTool:
    """
    AEA test wrapper tool.

    To make testing AEA instances easier
    """

    def __init__(self, aea: AEA):
        """
        Instantiate AeaTool.

        :param aea: AEA instance to wrap for tests.
        """
        self.aea = aea

    def setup(self) -> "AeaTool":
        """Call AEA._start_setup."""
        self.aea._start_setup()
        return self

    def spin_main_loop(self) -> "AeaTool":
        """
        Run one cycle of agent's main loop.

        :return: AeaTool
        """
        old_timeout, self.aea._timeout = self.aea._timeout, 0
        self.aea._spin_main_loop()
        self.aea._timeout = old_timeout
        return self

    def wait_outbox_empty(
        self, sleep: float = DEFAULT_SLEEP, timeout: float = DEFAULT_TIMEOUT
    ) -> "AeaTool":
        """
        Wait till agent's outbox consumed completely.

        :return: AeaTool
        """
        start_time = time.time()
        while not self.aea.outbox.empty():
            time.sleep(sleep)
            if time.time() - start_time > timeout:
                raise Exception("timeout")
        return self

    def wait_inbox(
        self, sleep: float = DEFAULT_SLEEP, timeout: float = DEFAULT_TIMEOUT
    ) -> "AeaTool":
        """
        Wait till something appears on agents inbox and spin loop.

        :return: AeaTool
        """
        start_time = time.time()
        while self.aea.inbox.empty():
            time.sleep(sleep)
            if time.time() - start_time > timeout:
                raise Exception("timeout")
        return self

    def react_one(self) -> "AeaTool":
        """
        Run AEA.react once to process inbox messages.

        :return: AeaTool
        """
        self.aea._react_one()
        return self

    def act_one(self) -> "AeaTool":
        """
        Run AEA.act once to process behaviours act.

        :return: AeaTool
        """
        self.aea.act()
        return self

    @classmethod
    def dummy_default_message(
        cls,
        dialogue_reference: Tuple[str, str] = ("", ""),
        message_id: int = 1,
        target: int = 0,
        performative: DefaultMessage.Performative = DefaultMessage.Performative.BYTES,
        content: Union[str, bytes] = "hello world!",
    ) -> Message:
        """
        Construct simple message, all arguments are optional.

        :return: Message
        """
        if isinstance(content, str):
            content = content.encode("utf-8")

        return DefaultMessage(
            dialogue_reference=dialogue_reference,
            message_id=message_id,
            target=target,
            performative=performative,
            content=content,
        )

    @classmethod
    def dummy_envelope(
        cls,
        to: str = "test",
        sender: str = "test",
        protocol_id: ProtocolId = DefaultMessage.protocol_id,
        message: Message = None,
    ) -> Envelope:
        """
        Create envelope, if message is not passed use .dummy_message method.

        :return: Envelope
        """
        message = message or cls.dummy_default_message()
        return Envelope(
            to=to,
            sender=sender,
            protocol_id=protocol_id,
            message=DefaultSerializer().encode(message),
        )

    def put_inbox(self, envelope: Envelope) -> None:
        """Add an envelope to agent's inbox."""
        self.aea._multiplexer.in_queue.put(envelope)

    def is_inbox_empty(self) -> bool:
        """Check there is no messages in inbox."""
        return self.aea._multiplexer.in_queue.empty()

    def set_execution_timeout(self, timeout: float) -> None:
        """Set act/handle exeution timeout for AEE.

        :param timeout: amount of time to limit single act/handle to execute.
        """
        self.aea._execution_timeout = timeout

    def stop(self) -> None:
        """Stop AEA instance."""
        self.aea.stop()


def make_handler_cls_from_funcion(func: Callable) -> Type[Handler]:
    """Make Handler class with handler function call `func`.

    :param func: function or callable to be called from Handler.handle method
    :return: Handler class
    """
    # pydocstyle: igonre # case confilct with black
    class TestHandler(Handler):
        SUPPORTED_PROTOCOL = DefaultMessage.protocol_id

        def setup(self):
            pass

        def teardown(self):
            pass

        def handle(self, msg):
            func(self)

    return TestHandler


def make_behaviour_cls_from_funcion(func: Callable) -> Type[Behaviour]:
    """Make Behaviour class with act function call `func`.

    :param func: function or callable to be called from Behaviour.act method
    :return: Behaviour class
    """
    # pydocstyle: igonre # case confilct with black
    class TestBehaviour(Behaviour):
        def act(self) -> None:
            func(self)

        def setup(self):
            self._completed = False

        def teardown(self):
            pass

    return TestBehaviour
