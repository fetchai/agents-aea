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

"""Implementation of the TCP client."""
import asyncio
import logging
from asyncio import AbstractEventLoop, Task, StreamWriter, StreamReader
from concurrent.futures import CancelledError, Executor
from typing import Optional, cast

from aea.configurations.base import ConnectionConfig
from aea.connections.base import Connection
from aea.connections.tcp.base import TCPConnection
from aea.mail.base import Envelope

logger = logging.getLogger(__name__)

STUB_DIALOGUE_ID = 0


class TCPClientConnection(TCPConnection):
    """This class implements a TCP client."""

    def __init__(self,
                 public_key: str,
                 host: str,
                 port: int,
                 loop: Optional[AbstractEventLoop] = None,
                 executor: Optional[Executor] = None):
        """
        Initialize a TCP channel.

        :param public_key: public key.
        :param host: the socket bind address.
        :param loop: the asyncio loop.
        """
        super().__init__(public_key, host, port, loop=loop, executor=executor)

        self._reader, self._writer = (None, None)  # type: Optional[StreamReader], Optional[StreamWriter]
        self._read_task = None  # type: Optional[Task]

    def setup(self):
        """Set the connection up."""
        future = self._run_task(asyncio.open_connection(self.host, self.port, loop=self._loop))
        self._reader, self._writer = future.result()
        public_key_bytes = self.public_key.encode("utf-8")
        future = self._run_task(self._send(self._writer, public_key_bytes))
        future.result(timeout=3.0)
        self._read_task = self._run_task(self._recv_loop(self._reader))
        self._fetch_task = self._run_task(self._send_loop())

    def teardown(self):
        """Tear the connection down."""
        try:
            self.out_queue.put_nowait(None)
            self._fetch_task.result()
            self._reader.feed_eof()
            self._read_task.cancel()
        except CancelledError:
            pass
        self._writer.close()

    def select_writer_from_envelope(self, envelope: Envelope) -> Optional[StreamWriter]:
        """Select the destination, given the envelope."""
        return self._writer

    @classmethod
    def from_config(cls, public_key: str, connection_configuration: ConnectionConfig) -> 'Connection':
        """Get the TCP server connection from the connection configuration.

        :param public_key: the public key of the agent.
        :param connection_configuration: the connection configuration object.
        :return: the connection object
        """
        address = cast(str, connection_configuration.config.get("address"))
        port = cast(int, connection_configuration.config.get("port"))
        return TCPClientConnection(public_key, address, port)
