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
import logging
import os
import time
from pathlib import Path
from threading import Thread

from watchdog.events import FileSystemEventHandler, FileModifiedEvent
from watchdog.observers import Observer

from aea.configurations.base import ConnectionConfig
from aea.connections.base import Connection
from aea.mail.base import Envelope

logger = logging.getLogger(__name__)

SEPARATOR = b","


class _ConnectionFileSystemEventHandler(FileSystemEventHandler):

    def __init__(self, connection, file_to_observe: str):
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
    split = e.split(separator)

    if len(split) != 4:
        raise ValueError("Expected 4 values, got {}".format(len(split)))

    to = split[0].decode("utf-8")
    sender = split[1].decode("utf-8")
    protocol_id = split[2].decode("utf-8")
    message = split[3]

    return Envelope(to=to, sender=sender, protocol_id=protocol_id, message=message)


class StubConnection(Connection):
    """A stub connection."""

    def __init__(self, in_file_path: str, out_file_path: str):
        super().__init__()

        in_file_path = Path(in_file_path)
        out_file_path = Path(out_file_path)
        if not in_file_path.exists():
            in_file_path.touch()

        self.in_file = open(in_file_path, "rb+", buffering=1)
        self.out_file = open(out_file_path, "wb+", buffering=1)

        self._stopped = True
        self._observer = Observer()

        dir = os.path.dirname(in_file_path.absolute())
        self._event_handler = _ConnectionFileSystemEventHandler(self, in_file_path)
        self._observer.schedule(self._event_handler, dir)

    @property
    def is_established(self) -> bool:
        """Get the connection status."""
        return not self._stopped

    def receive(self):
        line = self.in_file.readline()
        while len(line) > 0:
            self._process_line(line[:-1])
            line = self.in_file.readline()

    def _process_line(self, line):
        logger.debug("read {}".format(line))
        try:
            envelope = _decode(line, separator=SEPARATOR)
            self.in_queue.put(envelope)
        except ValueError:
            logger.error("Bad formatted line: {}".format(line))

    def connect(self) -> None:
        """
        Connect to the channel.

        In this type of connection there's no channel to connect.
        """
        if self._stopped:
            self._stopped = False
            try:
                self._observer.start()
            except Exception as e:
                self._stopped = True
                raise e

            self.receive()

    def disconnect(self) -> None:
        """
        Disconnect from the channel.

        In this type of connection there's no channel to disconnect.
        """
        if not self._stopped:
            self._stopped = True
            try:
                self._observer.stop()
            except Exception as e:
                self._stopped = False
                raise e

    def send(self, envelope: Envelope):
        """
        Send messages.

        :return: None
        """
        encoded_envelope = _encode(envelope, separator=SEPARATOR)
        logger.debug("write {}".format(encoded_envelope))
        self.out_file.write(encoded_envelope + b"\n")

    @classmethod
    def from_config(cls, public_key: str, connection_configuration: ConnectionConfig) -> 'Connection':
        """
        Get the OEF connection from the connection configuration.

        :param public_key: the public key of the agent.
        :param connection_configuration: the connection configuration object.
        :return: the connection object
        """
        in_file = connection_configuration.config.get("in_file")
        out_file = connection_configuration.config.get("out_file")
        return StubConnection(in_file, out_file)


