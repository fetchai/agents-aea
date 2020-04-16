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

"""This package contains a scaffold of a handler."""

from typing import Optional, cast

from aea.configurations.base import ProtocolId
from aea.protocols.base import Message
from aea.skills.base import Handler
from packages.aris.protocols.rail_stomp.message import RailStompMessage

from packages.aris.skills.rail_receiver.parameters import Parameters


class MyScaffoldHandler(Handler):
    """This class scaffolds a handler."""

    SUPPORTED_PROTOCOL = RailStompMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to an envelope.

        :param message: the message
        :return: None
        """
        msg = cast(RailStompMessage, message)
        parameters = cast(Parameters, self.context.parameters)
        self.context.logger.info(parameters.train_id)


    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass
