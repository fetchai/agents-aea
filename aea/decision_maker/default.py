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
from enum import Enum
from typing import Dict, List, Optional, cast

from aea.crypto.wallet import Wallet
from aea.decision_maker.base import DecisionMakerHandler as BaseDecisionMakerHandler
from aea.decision_maker.base import OwnershipState as BaseOwnershipState
from aea.decision_maker.base import Preferences as BasePreferences
from aea.helpers.preference_representations.base import (
    linear_utility,
    logarithmic_utility,
)
from aea.helpers.transaction.base import Terms
from aea.identity.base import Identity
from aea.protocols.base import Message
from aea.protocols.signing.message import SigningMessage

CurrencyHoldings = Dict[str, int]  # a map from identifier to quantity
GoodHoldings = Dict[str, int]  # a map from identifier to quantity
UtilityParams = Dict[str, float]  # a map from identifier to quantity
ExchangeParams = Dict[str, float]  # a map from identifier to quantity

SENDER_TX_SHARE = 0.5
QUANTITY_SHIFT = 100

logger = logging.getLogger(__name__)


class GoalPursuitReadiness:
    """The goal pursuit readiness."""

    class Status(Enum):
        """
        The enum of the readiness status.

        In particular, it can be one of the following:

        - Status.READY: when the agent is ready to pursuit its goal
        - Status.NOT_READY: when the agent is not ready to pursuit its goal
        """

        READY = "ready"
        NOT_READY = "not_ready"

    def __init__(self):
        """Instantiate the goal pursuit readiness."""
        self._status = GoalPursuitReadiness.Status.NOT_READY

    @property
    def is_ready(self) -> bool:
        """Get the readiness."""
        return self._status.value == GoalPursuitReadiness.Status.READY.value

    def update(self, new_status: Status) -> None:
        """
        Update the goal pursuit readiness.

        :param new_status: the new status
        :return: None
        """
        self._status = new_status


