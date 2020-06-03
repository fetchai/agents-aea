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

import logging
import os
import tempfile
from pathlib import Path
from typing import Union, cast

from aea.configurations.base import ConnectionConfig, PublicId
from aea.connections.stub.connection import (
    StubConnection,
    _encode,
    lock_file,
)
from aea.identity.base import Identity
from aea.mail.base import Envelope

logger = logging.getLogger(__name__)

PUBLIC_ID = PublicId.from_str("fetchai/p2p_stub:0.2.0")


class P2PStubConnection(StubConnection):
    r"""A p2p stub connection.

    This connection uses an existing directory as a Rendez-Vous point for agents to communicate locally.
    Each connected agent will create a file named after its address/identity where it can receive messages.

    The connection detects new messages by watchdogging the input file looking for new lines.
    """

    connection_id = PUBLIC_ID

    def __init__(self, configuration: ConnectionConfig, identity: Identity, **kwargs):
        """
        Initialize a p2p stub connection.

        :param configuration: the connection configuration
        :param identity: the identity
        """
        namespace_dir_path = cast(
            Union[str, Path],
            configuration.config.get("namespace_dir", tempfile.mkdtemp()),
        )
        assert namespace_dir_path is not None, "namespace_dir_path must be set!"
        self.namespace = os.path.abspath(namespace_dir_path)

        input_file_path = os.path.join(self.namespace, "{}.in".format(identity.address))
        output_file_path = os.path.join(
            self.namespace, "{}.out".format(identity.address)
        )
        configuration.config["input_file"] = input_file_path
        configuration.config["output_file"] = output_file_path
        super().__init__(configuration=configuration, identity=identity, **kwargs)

    async def send(self, envelope: Envelope):
        """
        Send messages.

        :return: None
        """

        target_file = Path(os.path.join(self.namespace, "{}.in".format(envelope.to)))
        if not target_file.is_file():
            target_file.touch()
            logger.warn("file {} doesn't exist, creating it ...".format(target_file))

        encoded_envelope = _encode(envelope)
        logger.debug("write to {}: {}".format(target_file, encoded_envelope))

        with open(target_file, "ab") as file:
            with lock_file(file):
                file.write(encoded_envelope)
                file.flush()

    async def disconnect(self) -> None:
        await super().disconnect()
        os.rmdir(self.namespace)
