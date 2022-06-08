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

"""This module contains a scaffold of the decision maker class and auxiliary classes."""

from typing import Any, Dict

from aea.crypto.wallet import Wallet
from aea.decision_maker.base import DecisionMakerHandler as BaseDecisionMakerHandler
from aea.identity.base import Identity
from aea.protocols.base import Message


class DecisionMakerHandler(BaseDecisionMakerHandler):
    """This class implements the decision maker."""

    def __init__(
        self, identity: Identity, wallet: Wallet, config: Dict[str, Any]
    ) -> None:
        """
        Initialize the decision maker.

        :param identity: the identity
        :param wallet: the wallet
        :param config: the user defined configuration of the handler
        """
        kwargs = {
            # Add your objects here, they will be accessible in the `handle` method via `self.context`.
            # They will also be accessible from the skill context.
        }  # type: Dict[str, Any]
        # You MUST NOT modify the constructor below:
        super().__init__(
            identity=identity,
            wallet=wallet,
            config=config,
            **kwargs,
        )

    def handle(self, message: Message) -> None:
        """
        Handle an internal message from the skills.

        This method is used to:
            - update the ownership state
            - check transactions satisfy the preferences

        :param message: the message
        """
        raise NotImplementedError
