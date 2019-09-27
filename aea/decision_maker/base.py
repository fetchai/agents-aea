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

"""This module contains the decision maker class."""

from queue import Queue
from typing import Optional

from aea.mail.base import OutBox
from aea.protocols.base import Message


class DecisionMaker:
    """This class implements the decision maker."""

    def __init__(self, max_reactions: int, outbox: OutBox, resetable: bool = True):
        """
        Initialize the decision maker.

        :param max_reactions: the processing rate of messages per iteration.
        :param resetable: whether the agent state can be reset or not
        :param outbox: the outbox
        """
        self.max_reactions = max_reactions
        self._outbox = outbox
        # self._resetable = resetable
        self._queue = Queue()  # type: Queue

    @property
    def queue(self) -> Queue:
        """Get (in) queue."""
        return self._queue

    @property
    def outbox(self) -> OutBox:
        """Get outbox."""
        return self._outbox

    def execute(self) -> None:
        """
        Execute the decision maker.

        :return: None
        """
        counter = 0
        while not self.queue.empty() and counter < self.max_reactions:
            counter += 1
            message = self.queue.get_nowait()  # type: Optional[Message]
            if message is not None:
                self.handle(message)

    def handle(self, message: Message) -> None:
        """
        Handle a message.

        :param message: the message
        :return: None
        """
        # check message against agent state > hence must have an agent state
        # if self.resetable:
        # permit agent state reset (special message which needs to be signed)
        # agent state vs utility/preference & goal
