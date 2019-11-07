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

"""Scaffold connection and channel."""

import logging
from queue import Queue
from typing import Optional

from aea.configurations.base import ConnectionConfig
from aea.connections.base import Channel, Connection
from aea.mail.base import Envelope

logger = logging.getLogger(__name__)


class MyScaffoldChannel(Channel):
    """A wrapper for an SDK or API."""

    def __init__(self, public_key: str):
        """
        Initialize a channel.

        :param public_key: the public key
        """
        self.public_key = public_key

    def connect(self) -> Optional[Queue]:
        """
        Connect.

        :return: an asynchronous queue, that constitutes the communication channel.
        """
        raise NotImplementedError  # pragma: no cover

    def send(self, envelope: Envelope) -> None:
        """
        Process the envelopes.

        :param envelope: the envelope
        :return: None
        """
        raise NotImplementedError  # pragma: no cover

    def disconnect(self) -> None:
        """
        Disconnect.

        :return: None
        """
        raise NotImplementedError  # pragma: no cover


class MyScaffoldConnection(Connection):
    """Proxy to the functionality of the SDK or API."""

    def __init__(self, public_key: str):
        """
        Initialize a connection to an SDK or API.

        :param public_key: the public key used in the protocols.
        """
        super().__init__()
        self.public_key = public_key
        self.channel = MyScaffoldChannel(public_key)

    def connect(self) -> None:
        """
        Connect to the gym.

        :return: None
        """
        raise NotImplementedError  # pragma: no cover

    def disconnect(self) -> None:
        """
        Disconnect from the gym.

        :return: None
        """
        raise NotImplementedError  # pragma: no cover

    def send(self, envelope: Envelope) -> None:
        """
        Send an envelope.

        :param envelope: the envelop
        :return: None
        """
        raise NotImplementedError  # pragma: no cover

    @classmethod
    def from_config(cls, public_key: str, connection_configuration: ConnectionConfig) -> 'Connection':
        """
        Get the Gym connection from the connection configuration.

        :param public_key: the public key of the agent.
        :param connection_configuration: the connection configuration object.
        :return: the connection object
        """
        raise NotImplementedError  # pragma: no cover
