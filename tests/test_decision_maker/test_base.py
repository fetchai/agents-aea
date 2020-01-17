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
import os
from queue import Queue
from unittest import mock

import pytest

import aea
import aea.decision_maker.base
from aea.crypto.ethereum import ETHEREUM
from aea.decision_maker.base import LedgerStateProxy
from aea.crypto.fetchai import DEFAULT_FETCHAI_CONFIG
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import FETCHAI, Wallet
from aea.decision_maker.base import DecisionMaker, OwnershipState, Preferences
from aea.decision_maker.messages.base import InternalMessage
from aea.decision_maker.messages.state_update import StateUpdateMessage
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.mail.base import Multiplexer, OutBox
from aea.protocols.default.message import DefaultMessage

from ..conftest import CUR_PATH, DummyConnection
from web3.auto import Web3

MAX_REACTIONS = 10


class TestOwnershipState:
    """Test the base.py for DecisionMaker."""

    @classmethod
    def setup_class(cls):
        """Initialise the class."""
        cls.ownership_state = OwnershipState()

    def test_properties(self):
        """Test the assertion error for *_holdings."""
        with pytest.raises(AssertionError):
            self.ownership_state.amount_by_currency_id

        with pytest.raises(AssertionError):
            self.ownership_state.quantities_by_good_id

    def test_initialisation(self):
        """Test the initialisation of the ownership_state."""
        currency_endowment = {"FET": 100}
        good_endowment = {"good_id": 2}
        self.ownership_state.init(
            amount_by_currency_id=currency_endowment,
            quantities_by_good_id=good_endowment,
        )
        assert self.ownership_state.amount_by_currency_id is not None
        assert self.ownership_state.quantities_by_good_id is not None
        assert self.ownership_state.is_initialized

    def test_body(self):
        """Test the setter for the body."""
        msg = InternalMessage()
        msg.body = {"test_key": "test_value"}

        other_msg = InternalMessage(body={"test_key": "test_value"})
        assert msg == other_msg, "Messages should be equal."
        assert msg.check_consistency(), "It is true."
        assert str(msg) == "InternalMessage(test_key=test_value)"
        assert msg._body is not None
        msg.body = {"Test": "My_test"}
        assert msg._body == {
            "Test": "My_test"
        }, "Message body must be equal with the above dictionary."
        msg.set("Test", 2)
        assert msg._body["Test"] == 2, "body['Test'] should be equal to 2."
        msg.unset("Test")
        assert "Test" not in msg._body.keys(), "Test should not exist."

    def test_transaction_is_affordable_agent_is_buyer(self):
        """Check if the agent has the money to cover the sender_amount (the agent=sender is the buyer)."""
        currency_endowment = {"FET": 100}
        good_endowment = {"good_id": 20}
        self.ownership_state.init(
            amount_by_currency_id=currency_endowment,
            quantities_by_good_id=good_endowment,
        )
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=["default"],
            tx_id="transaction0",
            tx_sender_addr="agent_1",
            tx_counterparty_addr="pk",
            tx_amount_by_currency_id={"FET": -1},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 10},
            info={"some_info_key": "some_info_value"},
            ledger_id="fetchai",
        )

        assert self.ownership_state.check_transaction_is_affordable(
            tx_message=tx_message
        ), "We should have the money for the transaction!"


    def test_transaction_is_affordable_there_is_no_wealth(self):
        """Reject the transaction when there is no wealth exchange."""
        currency_endowment = {"FET": 0}
        good_endowment = {"good_id": 0}
        self.ownership_state.init(
            amount_by_currency_id=currency_endowment,
            quantities_by_good_id=good_endowment,
        )
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=["default"],
            tx_id="transaction0",
            tx_sender_addr="agent_1",
            tx_counterparty_addr="pk",
            tx_amount_by_currency_id={"FET": 0},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 0},
            info={"some_info_key": "some_info_value"},
            ledger_id="fetchai",
        )

        assert not self.ownership_state.check_transaction_is_affordable(
            tx_message=tx_message
        ), "We must reject the transaction."

    def tests_transaction_is_affordable_agent_is_the_seller(self):
        """Check if the agent has the goods (the agent=sender is the seller)."""
        currency_endowment = {"FET": 0}
        good_endowment = {"good_id": 0}
        self.ownership_state.init(
            amount_by_currency_id=currency_endowment,
            quantities_by_good_id=good_endowment,
        )
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=["default"],
            tx_id="transaction0",
            tx_sender_addr="agent_1",
            tx_counterparty_addr="pk",
            tx_amount_by_currency_id={"FET": 10},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 0},
            info={"some_info_key": "some_info_value"},
            ledger_id="fetchai",
        )

        assert self.ownership_state.check_transaction_is_affordable(
            tx_message=tx_message
        ), "We must reject the transaction."

    def tests_transaction_is_affordable_else_statement(self):
        """Check that the function returns false if we cannot satisfy any if/elif statements."""
        currency_endowment = {"FET": 0}
        good_endowment = {"good_id": 0}
        self.ownership_state.init(
            amount_by_currency_id=currency_endowment,
            quantities_by_good_id=good_endowment,
        )
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=["default"],
            tx_id="transaction0",
            tx_sender_addr="agent_1",
            tx_counterparty_addr="pk",
            tx_amount_by_currency_id={"FET": 10},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 50},
            info={"some_info_key": "some_info_value"},
            ledger_id="fetchai",
        )

        assert not self.ownership_state.check_transaction_is_affordable(
            tx_message=tx_message
        ), "We must reject the transaction."

    def test_apply(self):
        """Test the apply function."""
        currency_endowment = {"FET": 100}
        good_endowment = {"good_id": 2}
        self.ownership_state.init(
            amount_by_currency_id=currency_endowment,
            quantities_by_good_id=good_endowment,
        )
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=["default"],
            tx_id="transaction0",
            tx_sender_addr="agent_1",
            tx_counterparty_addr="pk",
            tx_amount_by_currency_id={"FET": -20},
            tx_sender_fee=5,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 10},
            info={"some_info_key": "some_info_value"},
            ledger_id="fetchai",
        )
        list_of_transactions = [tx_message]
        state = self.ownership_state
        new_state = self.ownership_state.apply_transactions(
            transactions=list_of_transactions
        )
        assert (
            state != new_state
        ), "after applying a list_of_transactions must have a different state!"


    def test_transaction_update(self):
        """Test the transaction update when sending tokens."""
        currency_endowment = {"FET": 100}
        good_endowment = {"good_id": 20}

        self.ownership_state.init(
            amount_by_currency_id=currency_endowment,
            quantities_by_good_id=good_endowment,
        )
        assert self.ownership_state.amount_by_currency_id == currency_endowment
        assert self.ownership_state.quantities_by_good_id == good_endowment
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=["default"],
            tx_id="transaction0",
            tx_sender_addr="agent_1",
            tx_counterparty_addr="pk",
            tx_amount_by_currency_id={"FET": -20},
            tx_sender_fee=5,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 10},
            info={"some_info_key": "some_info_value"},
            ledger_id="fetchai",
        )
        self.ownership_state._update(tx_message=tx_message)
        expected_amount_by_currency_id = {"FET": 75}
        expected_quantities_by_good_id = {"good_id": 30}
        assert (
            self.ownership_state.amount_by_currency_id == expected_amount_by_currency_id
        )
        assert (
            self.ownership_state.quantities_by_good_id == expected_quantities_by_good_id
        )

    def test_transaction_update_receive(self):
        """Test the transaction update when receiving tokens."""
        currency_endowment = {"FET": 75}
        good_endowment = {"good_id": 30}
        self.ownership_state.init(
            amount_by_currency_id=currency_endowment,
            quantities_by_good_id=good_endowment,
        )
        assert self.ownership_state.amount_by_currency_id == currency_endowment
        assert self.ownership_state.quantities_by_good_id == good_endowment
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=["default"],
            tx_id="transaction0",
            tx_sender_addr="agent_1",
            tx_counterparty_addr="pk",
            tx_amount_by_currency_id={"FET": 20},
            tx_sender_fee=5,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": -10},
            info={"some_info_key": "some_info_value"},
            ledger_id="fetchai",
        )
        self.ownership_state._update(tx_message=tx_message)
        expected_amount_by_currency_id = {"FET": 90}
        expected_quantities_by_good_id = {"good_id": 20}
        assert (
            self.ownership_state.amount_by_currency_id == expected_amount_by_currency_id
        )
        assert (
            self.ownership_state.quantities_by_good_id == expected_quantities_by_good_id
        )

