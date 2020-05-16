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
import time
from queue import Queue
from unittest import TestCase, mock

import pytest

from web3.auto import Web3

import aea
import aea.decision_maker.base
from aea.configurations.base import PublicId
from aea.crypto.ethereum import EthereumCrypto
from aea.crypto.fetchai import FetchAICrypto
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import Wallet
from aea.decision_maker.base import DecisionMaker, OwnershipState, Preferences
from aea.decision_maker.base import LedgerStateProxy
from aea.decision_maker.messages.state_update import StateUpdateMessage
from aea.decision_maker.messages.transaction import OFF_CHAIN, TransactionMessage
from aea.identity.base import Identity
from aea.mail.base import Multiplexer
from aea.protocols.default.message import DefaultMessage

from ..conftest import (
    AUTHOR,
    CUR_PATH,
    _make_dummy_connection,
)

MAX_REACTIONS = 10
DEFAULT_FETCHAI_CONFIG = {"network": "testnet"}


def test_preferences_properties():
    """Test the properties of the preferences class."""
    preferences = Preferences()
    with pytest.raises(AssertionError):
        preferences.exchange_params_by_currency_id
    with pytest.raises(AssertionError):
        preferences.utility_params_by_good_id


def test_preferences_init():
    """Test the preferences init()."""
    utility_params = {"good_id": 20.0}
    exchange_params = {"FET": 10.0}
    tx_fee = 9
    preferences = Preferences()
    preferences._set(
        exchange_params_by_currency_id=exchange_params,
        utility_params_by_good_id=utility_params,
        tx_fee=tx_fee,
    )
    assert preferences.utility_params_by_good_id is not None
    assert preferences.exchange_params_by_currency_id is not None
    assert preferences.seller_transaction_fee == 4
    assert preferences.buyer_transaction_fee == 5
    assert preferences.is_initialized


def test_logarithmic_utility():
    """Calculate the logarithmic utility and checks that it is not none.."""
    utility_params = {"good_id": 20.0}
    exchange_params = {"FET": 10.0}
    good_holdings = {"good_id": 2}
    tx_fee = 9
    preferences = Preferences()
    preferences._set(
        utility_params_by_good_id=utility_params,
        exchange_params_by_currency_id=exchange_params,
        tx_fee=tx_fee,
    )
    log_utility = preferences.logarithmic_utility(quantities_by_good_id=good_holdings)
    assert log_utility is not None, "Log_utility must not be none."


def test_linear_utility():
    """Calculate the linear_utility and checks that it is not none."""
    currency_holdings = {"FET": 100}
    utility_params = {"good_id": 20.0}
    exchange_params = {"FET": 10.0}
    tx_fee = 9
    preferences = Preferences()
    preferences._set(
        utility_params_by_good_id=utility_params,
        exchange_params_by_currency_id=exchange_params,
        tx_fee=tx_fee,
    )
    linear_utility = preferences.linear_utility(amount_by_currency_id=currency_holdings)
    assert linear_utility is not None, "Linear utility must not be none."


def test_utility():
    """Calculate the score."""
    utility_params = {"good_id": 20.0}
    exchange_params = {"FET": 10.0}
    currency_holdings = {"FET": 100}
    good_holdings = {"good_id": 2}
    tx_fee = 9
    preferences = Preferences()
    preferences._set(
        utility_params_by_good_id=utility_params,
        exchange_params_by_currency_id=exchange_params,
        tx_fee=tx_fee,
    )
    score = preferences.utility(
        quantities_by_good_id=good_holdings, amount_by_currency_id=currency_holdings,
    )
    linear_utility = preferences.linear_utility(amount_by_currency_id=currency_holdings)
    log_utility = preferences.logarithmic_utility(quantities_by_good_id=good_holdings)
    assert (
        score == log_utility + linear_utility
    ), "The score must be equal to the sum of log_utility and linear_utility."


