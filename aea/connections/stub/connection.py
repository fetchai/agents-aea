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
"""This module contains the stub connection."""

import asyncio
import logging
import os
import re
from contextlib import contextmanager
from pathlib import Path
from typing import IO, List, Optional, Union

from watchdog.events import FileModifiedEvent, FileSystemEventHandler
from watchdog.utils import platform

from aea.configurations.base import PublicId
from aea.connections.base import Connection
from aea.helpers import file_lock
from aea.mail.base import Envelope


if platform.is_darwin():
    """Cause fsevent fails on multithreading on macos."""
    from watchdog.observers.kqueue import KqueueObserver as Observer
else:
    from watchdog.observers import Observer


logger = logging.getLogger(__name__)

INPUT_FILE_KEY = "input_file"
OUTPUT_FILE_KEY = "output_file"
DEFAULT_INPUT_FILE_NAME = "./input_file"
DEFAULT_OUTPUT_FILE_NAME = "./output_file"
SEPARATOR = b","

PUBLIC_ID = PublicId.from_str("fetchai/stub:0.4.0")


class _ConnectionFileSystemEventHandler(FileSystemEventHandler):
    def __init__(self, connection, file_to_observe: Union[str, Path]):
        self._connection = connection
        self._file_to_observe = Path(file_to_observe).absolute()

    def on_modified(self, event: FileModifiedEvent):
        modified_file_path = Path(event.src_path).absolute()
        if modified_file_path == self._file_to_observe:
            self._connection.read_envelopes()


def _encode(e: Envelope, separator: bytes = SEPARATOR):
    result = b""
    result += e.to.encode("utf-8")
    result += separator
    result += e.sender.encode("utf-8")
    result += separator
    result += str(e.protocol_id).encode("utf-8")
    result += separator
    result += e.message
    result += separator

    return result


def _decode(e: bytes, separator: bytes = SEPARATOR):
    split = e.split(separator)

    if len(split) < 5 or split[-1] not in [b"", b"\n"]:
        raise ValueError(
            "Expected at least 5 values separated by commas and last value being empty or new line, got {}".format(
                len(split)
            )
        )

    to = split[0].decode("utf-8").strip()
    sender = split[1].decode("utf-8").strip()
    protocol_id = PublicId.from_str(split[2].decode("utf-8").strip())
    # protobuf messages cannot be delimited as they can contain an arbitrary byte sequence; however
    # we know everything remaining constitutes the protobuf message.
    message = SEPARATOR.join(split[3:-1])

    return Envelope(to=to, sender=sender, protocol_id=protocol_id, message=message)


@contextmanager
def lock_file(file_descriptor: IO[bytes]):
    """Lock file in context manager.

    :param file_descriptor: file descriptio of file to lock.
    """
    try:
        file_lock.lock(file_descriptor, file_lock.LOCK_EX)
    except OSError as e:
        logger.error(
            "Couldn't acquire lock for file {}: {}".format(file_descriptor.name, e)
        )
        raise e
    try:
        yield
    finally:
        file_lock.unlock(file_descriptor)


def read_envelopes(file_pointer: IO[bytes]) -> List[Envelope]:
    """Receive new envelopes, if any."""
    envelopes = []  # type: List[Envelope]
    with lock_file(file_pointer):
        lines = file_pointer.read()
        if len(lines) > 0:
            file_pointer.truncate(0)
            file_pointer.seek(0)

    if len(lines) == 0:
        return envelopes

    # get messages
    # match with b"[^,]*,[^,]*,[^,]*,.*,[\n]?"
    regex = re.compile(
        (b"[^" + SEPARATOR + b"]*" + SEPARATOR) * 3 + b".*,[\n]?", re.DOTALL
    )
    messages = [m.group(0) for m in regex.finditer(lines)]
    for msg in messages:
        logger.debug("processing: {!r}".format(msg))
        envelope = _process_line(msg)
        if envelope is not None:
            envelopes.append(envelope)
    return envelopes


def write_envelope(envelope: Envelope, file_pointer: IO[bytes]) -> None:
    """Write envelope to file."""
    encoded_envelope = _encode(envelope, separator=SEPARATOR)
    logger.debug("write {}".format(encoded_envelope))
    with lock_file(file_pointer):
        file_pointer.write(encoded_envelope)
        file_pointer.flush()