class OwnershipState(BaseOwnershipState):
    """Represent the ownership state of an agent (can proxy a ledger)."""

    def __init__(self):
        """
        Instantiate an ownership state object.

        :param decision_maker: the decision maker
        """
        self._amount_by_currency_id = None  # type: Optional[CurrencyHoldings]
        self._quantities_by_good_id = None  # type: Optional[GoodHoldings]

    def set(
        self,
        amount_by_currency_id: CurrencyHoldings = None,
        quantities_by_good_id: GoodHoldings = None,
        **kwargs,
    ) -> None:
        """
        Set values on the ownership state.

        :param amount_by_currency_id: the currency endowment of the agent in this state.
        :param quantities_by_good_id: the good endowment of the agent in this state.
        """
        assert (
            amount_by_currency_id is not None and quantities_by_good_id is not None
        ), "Must provide values."
        assert (
            not self.is_initialized
        ), "Cannot apply state update, current state is already initialized!"

        self._amount_by_currency_id = copy.copy(amount_by_currency_id)
        self._quantities_by_good_id = copy.copy(quantities_by_good_id)

    def apply_delta(
        self,
        delta_amount_by_currency_id: Dict[str, int] = None,
        delta_quantities_by_good_id: Dict[str, int] = None,
        **kwargs,
    ) -> None:
        """
        Apply a state update to the ownership state.

        This method is used to apply a raw state update without a transaction.

        :param delta_amount_by_currency_id: the delta in the currency amounts
        :param delta_quantities_by_good_id: the delta in the quantities by good
        :return: None
        """
        assert (
            delta_amount_by_currency_id is not None
            and delta_quantities_by_good_id is not None
        ), "Must provide values."
        assert (
            self._amount_by_currency_id is not None
            and self._quantities_by_good_id is not None
        ), "Cannot apply state update, current state is not initialized!"
        assert all(
            [
                key in self._amount_by_currency_id
                for key in delta_amount_by_currency_id.keys()
            ]
        ), "Invalid keys present in delta_amount_by_currency_id."
        assert all(
            [
                key in self._quantities_by_good_id
                for key in delta_quantities_by_good_id.keys()
            ]
        ), "Invalid keys present in delta_quantities_by_good_id."

        for currency_id, amount_delta in delta_amount_by_currency_id.items():
            self._amount_by_currency_id[currency_id] += amount_delta

        for good_id, quantity_delta in delta_quantities_by_good_id.items():
            self._quantities_by_good_id[good_id] += quantity_delta

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

    def is_affordable_transaction(self, terms: Terms) -> bool:
        """
        Check if the transaction is affordable (and consistent).

        E.g. check that the agent state has enough money if it is a buyer or enough holdings if it is a seller.
        Note, the agent is the sender of the transaction message by design.

        :param terms: the transaction terms
        :return: True if the transaction is legal wrt the current state, false otherwise.
        """
        if all(amount == 0 for amount in terms.amount_by_currency_id.values()) and all(
            quantity == 0 for quantity in terms.quantities_by_good_id.values()
        ):
            # reject the transaction when there is no wealth exchange
            result = False
        elif all(
            amount <= 0 for amount in terms.amount_by_currency_id.values()
        ) and all(quantity >= 0 for quantity in terms.quantities_by_good_id.values()):
            # check if the agent has the money to cover the sender_amount (the agent=sender is the buyer)
            result = all(
                self.amount_by_currency_id[currency_id] >= -amount
                for currency_id, amount in terms.amount_by_currency_id.items()
            )
        elif all(
            amount >= 0 for amount in terms.amount_by_currency_id.values()
        ) and all(quantity <= 0 for quantity in terms.quantities_by_good_id.values()):
            # check if the agent has the goods (the agent=sender is the seller).
            result = all(
                self.quantities_by_good_id[good_id] >= -quantity
                for good_id, quantity in terms.quantities_by_good_id.items()
            )
        else:
            result = False
        return result

    def is_affordable(self, terms: Terms) -> bool:
        """
        Check if the tx is affordable.

        :param terms: the transaction terms
        :return: whether the transaction is affordable or not
        """
        if self.is_initialized:
            is_affordable = self.is_affordable_transaction(terms)
        else:
            logger.warning(
                "Cannot verify whether transaction is affordable as ownership state is not initialized. Assuming it is!"
            )
            is_affordable = True
        return is_affordable

    def update(self, terms: Terms) -> None:
        """
        Update the agent state from a transaction.

        :param terms: the transaction terms
        :return: None
        """
        assert (
            self._amount_by_currency_id is not None
            and self._quantities_by_good_id is not None
        ), "Cannot apply state update, current state is not initialized!"
        for currency_id, amount_delta in terms.amount_by_currency_id.items():
            self._amount_by_currency_id[currency_id] += amount_delta

        for good_id, quantity_delta in terms.quantities_by_good_id.items():
            self._quantities_by_good_id[good_id] += quantity_delta

    def apply_transactions(self, list_of_terms: List[Terms]) -> "OwnershipState":
        """
        Apply a list of transactions to (a copy of) the current state.

        :param list_of_terms: the sequence of transaction terms.
        :return: the final state.
        """
        new_state = copy.copy(self)
        for terms in list_of_terms:
            new_state.update(terms)

        return new_state

    def __copy__(self) -> "OwnershipState":
        """Copy the object."""
        state = OwnershipState()
        if self.is_initialized:
            state._amount_by_currency_id = self.amount_by_currency_id
            state._quantities_by_good_id = self.quantities_by_good_id
        return state