class Test_Preferences_Decision_maker:
    """Test the preferences."""

    @classmethod
    def setup_class(cls):
        """Initialise the class."""
        cls.preferences = Preferences()
        cls.ownership_state = OwnershipState()
        cls.good_holdings = {"good_id": 2}
        cls.currency_holdings = {"FET": 100}
        cls.utility_params = {"good_id": 20.0}
        cls.exchange_params = {"FET": 10.0}
        cls.tx_fee = 9

    def test_preferences_properties(self):
        """Test the properties of the preferences class."""
        with pytest.raises(AssertionError):
            self.preferences.exchange_params_by_currency_id
        with pytest.raises(AssertionError):
            self.preferences.utility_params_by_good_id

    def test_preferences_init(self):
        """Test the preferences init()."""
        self.preferences.init(
            exchange_params_by_currency_id=self.exchange_params,
            utility_params_by_good_id=self.utility_params,
            tx_fee=self.tx_fee,
        )
        assert self.preferences.utility_params_by_good_id is not None
        assert self.preferences.exchange_params_by_currency_id is not None
        assert self.preferences.transaction_fees["seller_tx_fee"] == 4
        assert self.preferences.transaction_fees["buyer_tx_fee"] == 5
        assert self.preferences.is_initialized

    def test_logarithmic_utility(self):
        """Calculate the logarithmic utility and checks that it is not none.."""
        self.preferences.init(
            utility_params_by_good_id=self.utility_params,
            exchange_params_by_currency_id=self.exchange_params,
            tx_fee=self.tx_fee,
        )
        log_utility = self.preferences.logarithmic_utility(
            quantities_by_good_id=self.good_holdings
        )
        assert log_utility is not None, "Log_utility must not be none."

    def test_linear_utility(self):
        """Calculate the linear_utility and checks that it is not none."""
        linear_utility = self.preferences.linear_utility(
            amount_by_currency_id=self.currency_holdings
        )
        assert linear_utility is not None, "Linear utility must not be none."

    def test_get_score(self):
        """Calculate the score."""
        score = self.preferences.get_score(
            quantities_by_good_id=self.good_holdings,
            amount_by_currency_id=self.currency_holdings,
        )
        linear_utility = self.preferences.linear_utility(
            amount_by_currency_id=self.currency_holdings
        )
        log_utility = self.preferences.logarithmic_utility(
            quantities_by_good_id=self.good_holdings
        )
        assert (
            score == log_utility + linear_utility
        ), "The score must be equal to the sum of log_utility and linear_utility."

    def test_marginal_utility(self):
        """Test the marginal utility."""
        delta_good_holdings = {"good_id": 1}
        delta_currency_holdings = {"FET": -5}
        self.ownership_state.init(
            amount_by_currency_id=self.currency_holdings,
            quantities_by_good_id=self.good_holdings,
        )
        marginal_utility = self.preferences.marginal_utility(
            ownership_state=self.ownership_state,
            delta_quantities_by_good_id=delta_good_holdings,
            delta_amount_by_currency_id=delta_currency_holdings,
        )
        assert marginal_utility is not None, "Marginal utility must not be none."


    def test_score_diff_from_transaction(self):
        """Test the difference between the scores."""
        good_holdings = {"good_id": 2}
        currency_holdings = {"FET": 100}
        utility_params = {"good_id": 20.0}
        exchange_params = {"FET": 10.0}
        tx_fee = 3
        self.ownership_state.init(
            amount_by_currency_id=currency_holdings, quantities_by_good_id=good_holdings
        )
        self.preferences.init(
            utility_params_by_good_id=utility_params,
            exchange_params_by_currency_id=exchange_params,
            tx_fee=tx_fee,
        )
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=["default"],
            tx_id="transaction0",
            tx_sender_addr="agent_1",
            tx_counterparty_addr="pk",
            tx_amount_by_currency_id={"FET": -20},
            tx_sender_fee=self.preferences.transaction_fees["seller_tx_fee"],
            tx_counterparty_fee=self.preferences.transaction_fees["buyer_tx_fee"],
            tx_quantities_by_good_id={"good_id": 10},
            info={"some_info_key": "some_info_value"},
            ledger_id="fetchai",
        )

        cur_score = self.preferences.get_score(
            quantities_by_good_id=good_holdings, amount_by_currency_id=currency_holdings
        )
        new_state = self.ownership_state.apply_transactions([tx_message])
        new_score = self.preferences.get_score(
            quantities_by_good_id=new_state.quantities_by_good_id,
            amount_by_currency_id=new_state.amount_by_currency_id,
        )
        dif_scores = new_score - cur_score
        score_difference = self.preferences.get_score_diff_from_transaction(
            ownership_state=self.ownership_state, tx_message=tx_message
        )
        assert (
            score_difference == dif_scores
        ), "The calculated difference must be equal to the return difference from the function."

    @classmethod
    def teardown_class(cls):
        """Teardown any state that was previously setup with a call to setup_class."""