def _process_line(line: bytes) -> Optional[Envelope]:
    """
    Process a line of the file.

    Decode the line to get the envelope, and put it in the agent's inbox.

    :return: Envelope
    :raise: Exception
    """
    envelope = None  # type: Optional[Envelope]
    try:
        envelope = _decode(line, separator=SEPARATOR)
    except ValueError as e:
        logger.error("Bad formatted line: {!r}. {}".format(line, e))
    except Exception as e:
        logger.error("Error when processing a line. Message: {}".format(str(e)))
    return envelope


class StubConnection(Connection):
    r"""A stub connection.

    This connection uses two files to communicate: one for the incoming messages and
    the other for the outgoing messages. Each line contains an encoded envelope.

    The format of each line is the following:

        TO,SENDER,PROTOCOL_ID,ENCODED_MESSAGE

    e.g.:

        recipient_agent,sender_agent,default,{"type": "bytes", "content": "aGVsbG8="}

    The connection detects new messages by watchdogging the input file looking for new lines.

    To post a message on the input file, you can use e.g.

        echo "..." >> input_file

    or:

        #>>> fp = open(DEFAULT_INPUT_FILE_NAME, "ab+")
        #>>> fp.write(b"...\n")

    It is discouraged adding a message with a text editor since the outcome depends on the actual text editor used.
    """

    connection_id = PUBLIC_ID

    def __init__(self, **kwargs):
        """Initialize a stub connection."""
        if kwargs.get("configuration") is None and kwargs.get("connection_id") is None:
            kwargs["connection_id"] = PUBLIC_ID
        super().__init__(**kwargs)
        input_file: str = self.configuration.config.get(
            INPUT_FILE_KEY, DEFAULT_INPUT_FILE_NAME
        )
        output_file: str = self.configuration.config.get(
            OUTPUT_FILE_KEY, DEFAULT_OUTPUT_FILE_NAME
        )
        input_file_path = Path(input_file)
        output_file_path = Path(output_file)
        if not input_file_path.exists():
            input_file_path.touch()

        self.input_file = open(input_file_path, "rb+")
        self.output_file = open(output_file_path, "wb+")

        self.in_queue = None  # type: Optional[asyncio.Queue]

        self._observer = Observer()

        directory = os.path.dirname(input_file_path.absolute())
        self._event_handler = _ConnectionFileSystemEventHandler(self, input_file_path)
        self._observer.schedule(self._event_handler, directory)

    def read_envelopes(self) -> None:
        """Receive new envelopes, if any."""
        envelopes = read_envelopes(self.input_file)
        self._put_envelopes(envelopes)

    def _put_envelopes(self, envelopes: List[Envelope]) -> None:
        """
        Put the envelopes in the inqueue.

        :param envelopes: the list of envelopes
        """
        assert self.in_queue is not None, "Input queue not initialized."
        assert self._loop is not None, "Loop not initialized."
        for envelope in envelopes:
            asyncio.run_coroutine_threadsafe(self.in_queue.put(envelope), self._loop)

    async def receive(self, *args, **kwargs) -> Optional["Envelope"]:
        """Receive an envelope."""
        try:
            assert self.in_queue is not None, "Input queue not initialized."
            envelope = await self.in_queue.get()
            return envelope
        except Exception as e:
            logger.exception(e)
            return None

    async def connect(self) -> None:
        """Set up the connection."""
        if self.connection_status.is_connected:
            return

        try:
            # initialize the queue here because the queue
            # must be initialized with the right event loop
            # which is known only at connection time.
            self.in_queue = asyncio.Queue()
            self._observer.start()
        except Exception as e:  # pragma: no cover
            self._observer.stop()
            self._observer.join()
            raise e
        finally:
            self.connection_status.is_connected = False

        self.connection_status.is_connected = True

        # do a first processing of messages.
        #  self.read_envelopes()

    async def disconnect(self) -> None:
        """
        Disconnect from the channel.

        In this type of connection there's no channel to disconnect.
        """
        if not self.connection_status.is_connected:
            return

        assert self.in_queue is not None, "Input queue not initialized."
        self._observer.stop()
        self._observer.join()
        self.in_queue.put_nowait(None)

        self.connection_status.is_connected = False

    async def send(self, envelope: Envelope):
        """
        Send messages.

        :return: None
        """
        write_envelope(envelope, self.output_file)
