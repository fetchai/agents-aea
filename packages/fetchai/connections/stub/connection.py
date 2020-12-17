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
import re
from asyncio import CancelledError
from asyncio.tasks import Task
from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path
from typing import AsyncIterable, List, Optional

from aea.configurations.base import PublicId
from aea.configurations.constants import (
    DEFAULT_INPUT_FILE_NAME,
    DEFAULT_OUTPUT_FILE_NAME,
)
from aea.connections.base import Connection, ConnectionStates
from aea.helpers.file_io import envelope_from_bytes, lock_file, write_envelope
from aea.mail.base import Envelope


_default_logger = logging.getLogger("aea.packages.fetchai.connections.stub")

INPUT_FILE_KEY = "input_file"
OUTPUT_FILE_KEY = "output_file"
SEPARATOR = b","

PUBLIC_ID = PublicId.from_str("fetchai/stub:0.13.0")


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

    message_regex = re.compile(
        (b"[^" + SEPARATOR + b"]*" + SEPARATOR) * 3 + b".*,[\n]?", re.DOTALL
    )

    read_delay = 0.001

    def __init__(self, **kwargs):
        """Initialize a stub connection."""
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

        self._read_envelopes_task: Optional[Task] = None
        self._write_pool = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="stub_connection_writer_"
        )  # sequential write only! but threaded!

    async def _file_read_and_trunc(self, delay: float = 0.001) -> AsyncIterable[bytes]:
        """
        Generate input file read chunks and trunc data already read.

        :param delay: float, delay on empty read.

        :return: async generator return file read bytes.
        """
        while True:
            with lock_file(self.input_file):
                data = self.input_file.read()
                if data:
                    self.input_file.truncate(0)
                    self.input_file.seek(0)

            if data:
                yield data
            else:
                await asyncio.sleep(delay)

    async def read_envelopes(self) -> None:
        """Read envelopes from inptut file, decode and put into in_queue."""
        self._ensure_connected()
        if self.in_queue is None:  # pragma: nocover
            raise ValueError("Input queue not initialized.")

        self.logger.debug("Read messages!")
        async for data in self._file_read_and_trunc(delay=self.read_delay):
            lines = self._split_messages(data)
            for line in lines:
                envelope = envelope_from_bytes(line, SEPARATOR, self.logger)

                if envelope is None:
                    continue

                self.logger.debug(f"Add envelope {envelope}")
                await self.in_queue.put(envelope)

    @classmethod
    def _split_messages(cls, data: bytes) -> List[bytes]:
        """
        Split binary data on messages.

        :param data: bytes

        :return: list of bytes
        """
        return [m.group(0) for m in cls.message_regex.finditer(data)]

    async def receive(self, *args, **kwargs) -> Optional["Envelope"]:
        """Receive an envelope."""
        self._ensure_connected()
        if self.in_queue is None:  # pragma: nocover
            self.logger.error("Input queue not initialized.")
            return None

        try:
            return await self.in_queue.get()
        except CancelledError:  # pragma: no cover
            self.logger.debug("Receive cancelled.")
            return None
        except Exception:  # pylint: disable=broad-except
            self.logger.exception("Stub connection receive error:")
            return None

    async def connect(self) -> None:
        """Set up the connection."""
        if self.is_connected:
            return

        with self._connect_context():
            self.in_queue = asyncio.Queue()
            self._read_envelopes_task = self.loop.create_task(self.read_envelopes())

    async def _stop_read_envelopes(self) -> None:
        """
        Stop read envelopes task.

        Cancel task and wait for completed.
        """
        if not self._read_envelopes_task:
            return  # pragma: nocover

        if not self._read_envelopes_task.done():
            self._read_envelopes_task.cancel()

        try:
            await self._read_envelopes_task
        except CancelledError:
            pass  # task was cancelled, that was expected
        except BaseException:  # pragma: nocover  # pylint: disable=broad-except
            self.logger.exception(
                "during envelop read"
            )  # do not raise exception cause it's on task stop

    async def disconnect(self) -> None:
        """
        Disconnect from the channel.

        In this type of connection there's no channel to disconnect.
        """
        if self.is_disconnected:
            return

        if self.in_queue is None:  # pragma: nocover
            raise ValueError("Input queue not initialized.")

        self._state.set(ConnectionStates.disconnecting)
        await self._stop_read_envelopes()
        self._write_pool.shutdown(wait=False)
        self.in_queue.put_nowait(None)
        self._state.set(ConnectionStates.disconnected)

    async def send(self, envelope: Envelope) -> None:
        """
        Send messages.

        :return: None
        """
        self._ensure_connected()
        self._ensure_valid_envelope_for_external_comms(envelope)
        await self.loop.run_in_executor(
            self._write_pool,
            write_envelope,
            envelope,
            self.output_file,
            SEPARATOR,
            self.logger,
        )
