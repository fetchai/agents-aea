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
"""This module contains the p2p stub connection."""

import os
import tempfile
from pathlib import Path
from typing import Any, Union, cast

from aea.configurations.base import ConnectionConfig, PublicId
from aea.identity.base import Identity
from aea.mail.base import Envelope

from packages.fetchai.connections.stub.connection import StubConnection, write_envelope


PUBLIC_ID = PublicId.from_str("fetchai/p2p_stub:0.18.0")


class P2PStubConnection(StubConnection):
    r"""A p2p stub connection.

    This connection uses an existing directory as a Rendez-Vous point for agents to communicate locally.
    Each connected agent will create a file named after its address/identity where it can receive messages.

    The connection detects new messages by watchdogging the input file looking for new lines.
    """

    connection_id = PUBLIC_ID

    def __init__(
        self, configuration: ConnectionConfig, identity: Identity, **kwargs: Any
    ) -> None:
        """
        Initialize a p2p stub connection.

        :param configuration: the connection configuration
        :param identity: the identity
        :param kwargs: positional arguments
        """
        namespace_dir_path = cast(
            Union[str, Path],
            configuration.config.get("namespace_dir", tempfile.mkdtemp()),
        )
        if namespace_dir_path is None:
            raise ValueError("namespace_dir_path must be set!")  # pragma: nocover
        self.namespace = os.path.abspath(namespace_dir_path)

        input_file_path = os.path.join(self.namespace, "{}.in".format(identity.address))
        output_file_path = os.path.join(
            self.namespace, "{}.out".format(identity.address)
        )
        configuration.config["input_file"] = input_file_path
        configuration.config["output_file"] = output_file_path
        super().__init__(configuration=configuration, identity=identity, **kwargs)

    async def send(self, envelope: Envelope) -> None:
        """
        Send messages.

        :param envelope: the envelope
        """
        if self.loop is None:
            raise ValueError("Loop not initialized.")  # pragma: nocover
        self._ensure_valid_envelope_for_external_comms(envelope)
        target_file = Path(os.path.join(self.namespace, "{}.in".format(envelope.to)))

        with open(target_file, "ab") as file:
            await self.loop.run_in_executor(
                self._write_pool, write_envelope, envelope, file
            )

    async def disconnect(self) -> None:
        """Disconnect the connection."""
        if self.loop is None:
            raise ValueError("Loop not initialized.")  # pragma: nocover
        await self.loop.run_in_executor(self._write_pool, self._cleanup)
        await super().disconnect()

    def _cleanup(self) -> None:
        try:
            os.unlink(self.configuration.config["input_file"])
        except OSError:
            pass
        try:
            os.unlink(self.configuration.config["output_file"])
        except OSError:
            pass
        try:
            os.rmdir(self.namespace)
        except OSError:
            pass
