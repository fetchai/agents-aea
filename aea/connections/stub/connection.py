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
import datetime
import logging
import pickle
from queue import Empty, Queue
from threading import Thread
from typing import List, Dict, Optional, cast

import oef
from oef.agents import OEFAgent
from oef.core import AsyncioCore
from oef.messages import CFP_TYPES, PROPOSE_TYPES
from oef.query import (
    Query as OEFQuery,
    ConstraintExpr as OEFConstraintExpr,
    And as OEFAnd,
    Or as OEFOr,
    Not as OEFNot,
    Constraint as OEFConstraint,
    ConstraintType as OEFConstraintType, Eq, NotEq, Lt, LtEq, Gt, GtEq, Range, In, NotIn)
from oef.schema import Description as OEFDescription, DataModel as OEFDataModel, AttributeSchema as OEFAttribute

from aea.configurations.base import ConnectionConfig
from aea.connections.base import Channel, Connection
from aea.mail.base import MailBox, Envelope
from aea.protocols.fipa.message import FIPAMessage
from aea.protocols.fipa.serialization import FIPASerializer
from aea.protocols.oef.message import OEFMessage
from aea.protocols.oef.models import Description, Attribute, DataModel, Query, ConstraintExpr, And, Or, Not, Constraint, \
    ConstraintType, ConstraintTypes
from aea.protocols.oef.serialization import OEFSerializer, DEFAULT_OEF

logger = logging.getLogger(__name__)


class StubConnection(Connection):
    """A stub connection."""

    def __init__(self):
        """Initialize a stub connection."""
        super().__init__()

        self._stopped = True
        self.out_thread = None  # type: Optional[Thread]

    @property
    def is_established(self) -> bool:
        """Get the connection status."""
        return not self._stopped

    def _fetch(self) -> None:
        """
        Fetch the messages from the outqueue and send them.

        :return: None
        """
        while not self._stopped:
            try:
                msg = self.out_queue.get(block=True, timeout=1.0)
                self.send(msg)
            except Empty:
                pass

    def connect(self) -> None:
        """
        Connect to the channel.

        :return: None
        :raises ConnectionError if the connection to the OEF fails.
        """
        if self._stopped:
            self._stopped = False
            self.out_thread = Thread(target=self._fetch)
            self.out_thread.start()

    def disconnect(self) -> None:
        """
        Disconnect from the channel.

        :return: None
        """
        if not self._stopped:
            self._stopped = False
            self.out_thread.join()
            self.out_thread = None

    def send(self, envelope: Envelope):
        """
        Send messages.

        :return: None
        """
        if not self._stopped:
            self.in_queue.put(envelope)

    @classmethod
    def from_config(cls, public_key: str, connection_configuration: ConnectionConfig) -> 'Connection':
        """
        Get the OEF connection from the connection configuration.

        :param public_key: the public key of the agent.
        :param connection_configuration: the connection configuration object.
        :return: the connection object
        """
        return StubConnection()