def test_marginal_utility():
    """Test the marginal utility."""
    currency_holdings = {"FET": 100}
    utility_params = {"good_id": 20.0}
    exchange_params = {"FET": 10.0}
    good_holdings = {"good_id": 2}
    tx_fee = 9
    preferences = Preferences()
    preferences._set(
        utility_params_by_good_id=utility_params,
        exchange_params_by_currency_id=exchange_params,
        tx_fee=tx_fee,
    )
    delta_good_holdings = {"good_id": 1}
    delta_currency_holdings = {"FET": -5}
    ownership_state = OwnershipState()
    ownership_state._set(
        amount_by_currency_id=currency_holdings, quantities_by_good_id=good_holdings,
    )
    marginal_utility = preferences.marginal_utility(
        ownership_state=ownership_state,
        delta_quantities_by_good_id=delta_good_holdings,
        delta_amount_by_currency_id=delta_currency_holdings,
    )
    assert marginal_utility is not None, "Marginal utility must not be none."


def test_score_diff_from_transaction():
    """Test the difference between the scores."""
    good_holdings = {"good_id": 2}
    currency_holdings = {"FET": 100}
    utility_params = {"good_id": 20.0}
    exchange_params = {"FET": 10.0}
    tx_fee = 3
    ownership_state = OwnershipState()
    ownership_state._set(
        amount_by_currency_id=currency_holdings, quantities_by_good_id=good_holdings
    )
    preferences = Preferences()
    preferences._set(
        utility_params_by_good_id=utility_params,
        exchange_params_by_currency_id=exchange_params,
        tx_fee=tx_fee,
    )
    tx_message = TransactionMessage(
        performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
        skill_callback_ids=[PublicId(AUTHOR, "a_skill", "0.1.0")],
        tx_id="transaction0",
        tx_sender_addr="agent_1",
        tx_counterparty_addr="pk",
        tx_amount_by_currency_id={"FET": -20},
        tx_sender_fee=preferences.seller_transaction_fee,
        tx_counterparty_fee=preferences.buyer_transaction_fee,
        tx_quantities_by_good_id={"good_id": 10},
        info={"some_info_key": "some_info_value"},
        ledger_id="fetchai",
        tx_nonce="transaction nonce",
    )

    cur_score = preferences.utility(
        quantities_by_good_id=good_holdings, amount_by_currency_id=currency_holdings
    )
    new_state = ownership_state.apply_transactions([tx_message])
    new_score = preferences.utility(
        quantities_by_good_id=new_state.quantities_by_good_id,
        amount_by_currency_id=new_state.amount_by_currency_id,
    )
    dif_scores = new_score - cur_score
    score_difference = preferences.utility_diff_from_transaction(
        ownership_state=ownership_state, tx_message=tx_message
    )
    assert (
        score_difference == dif_scores
    ), "The calculated difference must be equal to the return difference from the function."


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
        cls.multiplexer = Multiplexer([_make_dummy_connection()])
        private_key_pem_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
        eth_private_key_pem_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
        cls.wallet = Wallet(
            {
                FetchAICrypto.identifier: private_key_pem_path,
                EthereumCrypto.identifier: eth_private_key_pem_path,
            }
        )
        cls.ledger_apis = LedgerApis(
            {FetchAICrypto.identifier: DEFAULT_FETCHAI_CONFIG}, FetchAICrypto.identifier
        )
        cls.agent_name = "test"
        cls.identity = Identity(
            cls.agent_name,
            addresses=cls.wallet.addresses,
            default_address_key=FetchAICrypto.identifier,
        )
        cls.ownership_state = OwnershipState()
        cls.preferences = Preferences()
        cls.decision_maker = DecisionMaker(
            identity=cls.identity, wallet=cls.wallet, ledger_apis=cls.ledger_apis,
        )
        cls.multiplexer.connect()

        cls.tx_id = "transaction0"
        cls.tx_sender_addr = "agent_1"
        cls.tx_counterparty_addr = "pk"
        cls.info = {"some_info_key": "some_info_value"}
        cls.ledger_id = "fetchai"

        cls.decision_maker.start()

    def test_properties(self):
        """Test the properties of the decision maker."""
        assert isinstance(self.decision_maker.message_in_queue, Queue)
        assert isinstance(self.decision_maker.message_out_queue, Queue)
        assert isinstance(self.decision_maker.ledger_apis, LedgerApis)

    def test_decision_maker_execute(self):
        """Test the execute method."""
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=[PublicId(AUTHOR, "a_skill", "0.1.0")],
            tx_id=self.tx_id,
            tx_sender_addr=self.tx_sender_addr,
            tx_counterparty_addr=self.tx_counterparty_addr,
            tx_amount_by_currency_id={"FET": -20},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 10},
            info=self.info,
            ledger_id=self.ledger_id,
            tx_nonce="Transaction nonce",
        )

        self.decision_maker.message_in_queue.put_nowait(tx_message)
        # test that after a while the queue has been consumed.
        time.sleep(0.5)
        assert self.decision_maker.message_in_queue.empty()
        time.sleep(0.5)
        assert not self.decision_maker.message_out_queue.empty()
        # TODO test the content of the response.
        response = self.decision_maker.message_out_queue.get()  # noqa

    def test_decision_maker_handle_state_update_initialize_and_apply(self):
        """Test the handle method for a stateUpdate message with Initialize and Apply performative."""
        good_holdings = {"good_id": 2}
        currency_holdings = {"FET": 100}
        utility_params = {"good_id": 20.0}
        exchange_params = {"FET": 10.0}
        currency_deltas = {"FET": -10}
        good_deltas = {"good_id": 1}

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

    # TODO this used to work with the testnet
    def test_decision_maker_handle_tx_message(self):
        """Test the handle tx message method."""
        assert self.decision_maker.message_out_queue.empty()
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=[PublicId(AUTHOR, "a_skill", "0.1.0")],
            tx_id=self.tx_id,
            tx_sender_addr=self.tx_sender_addr,
            tx_counterparty_addr=self.tx_counterparty_addr,
            tx_amount_by_currency_id={"FET": -2},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 10},
            info=self.info,
            ledger_id=self.ledger_id,
            tx_nonce="Transaction nonce",
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
                self.decision_maker.message_out_queue.get()

    def test_decision_maker_handle_unknown_tx_message(self):
        """Test the handle tx message method."""
        patch_logger_error = mock.patch.object(aea.decision_maker.base.logger, "error")
        mocked_logger_error = patch_logger_error.__enter__()

        with mock.patch(
            "aea.decision_maker.messages.transaction.TransactionMessage._is_consistent",
            return_value=True,
        ):
            tx_message = TransactionMessage(
                performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
                skill_callback_ids=[PublicId(AUTHOR, "a_skill", "0.1.0")],
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
            skill_callback_ids=[PublicId(AUTHOR, "a_skill", "0.1.0")],
            tx_id=self.tx_id,
            tx_sender_addr=self.tx_sender_addr,
            tx_counterparty_addr=self.tx_counterparty_addr,
            tx_amount_by_currency_id={"FET": -2},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 10},
            info=self.info,
            ledger_id=self.ledger_id,
            tx_nonce="Transaction nonce",
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
                    self.decision_maker.message_out_queue.get()

        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=[PublicId(AUTHOR, "a_skill", "0.1.0")],
            tx_id=self.tx_id,
            tx_sender_addr=self.tx_sender_addr,
            tx_counterparty_addr=self.tx_counterparty_addr,
            tx_amount_by_currency_id={"FET": -2},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 10},
            info=self.info,
            ledger_id=self.ledger_id,
            tx_nonce="transaction nonce",
        )
        self.decision_maker.handle(tx_message)
        assert not self.decision_maker.message_out_queue.empty()
        self.decision_maker.message_out_queue.get()

    def test_decision_maker_hand_tx_ready_for_signing(self):
        """Test that the decision maker can handle a message that is ready for signing."""
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SIGNING,
            skill_callback_ids=[PublicId(AUTHOR, "a_skill", "0.1.0")],
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
        self.decision_maker.message_out_queue.get()

    def test_decision_maker_handle_tx_message_acceptable_for_settlement(self):
        """Test that a tx_message is acceptable for settlement."""
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=[PublicId(AUTHOR, "a_skill", "0.1.0")],
            tx_id=self.tx_id,
            tx_sender_addr=self.tx_sender_addr,
            tx_counterparty_addr=self.tx_counterparty_addr,
            tx_amount_by_currency_id={"FET": -2},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 10},
            info=self.info,
            ledger_id=self.ledger_id,
            tx_nonce="Transaction nonce",
        )
        with mock.patch.object(
            self.decision_maker, "_is_acceptable_for_settlement", return_value=True
        ):
            with mock.patch.object(
                self.decision_maker, "_settle_tx", return_value="tx_digest"
            ):
                self.decision_maker.handle(tx_message)
                assert not self.decision_maker.message_out_queue.empty()
                self.decision_maker.message_out_queue.get()

    def test_decision_maker_tx_message_is_not_acceptable_for_settlement(self):
        """Test that a tx_message is not acceptable for settlement."""
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=[PublicId(AUTHOR, "a_skill", "0.1.0")],
            tx_id=self.tx_id,
            tx_sender_addr=self.tx_sender_addr,
            tx_counterparty_addr=self.tx_counterparty_addr,
            tx_amount_by_currency_id={"FET": -2},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 10},
            ledger_id=self.ledger_id,
            info=self.info,
            tx_nonce="Transaction nonce",
        )

        with mock.patch.object(
            self.decision_maker, "_is_acceptable_for_settlement", return_value=True
        ):
            with mock.patch.object(
                self.decision_maker, "_settle_tx", return_value=None
            ):
                self.decision_maker.handle(tx_message)
                assert not self.decision_maker.message_out_queue.empty()
                self.decision_maker.message_out_queue.get()

    def test_decision_maker_execute_w_wrong_input(self):
        """Test the execute method with wrong input."""
        default_message = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )

        with pytest.raises(ValueError):
            self.decision_maker.message_in_queue.put_nowait(default_message)

    def test_is_affordable_off_chain(self):
        """Test the off_chain message."""
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=[PublicId(AUTHOR, "a_skill", "0.1.0")],
            tx_id=self.tx_id,
            tx_sender_addr=self.tx_sender_addr,
            tx_counterparty_addr=self.tx_counterparty_addr,
            tx_amount_by_currency_id={"FET": -20},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 10},
            ledger_id="off_chain",
            info=self.info,
            tx_nonce="Transaction nonce",
        )

        assert self.decision_maker._is_affordable(tx_message)

    def test_is_not_affordable_ledger_state_proxy(self):
        """Test that the tx_message is not affordable with initialized ledger_state_proxy."""
        with mock.patch(
            "aea.decision_maker.messages.transaction.TransactionMessage._is_consistent",
            return_value=True,
        ):
            tx_message = TransactionMessage(
                performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
                skill_callback_ids=[PublicId(AUTHOR, "a_skill", "0.1.0")],
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
            skill_callback_ids=[PublicId(AUTHOR, "a_skill", "0.1.0")],
            tx_id=self.tx_id,
            tx_sender_addr=self.tx_sender_addr,
            tx_counterparty_addr=self.tx_counterparty_addr,
            tx_amount_by_currency_id={"FET": -20},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 10},
            ledger_id=self.ledger_id,
            info=self.info,
            tx_nonce="Transaction nonce",
        )

        with mock.patch.object(
            self.decision_maker, "_is_acceptable_for_settlement", return_value=True
        ):
            with mock.patch.object(
                self.decision_maker, "_settle_tx", return_value="tx_digest"
            ):
                self.decision_maker._is_affordable(tx_message)

    def test_settle_tx_off_chain(self):
        """Test the off_chain message."""
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=[PublicId(AUTHOR, "a_skill", "0.1.0")],
            tx_id=self.tx_id,
            tx_sender_addr=self.tx_sender_addr,
            tx_counterparty_addr=self.tx_counterparty_addr,
            tx_amount_by_currency_id={"FET": -20},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 10},
            ledger_id="off_chain",
            info=self.info,
            tx_nonce="Transaction nonce",
        )

        tx_digest = self.decision_maker._settle_tx(tx_message)
        assert tx_digest == "off_chain_settlement"

    def test_settle_tx_known_chain(self):
        """Test the off_chain message."""
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=[PublicId(AUTHOR, "a_skill", "0.1.0")],
            tx_id=self.tx_id,
            tx_sender_addr=self.tx_sender_addr,
            tx_counterparty_addr=self.tx_counterparty_addr,
            tx_amount_by_currency_id={"FET": -20},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 10},
            ledger_id=self.ledger_id,
            info=self.info,
            tx_nonce="Transaction nonce",
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
            skill_callback_ids=[PublicId(AUTHOR, "a_skill", "0.1.0")],
            tx_id=self.tx_id,
            tx_sender_addr=self.tx_sender_addr,
            tx_counterparty_addr=self.tx_counterparty_addr,
            tx_amount_by_currency_id={"FET": -20},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 10},
            ledger_id="off_chain",
            info=self.info,
            tx_nonce="Transaction nonce",
        )
        self.decision_maker.ownership_state._quantities_by_good_id = None
        assert self.decision_maker._is_utility_enhancing(tx_message)

    def test_sign_tx_hash_fetchai(self):
        """Test the private function sign_tx of the decision maker for fetchai ledger_id."""
        tx_hash = Web3.keccak(text="some_bytes")

        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SIGNING,
            skill_callback_ids=[PublicId(AUTHOR, "a_skill", "0.1.0")],
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

        tx_signature = self.decision_maker._sign_tx_hash(tx_message)
        assert tx_signature is not None

    def test_sign_tx_hash_fetchai_is_acceptable_for_signing(self):
        """Test the private function sign_tx of the decision maker for fetchai ledger_id."""
        tx_hash = Web3.keccak(text="some_bytes")

        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SIGNING,
            skill_callback_ids=[PublicId(AUTHOR, "a_skill", "0.1.0")],
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

        tx_signature = self.decision_maker._sign_tx_hash(tx_message)
        assert tx_signature is not None

    def test_sing_tx_offchain(self):
        """Test the private function sign_tx for the offchain ledger_id."""
        tx_hash = Web3.keccak(text="some_bytes")
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SIGNING,
            skill_callback_ids=[PublicId(AUTHOR, "a_skill", "0.1.0")],
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

        tx_signature = self.decision_maker._sign_tx_hash(tx_message)
        assert tx_signature is not None

    def test_respond_message(self):
        tx_hash = Web3.keccak(text="some_bytes")
        tx_signature = Web3.keccak(text="tx_signature")

        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SIGNING,
            skill_callback_ids=[PublicId(AUTHOR, "a_skill", "0.1.0")],
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

        tx_message_response = TransactionMessage.respond_signing(
            tx_message,
            performative=TransactionMessage.Performative.SUCCESSFUL_SIGNING,
            signed_payload={"tx_signature": tx_signature},
        )
        assert tx_message_response.signed_payload.get("tx_signature") == tx_signature

    @classmethod
    def teardown_class(cls):
        """Tear the tests down."""
        cls._unpatch_logger()
        cls.multiplexer.disconnect()
        cls.decision_maker.stop()


