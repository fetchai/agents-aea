# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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

from typing import Optional

from aea.configurations.base import PublicId
from aea.protocols.base import Message
from aea.skills.base import Handler


class MyScaffoldHandler(Handler):
    """This class scaffolds a handler."""

    SUPPORTED_PROTOCOL = None  # type: Optional[PublicId]

    def setup(self) -> None:
        """Implement the setup."""
        raise NotImplementedError

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to an envelope.

        :param message: the message
        """
        raise NotImplementedError

    def teardown(self) -> None:
        """Implement the handler teardown."""
        raise NotImplementedError