class Preferences(BasePreferences):
    """Class to represent the preferences."""

    def __init__(self):
        """Instantiate an agent preference object."""
        self._exchange_params_by_currency_id = None  # type: Optional[ExchangeParams]
        self._utility_params_by_good_id = None  # type: Optional[UtilityParams]
        self._transaction_fees = None  # type: Optional[Dict[str, int]]
        self._quantity_shift = QUANTITY_SHIFT

    def set(
        self,
        exchange_params_by_currency_id: ExchangeParams = None,
        utility_params_by_good_id: UtilityParams = None,
        tx_fee: int = None,
        **kwargs,
    ) -> None:
        """
        Set values on the preferences.

        :param exchange_params_by_currency_id: the exchange params.
        :param utility_params_by_good_id: the utility params for every asset.
        :param tx_fee: the acceptable transaction fee.
        """
        assert (
            exchange_params_by_currency_id is not None
            and utility_params_by_good_id is not None
            and tx_fee is not None
        ), "Must provide values."
        assert (
            not self.is_initialized
        ), "Cannot apply preferences update, preferences already initialized!"

        self._exchange_params_by_currency_id = copy.copy(exchange_params_by_currency_id)
        self._utility_params_by_good_id = copy.copy(utility_params_by_good_id)
        self._transaction_fees = self._split_tx_fees(tx_fee)  # TODO: update

    @property
    def is_initialized(self) -> bool:
        """
        Get the initialization status.

        Returns True if exchange_params_by_currency_id and utility_params_by_good_id are not None.
        """
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
    def seller_transaction_fee(self) -> int:
        """Get the transaction fee."""
        assert self._transaction_fees is not None, "Transaction fee not set!"
        return self._transaction_fees["seller_tx_fee"]

    @property
    def buyer_transaction_fee(self) -> int:
        """Get the transaction fee."""
        assert self._transaction_fees is not None, "Transaction fee not set!"
        return self._transaction_fees["buyer_tx_fee"]

    def logarithmic_utility(self, quantities_by_good_id: GoodHoldings) -> float:
        """
        Compute agent's utility given her utility function params and a good bundle.

        :param quantities_by_good_id: the good holdings (dictionary) with the identifier (key) and quantity (value) for each good
        :return: utility value
        """
        assert self.is_initialized, "Preferences params not set!"
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
        assert self.is_initialized, "Preferences params not set!"
        result = linear_utility(
            self.exchange_params_by_currency_id, amount_by_currency_id
        )
        return result

    def utility(
        self,
        quantities_by_good_id: GoodHoldings,
        amount_by_currency_id: CurrencyHoldings,
    ) -> float:
        """
        Compute the utility given the good and currency holdings.

        :param quantities_by_good_id: the good holdings
        :param amount_by_currency_id: the currency holdings
        :return: the utility value.
        """
        assert self.is_initialized, "Preferences params not set!"
        goods_score = self.logarithmic_utility(quantities_by_good_id)
        currency_score = self.linear_utility(amount_by_currency_id)
        score = goods_score + currency_score
        return score

    def marginal_utility(
        self,
        ownership_state: BaseOwnershipState,
        delta_quantities_by_good_id: Optional[GoodHoldings] = None,
        delta_amount_by_currency_id: Optional[CurrencyHoldings] = None,
        **kwargs,
    ) -> float:
        """
        Compute the marginal utility.

        :param ownership_state: the ownership state against which to compute the marginal utility.
        :param delta_quantities_by_good_id: the change in good holdings
        :param delta_amount_by_currency_id: the change in money holdings
        :return: the marginal utility score
        """
        assert self.is_initialized, "Preferences params not set!"
        ownership_state = cast(OwnershipState, ownership_state)
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
        marginal_utility = (
            new_goods_score
            + new_currency_score
            - current_goods_score
            - current_currency_score
        )
        return marginal_utility

    def utility_diff_from_transaction(
        self, ownership_state: BaseOwnershipState, terms: Terms
    ) -> float:
        """
        Simulate a transaction and get the resulting utility difference (taking into account the fee).

        :param ownership_state: the ownership state against which to apply the transaction.
        :param terms: the transaction terms.
        :return: the score.
        """
        assert self.is_initialized, "Preferences params not set!"
        ownership_state = cast(OwnershipState, ownership_state)
        current_score = self.utility(
            quantities_by_good_id=ownership_state.quantities_by_good_id,
            amount_by_currency_id=ownership_state.amount_by_currency_id,
        )
        new_ownership_state = ownership_state.apply_transactions([terms])
        new_score = self.utility(
            quantities_by_good_id=new_ownership_state.quantities_by_good_id,
            amount_by_currency_id=new_ownership_state.amount_by_currency_id,
        )
        score_difference = new_score - current_score
        return score_difference

    def is_utility_enhancing(
        self, ownership_state: BaseOwnershipState, terms: Terms
    ) -> bool:
        """
        Check if the tx is utility enhancing.

        :param ownership_state: the ownership state against which to apply the transaction.
        :param terms: the transaction terms
        :return: whether the transaction is utility enhancing or not
        """
        if self.is_initialized and ownership_state.is_initialized:
            is_utility_enhancing = (
                self.utility_diff_from_transaction(ownership_state, terms) >= 0.0
            )
        else:
            logger.warning(
                "Cannot verify whether transaction improves utility as preferences are not initialized. Assuming it does!"
            )
            is_utility_enhancing = True
        return is_utility_enhancing

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
        tx_fee_split = {"seller_tx_fee": seller_part, "buyer_tx_fee": buyer_part}
        return tx_fee_split

    def __copy__(self) -> "Preferences":
        """Copy the object."""
        preferences = Preferences()
        if self.is_initialized:
            preferences._exchange_params_by_currency_id = (
                self.exchange_params_by_currency_id
            )
            preferences._utility_params_by_good_id = self.utility_params_by_good_id
            preferences._transaction_fees = self._transaction_fees
        return preferences


