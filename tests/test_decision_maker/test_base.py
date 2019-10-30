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

"""This module contains tests for decision_maker."""
from unittest import mock

import os
from queue import Queue

import pytest

from aea.crypto.ledger_apis import LedgerApis, DEFAULT_FETCHAI_CONFIG
from aea.crypto.wallet import Wallet, FETCHAI
from aea.decision_maker.base import OwnershipState, Preferences, DecisionMaker
from aea.decision_maker.messages.state_update import StateUpdateMessage
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.mail.base import OutBox  # , Envelope
from tests.conftest import CUR_PATH

MAX_REACTIONS = 10


class TestUtilityPreferencesBase:
    """Test the base.py for DecisionMaker."""

    @classmethod
    def setup_class(cls):
        """Initialise the class."""
        cls.ownership_state = OwnershipState()
        cls.preferences = Preferences()

    # OWNERSHIP_STATE
    def test_properties(self):
        """Test the assertion error for *_holdings."""
        with pytest.raises(AssertionError):
            self.ownership_state.currency_holdings

        with pytest.raises(AssertionError):
            self.ownership_state.good_holdings

    def test_initialisation(self):
        """Test the initialisation of the ownership_state."""
        currency_endowment = {"FET": 100.0}
        good_endowment = {"FET": 2}
        self.ownership_state.init(currency_endowment=currency_endowment, good_endowment=good_endowment)
        assert self.ownership_state.currency_holdings is not None
        assert self.ownership_state.good_holdings is not None

    def test_transaction_is_consistent(self):
        """Test the consistency of the transaction message."""
        currency_endowment = {"FET": 100.0}
        good_endowment = {"FET": 2}
        self.ownership_state.init(currency_endowment=currency_endowment, good_endowment=good_endowment)
        tx_message = TransactionMessage(performative=TransactionMessage.Performative.ACCEPT,
                                        skill_id="default",
                                        transaction_id="transaction0",
                                        sender="agent_1",
                                        counterparty="pk",
                                        is_sender_buyer=True,
                                        currency_pbk="FET",
                                        amount=1,
                                        sender_tx_fee=0,
                                        counterparty_tx_fee=0,
                                        quantities_by_good_pbk={"FET": 10},
                                        ledger_id="fetchai")

        assert self.ownership_state.check_transaction_is_consistent(tx_message=tx_message),\
            "We should have the money for the transaction!"

        tx_message = TransactionMessage(performative=TransactionMessage.Performative.ACCEPT,
                                        skill_id="default",
                                        transaction_id="transaction0",
                                        sender="agent_1",
                                        counterparty="pk",
                                        is_sender_buyer=False,
                                        currency_pbk="FET",
                                        amount=1,
                                        sender_tx_fee=0,
                                        counterparty_tx_fee=0,
                                        quantities_by_good_pbk={"FET": 10},
                                        ledger_id="fetchai")

        assert self.ownership_state.check_transaction_is_consistent(tx_message=tx_message), \
            "We should have the money for the transaction!"

    def test_apply(self):
        """Test the apply function."""
        currency_endowment = {"FET": 100.0}
        good_endowment = {"FET": 2}
        self.ownership_state.init(currency_endowment=currency_endowment, good_endowment=good_endowment)
        tx_message = TransactionMessage(performative=TransactionMessage.Performative.ACCEPT,
                                        skill_id="default",
                                        transaction_id="transaction0",
                                        sender="agent_1",
                                        counterparty="pk",
                                        is_sender_buyer=True,
                                        currency_pbk="FET",
                                        amount=20,
                                        sender_tx_fee=5,
                                        counterparty_tx_fee=0,
                                        quantities_by_good_pbk={"FET": 10},
                                        ledger_id="fetchai")
        list_of_transactions = [tx_message]
        state = self.ownership_state
        new_state = self.ownership_state.apply(transactions=list_of_transactions)
        assert state != new_state, "after applying a list_of_transactions must have a different state!"

    def test_transaction_update(self):
        """Test the tranasction update."""
        currency_endowment = {"FET": 100.0}
        good_endowment = {"FET": 2}

        self.ownership_state.init(currency_endowment=currency_endowment, good_endowment=good_endowment)
        tx_message = TransactionMessage(performative=TransactionMessage.Performative.ACCEPT,
                                        skill_id="default",
                                        transaction_id="transaction0",
                                        sender="agent_1",
                                        counterparty="pk",
                                        is_sender_buyer=True,
                                        currency_pbk="FET",
                                        amount=20,
                                        sender_tx_fee=5,
                                        counterparty_tx_fee=0,
                                        quantities_by_good_pbk={"FET": 10},
                                        ledger_id="fetchai")
        cur_holdings = self.ownership_state.currency_holdings['FET']
        self.ownership_state.update(tx_message=tx_message)
        assert self.ownership_state.currency_holdings['FET'] < cur_holdings

        tx_message = TransactionMessage(performative=TransactionMessage.Performative.ACCEPT,
                                        skill_id="default",
                                        transaction_id="transaction0",
                                        sender="agent_1",
                                        counterparty="pk",
                                        is_sender_buyer=False,
                                        currency_pbk="FET",
                                        amount=20,
                                        sender_tx_fee=5,
                                        counterparty_tx_fee=0,
                                        quantities_by_good_pbk={"FET": 10},
                                        ledger_id="fetchai")
        cur_holdings = self.ownership_state.currency_holdings['FET']
        self.ownership_state.update(tx_message=tx_message)
        assert self.ownership_state.currency_holdings['FET'] > cur_holdings

    # # PREFERENCES
    def test_preferences_properties(self):
        """Test the properties of the preferences class."""
        with pytest.raises(AssertionError):
            self.preferences.exchange_params
        with pytest.raises(AssertionError):
            self.preferences.utility_params

    def test_preferences_init(self):
        """Test the preferences init()."""
        utility_params = {"FET": 20.0}
        exchange_params = {"FET": 10.0}
        self.preferences.init(utility_params=utility_params, exchange_params=exchange_params)
        assert self.preferences.utility_params is not None
        assert self.preferences.exchange_params is not None

    def test_utilities(self):
        """Test the utilities."""
        good_holdings = {"FET": 2}
        currency_holdings = {"FET": 100.0}
        utility_params = {"FET": 20.0}
        exchange_params = {"FET": 10.0}
        self.preferences.init(utility_params=utility_params, exchange_params=exchange_params)
        log_utility = self.preferences.logarithmic_utility(good_holdings=good_holdings)
        assert log_utility is not None

        linear_utility = self.preferences.linear_utility(currency_holdings=currency_holdings)
        assert linear_utility is not None

        score = self.preferences.get_score(good_holdings=good_holdings, currency_holdings=currency_holdings)
        assert score == log_utility + linear_utility

    def test_score_diff_from_transaction(self):
        """Test the difference between the scores."""
        good_holdings = {"FET": 2}
        currency_holdings = {"FET": 100.0}
        utility_params = {"FET": 20.0}
        exchange_params = {"FET": 10.0}
        self.ownership_state.init(currency_endowment=currency_holdings, good_endowment=good_holdings)
        self.preferences.init(utility_params=utility_params, exchange_params=exchange_params)
        tx_message = TransactionMessage(performative=TransactionMessage.Performative.ACCEPT,
                                        skill_id="default",
                                        transaction_id="transaction0",
                                        sender="agent_1",
                                        counterparty="pk",
                                        is_sender_buyer=False,
                                        currency_pbk="FET",
                                        amount=20,
                                        sender_tx_fee=5,
                                        counterparty_tx_fee=0,
                                        quantities_by_good_pbk={"FET": 10},
                                        ledger_id="fetchai")

        cur_score = self.preferences.get_score(good_holdings=good_holdings, currency_holdings=currency_holdings)
        new_state = self.ownership_state.apply([tx_message])
        new_score = self.preferences.get_score(good_holdings=new_state.good_holdings, currency_holdings=new_state.currency_holdings)
        dif_scores = new_score - cur_score
        score_difference = self.preferences.get_score_diff_from_transaction(ownership_state=self.ownership_state, tx_message=tx_message)
        assert score_difference == dif_scores

    @classmethod
    def teardown_class(cls):
        """Teardown any state that was previously setup with a call to setup_class."""


