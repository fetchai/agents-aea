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

"""This package contains a scaffold of a behaviour."""

from typing import Dict, List, Optional, Set, cast

from aea.helpers.transaction.base import RawMessage, Terms
from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.protocols.register.message import RegisterMessage
from packages.fetchai.protocols.signing.message import SigningMessage
from packages.fetchai.skills.registration_aw1.dialogues import (
    RegisterDialogues,
    SigningDialogues,
)
from packages.fetchai.skills.registration_aw1.strategy import Strategy


class AW1RegistrationBehaviour(TickerBehaviour):
    """This class scaffolds a behaviour."""

    def setup(self) -> None:
        """Implement the setup."""
        strategy = cast(Strategy, self.context.strategy)
        if strategy.announce_termination_key is not None:
            self.context.shared_state[strategy.announce_termination_key] = False

        if not strategy.developer_handle_only:
            signing_dialogues = cast(SigningDialogues, self.context.signing_dialogues)
            msg, _ = signing_dialogues.create(
                counterparty=self.context.decision_maker_address,
                performative=SigningMessage.Performative.SIGN_MESSAGE,
                raw_message=RawMessage(
                    strategy.ledger_id, strategy.ethereum_address.encode("utf-8")
                ),
                terms=Terms(
                    ledger_id=strategy.ledger_id,
                    sender_address="",
                    counterparty_address="",
                    amount_by_currency_id={},
                    quantities_by_good_id={},
                    nonce="",
                ),
            )
            self.context.logger.info("sending signing_msg to decision maker...")
            self.context.decision_maker_message_queue.put_nowait(msg)

    def act(self) -> None:
        """Implement the act."""
        strategy = cast(Strategy, self.context.strategy)
        if not strategy.is_ready_to_register:
            return

        aw1_registration_aeas: Optional[Set[str]] = self.context.shared_state.get(
            strategy.shared_storage_key, None
        )
        if aw1_registration_aeas is None:
            return

        if strategy.is_registered or strategy.is_registration_pending:
            return

        strategy.is_registration_pending = True

        self._register_for_aw1(
            aw1_registration_aeas, strategy.registration_info, strategy.whitelist
        )

    def teardown(self) -> None:
        """Implement the task teardown."""

    def _register_for_aw1(
        self,
        aw1_registration_aeas: Set[str],
        registration_info: Dict[str, str],
        whitelist: List[str],
    ) -> None:
        """
        Register for Agent World 1.

        :param aw1_registration_aeas: the AEAs to register with
        :param registration_info: the info to send
        :param whitelist: the allowed agents
        """
        register_dialogues = cast(RegisterDialogues, self.context.register_dialogues)
        for agent in aw1_registration_aeas:
            if agent not in whitelist:
                self.context.logger.info(f"agent={agent} not in whitelist={whitelist}")
                return
            msg, _ = register_dialogues.create(
                counterparty=agent,
                performative=RegisterMessage.Performative.REGISTER,
                info=registration_info,
            )
            self.context.logger.info(f"sending registration info: {registration_info}")
            self.context.outbox.put_message(msg)
