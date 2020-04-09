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
from pathlib import Path
from typing import Union

from aea.configurations.base import ConnectionConfig, PublicId
from aea.mail.base import Address, Envelope

from aea.connections.stub.connection import StubConnection, _encode, _lock_fd, _unlock_fd

logger = logging.getLogger(__name__)

class P2PStubConnection(StubConnection):
    r"""A p2p stub connection.

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

    def __init__(
        self,
        address: Address,
        namespace_dir_path: Union[str, Path],
        **kwargs
    ):
        """
        Initialize a stub connection.

        :param address: agent address.
        :param namesapce_dir_path: directory path to share with other agents.
        """
        if kwargs.get("configuration") is None and kwargs.get("connection_id") is None:
            kwargs["connection_id"] = PublicId("fetchai", "p2p-stub", "0.1.0")
        
        self.namespace = os.path.abspath(namespace_dir_path)
        
        input_file_path = os.path.join(self.namespace, "{}.in".format(address))
        output_file_path = os.path.join(self.namespace, "{}.out".format(address))
        super().__init__(input_file_path, output_file_path, **kwargs)
    
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
          ok = _lock_fd(file)
          file.write(encoded_envelope)
          file.flush()
          ok = _unlock_fd(file)
          # TOFIX(LR) handle (un)locking errors

    @classmethod
    def from_config(
        cls, address: Address, configuration: ConnectionConfig
    ) -> "Connection":
        """
        Get the stub connection from the connection configuration.

        :param address: the address of the agent.
        :param configuration: the connection configuration object.
        :return: the connection object
        """
        namespace_dir = configuration.config.get("namespace_dir", "/tmp")  # type: str
        restricted_to_protocols_names = {
            p.name for p in configuration.restricted_to_protocols
        }
        excluded_protocols_names = {p.name for p in configuration.excluded_protocols}
        return P2PStubConnection(
            address,
            namespace_dir,
            connection_id=configuration.public_id,
            restricted_to_protocols=restricted_to_protocols_names,
            excluded_protocols=excluded_protocols_names,
        )