class TestLedgerStateProxy:
    """Test the Ledger State Proxy."""

    @classmethod
    def setup_class(cls):
        """Set up the test."""
        cls.ledger_apis = LedgerApis(
            {FetchAICrypto.identifier: DEFAULT_FETCHAI_CONFIG}, FetchAICrypto.identifier
        )
        cls.ledger_state_proxy = LedgerStateProxy(ledger_apis=cls.ledger_apis)

    def test_ledger_apis(self):
        """Test the returned ledger_apis."""
        assert self.ledger_state_proxy.ledger_apis == self.ledger_apis, "Must be equal."

    def test_transaction_is_not_affordable(self):
        """Test if the transaction is affordable on the ledger."""
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=[PublicId(AUTHOR, "a_skill", "0.1.0")],
            tx_id="transaction0",
            tx_sender_addr="agent_1",
            tx_counterparty_addr="pk",
            tx_amount_by_currency_id={"FET": -20},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 10},
            ledger_id="off_chain",
            info={"some_info_key": "some_info_value"},
            tx_nonce="Transaction nonce",
        )

        with mock.patch.object(
            self.ledger_state_proxy.ledger_apis, "token_balance", return_value=0
        ):
            result = self.ledger_state_proxy.is_affordable_transaction(
                tx_message=tx_message
            )
        assert not result

    def test_transaction_is_affordable(self):
        """Test if the transaction is affordable on the ledger."""
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=[PublicId(AUTHOR, "a_skill", "0.1.0")],
            tx_id="transaction0",
            tx_sender_addr="agent_1",
            tx_counterparty_addr="pk",
            tx_amount_by_currency_id={"FET": 20},
            tx_sender_fee=5,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"good_id": 10},
            ledger_id="off_chain",
            info={"some_info_key": "some_info_value"},
            tx_nonce="Transaction nonce",
        )
        with mock.patch.object(
            self.ledger_state_proxy.ledger_apis, "token_balance", return_value=0
        ):
            result = self.ledger_state_proxy.is_affordable_transaction(
                tx_message=tx_message
            )
        assert result


