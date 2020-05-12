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

"""This module contains a scaffold of the decision maker class and auxilliary classes."""

from typing import List

from aea.decision_maker.base import DecisionMaker as BaseDecisionMaker
from aea.decision_maker.base import LedgerStateProxy as BaseLedgerStateProxy
from aea.decision_maker.base import OwnershipState as BaseOwnershipState
from aea.decision_maker.base import Preferences as BasePreferences
from aea.decision_maker.messages.base import InternalMessage
from aea.decision_maker.messages.transaction import TransactionMessage


class OwnershipState(BaseOwnershipState):
    """Represent the ownership state of an agent."""

    def __init__(self):
        """
        Instantiate an ownership state object.

        :param decision_maker: the decision maker
        """
        raise NotImplementedError

    def set(self, **kwargs) -> None:
        """
        Set values on the ownership state.

        This method is used to initialize the ownership state with raw values.

        :param kwargs: the keyword arguments required to set the ownership state.
        """
        raise NotImplementedError

    def apply_delta(self, **kwargs) -> None:
        """
        Apply a state update to the ownership state.

        This method is used to apply a raw state update without a transaction.

        :param kwargs: the keyword arguments required to apply an update the ownership state.
        :return: None
        """
        raise NotImplementedError

    def is_affordable_transaction(self, tx_message: TransactionMessage) -> bool:
        """
        Check if the transaction is affordable (and consistent).

        :param tx_message: the transaction message
        :return: True if the transaction is legal wrt the current state, false otherwise.
        """
        raise NotImplementedError

    def apply_transactions(
        self, transactions: List[TransactionMessage]
    ) -> "OwnershipState":
        """
        Apply a list of transactions to (a copy of) the current state.

        :param transactions: the sequence of transaction messages.
        :return: the final state.
        """
        raise NotImplementedError

    def __copy__(self) -> "OwnershipState":
        """Copy the object."""
        raise NotImplementedError


class LedgerStateProxy(BaseLedgerStateProxy):
    """Class to represent a proxy to a ledger state."""

    def __init__(self):
        """Instantiate a ledger state proxy."""
        raise NotImplementedError

    @property
    def is_initialized(self) -> bool:
        """Get the initialization status."""
        raise NotImplementedError

    def is_affordable_transaction(self, tx_message: TransactionMessage) -> bool:
        """
        Check if the transaction is affordable on the default ledger.

        :param tx_message: the transaction message
        :return: whether the transaction is affordable on the ledger
        """
        raise NotImplementedError


class Preferences(BasePreferences):
    """Class to represent the preferences."""

    def __init__(self):
        """
        Instantiate an agent preference object.
        """
        raise NotImplementedError

    def set(self, **kwargs) -> None:
        """
        Set values on the preferences.

        This method is used to initialize the preferences with raw values.

        :param kwargs: the keyword arguments required to apply an update the preferences.
        """
        raise NotImplementedError

    @property
    def is_initialized(self) -> bool:
        """
        Get the initialization status.

        Returns True if exchange_params_by_currency_id and utility_params_by_good_id are not None.
        """
        raise NotImplementedError

    def marginal_utility(self, ownership_state: BaseOwnershipState, **kwargs) -> float:
        """
        Compute the marginal utility.

        :param ownership_state: the ownership state against which to compute the marginal utility.
        :param kwargs: additional key word arguments
        :return: the marginal utility score
        """
        raise NotImplementedError

    def utility_diff_from_transaction(
        self,
        ownership_state: BaseOwnershipState,
        tx_message: TransactionMessage,
        **kwargs
    ) -> float:
        """
        Simulate a transaction and get the resulting utility difference (taking into account the fee).

        :param ownership_state: the ownership state against which to apply the transaction.
        :param tx_message: a transaction message.
        :param kwargs: additional key word arguments
        :return: the score.
        """
        raise NotImplementedError

    def __copy__(self) -> "Preferences":
        """Copy the object."""
        raise NotImplementedError


class DecisionMaker(BaseDecisionMaker):
    """This class implements the decision maker."""

    def __init__(self, **kwargs):
        """
        Initialize the decision maker.
        """
        ownership_state = OwnershipState()
        ledger_state_proxy = LedgerStateProxy()
        preferences = Preferences()
        super().__init__(
            ownership_state=ownership_state,
            ledger_state_proxy=ledger_state_proxy,
            preferences=preferences,
            **kwargs,
        )

    def handle(self, message: InternalMessage) -> None:
        """
        Handle an internal message from the skills.

        This method is used to:
            - update the ownership state
            - check transactions satisfy the preferences

        :param message: the internal message
        :return: None
        """
        raise NotImplementedError