class TestDecisionMaker:
    """Test the decision maker."""

    @classmethod
    def _patch_logger(cls):
        cls.patch_logger_warning = mock.patch.object(
            aea.decision_maker.base.logger, "warning"
        )
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
        eth_private_key_pem_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
        cls.wallet = Wallet(
            {FETCHAI: private_key_pem_path, ETHEREUM: eth_private_key_pem_path}
        )
        cls.ledger_apis = LedgerApis({FETCHAI: DEFAULT_FETCHAI_CONFIG}, FETCHAI)
        cls.agent_name = "test"
        cls.ownership_state = OwnershipState()
        cls.preferences = Preferences()
        cls.decision_maker = DecisionMaker(
            agent_name=cls.agent_name,
            max_reactions=MAX_REACTIONS,
            outbox=cls.outbox,
            wallet=cls.wallet,
            ledger_apis=cls.ledger_apis,
        )
        cls.multiplexer.connect()

        cls.tx_id = "transaction0"
        cls.tx_sender_addr = "agent_1"
        cls.tx_counterparty_addr = "pk"
        cls.info = {"some_info_key": "some_info_value"}
        cls.ledger_id = "fetchai"

    def test_properties(self):
        """Test the properties of the decision maker."""
        assert self.decision_maker.outbox.empty()
        assert isinstance(self.decision_maker.message_in_queue, Queue)
        assert isinstance(self.decision_maker.message_out_queue, Queue)
        assert isinstance(self.decision_maker.ledger_apis, LedgerApis)
        assert isinstance(self.outbox, OutBox)

    def test_decision_maker_execute(self):
        """Test the execute method."""
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=["default"],
            tx_id=self.tx_id,
            tx_sender_addr=self.tx_sender_addr,
            tx_counterparty_addr=self.tx_counterparty_addr,
            tx_amount_by_currency_id={"FET": -20},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 10},
            info=self.info,
            ledger_id=self.ledger_id,
        )

        self.decision_maker.message_in_queue.put_nowait(tx_message)
        with mock.patch.object(self.decision_maker, "handle"):
            self.decision_maker.execute()
        assert self.decision_maker.message_in_queue.empty()

    def test_decision_maker_handle_state_update_initialize(self):
        """Test the handle method for a stateUpdate message with Initialize performative."""
        good_holdings = {"good_id": 2}
        currency_holdings = {"FET": 100}
        utility_params = {"good_id": 20.0}
        exchange_params = {"FET": 10.0}
        tx_fee = 1
        state_update_message = StateUpdateMessage(
            performative=StateUpdateMessage.Performative.INITIALIZE,
            amount_by_currency_id=currency_holdings,
            quantities_by_good_id=good_holdings,
            exchange_params_by_currency_id=exchange_params,
            utility_params_by_good_id=utility_params,
            tx_fee=tx_fee,
        )
        self.decision_maker.handle(state_update_message)
        assert self.decision_maker.ownership_state.amount_by_currency_id is not None
        assert self.decision_maker.ownership_state.quantities_by_good_id is not None
        assert (
            self.decision_maker.preferences.exchange_params_by_currency_id is not None
        )
        assert self.decision_maker.preferences.utility_params_by_good_id is not None

    def test_decision_maker_handle_update_apply(self):
        """Test the handle method for a stateUpdate message with APPLY performative."""
        good_holdings = {"good_id": 2}
        currency_holdings = {"FET": 100}
        currency_deltas = {"FET": -10}
        good_deltas = {"good_id": 1}
        state_update_message = StateUpdateMessage(
            performative=StateUpdateMessage.Performative.APPLY,
            amount_by_currency_id=currency_deltas,
            quantities_by_good_id=good_deltas,
        )
        self.decision_maker.handle(state_update_message)
        expected_amount_by_currency_id = {
            key: currency_holdings.get(key, 0) + currency_deltas.get(key, 0)
            for key in set(currency_holdings) | set(currency_deltas)
        }
        expected_quantities_by_good_id = {
            key: good_holdings.get(key, 0) + good_deltas.get(key, 0)
            for key in set(good_holdings) | set(good_deltas)
        }
        assert (
            self.decision_maker.ownership_state.amount_by_currency_id
            == expected_amount_by_currency_id
        ), "The amount_by_currency_id must be equal with the expected amount."
        assert (
            self.decision_maker.ownership_state.quantities_by_good_id
            == expected_quantities_by_good_id
        )

    def test_decision_maker_handle_tx_message(self):
        """Test the handle tx message method."""
        assert self.decision_maker.message_out_queue.empty()

        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=["default"],
            tx_id=self.tx_id,
            tx_sender_addr=self.tx_sender_addr,
            tx_counterparty_addr=self.tx_counterparty_addr,
            tx_amount_by_currency_id={"FET": -2},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 10},
            info=self.info,
            ledger_id=self.ledger_id,
        )

        with mock.patch.object(
            self.decision_maker.ledger_apis, "token_balance", return_value=1000000
        ):
            with mock.patch.object(
                self.decision_maker.ledger_apis,
                "transfer",
                return_value="This is a test digest",
            ):
                self.decision_maker.handle(tx_message)
                assert not self.decision_maker.message_out_queue.empty()

    def test_decision_maker_handle_unknown_tx_message(self):
        """Test the handle tx message method."""
        patch_logger_error = mock.patch.object(aea.decision_maker.base.logger, "error")
        mocked_logger_error = patch_logger_error.__enter__()

        with mock.patch(
            "aea.decision_maker.messages.transaction.TransactionMessage.check_consistency",
            return_value=True,
        ):
            tx_message = TransactionMessage(
                performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
                skill_callback_ids=["default"],
                tx_id=self.tx_id,
                tx_sender_addr=self.tx_sender_addr,
                tx_counterparty_addr=self.tx_counterparty_addr,
                tx_amount_by_currency_id={"FET": -2},
                tx_sender_fee=0,
                tx_counterparty_fee=0,
                tx_quantities_by_good_id={"good_id": 10},
                info=self.info,
                ledger_id="bitcoin",
            )
            self.decision_maker.handle(tx_message)
        mocked_logger_error.assert_called_with(
            "[test]: ledger_id=bitcoin is not supported"
        )

    def test_decision_maker_handle_tx_message_not_ready(self):
        """Test that the decision maker is not ready to pursuit the goals.Cannot handle the message."""
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=["default"],
            tx_id=self.tx_id,
            tx_sender_addr=self.tx_sender_addr,
            tx_counterparty_addr=self.tx_counterparty_addr,
            tx_amount_by_currency_id={"FET": -2},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 10},
            info=self.info,
            ledger_id=self.ledger_id,
        )

        with mock.patch.object(
            self.decision_maker.ledger_apis, "token_balance", return_value=1000000
        ):
            with mock.patch.object(
                self.decision_maker.ledger_apis,
                "transfer",
                return_value="This is a test digest",
            ):
                with mock.patch(
                    "aea.decision_maker.base.GoalPursuitReadiness.Status"
                ) as mocked_status:
                    mocked_status.READY.value = False
                    self.decision_maker.handle(tx_message)
                    assert not self.decision_maker.goal_pursuit_readiness.is_ready

        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=["default"],
            tx_id=self.tx_id,
            tx_sender_addr=self.tx_sender_addr,
            tx_counterparty_addr=self.tx_counterparty_addr,
            tx_amount_by_currency_id={"FET": -2},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 10},
            info=self.info,
            ledger_id=self.ledger_id,
        )
        self.decision_maker.handle(tx_message)
        assert not self.decision_maker.message_out_queue.empty()

    def test_decision_maker_hand_tx_ready_for_signing(self):
        """Test that the decision maker can handle a message that is ready for signing."""
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SIGNING,
            skill_callback_ids=["default"],
            tx_id=self.tx_id,
            tx_sender_addr=self.tx_sender_addr,
            tx_counterparty_addr=self.tx_counterparty_addr,
            tx_amount_by_currency_id={"FET": -20},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 0},
            ledger_id=self.ledger_id,
            info=self.info,
            signing_payload={"key": b"some_bytes"},
        )
        self.decision_maker.handle(tx_message)
        assert not self.decision_maker.message_out_queue.empty()

    def test_decision_maker_handle_tx_message_acceptable_for_settlement(self):
        """Test that a tx_message is acceptable for settlement."""
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=["default"],
            tx_id=self.tx_id,
            tx_sender_addr=self.tx_sender_addr,
            tx_counterparty_addr=self.tx_counterparty_addr,
            tx_amount_by_currency_id={"FET": -2},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 10},
            info=self.info,
            ledger_id=self.ledger_id,
        )
        with mock.patch.object(
            self.decision_maker, "_is_acceptable_for_settlement", return_value=True
        ):
            with mock.patch.object(
                self.decision_maker, "_settle_tx", return_value="tx_digest"
            ):
                self.decision_maker.handle(tx_message)
                assert not self.decision_maker.message_out_queue.empty()

    def test_decision_maker_tx_message_is_not_acceptable_for_settlement(self):
        """Test that a tx_message is not acceptable for settlement."""
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=["default"],
            tx_id=self.tx_id,
            tx_sender_addr=self.tx_sender_addr,
            tx_counterparty_addr=self.tx_counterparty_addr,
            tx_amount_by_currency_id={"FET": -2},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 10},
            info=self.info,
            ledger_id=self.ledger_id,
        )

        with mock.patch.object(
            self.decision_maker, "_is_acceptable_for_settlement", return_value=True
        ):
            with mock.patch.object(
                self.decision_maker, "_settle_tx", return_value=None
            ):
                self.decision_maker.handle(tx_message)
                assert not self.decision_maker.message_out_queue.empty()

    def test_decision_maker_execute_w_wrong_input(self):
        """Test the execute method with wrong input."""
        default_message = DefaultMessage(
            type=DefaultMessage.Type.BYTES, content=b"hello"
        )

        self.decision_maker.message_in_queue.put_nowait(default_message)
        self.decision_maker.execute()

        self.mocked_logger_warning.assert_called_with(
            "[{}]: Message received by the decision maker is not of protocol_id=internal.".format(
                self.agent_name
            )
        )

    def test_is_affordable_off_chain(self):
        """Test the off_chain message."""
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=["default"],
            tx_id=self.tx_id,
            tx_sender_addr=self.tx_sender_addr,
            tx_counterparty_addr=self.tx_counterparty_addr,
            tx_amount_by_currency_id={"FET": -20},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 10},
            ledger_id="off_chain",
            info=self.info,
        )

        assert self.decision_maker._is_affordable(tx_message)

    def test_is_not_affordable_ledger_state_proxy(self):
        """Test that the tx_message is not affordable with initialized ledger_state_proxy."""
        with mock.patch(
            "aea.decision_maker.messages.transaction.TransactionMessage.check_consistency",
            return_value=True,
        ):
            tx_message = TransactionMessage(
                performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
                skill_callback_ids=["default"],
                tx_id=self.tx_id,
                tx_sender_addr=self.tx_sender_addr,
                tx_counterparty_addr=self.tx_counterparty_addr,
                tx_amount_by_currency_id={"FET": -20},
                tx_sender_fee=0,
                tx_counterparty_fee=0,
                tx_quantities_by_good_id={"good_id": 10},
                ledger_id="bitcoin",
                info=self.info,
            )
            var = self.decision_maker._is_affordable(tx_message)
            assert not var

    def test_is_affordable_ledger_state_proxy(self):
        """Test that the tx_message is affordable with initialized ledger_state_proxy."""
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=["default"],
            tx_id=self.tx_id,
            tx_sender_addr=self.tx_sender_addr,
            tx_counterparty_addr=self.tx_counterparty_addr,
            tx_amount_by_currency_id={"FET": -20},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 10},
            ledger_id=self.ledger_id,
            info=self.info,
        )

        with mock.patch.object(
            self.decision_maker, "_is_acceptable_for_settlement", return_value=True
        ):
            with mock.patch.object(
                self.decision_maker, "_settle_tx", return_value="tx_digest"
            ):
                self.decision_maker._is_affordable(tx_message)
                assert not self.decision_maker.message_out_queue.empty()

    def test_settle_tx_off_chain(self):
        """Test the off_chain message."""
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=["default"],
            tx_id=self.tx_id,
            tx_sender_addr=self.tx_sender_addr,
            tx_counterparty_addr=self.tx_counterparty_addr,
            tx_amount_by_currency_id={"FET": -20},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 10},
            ledger_id="off_chain",
            info=self.info,
        )

        tx_digest = self.decision_maker._settle_tx(tx_message)
        assert tx_digest == "off_chain_settlement"

    def test_settle_tx_known_chain(self):
        """Test the off_chain message."""
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=["default"],
            tx_id=self.tx_id,
            tx_sender_addr=self.tx_sender_addr,
            tx_counterparty_addr=self.tx_counterparty_addr,
            tx_amount_by_currency_id={"FET": -20},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 10},
            ledger_id=self.ledger_id,
            info=self.info,
        )

        with mock.patch.object(
            self.decision_maker.ledger_apis, "transfer", return_value="tx_digest"
        ):
            tx_digest = self.decision_maker._settle_tx(tx_message)
        assert tx_digest == "tx_digest"

    def test_is_utility_enhancing(self):
        """Test the utility enhancing for off_chain message."""
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=["default"],
            tx_id=self.tx_id,
            tx_sender_addr=self.tx_sender_addr,
            tx_counterparty_addr=self.tx_counterparty_addr,
            tx_amount_by_currency_id={"FET": -20},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 10},
            ledger_id="off_chain",
            info=self.info,
        )
        self.decision_maker.ownership_state._quantities_by_good_id = None
        assert self.decision_maker._is_utility_enhancing(tx_message)

    def test_sign_tx_fetchai(self):
        """Test the private function sign_tx of the decision maker for fetchai ledger_id."""
        tx_hash = Web3.keccak(text="some_bytes")

        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SIGNING,
            skill_callback_ids=["default"],
            tx_id=self.tx_id,
            tx_sender_addr=self.tx_sender_addr,
            tx_counterparty_addr=self.tx_counterparty_addr,
            tx_amount_by_currency_id={"FET": -20},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 0},
            ledger_id=self.ledger_id,
            info=self.info,
            signing_payload={"tx_hash": tx_hash},
        )

        tx_signature = self.decision_maker._sign_tx(tx_message)
        assert tx_signature is not None

    def test_sign_tx_fetchai_is_acceptable_for_signing(self):
        """Test the private function sign_tx of the decision maker for fetchai ledger_id."""
        tx_hash = Web3.keccak(text="some_bytes")

        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SIGNING,
            skill_callback_ids=["default"],
            tx_id=self.tx_id,
            tx_sender_addr=self.tx_sender_addr,
            tx_counterparty_addr=self.tx_counterparty_addr,
            tx_amount_by_currency_id={"FET": -20},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 0},
            ledger_id=self.ledger_id,
            info=self.info,
            signing_payload={"tx_hash": tx_hash},
        )

        tx_signature = self.decision_maker._sign_tx(tx_message)
        assert tx_signature is not None

    def test_sing_tx_offchain(self):
        """Test the private function sign_tx for the offchain ledger_id."""
        tx_hash = Web3.keccak(text="some_bytes")
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SIGNING,
            skill_callback_ids=["default"],
            tx_id=self.tx_id,
            tx_sender_addr=self.tx_sender_addr,
            tx_counterparty_addr=self.tx_counterparty_addr,
            tx_amount_by_currency_id={"FET": -20},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 0},
            ledger_id="off_chain",
            info=self.info,
            signing_payload={"tx_hash": tx_hash},
        )

        tx_signature = self.decision_maker._sign_tx(tx_message)
        assert tx_signature is not None

    @classmethod
    def teardown_class(cls):
        """Tear the tests down."""
        cls._unpatch_logger()
        cls.multiplexer.disconnect()