class DecisionMakerHandler(BaseDecisionMakerHandler):
    """This class implements the decision maker."""

    def __init__(self, identity: Identity, wallet: Wallet):
        """
        Initialize the decision maker.

        :param identity: the identity
        :param wallet: the wallet
        """
        kwargs = {
            "goal_pursuit_readiness": GoalPursuitReadiness(),
            "ownership_state": OwnershipState(),
            "preferences": Preferences(),
        }
        super().__init__(
            identity=identity, wallet=wallet, **kwargs,
        )

    def handle(self, message: Message) -> None:
        """
        Handle an internal message from the skills.

        :param message: the internal message
        :return: None
        """
        if isinstance(message, SigningMessage):
            self._handle_signing_message(message)

    def _handle_signing_message(self, signing_msg: SigningMessage) -> None:
        """
        Handle a signing message.

        :param signing_msg: the transaction message
        :return: None
        """
        if not self.context.goal_pursuit_readiness.is_ready:
            logger.debug(
                "[{}]: Preferences and ownership state not initialized!".format(
                    self.agent_name
                )
            )

        # check if the transaction is acceptable and process it accordingly
        if signing_msg.performative == SigningMessage.Performative.SIGN_MESSAGE:
            self._handle_message_signing(signing_msg)
        elif signing_msg.performative == SigningMessage.Performative.SIGN_TRANSACTION:
            self._handle_transaction_signing(signing_msg)
        else:
            logger.error(
                "[{}]: Unexpected transaction message performative".format(
                    self.agent_name
                )
            )  # pragma: no cover

    def _handle_message_signing(self, signing_msg: SigningMessage) -> None:
        """
        Handle a message for signing.

        :param signing_msg: the transaction message
        :return: None
        """
        signing_msg_response = SigningMessage(
            performative=SigningMessage.Performative.ERROR,
            skill_callback_ids=signing_msg.skill_callback_ids,
            skill_callback_info=signing_msg.skill_callback_info,
            crypto_id=signing_msg.crypto_id,
            error_code=SigningMessage.ErrorCode.UNSUCCESSFUL_MESSAGE_SIGNING,
        )
        if self._is_acceptable_for_signing(signing_msg):
            signed_message = self.wallet.sign_message(
                signing_msg.crypto_id,
                signing_msg.message,
                signing_msg.is_deprecated_signing_mode,
            )
            if signed_message is not None:
                signing_msg_response = SigningMessage(
                    performative=SigningMessage.Performative.SIGNED_MESSAGE,
                    skill_callback_ids=signing_msg.skill_callback_ids,
                    skill_callback_info=signing_msg.skill_callback_info,
                    crypto_id=signing_msg.crypto_id,
                    signed_message=signed_message,
                )
        self.message_out_queue.put(signing_msg_response)

    def _handle_transaction_signing(self, signing_msg: SigningMessage) -> None:
        """
        Handle a transaction for signing.

        :param signing_msg: the transaction message
        :return: None
        """
        signing_msg_response = SigningMessage(
            performative=SigningMessage.Performative.ERROR,
            skill_callback_ids=signing_msg.skill_callback_ids,
            skill_callback_info=signing_msg.skill_callback_info,
            crypto_id=signing_msg.crypto_id,
            error_code=SigningMessage.ErrorCode.UNSUCCESSFUL_TRANSACTION_SIGNING,
        )
        if self._is_acceptable_for_signing(signing_msg):
            signed_tx = self.wallet.sign_transaction(
                signing_msg.crypto_id, signing_msg.raw_transaction.body
            )
            if signed_tx is not None:
                signing_msg_response = SigningMessage(
                    performative=SigningMessage.Performative.SIGNED_TRANSACTION,
                    skill_callback_ids=signing_msg.skill_callback_ids,
                    skill_callback_info=signing_msg.skill_callback_info,
                    crypto_id=signing_msg.crypto_id,
                    signed_transaction=signed_tx,
                )
        self.message_out_queue.put(signing_msg_response)

    def _is_acceptable_for_signing(self, signing_msg: SigningMessage) -> bool:
        """
        Check if the tx message is acceptable for signing.

        :param signing_msg: the transaction message
        :return: whether the transaction is acceptable or not
        """
        if signing_msg.has_terms:
            result = self.context.preferences.is_utility_enhancing(
                self.context.ownership_state, signing_msg.terms
            ) and self.context.ownership_state.is_affordable(signing_msg.terms)
        else:
            logger.warning(
                "Cannot verify whether transaction improves utility and is affordable as no terms are provided. Assuming it does!"
            )
            result = True
        return result
