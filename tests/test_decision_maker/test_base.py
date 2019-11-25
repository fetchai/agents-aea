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

import aea
import aea.decision_maker.base
from aea.crypto.ledger_apis import LedgerApis, DEFAULT_FETCHAI_CONFIG
from aea.crypto.wallet import Wallet, FETCHAI
from aea.decision_maker.base import OwnershipState, Preferences, DecisionMaker
from aea.decision_maker.messages.state_update import StateUpdateMessage
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.mail.base import OutBox, Multiplexer  # , Envelope
from aea.protocols.default.message import DefaultMessage
from tests.conftest import CUR_PATH, DummyConnection

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
            self.ownership_state.amount_by_currency

        with pytest.raises(AssertionError):
            self.ownership_state.quantities_by_good_pbk

    def test_initialisation(self):
        """Test the initialisation of the ownership_state."""
        currency_endowment = {"FET": 100}
        good_endowment = {"good_pbk": 2}
        self.ownership_state.init(amount_by_currency=currency_endowment, quantities_by_good_pbk=good_endowment)
        assert self.ownership_state.amount_by_currency is not None
        assert self.ownership_state.quantities_by_good_pbk is not None
        assert self.ownership_state.is_initialized

    def test_transaction_is_consistent(self):
        """Test the consistency of the transaction message."""
        currency_endowment = {"FET": 100}
        good_endowment = {"good_pbk": 2}
        self.ownership_state.init(amount_by_currency=currency_endowment, quantities_by_good_pbk=good_endowment)
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
                                        quantities_by_good_pbk={"good_pbk": 10},
                                        ledger_id="fetchai")

        assert self.ownership_state.check_transaction_is_consistent(tx_message=tx_message),\
            "We should have the money for the transaction!"

        tx_message = TransactionMessage(performative=TransactionMessage.Performative.PROPOSE,
                                        skill_id="default",
                                        transaction_id="transaction0",
                                        sender="agent_1",
                                        counterparty="pk",
                                        is_sender_buyer=False,
                                        currency_pbk="FET",
                                        amount=1,
                                        sender_tx_fee=0,
                                        counterparty_tx_fee=0,
                                        quantities_by_good_pbk={"good_pbk": 10},
                                        ledger_id="fetchai")

        assert self.ownership_state.check_transaction_is_consistent(tx_message=tx_message), \
            "We should have the money for the transaction!"

    def test_apply(self):
        """Test the apply function."""
        currency_endowment = {"FET": 100}
        good_endowment = {"good_pbk": 2}
        self.ownership_state.init(amount_by_currency=currency_endowment, quantities_by_good_pbk=good_endowment)
        tx_message = TransactionMessage(performative=TransactionMessage.Performative.PROPOSE,
                                        skill_id="default",
                                        transaction_id="transaction0",
                                        sender="agent_1",
                                        counterparty="pk",
                                        is_sender_buyer=True,
                                        currency_pbk="FET",
                                        amount=20,
                                        sender_tx_fee=5,
                                        counterparty_tx_fee=0,
                                        quantities_by_good_pbk={"good_pbk": 10},
                                        ledger_id="fetchai")
        list_of_transactions = [tx_message]
        state = self.ownership_state
        new_state = self.ownership_state.apply(transactions=list_of_transactions)
        assert state != new_state, "after applying a list_of_transactions must have a different state!"

    def test_transaction_update(self):
        """Test the tranasction update."""
        currency_endowment = {"FET": 100}
        good_endowment = {"good_pbk": 2}

        self.ownership_state.init(amount_by_currency=currency_endowment, quantities_by_good_pbk=good_endowment)
        tx_message = TransactionMessage(performative=TransactionMessage.Performative.PROPOSE,
                                        skill_id="default",
                                        transaction_id="transaction0",
                                        sender="agent_1",
                                        counterparty="pk",
                                        is_sender_buyer=True,
                                        currency_pbk="FET",
                                        amount=20,
                                        sender_tx_fee=5,
                                        counterparty_tx_fee=0,
                                        quantities_by_good_pbk={"good_pbk": 10},
                                        ledger_id="fetchai")
        cur_holdings = self.ownership_state.amount_by_currency['FET']
        self.ownership_state.update(tx_message=tx_message)
        assert self.ownership_state.amount_by_currency['FET'] < cur_holdings

        tx_message = TransactionMessage(performative=TransactionMessage.Performative.PROPOSE,
                                        skill_id="default",
                                        transaction_id="transaction0",
                                        sender="agent_1",
                                        counterparty="pk",
                                        is_sender_buyer=False,
                                        currency_pbk="FET",
                                        amount=20,
                                        sender_tx_fee=5,
                                        counterparty_tx_fee=0,
                                        quantities_by_good_pbk={"good_pbk": 10},
                                        ledger_id="fetchai")
        cur_holdings = self.ownership_state.amount_by_currency['FET']
        self.ownership_state.update(tx_message=tx_message)
        assert self.ownership_state.amount_by_currency['FET'] > cur_holdings

    # # PREFERENCES
    def test_preferences_properties(self):
        """Test the properties of the preferences class."""
        with pytest.raises(AssertionError):
            self.preferences.exchange_params_by_currency
        with pytest.raises(AssertionError):
            self.preferences.utility_params_by_good_pbk

    def test_preferences_init(self):
        """Test the preferences init()."""
        utility_params = {"good_pbk": 20.0}
        exchange_params = {"FET": 10.0}
        tx_fee = 9
        self.preferences.init(exchange_params_by_currency=exchange_params, utility_params_by_good_pbk=utility_params, tx_fee=tx_fee)
        assert self.preferences.utility_params_by_good_pbk is not None
        assert self.preferences.exchange_params_by_currency is not None
        assert self.preferences.transaction_fees['seller_tx_fee'] == 4
        assert self.preferences.transaction_fees['buyer_tx_fee'] == 5
        assert self.preferences.is_initialized

    def test_utilities(self):
        """Test the utilities."""
        good_holdings = {"good_pbk": 2}
        currency_holdings = {"FET": 100}
        utility_params = {"good_pbk": 20.0}
        exchange_params = {"FET": 10.0}
        tx_fee = 9
        self.preferences.init(utility_params_by_good_pbk=utility_params, exchange_params_by_currency=exchange_params, tx_fee=tx_fee)
        log_utility = self.preferences.logarithmic_utility(quantities_by_good_pbk=good_holdings)
        assert log_utility is not None

        linear_utility = self.preferences.linear_utility(amount_by_currency=currency_holdings)
        assert linear_utility is not None

        score = self.preferences.get_score(quantities_by_good_pbk=good_holdings, amount_by_currency=currency_holdings)
        assert score == log_utility + linear_utility

        delta_good_holdings = {"good_pbk": 1}
        delta_currency_holdings = {"FET": -5}
        self.ownership_state.init(amount_by_currency=currency_holdings, quantities_by_good_pbk=good_holdings)
        marginal_utility = self.preferences.marginal_utility(ownership_state=self.ownership_state, delta_good_holdings=delta_good_holdings, delta_currency_holdings=delta_currency_holdings)
        assert marginal_utility is not None

    def test_score_diff_from_transaction(self):
        """Test the difference between the scores."""
        good_holdings = {"good_pbk": 2}
        currency_holdings = {"FET": 100}
        utility_params = {"good_pbk": 20.0}
        exchange_params = {"FET": 10.0}
        tx_fee = 3
        self.ownership_state.init(amount_by_currency=currency_holdings, quantities_by_good_pbk=good_holdings)
        self.preferences.init(utility_params_by_good_pbk=utility_params, exchange_params_by_currency=exchange_params, tx_fee=tx_fee)
        tx_message = TransactionMessage(performative=TransactionMessage.Performative.PROPOSE,
                                        skill_id="default",
                                        transaction_id="transaction0",
                                        sender="agent_1",
                                        counterparty="pk",
                                        is_sender_buyer=False,
                                        currency_pbk="FET",
                                        amount=20,
                                        sender_tx_fee=self.preferences.transaction_fees['seller_tx_fee'],
                                        counterparty_tx_fee=self.preferences.transaction_fees['buyer_tx_fee'],
                                        quantities_by_good_pbk={"good_pbk": 10},
                                        ledger_id="fetchai")

        cur_score = self.preferences.get_score(quantities_by_good_pbk=good_holdings, amount_by_currency=currency_holdings)
        new_state = self.ownership_state.apply([tx_message])
        new_score = self.preferences.get_score(quantities_by_good_pbk=new_state.quantities_by_good_pbk, amount_by_currency=new_state.amount_by_currency)
        dif_scores = new_score - cur_score
        score_difference = self.preferences.get_score_diff_from_transaction(ownership_state=self.ownership_state, tx_message=tx_message)
        assert score_difference == dif_scores

    @classmethod
    def teardown_class(cls):
        """Teardown any state that was previously setup with a call to setup_class."""


