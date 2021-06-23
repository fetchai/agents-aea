# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
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
"""This package contains the behaviour for the fipa dummy buyer skill."""

from typing import Any, cast

from aea.helpers.search.models import Constraint, ConstraintType, Query
from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.skills.fipa_dummy_buyer.dialogues import FipaDialogues


class FIPAInitializerBehaviour(TickerBehaviour):
    """Fipa buyer cfp initializer."""

    def __init__(self, **kwargs: Any) -> None:
        """Init fipa behaviour."""
        if "opponent_address" not in kwargs:
            raise ValueError("Opponent address has to be specified for behaviour!")
        self.opponent_address: str = cast(str, kwargs.pop("opponent_address", None))
        self.is_enabled: bool = True
        super().__init__(**kwargs)

    def setup(self) -> None:
        """Implement the setup for the behaviour."""

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        if not self.is_enabled:
            return
        dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
        cfp_msg, _ = dialogues.create(
            counterparty=self.opponent_address,
            performative=FipaMessage.Performative.CFP,
            query=Query([Constraint("something", ConstraintType(">", 1))]),
        )
        self.context.outbox.put_message(cfp_msg)
        self.context.logger.info("CFP message sent.")

    def teardown(self) -> None:
        """Implement the task teardown."""
