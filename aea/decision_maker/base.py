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

import copy
import logging
import math
import threading
from enum import Enum
from queue import Queue
from threading import Thread
from typing import Any, Dict, List, Optional, cast

from aea.crypto.ethereum import ETHEREUM
from aea.crypto.ledger_apis import LedgerApis, SUPPORTED_LEDGER_APIS
from aea.crypto.wallet import Wallet
from aea.decision_maker.messages.base import InternalMessage
from aea.decision_maker.messages.state_update import StateUpdateMessage
from aea.decision_maker.messages.transaction import OFF_CHAIN, TransactionMessage
from aea.helpers.preference_representations.base import (
    linear_utility,
    logarithmic_utility,
)
from aea.mail.base import OutBox

CurrencyHoldings = Dict[str, int]  # a map from identifier to quantity
GoodHoldings = Dict[str, int]  # a map from identifier to quantity
UtilityParams = Dict[str, float]  # a map from identifier to quantity
ExchangeParams = Dict[str, float]  # a map from identifier to quantity

SENDER_TX_SHARE = 0.5
QUANTITY_SHIFT = 100
OFF_CHAIN_SETTLEMENT_DIGEST = cast(Optional[str], "off_chain_settlement")

logger = logging.getLogger(__name__)


class GoalPursuitReadiness:
    """The goal pursuit readiness."""

    class Status(Enum):
        """The enum of status."""

        READY = "ready"
        NOT_READY = "not_ready"

    def __init__(self):
        """Instantiate an ownership state object."""
        self._status = GoalPursuitReadiness.Status.NOT_READY

    @property
    def is_ready(self) -> bool:
        """Get the readiness."""
        return self._status.value == GoalPursuitReadiness.Status.READY.value

    def update(self, new_status: Status) -> None:
        """Update the goal pursuit readiness."""
        self._status = new_status


