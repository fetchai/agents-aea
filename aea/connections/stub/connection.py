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
import threading
from pathlib import Path
from typing import Union, Optional

from watchdog.events import FileSystemEventHandler, FileModifiedEvent
from watchdog.observers import Observer

from aea.configurations.base import ConnectionConfig
from aea.connections.base import Connection
from aea.mail.base import Envelope

logger = logging.getLogger(__name__)

SEPARATOR = b","


class _ConnectionFileSystemEventHandler(FileSystemEventHandler):

    def __init__(self, connection, file_to_observe: Union[str, Path]):
        self._connection = connection
        self._file_to_observe = Path(file_to_observe).absolute()

    def on_modified(self, event: FileModifiedEvent):
        modified_file_path = Path(event.src_path).absolute()
        if modified_file_path == self._file_to_observe:
            self._connection.receive()


def _encode(e: Envelope, separator: bytes = SEPARATOR):
    result = b""
    result += e.to.encode("utf-8")
    result += separator
    result += e.sender.encode("utf-8")
    result += separator
    result += e.protocol_id.encode("utf-8")
    result += separator
    result += e.message

    return result


def _decode(e: bytes, separator: bytes = SEPARATOR):
    split = e.split(separator, maxsplit=3)

    if len(split) != 4:
        raise ValueError("Expected 4 values, got {}".format(len(split)))

    to = split[0].decode("utf-8").strip()
    sender = split[1].decode("utf-8").strip()
    protocol_id = split[2].decode("utf-8").strip()
    message = split[3]

    return Envelope(to=to, sender=sender, protocol_id=protocol_id, message=message)


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

        #>>> fp = open("input_file", "ab+")
        #>>> fp.write(b"...\n")

    It is discouraged adding a message with a text editor since the outcome depends on the actual text editor used.
    """

    def __init__(self, input_file_path: Union[str, Path], output_file_path: Union[str, Path],
                 connection_id: str = "stub"):
        """
        Initialize a stub connection.

        :param input_file_path: the input file for the incoming messages.
        :param output_file_path: the output file for the outgoing messages.
        """
        super().__init__(connection_id=connection_id)

        input_file_path = Path(input_file_path)
        output_file_path = Path(output_file_path)
        if not input_file_path.exists():
            input_file_path.touch()

        self.input_file = open(input_file_path, "rb+", buffering=1)
        self.output_file = open(output_file_path, "wb+", buffering=1)

        self._stopped = True
        self._connected = False
        self.in_queue = None  # type: Optional[asyncio.Queue]
        self._lock = threading.Lock()
        self._observer = Observer()

        dir = os.path.dirname(input_file_path.absolute())
        self._event_handler = _ConnectionFileSystemEventHandler(self, input_file_path)
        self._observer.schedule(self._event_handler, dir)

    @property
    def is_established(self) -> bool:
        """Get the connection status."""
        return self._connected

    def receive(self) -> None:
        """Receive new messages, if any."""
        line = self.input_file.readline()
        logger.debug("read line: {!r}".format(line))
        while len(line) > 0:
            self._process_line(line[:-1])
            line = self.input_file.readline()

    def _process_line(self, line) -> None:
        """Process a line of the file.

        Decode the line to get the envelope, and put it in the agent's inbox.
        """
        try:
            envelope = _decode(line, separator=SEPARATOR)
            asyncio.run_coroutine_threadsafe(self.in_queue.put(envelope), self._loop)
        except ValueError:
            logger.error("Bad formatted line: {}".format(line))

    async def recv(self) -> Optional['Envelope']:
        try:
            envelope = await self.in_queue.get()
            return envelope
        except Exception as e:
            logger.exception(e)
            return None

    async def connect(self) -> None:
        """Set up the connection."""
        with self._lock:
            if self._stopped:
                self._stopped = False
                try:
                    # initialize the queue here because the queue
                    # must be initialized with the right event loop
                    # which is known only at connection time.
                    self.in_queue = asyncio.Queue()
                    self._observer.start()
                except Exception as e:      # pragma: no cover
                    raise e
                finally:
                    self._stopped = True

                self._connected = True
                # do a first processing of messages.
                self.receive()

    async def disconnect(self) -> None:
        """
        Disconnect from the channel.

        In this type of connection there's no channel to disconnect.
        """
        with self._lock:
            if self._connected:
                self._connected = False
                self._observer.stop()
                self._observer.join()
                self.in_queue.put_nowait(None)
                self._stopped = True

    async def send(self, envelope: Envelope):
        """
        Send messages.

        :return: None
        """
        encoded_envelope = _encode(envelope, separator=SEPARATOR)
        logger.debug("write {}".format(encoded_envelope))
        self.output_file.write(encoded_envelope + b"\n")
        self.output_file.flush()

    @classmethod
    def from_config(cls, public_key: str, connection_configuration: ConnectionConfig) -> 'Connection':
        """
        Get the OEF connection from the connection configuration.

        :param public_key: the public key of the agent.
        :param connection_configuration: the connection configuration object.
        :return: the connection object
        """
        input_file = connection_configuration.config.get("input_file", "./input_file")  # type: str
        output_file = connection_configuration.config.get("output_file", "./output_file")  # type: str
        return StubConnection(input_file, output_file)