class DecisionMakerTestCase(TestCase):
    """Test case for DecisionMaker class."""

    # @mock.patch(
    #     "aea.decision_maker.base.DecisionMaker._is_acceptable_for_signing",
    #     return_value=True,
    # )
    # @mock.patch("aea.decision_maker.base.DecisionMaker._sign_ledger_tx")
    # @mock.patch("aea.decision_maker.base.TransactionMessage.respond_signing")
    # def test__handle_tx_message_for_signing_positive(self, *mocks):
    #     """Test for _handle_tx_message_for_signing positive result."""
    #     private_key_pem_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
    #     wallet = Wallet({FetchAICrypto.identifier: private_key_pem_path})
    #     ledger_apis = LedgerApis({FetchAICrypto.identifier: DEFAULT_FETCHAI_CONFIG}, FetchAICrypto.identifier)
    #     identity = Identity(
    #         "agent_name", addresses=wallet.addresses, default_address_key=FetchAICrypto.identifier
    #     )
    #     dm = DecisionMaker(identity, wallet, ledger_apis)
    #     dm._handle_tx_message_for_signing("tx_message")

    def test__is_affordable_positive(self, *mocks):
        """Test for _is_affordable positive result."""
        private_key_pem_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
        wallet = Wallet({FetchAICrypto.identifier: private_key_pem_path})
        ledger_apis = LedgerApis(
            {FetchAICrypto.identifier: DEFAULT_FETCHAI_CONFIG}, FetchAICrypto.identifier
        )
        identity = Identity(
            "agent_name",
            addresses=wallet.addresses,
            default_address_key=FetchAICrypto.identifier,
        )
        dm = DecisionMaker(identity, wallet, ledger_apis)
        tx_message = mock.Mock()
        tx_message.ledger_id = OFF_CHAIN
        dm._is_affordable(tx_message)