class OwnershipState:
    """Represent the ownership state of an agent."""

    def __init__(self):
        """Instantiate an ownership state object."""
        self._amount_by_currency_id = None  # type: CurrencyHoldings
        self._quantities_by_good_id = None  # type: GoodHoldings

    def init(
        self,
        amount_by_currency_id: CurrencyHoldings,
        quantities_by_good_id: GoodHoldings,
        agent_name: str = "",
    ):
        """
        Instantiate an ownership state object.

        :param amount_by_currency_id: the currency endowment of the agent in this state.
        :param quantities_by_good_id: the good endowment of the agent in this state.
        :param agent_name: the agent name
        """
        logger.warning(
            "[{}]: Careful! OwnershipState are being initialized!".format(agent_name)
        )
        self._amount_by_currency_id = copy.copy(amount_by_currency_id)
        self._quantities_by_good_id = copy.copy(quantities_by_good_id)

    @property
    def is_initialized(self) -> bool:
        """Get the initialization status."""
        return (
            self._amount_by_currency_id is not None
            and self._quantities_by_good_id is not None
        )

    @property
    def amount_by_currency_id(self) -> CurrencyHoldings:
        """Get currency holdings in this state."""
        assert self._amount_by_currency_id is not None, "CurrencyHoldings not set!"
        return copy.copy(self._amount_by_currency_id)

    @property
    def quantities_by_good_id(self) -> GoodHoldings:
        """Get good holdings in this state."""
        assert self._quantities_by_good_id is not None, "GoodHoldings not set!"
        return copy.copy(self._quantities_by_good_id)

    def is_affordable_transaction(self, tx_message: TransactionMessage) -> bool:
        """
        Check if the transaction is affordable (and consistent).

        E.g. check that the agent state has enough money if it is a buyer or enough holdings if it is a seller.
        Note, the agent is the sender of the transaction message by design.
        :return: True if the transaction is legal wrt the current state, false otherwise.
        """
        if tx_message.amount == 0 and all(
            quantity == 0 for quantity in tx_message.tx_quantities_by_good_id.values()
        ):
            # reject the transaction when there is no wealth exchange
            result = False
        elif tx_message.amount <= 0 and all(
            quantity >= 0 for quantity in tx_message.tx_quantities_by_good_id.values()
        ):
            # check if the agent has the money to cover the sender_amount (the agent=sender is the buyer)
            result = (
                self.amount_by_currency_id[tx_message.currency_id]
                >= tx_message.sender_amount
            )
        elif tx_message.amount >= 0 and all(
            quantity <= 0 for quantity in tx_message.tx_quantities_by_good_id.values()
        ):
            # check if the agent has the goods (the agent=sender is the seller).
            result = all(
                self.quantities_by_good_id[good_id] >= -quantity
                for good_id, quantity in tx_message.tx_quantities_by_good_id.items()
            )
        else:
            result = False
        return result

    def _update(self, tx_message: TransactionMessage) -> None:
        """
        Update the agent state from a transaction.

        :param tx_message:
        :return: None
        """
        assert self.is_affordable_transaction(tx_message), "Inconsistent transaction."

        self._amount_by_currency_id[tx_message.currency_id] += tx_message.sender_amount

        for good_id, quantity_delta in tx_message.tx_quantities_by_good_id.items():
            self._quantities_by_good_id[good_id] += quantity_delta

    def apply_transactions(
        self, transactions: List[TransactionMessage]
    ) -> "OwnershipState":
        """
        Apply a list of transactions to (a copy of) the current state.

        :param transactions: the sequence of transaction messages.
        :return: the final state.
        """
        new_state = copy.copy(self)
        for tx_message in transactions:
            new_state._update(tx_message)

        return new_state

    def apply_state_update(
        self,
        amount_by_currency_id: Dict[str, int],
        quantities_by_good_id: Dict[str, int],
    ) -> "OwnershipState":
        """
        Apply a state update to the current state.

        :param amount_by_currency_id: the delta in the currency amounts
        :param quantities_by_good_id: the delta in the quantities by good
        :return: the final state.
        """
        new_state = copy.copy(self)

        for currency, amount_delta in amount_by_currency_id.items():
            new_state._amount_by_currency_id[currency] += amount_delta

        for good_id, quantity_delta in quantities_by_good_id.items():
            new_state._quantities_by_good_id[good_id] += quantity_delta

        return new_state

    def __copy__(self):
        """Copy the object."""
        state = OwnershipState()
        if (
            self.amount_by_currency_id is not None
            and self.quantities_by_good_id is not None
        ):
            state._amount_by_currency_id = self.amount_by_currency_id
            state._quantities_by_good_id = self.quantities_by_good_id
        return state


class LedgerStateProxy:
    """Class to represent a proxy to a ledger state."""

    def __init__(self, ledger_apis: LedgerApis):
        """Instantiate a ledger state proxy."""
        self._ledger_apis = ledger_apis

    @property
    def ledger_apis(self) -> LedgerApis:
        """Get the ledger_apis."""
        return self._ledger_apis

    @property
    def is_initialized(self) -> bool:
        """Get the initialization status."""
        return self._ledger_apis.has_default_ledger

    def is_affordable_transaction(self, tx_message: TransactionMessage) -> bool:
        """
        Check if the transaction is affordable on the ledger.

        :param tx_message: the transaction message
        :return: whether the transaction is affordable on the ledger
        """
        if tx_message.sender_amount <= 0:
            # check if the agent has the money to cover counterparty amount and tx fees
            available_balance = self.ledger_apis.token_balance(
                tx_message.ledger_id, tx_message.tx_sender_addr
            )
            is_affordable = (
                tx_message.counterparty_amount + tx_message.fees <= available_balance
            )
        else:
            is_affordable = True
        return is_affordable