class TestDecisionMaker:
    """Test the decision maker."""

    @classmethod
    def _patch_logger(cls):
        cls.patch_logger_warning = mock.patch.object(aea.decision_maker.base.logger, 'warning')
        cls.mocked_logger_warning = cls.patch_logger_warning.__enter__()

    @classmethod
    def _unpatch_logger(cls):
        cls.mocked_logger_warning.__exit__()

    @classmethod
    def setup_class(cls):
        """Initialise the decision maker."""
        cls._patch_logger()
        cls.multiplexer = Multiplexer([DummyConnection()])
        cls.outbox = OutBox(cls.multiplexer)
        private_key_pem_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
        cls.wallet = Wallet({FETCHAI: private_key_pem_path})
        cls.ledger_apis = LedgerApis({FETCHAI: DEFAULT_FETCHAI_CONFIG})
        cls.agent_name = "test"
        cls.ownership_state = OwnershipState()
        cls.preferences = Preferences()
        cls.decision_maker = DecisionMaker(agent_name=cls.agent_name, max_reactions=MAX_REACTIONS, outbox=cls.outbox,
                                           wallet=cls.wallet, ledger_apis=cls.ledger_apis)
        cls.multiplexer.connect()

    def test_properties(self):
        """Test the properties of the decision maker."""
        assert self.decision_maker.outbox.empty()
        assert isinstance(self.decision_maker.message_in_queue, Queue)
        assert isinstance(self.decision_maker.message_out_queue, Queue)
        assert isinstance(self.decision_maker.ledger_apis, LedgerApis)
        assert isinstance(self.outbox, OutBox)

    def test_decision_maker_execute(self):
        """Test the execute method."""
        tx_message = TransactionMessage(performative=TransactionMessage.Performative.PROPOSE,
                                        skill_id="default",
                                        transaction_id="transaction0",
                                        sender="agent_1",
                                        counterparty="pk",
                                        is_sender_buyer=True,
                                        currency_pbk="FET",
                                        amount=2,
                                        sender_tx_fee=0,
                                        counterparty_tx_fee=0,
                                        quantities_by_good_pbk={"good_pbk": 10},
                                        ledger_id="fetchai")

        self.decision_maker.message_in_queue.put_nowait(tx_message)
        with mock.patch.object(self.decision_maker, 'handle'):
            self.decision_maker.execute()
        assert self.decision_maker.message_in_queue.empty()

    def test_decision_maker_handle_state_update(self):
        """Test the execute method."""
        good_holdings = {"good_pbk": 2}
        currency_holdings = {"FET": 100}
        utility_params = {"good_pbk": 20.0}
        exchange_params = {"FET": 10.0}
        tx_fee = 1
        state_update_message = StateUpdateMessage(performative=StateUpdateMessage.Performative.INITIALIZE,
                                                  amount_by_currency=currency_holdings,
                                                  quantities_by_good_pbk=good_holdings,
                                                  exchange_params_by_currency=exchange_params,
                                                  utility_params_by_good_pbk=utility_params,
                                                  tx_fee=tx_fee)
        self.decision_maker.handle(state_update_message)
        assert self.decision_maker.ownership_state.amount_by_currency is not None
        assert self.decision_maker.ownership_state.quantities_by_good_pbk is not None
        assert self.decision_maker.preferences.exchange_params_by_currency is not None
        assert self.decision_maker.preferences.utility_params_by_good_pbk is not None

        currency_deltas = {"FET": -10}
        good_deltas = {"good_pbk": 1}
        state_update_message = StateUpdateMessage(performative=StateUpdateMessage.Performative.APPLY,
                                                  amount_by_currency=currency_deltas,
                                                  quantities_by_good_pbk=good_deltas)
        self.decision_maker.handle(state_update_message)
        expected_amount_by_currency = {key: currency_holdings.get(key, 0) + currency_deltas.get(key, 0) for key in set(currency_holdings) | set(currency_deltas)}
        expected_quantities_by_good_pbk = {key: good_holdings.get(key, 0) + good_deltas.get(key, 0) for key in set(good_holdings) | set(good_deltas)}
        assert self.decision_maker.ownership_state.amount_by_currency == expected_amount_by_currency
        assert self.decision_maker.ownership_state.quantities_by_good_pbk == expected_quantities_by_good_pbk

    def test_decision_maker_handle_tx_message(self):
        """Test the handle tx meessa method."""
        tx_message = TransactionMessage(performative=TransactionMessage.Performative.PROPOSE,
                                        skill_id="default",
                                        transaction_id="transaction0",
                                        sender="agent_1",
                                        counterparty="pk",
                                        is_sender_buyer=True,
                                        currency_pbk="FET",
                                        amount=2,
                                        sender_tx_fee=0,
                                        counterparty_tx_fee=0,
                                        quantities_by_good_pbk={"good_pbk": 10},
                                        ledger_id="fetchai")

        with mock.patch.object(self.decision_maker.ledger_apis, "token_balance", return_value=1000000):
            with mock.patch.object(self.decision_maker.ledger_apis, "transfer", return_value="This is a test digest"):
                self.decision_maker.handle(tx_message)
                assert not self.decision_maker.message_out_queue.empty()

        with mock.patch.object(self.decision_maker.ledger_apis, "token_balance", return_value=1000000):
            with mock.patch.object(self.decision_maker.ledger_apis, "transfer", return_value="This is a test digest"):
                with mock.patch("aea.decision_maker.base.GoalPursuitReadiness.Status") as mocked_status:
                    mocked_status.READY.value = False
                    self.decision_maker.handle(tx_message)
                    assert not self.decision_maker.goal_pursuit_readiness.is_ready

        tx_message = TransactionMessage(performative=TransactionMessage.Performative.PROPOSE,
                                        skill_id="default",
                                        transaction_id="transaction0",
                                        sender="agent_1",
                                        counterparty="pk",
                                        is_sender_buyer=True,
                                        currency_pbk="FET",
                                        amount=2,
                                        sender_tx_fee=0,
                                        counterparty_tx_fee=0,
                                        quantities_by_good_pbk={"good_pbk": 10})
        self.decision_maker.handle(tx_message)
        assert not self.decision_maker.message_out_queue.empty()

        with mock.patch.object(self.decision_maker, '_is_acceptable_tx', return_value=True):
            self.decision_maker.handle(tx_message)
            assert not self.decision_maker.message_out_queue.empty()

        with mock.patch.object(self.decision_maker, '_is_acceptable_tx', return_value=True):
            with mock.patch.object(self.decision_maker, '_settle_tx', return_value=None):
                self.decision_maker.handle(tx_message)
                assert not self.decision_maker.message_out_queue.empty()

    def test_decision_maker_execute_w_wrong_input(self):
        """Test the execute method with wrong input."""
        default_message = DefaultMessage(type=DefaultMessage.Type.BYTES,
                                         content=b'hello')

        self.decision_maker.message_in_queue.put_nowait(default_message)
        self.decision_maker.execute()

        self.mocked_logger_warning.assert_called_with("[{}]: Message received by the decision maker is not of protocol_id=internal.".format(self.agent_name))

    @classmethod
    def teardown_class(cls):
        """Tear the tests down."""
        cls._unpatch_logger()
        cls.multiplexer.disconnect()
