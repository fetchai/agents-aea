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

"""This package contains a tac search behaviour."""

from collections import OrderedDict
from typing import Any, Dict, cast

from aea.crypto.helpers import fund_wallet
from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.connections.ledger.base import (
    CONNECTION_ID as LEDGER_CONNECTION_PUBLIC_ID,
)
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.tac.message import TacMessage
from packages.fetchai.skills.tac_participation.dialogues import LedgerApiDialogue, OefSearchDialogues
from packages.fetchai.skills.tac_participation.game import Game, Phase


LEDGER_API_ADDRESS = str(LEDGER_CONNECTION_PUBLIC_ID)


class TacSearchBehaviour(TickerBehaviour):
    """This class scaffolds a behaviour."""

    def setup(self) -> None:
        """Implement the setup."""
        game = cast(Game, self.context.game)
        address = self.context.agent_address
        identifier = game.ledger_id
        fund_wallet(self.context, identifier)

    def act(self) -> None:
        """Implement the act."""
        game = cast(Game, self.context.game)
        if game.phase.value == Phase.PRE_GAME.value:
            self._search_for_tac()

    def teardown(self) -> None:
        """Implement the task teardown."""

    def _search_for_tac(self) -> None:
        """
        Search for active TAC Controller.

        We assume that the controller is registered as a service with the 'tac' data model
        and with an attribute version = expected_version_id.
        """
        game = cast(Game, self.context.game)
        query = game.get_game_query()
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_msg, _ = oef_search_dialogues.create(
            counterparty=self.context.search_service_address,
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            query=query,
        )
        self.context.outbox.put_message(message=oef_search_msg)
        self.context.logger.info(
            "searching for TAC, search_id={}".format(oef_search_msg.dialogue_reference)
        )


class TransactionProcessBehaviour(TickerBehaviour):
    """This class implements the processing of the transactions class."""

    def setup(self) -> None:
        """Implement the setup."""

    def act(self) -> None:
        """Implement the task execution."""
        game = cast(Game, self.context.game)
        if game.phase.value == Phase.GAME.value:
            self._process_transactions()

    def teardown(self) -> None:
        """Implement the task teardown."""

    def _process_transactions(self) -> None:
        """Process transactions."""
        game = cast(Game, self.context.game)
        tac_dialogue = game.tac_dialogue
        transactions = cast(
            Dict[str, Dict[str, Any]],
            self.context.shared_state.get("transactions", OrderedDict()),
        )
        tx_ids = list(transactions.keys())
        for tx_id in tx_ids:
            last_msg = (
                tac_dialogue.last_message
            )  # could be a problem if messages are delivered out of order
            if last_msg is None:
                raise ValueError("No last message available.")
            tx_content = transactions.pop(tx_id, None)
            if tx_content is None:
                raise ValueError("Tx for id={} not found.".format(tx_id))
            terms = tx_content["terms"]
            sender_signature = tx_content["sender_signature"]
            counterparty_signature = tx_content["counterparty_signature"]
            msg = tac_dialogue.reply(
                performative=TacMessage.Performative.TRANSACTION,
                target_message=last_msg,
                transaction_id=tx_id,
                ledger_id=terms.ledger_id,
                sender_address=terms.sender_address,
                counterparty_address=terms.counterparty_address,
                amount_by_currency_id=terms.amount_by_currency_id,
                fee_by_currency_id=terms.fee_by_currency_id,
                quantities_by_good_id=terms.quantities_by_good_id,
                sender_signature=sender_signature,
                counterparty_signature=counterparty_signature,
                nonce=terms.nonce,
            )
            self.context.logger.info(
                "sending transaction {} to controller, message={}.".format(tx_id, msg)
            )
            self.context.outbox.put_message(message=msg)

    def _put_msg_get_balance(self):
        game = cast(Game, self.context.game)
        ledger_id = game.ledger_id

        ledger_api_dialogues = cast(
            LedgerApiDialogues, self.context.ledger_api_dialogues
        )
        ledger_api_msg, _ = ledger_api_dialogues.create(
            counterparty=LEDGER_API_ADDRESS,
            performative=LedgerApiMessage.Performative.GET_BALANCE,
            ledger_id=ledger_id,
            address=self.context.agent_address),
        )
        self.context.outbox.put_message(message=ledger_api_msg)

    def fund_wallet(self):
        self._put_msg_get_balance()
        # TODO: handle msg result
        fund_wallet()
        # TODO: check is wallet funded