class Preferences:
    """Class to represent the preferences."""

    def __init__(self):
        """Instantiate an agent preference object."""
        self._exchange_params_by_currency_id = None  # type: ExchangeParams
        self._utility_params_by_good_id = None  # type: UtilityParams
        self._transaction_fees = None  # type: Dict[str, int]
        self._quantity_shift = QUANTITY_SHIFT

    def init(
        self,
        exchange_params_by_currency_id: ExchangeParams,
        utility_params_by_good_id: UtilityParams,
        tx_fee: int,
        agent_name: str = "",
    ):
        """
        Instantiate an agent preference object.

        :param exchange_params_by_currency_id: the exchange params.
        :param utility_params_by_good_id: the utility params for every asset.
        :param agent_name: the agent name
        """
        logger.warning(
            "[{}]: Careful! Preferences are being initialized!".format(agent_name)
        )
        self._exchange_params_by_currency_id = exchange_params_by_currency_id
        self._utility_params_by_good_id = utility_params_by_good_id
        self._transaction_fees = self._split_tx_fees(tx_fee)

    @property
    def is_initialized(self) -> bool:
        """Get the initialization status."""
        return (
            (self._exchange_params_by_currency_id is not None)
            and (self._utility_params_by_good_id is not None)
            and (self._transaction_fees is not None)
        )

    @property
    def exchange_params_by_currency_id(self) -> ExchangeParams:
        """Get exchange parameter for each currency."""
        assert (
            self._exchange_params_by_currency_id is not None
        ), "ExchangeParams not set!"
        return self._exchange_params_by_currency_id

    @property
    def utility_params_by_good_id(self) -> UtilityParams:
        """Get utility parameter for each good."""
        assert self._utility_params_by_good_id is not None, "UtilityParams not set!"
        return self._utility_params_by_good_id

    @property
    def transaction_fees(self) -> Dict[str, int]:
        """Get the transaction fee."""
        assert self._transaction_fees is not None, "Transaction fee not set!"
        return self._transaction_fees

    def logarithmic_utility(self, quantities_by_good_id: GoodHoldings) -> float:
        """
        Compute agent's utility given her utility function params and a good bundle.

        :param quantities_by_good_id: the good holdings (dictionary) with the identifier (key) and quantity (value) for each good
        :return: utility value
        """
        result = logarithmic_utility(
            self.utility_params_by_good_id, quantities_by_good_id, self._quantity_shift
        )
        return result

    def linear_utility(self, amount_by_currency_id: CurrencyHoldings) -> float:
        """
        Compute agent's utility given her utility function params and a currency bundle.

        :param amount_by_currency_id: the currency holdings (dictionary) with the identifier (key) and quantity (value) for each currency
        :return: utility value
        """
        result = linear_utility(
            self.exchange_params_by_currency_id, amount_by_currency_id
        )
        return result

    def get_score(
        self,
        quantities_by_good_id: GoodHoldings,
        amount_by_currency_id: CurrencyHoldings,
    ) -> float:
        """
        Compute the score given the good and currency holdings.

        :param quantities_by_good_id: the good holdings
        :param amount_by_currency_id: the currency holdings
        :return: the score.
        """
        goods_score = self.logarithmic_utility(quantities_by_good_id)
        currency_score = self.linear_utility(amount_by_currency_id)
        score = goods_score + currency_score
        return score

    def marginal_utility(
        self,
        ownership_state: OwnershipState,
        delta_quantities_by_good_id: Optional[GoodHoldings] = None,
        delta_amount_by_currency_id: Optional[CurrencyHoldings] = None,
    ) -> float:
        """
        Compute the marginal utility.

        :param ownership_state: the current ownership state
        :param delta_quantities_by_good_id: the change in good holdings
        :param delta_amount_by_currency_id: the change in money holdings
        :return: the marginal utility score
        """
        current_goods_score = self.logarithmic_utility(
            ownership_state.quantities_by_good_id
        )
        current_currency_score = self.linear_utility(
            ownership_state.amount_by_currency_id
        )
        new_goods_score = current_goods_score
        new_currency_score = current_currency_score
        if delta_quantities_by_good_id is not None:
            new_quantities_by_good_id = {
                good_id: quantity + delta_quantities_by_good_id[good_id]
                for good_id, quantity in ownership_state.quantities_by_good_id.items()
            }
            new_goods_score = self.logarithmic_utility(new_quantities_by_good_id)
        if delta_amount_by_currency_id is not None:
            new_amount_by_currency_id = {
                currency: amount + delta_amount_by_currency_id[currency]
                for currency, amount in ownership_state.amount_by_currency_id.items()
            }
            new_currency_score = self.linear_utility(new_amount_by_currency_id)
        return (
            new_goods_score
            + new_currency_score
            - current_goods_score
            - current_currency_score
        )

    def get_score_diff_from_transaction(
        self, ownership_state: OwnershipState, tx_message: TransactionMessage
    ) -> float:
        """
        Simulate a transaction and get the resulting score (taking into account the fee).

        :param tx_message: a transaction object.
        :return: the score.
        """
        current_score = self.get_score(
            quantities_by_good_id=ownership_state.quantities_by_good_id,
            amount_by_currency_id=ownership_state.amount_by_currency_id,
        )
        new_ownership_state = ownership_state.apply_transactions([tx_message])
        new_score = self.get_score(
            quantities_by_good_id=new_ownership_state.quantities_by_good_id,
            amount_by_currency_id=new_ownership_state.amount_by_currency_id,
        )
        return new_score - current_score

    @staticmethod
    def _split_tx_fees(tx_fee: int) -> Dict[str, int]:
        """
        Split the transaction fee.

        :param tx_fee: the tx fee
        :return: the split into buyer and seller part
        """
        buyer_part = math.ceil(tx_fee * SENDER_TX_SHARE)
        seller_part = math.ceil(tx_fee * (1 - SENDER_TX_SHARE))
        if buyer_part + seller_part > tx_fee:
            seller_part -= 1
        return {"seller_tx_fee": seller_part, "buyer_tx_fee": buyer_part}