class TestDecisionMaker:
    """Test the decision maker."""

    @classmethod
    def setup_class(cls):
        """Initialise the decision maker."""
        cls.outbox = OutBox(Queue())
        private_key_pem_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
        cls.wallet = Wallet({FETCHAI: private_key_pem_path})
        cls.ledger_apis = LedgerApis({FETCHAI: DEFAULT_FETCHAI_CONFIG})
        cls.agent_name = "test"
        cls.ownership_state = OwnershipState()
        cls.preferences = Preferences()
        cls.decision_maker = DecisionMaker(agent_name=cls.agent_name, max_reactions=MAX_REACTIONS, outbox=cls.outbox,
                                           wallet=cls.wallet, ledger_apis=cls.ledger_apis)

    def test_properties(self):
        """Test the properties of the decision maker."""
        assert self.decision_maker.outbox.empty()
        assert isinstance(self.decision_maker.message_in_queue, Queue)
        assert isinstance(self.decision_maker.message_out_queue, Queue)
        assert isinstance(self.decision_maker.ledger_apis, LedgerApis)
        assert isinstance(self.outbox, OutBox)

    def test_decision_maker_execute(self):
        """Test the execute method."""
        tx_message = TransactionMessage(performative=TransactionMessage.Performative.ACCEPT,
                                        skill_id="default",
                                        transaction_id="transaction0",
                                        sender="agent_1",
                                        counterparty="pk",
                                        is_sender_buyer=True,
                                        currency_pbk="FET",
                                        amount=2,
                                        sender_tx_fee=0,
                                        counterparty_tx_fee=0,
                                        quantities_by_good_pbk={"FET": 10},
                                        ledger_id="fetchai")

        self.decision_maker.message_in_queue.put_nowait(tx_message)
        self.decision_maker.execute()
        assert self.decision_maker.message_in_queue.empty()
        good_endowment = {"FET": 2}
        currency_endowment = {"FET": 100.0}
        utility_params = {"FET": 20.0}
        exchange_params = {"FET": 10.0}

        state_update_message = StateUpdateMessage(currency_endowment=currency_endowment, good_endowment=good_endowment,
                                                  utility_params=utility_params, exchange_params=exchange_params)
        self.decision_maker.handle(state_update_message)
        assert self.decision_maker.ownership_state.good_holdings == good_endowment

        with mock.patch.object(self.decision_maker, "_is_acceptable_tx", return_value=True):
            self.decision_maker.handle(tx_message)
            assert not self.decision_maker.message_out_queue.empty()
            with mock.patch.object(self.decision_maker, "_settle_tx", return_value="This is a test digest"):
                self.decision_maker.handle(tx_message)
                assert not self.decision_maker.message_out_queue.empty()
