# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
import asyncio
import filecmp
import os
import subprocess  # nosec
import sys
import time
from contextlib import contextmanager
from functools import wraps
from threading import Thread
from typing import Any, Callable, List, Optional, Set, Tuple, Type, Union

import pytest

from aea.aea import AEA
from aea.configurations.base import PublicId
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.skills.base import Behaviour, Handler

from packages.fetchai.protocols.default.message import DefaultMessage

from tests.conftest import ROOT_DIR


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
        self.aea.setup()
        return self

    def teardown(self) -> "AeaTool":
        """Call AEA.teardown."""
        self.aea.teardown()
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

    def handle_envelope(self, envelope) -> "AeaTool":
        """
        Run AEA.react once to process inbox messages.

        :return: AeaTool
        """
        self.aea.handle_envelope(envelope)
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
        protocol_specification_id: PublicId = DefaultMessage.protocol_specification_id,
        message: Message = None,
    ) -> Envelope:
        """
        Create envelope, if message is not passed use .dummy_message method.

        :return: Envelope
        """
        message = message or cls.dummy_default_message()
        message.sender = sender
        message.to = to
        return Envelope(
            to=to,
            sender=sender,
            protocol_specification_id=protocol_specification_id,
            message=message,
        )

    def put_inbox(self, envelope: Envelope) -> None:
        """Add an envelope to agent's inbox."""
        self.aea.runtime.multiplexer.in_queue.put(envelope)

    def is_inbox_empty(self) -> bool:
        """Check there is no messages in inbox."""
        return self.aea.runtime.multiplexer.in_queue.empty()

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
    # pydocstyle: ignore # case conflicts with black # noqa: E800
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
    # pydocstyle: ignore # case conflicts with black # noqa: E800
    class TestBehaviour(Behaviour):
        def act(self) -> None:
            func(self)

        def setup(self):
            self._completed = False

        def teardown(self):
            pass

    return TestBehaviour


def run_in_root_dir(fn) -> Callable:
    """
    Chdir to ROOT DIR and return back during tests.

    Decorator.

    :param fn: function to decorate

    :return: wrapped function
    """
    # pydocstyle: ignore # case conflicts with black # noqa: E800
    @wraps(fn)
    def wrap(*args, **kwargs) -> Any:
        """Do a chdir."""
        cwd = os.getcwd()
        os.chdir(ROOT_DIR)
        try:
            return fn(*args, **kwargs)
        finally:
            os.chdir(cwd)

    return wrap


@contextmanager
def run_in_thread(fn, timeout=10, on_exit=None, **kwargs):
    """Run a function in contextmanager and test and awaits it completed."""
    thread = Thread(target=fn, **kwargs)
    thread.daemon = True
    thread.start()
    try:
        yield
    finally:
        if on_exit:
            on_exit()
        thread.join(timeout)
        if thread.is_alive():
            raise Exception("Thread was not stopped!")


def wait_for_condition(condition_checker, timeout=2, error_msg="Timeout", period=0.001):
    """Wait for condition to occur in selected timeout."""

    start_time = time.time()
    while not condition_checker():
        time.sleep(period)
        if time.time() > start_time + timeout:
            raise TimeoutError(error_msg)


async def wait_for_condition_async(
    condition_checker, timeout=2, error_msg="Timeout", period=0.001
):  # pragma: nocover
    """Wait for condition to occur in selected timeout."""

    start_time = time.time()
    while not condition_checker():
        await asyncio.sleep(period)
        if time.time() > start_time + timeout:
            raise TimeoutError(error_msg)


def are_dirs_equal(
    dir1: Union[str, os.PathLike],
    dir2: Union[str, os.PathLike],
    ignore: Optional[List[str]] = None,
) -> bool:
    """
    Compare the content of two directories, recursively.

    :param dir1: the left operand.
    :param dir2: the right operand.
    :param ignore: is a list of names to ignore (see dircmp docs regarding 'ignore').
    :return: True if the directories are equal, False otherwise.
    """
    ignore = ignore or None
    left_only, right_only, diff = dircmp_recursive(
        filecmp.dircmp(dir1, dir2, ignore=ignore)
    )
    return left_only == right_only == diff == set()


def dircmp_recursive(dircmp_obj: filecmp.dircmp) -> Tuple[Set[str], Set[str], Set[str]]:
    """
    Compare the content of two directories, recursively.

    :param dircmp_obj: the filecmp.dircmp object.
    :return: three sets:
     - the set of files that are only in the left operand
     - the set of files that are only in the right operand
     - the set of files in both operands, but that differ.
    """

    def _dircmp_recursive(
        dircmp_obj: filecmp.dircmp, prefix: str = ""
    ) -> Tuple[Set[str], Set[str], Set[str]]:
        """
        Helper private function that also accepts the 'prefix' parameter.

        It is used to keep track of the path prefix during the recursive calls.
        """

        def join_with_prefix(suffix: str) -> str:
            return os.path.join(prefix, suffix)

        left_only: Set[str] = set(map(join_with_prefix, dircmp_obj.left_only))
        right_only: Set[str] = set(map(join_with_prefix, dircmp_obj.right_only))
        diff_files: Set[str] = set(map(join_with_prefix, dircmp_obj.diff_files))
        for name, sub_dircmp_obj in dircmp_obj.subdirs.items():
            subprefix = join_with_prefix(name)
            subleft, subright, subdiff = _dircmp_recursive(
                sub_dircmp_obj, prefix=subprefix
            )
            left_only.update(subleft)
            right_only.update(subright)
            diff_files.update(subdiff)
        return left_only, right_only, diff_files

    return _dircmp_recursive(dircmp_obj, "")


def run_aea_subprocess(*args, cwd: str = ".") -> Tuple[subprocess.Popen, str, str]:
    """
    Run subprocess, bypassing ClickRunner.invoke.

    The reason is that for some reason ClickRunner.invoke doesn't capture
    well the stdout/stderr of nephew processes - children processes of children processes.
    """
    result = subprocess.Popen(  # type: ignore  # nosec
        [sys.executable, "-m", "aea.cli", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
    )
    result.wait()
    stdout, stderr = result.communicate()
    return result, stdout.decode("utf-8"), stderr.decode("utf-8")


@pytest.mark.integration
class UseOef:  # pylint: disable=too-few-public-methods
    """Inherit from this class to launch an OEF node."""

    @pytest.fixture(autouse=True)
    def _start_oef_node(self, network_node: Callable) -> None:
        """Start an oef node."""