class DecisionMaker:
    """This class implements the decision maker."""

    def __init__(
        self,
        agent_name: str,
        max_reactions: int,
        outbox: OutBox,
        wallet: Wallet,
        ledger_apis: LedgerApis,
    ):
        """
        Initialize the decision maker.

        :param agent_name: the name of the agent
        :param max_reactions: the processing rate of messages per iteration.
        :param outbox: the outbox
        :param wallet: the wallet
        :param ledger_apis: the ledger apis
        """
        self._max_reactions = max_reactions
        self._agent_name = agent_name
        self._outbox = outbox
        self._wallet = wallet
        self._ledger_apis = ledger_apis
        self._message_in_queue = Queue()  # type: Queue
        self._message_out_queue = Queue()  # type: Queue
        self._ownership_state = OwnershipState()
        self._ledger_state_proxy = LedgerStateProxy(ledger_apis)
        self._preferences = Preferences()
        self._goal_pursuit_readiness = GoalPursuitReadiness()

        self._thread = None  # type: Optional[Thread]
        self._lock = threading.Lock()
        self._stopped = True

    @property
    def message_in_queue(self) -> Queue:
        """Get (in) queue."""
        return self._message_in_queue

    @property
    def message_out_queue(self) -> Queue:
        """Get (out) queue."""
        return self._message_out_queue

    @property
    def wallet(self) -> Wallet:
        """Get wallet."""
        return self._wallet

    @property
    def ledger_apis(self) -> LedgerApis:
        """Get outbox."""
        return self._ledger_apis

    @property
    def outbox(self) -> OutBox:
        """Get outbox."""
        return self._outbox

    @property
    def ownership_state(self) -> OwnershipState:
        """Get ownership state."""
        return self._ownership_state

    @property
    def ledger_state_proxy(self) -> LedgerStateProxy:
        """Get ledger state proxy."""
        return self._ledger_state_proxy

    @property
    def preferences(self) -> Preferences:
        """Get preferences."""
        return self._preferences

    @property
    def goal_pursuit_readiness(self) -> GoalPursuitReadiness:
        """Get readiness of agent to pursuit its goals."""
        return self._goal_pursuit_readiness

    def start(self):
        """Start the decision maker."""
        with self._lock:
            if not self._stopped:  # pragma: no cover
                logger.debug("Decision maker already started.")
                return

            self._stopped = False
            self._thread = Thread(target=self.execute)
            self._thread.start()

    def stop(self):
        """Stop the decision maker."""
        with self._lock:
            self._stopped = True
            self.message_in_queue.put(None)
            if self._thread is not None:
                self._thread.join()
            logger.debug("Decision Maker stopped.")
            self._thread = None

    def execute(self) -> None:
        """
        Execute the decision maker.

        :return: None
        """
        while not self._stopped:
            message = self.message_in_queue.get(
                block=True
            )  # type: Optional[InternalMessage]

            if message is None:
                logger.debug(
                    "Decision Maker: Received empty message. Quitting the processing loop..."
                )
                continue

            if message.protocol_id == InternalMessage.protocol_id:
                self.handle(message)
            else:
                logger.warning(
                    "[{}]: Message received by the decision maker is not of protocol_id=internal.".format(
                        self._agent_name
                    )
                )

    def handle(self, message: InternalMessage) -> None:
        """
        Handle a message.

        :param message: the message
        :return: None
        """
        if isinstance(message, TransactionMessage):
            self._handle_tx_message(message)
        elif isinstance(message, StateUpdateMessage):
            self._handle_state_update_message(message)

    def _handle_tx_message(self, tx_message: TransactionMessage) -> None:
        """
        Handle a transaction message.

        :param tx_message: the transaction message
        :return: None
        """
        if tx_message.ledger_id not in SUPPORTED_LEDGER_APIS + [OFF_CHAIN]:
            logger.error(
                "[{}]: ledger_id={} is not supported".format(
                    self._agent_name, tx_message.ledger_id
                )
            )
            return

        if not self.goal_pursuit_readiness.is_ready:
            logger.debug(
                "[{}]: Preferences and ownership state not initialized!".format(
                    self._agent_name
                )
            )

        # check if the transaction is acceptable and process it accordingly
        if (
            tx_message.performative
            == TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT
        ):
            self._handle_tx_message_for_settlement(tx_message)
        elif (
            tx_message.performative
            == TransactionMessage.Performative.PROPOSE_FOR_SIGNING
        ):
            self._handle_tx_message_for_signing(tx_message)
        else:
            logger.error(
                "[{}]: Unexpected transaction message performative".format(
                    self._agent_name
                )
            )  # pragma: no cover

    def _handle_tx_message_for_settlement(self, tx_message) -> None:
        """
        Handle a transaction message for settlement.

        :param tx_message: the transaction message
        :return: None
        """
        if self._is_acceptable_for_settlement(tx_message):
            tx_digest = self._settle_tx(tx_message)
            if tx_digest is not None:
                tx_message_response = TransactionMessage.respond_settlement(
                    tx_message,
                    performative=TransactionMessage.Performative.SUCCESSFUL_SETTLEMENT,
                    tx_digest=tx_digest,
                )
            else:
                tx_message_response = TransactionMessage.respond_settlement(
                    tx_message,
                    performative=TransactionMessage.Performative.FAILED_SETTLEMENT,
                )
        else:
            tx_message_response = TransactionMessage.respond_settlement(
                tx_message,
                performative=TransactionMessage.Performative.REJECTED_SETTLEMENT,
            )
        self.message_out_queue.put(tx_message_response)

    def _is_acceptable_for_settlement(self, tx_message: TransactionMessage) -> bool:
        """
        Check if the tx is acceptable.

        :param tx_message: the transaction message
        :return: whether the transaction is acceptable or not
        """
        result = (
            self._is_valid_tx_amount(tx_message)
            and self._is_utility_enhancing(tx_message)
            and self._is_affordable(tx_message)
        )
        return result

    @staticmethod
    def _is_valid_tx_amount(tx_message: TransactionMessage) -> bool:
        """
        Check if the transaction amount is negative (agent is buyer).

        If the transaction amount is positive, then the agent is the seller, so abort.
        """
        result = tx_message.sender_amount <= 0
        return result

    def _is_utility_enhancing(self, tx_message: TransactionMessage) -> bool:
        """
        Check if the tx is utility enhancing.

        :param tx_message: the transaction message
        :return: whether the transaction is utility enhancing or not
        """
        if self.preferences.is_initialized and self.ownership_state.is_initialized:
            is_utility_enhancing = (
                self.preferences.get_score_diff_from_transaction(
                    self.ownership_state, tx_message
                )
                >= 0.0
            )
        else:
            logger.warning(
                "[{}]: Cannot verify whether transaction improves utility. Assuming it does!".format(
                    self._agent_name
                )
            )
            is_utility_enhancing = True
        return is_utility_enhancing

    def _is_affordable(self, tx_message: TransactionMessage) -> bool:
        """
        Check if the tx is affordable.

        :param tx_message: the transaction message
        :return: whether the transaction is affordable or not
        """
        is_affordable = True
        if self.ownership_state.is_initialized:
            is_affordable = self.ownership_state.is_affordable_transaction(tx_message)
        if self.ledger_state_proxy.is_initialized and (
            tx_message.ledger_id != OFF_CHAIN
        ):
            if tx_message.ledger_id in self.ledger_apis.apis.keys():
                is_affordable = (
                    is_affordable
                    and self.ledger_state_proxy.is_affordable_transaction(tx_message)
                )
            else:
                logger.error(
                    "[{}]: Ledger api not available for ledger_id={}!".format(
                        self._agent_name, tx_message.ledger_id
                    )
                )
                is_affordable = False
        if not self.ownership_state.is_initialized and not (
            self.ledger_state_proxy.is_initialized
            and (tx_message.ledger_id != OFF_CHAIN)
        ):
            logger.warning(
                "[{}]: Cannot verify whether transaction is affordable. Assuming it is!".format(
                    self._agent_name
                )
            )
            is_affordable = True
        return is_affordable

    def _settle_tx(self, tx_message: TransactionMessage) -> Optional[str]:
        """
        Settle the tx.

        :param tx_message: the transaction message
        :return: the transaction digest
        """
        if tx_message.ledger_id == OFF_CHAIN:
            logger.info(
                "[{}]: Cannot settle transaction, settlement happens off chain!".format(
                    self._agent_name
                )
            )
            tx_digest = OFF_CHAIN_SETTLEMENT_DIGEST
        else:
            logger.info("[{}]: Settling transaction on chain!".format(self._agent_name))
            crypto_object = self.wallet.crypto_objects.get(tx_message.ledger_id)
            tx_digest = self.ledger_apis.transfer(
                crypto_object,
                tx_message.tx_counterparty_addr,
                tx_message.counterparty_amount,
                tx_message.fees,
                info=tx_message.info,
                tx_nonce=cast(str, tx_message.get("tx_nonce")),
            )
        return tx_digest

    def _handle_tx_message_for_signing(self, tx_message: TransactionMessage) -> None:
        """
        Handle a transaction message for signing.

        :param tx_message: the transaction message
        :return: None
        """
        if self._is_acceptable_for_signing(tx_message):
            if self._is_valid_message(tx_message):
                tx_signature = self._sign_tx_hash(tx_message)
                tx_message_response = TransactionMessage.respond_signing(
                    tx_message,
                    performative=TransactionMessage.Performative.SUCCESSFUL_SIGNING,
                    signed_payload={"tx_signature": tx_signature},
                )
            if self._is_valid_tx(tx_message):
                tx_signed = self._sign_ledger_tx(tx_message)
                tx_message_response = TransactionMessage.respond_signing(
                    tx_message,
                    performative=TransactionMessage.Performative.SUCCESSFUL_SIGNING,
                    signed_payload={"tx_signed": tx_signed},
                )
        else:
            tx_message_response = TransactionMessage.respond_signing(
                tx_message,
                performative=TransactionMessage.Performative.REJECTED_SIGNING,
            )
        self.message_out_queue.put(tx_message_response)

    def _is_acceptable_for_signing(self, tx_message: TransactionMessage) -> bool:
        """
        Check if the tx message is acceptable for signing.

        :param tx_message: the transaction message
        :return: whether the transaction is acceptable or not
        """
        result = (
            (self._is_valid_message(tx_message) or self._is_valid_tx(tx_message))
            and self._is_utility_enhancing(tx_message)
            and self._is_affordable(tx_message)
        )
        return result

    @staticmethod
    def _is_valid_message(tx_message: TransactionMessage) -> bool:
        """
        Check if the tx hash is present and matches the terms.

        :param tx_message: the transaction message
        :return: whether the transaction hash is valid
        """
        # TODO check the hash matches the terms of the transaction, this means dm requires knowledge of how the hash is composed
        tx_hash = tx_message.signing_payload.get("tx_hash")
        is_valid = isinstance(tx_hash, bytes)
        return is_valid

    def _is_valid_tx(self, tx_message: TransactionMessage) -> bool:
        """
        Check if the transaction message contains a valid ledger transaction.


        :param tx_message: the transaction message
        :return: whether the transaction is valid
        """
        tx = tx_message.signing_payload.get("tx")
        is_valid = tx is not None
        return is_valid

    def _sign_tx_hash(self, tx_message: TransactionMessage) -> str:
        """
        Sign the tx hash.

        :param tx_message: the transaction message
        :return: the signature of the signing payload
        """
        if tx_message.ledger_id == OFF_CHAIN:
            crypto_object = self.wallet.crypto_objects.get(ETHEREUM)
            # TODO: replace with default_ledger when recover_hash function is available for FETCHAI
        else:
            crypto_object = self.wallet.crypto_objects.get(tx_message.ledger_id)
        tx_hash = tx_message.signing_payload.get("tx_hash")
        tx_signature = crypto_object.sign_message(tx_hash)
        return tx_signature

    def _sign_ledger_tx(self, tx_message) -> Any:
        """
        Handle a transaction message for deployment.

        :param tx_message: the transaction message
        :return: None
        """
        if tx_message.ledger_id == OFF_CHAIN:
            crypto_object = self.wallet.crypto_objects.get(ETHEREUM)
            # TODO: replace with default_ledger when recover_hash function is available for FETCHAI
        else:
            crypto_object = self.wallet.crypto_objects.get(tx_message.ledger_id)
        tx = tx_message.signing_payload.get("tx")
        tx_signed = crypto_object.sign_transaction(tx)
        return tx_signed

    def _handle_state_update_message(
        self, state_update_message: StateUpdateMessage
    ) -> None:
        """
        Handle a state update message.

        :param state_update_message: the state update message
        :return: None
        """
        if (
            state_update_message.performative
            == StateUpdateMessage.Performative.INITIALIZE
        ):
            logger.info("[{}]: Applying state initialization!".format(self._agent_name))
            self.ownership_state.init(
                amount_by_currency_id=state_update_message.amount_by_currency_id,
                quantities_by_good_id=state_update_message.quantities_by_good_id,
                agent_name=self._agent_name,
            )
            self.preferences.init(
                exchange_params_by_currency_id=state_update_message.exchange_params_by_currency_id,
                utility_params_by_good_id=state_update_message.utility_params_by_good_id,
                tx_fee=state_update_message.tx_fee,
                agent_name=self._agent_name,
            )
            self.goal_pursuit_readiness.update(GoalPursuitReadiness.Status.READY)
        elif state_update_message.performative == StateUpdateMessage.Performative.APPLY:
            logger.info("[{}]: Applying state update!".format(self._agent_name))
            new_ownership_state = self.ownership_state.apply_state_update(
                amount_by_currency_id=state_update_message.amount_by_currency_id,
                quantities_by_good_id=state_update_message.quantities_by_good_id,
            )
            self._ownership_state = new_ownership_state