class Test_LedgerStateProxy:
    """Test the Ledger State Proxy."""

    @classmethod
    def setup_class(cls):
        """Set up the test."""
        cls.ledger_apis = LedgerApis({FETCHAI: DEFAULT_FETCHAI_CONFIG}, FETCHAI)
        cls.ledger_state_proxy = LedgerStateProxy(ledger_apis=cls.ledger_apis)

    def test_ledger_apis(self):
        """Test the returned ledger_apis."""
        assert self.ledger_state_proxy.ledger_apis == self.ledger_apis, "Must be equal."

    def test_transaction_is_not_affordable(self):
        """Test if the transaction is affordable on the ledger."""
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=["default"],
            tx_id="transaction0",
            tx_sender_addr="agent_1",
            tx_counterparty_addr="pk",
            tx_amount_by_currency_id={"FET": -20},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 10},
            ledger_id="off_chain",
            info={"some_info_key": "some_info_value"},
        )

        with mock.patch.object(
            self.ledger_state_proxy.ledger_apis, "token_balance", return_value=0
        ):
            result = self.ledger_state_proxy.check_transaction_is_affordable(
                tx_message=tx_message
            )
        assert not result

    def test_transaction_is_affordable(self):
        """Test if the transaction is affordable on the ledger."""
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=["default"],
            tx_id="transaction0",
            tx_sender_addr="agent_1",
            tx_counterparty_addr="pk",
            tx_amount_by_currency_id={"FET": 20},
            tx_sender_fee=5,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 10},
            ledger_id="off_chain",
            info={"some_info_key": "some_info_value"},
        )
        with mock.patch.object(
            self.ledger_state_proxy.ledger_apis, "token_balance", return_value=0
        ):
            result = self.ledger_state_proxy.check_transaction_is_affordable(
                tx_message=tx_message
            )
        assert result
