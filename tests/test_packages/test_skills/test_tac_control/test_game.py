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
"""This module contains the tests of the models of the tac control skill."""

import datetime
import logging
import pprint
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from aea.crypto.ledger_apis import LedgerApis
from aea.exceptions import AEAEnforceError
from aea.helpers.preference_representations.base import (
    linear_utility,
    logarithmic_utility,
)
from aea.helpers.search.models import Description, Location
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.protocols.tac.message import TacMessage
from packages.fetchai.skills.tac_control.game import (
    AGENT_LOCATION_MODEL,
    AGENT_PERSONALITY_MODEL,
    AGENT_REMOVE_SERVICE_MODEL,
    AGENT_SET_SERVICE_MODEL,
    AgentState,
    Configuration,
    Game,
    Initialization,
    Phase,
    Registration,
    Transaction,
    Transactions,
)
from packages.fetchai.skills.tac_control.parameters import Parameters

from tests.conftest import ROOT_DIR


class TestConfiguration:
    """Test Configuration class of tac control."""

    @classmethod
    def setup(cls):
        """Setup the test class."""
        cls.version_id = "some_version_id"
        cls.tx_fee = 1
        cls.agent_addr_to_name = {
            "agent_address_1": "agent_name_1",
            "agent_address_2": "agent_name_2",
        }
        cls.currency_id_to_name = {"1": "currency_1"}
        cls.good_id_to_name = {"3": "good_1", "4": "good_2"}

        cls.configuration = Configuration(
            cls.version_id,
            cls.tx_fee,
            cls.agent_addr_to_name,
            cls.currency_id_to_name,
            cls.good_id_to_name,
        )

    def test_simple_properties(self):
        """Test the properties of Game class."""
        assert self.configuration.version_id == self.version_id

        assert self.configuration.fee_by_currency_id == {"1": 1}

        assert self.configuration.agent_addr_to_name == self.agent_addr_to_name

        assert self.configuration.currency_id_to_name == self.currency_id_to_name

        assert self.configuration.good_id_to_name == self.good_id_to_name

        assert self.configuration.has_contract_address is False

        with pytest.raises(AEAEnforceError, match="Contract_address not set yet!"):
            assert self.configuration.contract_address

        self.configuration.contract_address = "some_contract_address"

        assert self.configuration.has_contract_address is True
        assert self.configuration.contract_address == "some_contract_address"

        with pytest.raises(AEAEnforceError, match="Contract_address already set!"):
            self.configuration.contract_address = "some_other_contract_address"

    def test_check_consistency_succeeds(self):
        """Test the _check_consistency of Configuration class which succeeds."""
        self.configuration._check_consistency()

    def test_check_consistency_fails_i(self):
        """Test the _check_consistency of Configuration class which fails on version being None."""
        self.configuration._version_id = None
        with pytest.raises(AEAEnforceError, match="A version id must be set."):
            assert self.configuration._check_consistency()

    def test_check_consistency_fails_ii(self):
        """Test the _check_consistency of Configuration class which fails because tx_fee < 0."""
        self.configuration._tx_fee = -5
        with pytest.raises(AEAEnforceError, match="Tx fee must be non-negative."):
            assert self.configuration._check_consistency()

    def test_check_consistency_fails_iii(self):
        """Test the _check_consistency of Configuration class which fails because number of agents is less than 2."""
        self.configuration._agent_addr_to_name = {"agent_address_1": "agent_name_1"}
        with pytest.raises(AEAEnforceError, match="Must have at least two agents."):
            assert self.configuration._check_consistency()

    def test_check_consistency_fails_iv(self):
        """Test the _check_consistency of Configuration class which fails because number of goods is less than 2."""
        self.configuration._good_id_to_name = {"3": "good_1"}
        with pytest.raises(AEAEnforceError, match="Must have at least two goods."):
            assert self.configuration._check_consistency()

    def test_check_consistency_fails_v(self):
        """Test the _check_consistency of Configuration class which fails because number of currencies is not 1."""
        self.configuration._currency_id_to_name = {"1": "currency_1", "2": "currency_2"}
        with pytest.raises(AEAEnforceError, match="Must have exactly one currency."):
            assert self.configuration._check_consistency()

    def test_check_consistency_fails_vi(self):
        """Test the _check_consistency of Configuration class which fails because same id for good and currency."""
        self.configuration._good_id_to_name = {"1": "good_1", "2": "good_2"}
        self.configuration._currency_id_to_name = {"1": "currency_1"}
        with pytest.raises(
            AEAEnforceError, match="Currency id and good ids cannot overlap."
        ):
            assert self.configuration._check_consistency()


class TestInitialization:
    """Test Initialization class of tac control."""

    @classmethod
    def setup(cls):
        """Setup the test class."""
        cls.agent_addr_to_currency_endowments = {
            "agent_address_1": {"1": 10},
            "agent_address_2": {"1": 5},
        }
        cls.agent_addr_to_exchange_params = {
            "agent_address_1": {"1": 1.0},
            "agent_address_2": {"1": 1.5},
        }
        cls.agent_addr_to_good_endowments = {
            "agent_address_1": {"2": 5, "3": 7},
            "agent_address_2": {"2": 4, "3": 6},
        }
        cls.agent_addr_to_utility_params = {
            "agent_address_1": {"2": 1.0, "3": 1.1},
            "agent_address_2": {"2": 1.3, "3": 1.5},
        }
        cls.good_id_to_eq_prices = {"2": 1.7, "3": 1.3}
        cls.agent_addr_to_eq_good_holdings = {
            "agent_address_1": {"2": 1.2, "3": 1.1},
            "agent_address_2": {"2": 1.1, "3": 1.4},
        }
        cls.agent_addr_to_eq_currency_holdings = {
            "agent_address_1": {"1": 1.1},
            "agent_address_2": {"1": 1.2},
        }

        cls.initialization = Initialization(
            cls.agent_addr_to_currency_endowments,
            cls.agent_addr_to_exchange_params,
            cls.agent_addr_to_good_endowments,
            cls.agent_addr_to_utility_params,
            cls.good_id_to_eq_prices,
            cls.agent_addr_to_eq_good_holdings,
            cls.agent_addr_to_eq_currency_holdings,
        )

    def test_simple_properties(self):
        """Test the properties of Game class."""
        assert (
            self.initialization.agent_addr_to_currency_endowments
            == self.agent_addr_to_currency_endowments
        )
        assert (
            self.initialization.agent_addr_to_exchange_params
            == self.agent_addr_to_exchange_params
        )
        assert (
            self.initialization.agent_addr_to_good_endowments
            == self.agent_addr_to_good_endowments
        )
        assert (
            self.initialization.agent_addr_to_utility_params
            == self.agent_addr_to_utility_params
        )
        assert self.initialization.good_id_to_eq_prices == self.good_id_to_eq_prices
        assert (
            self.initialization.agent_addr_to_eq_good_holdings
            == self.agent_addr_to_eq_good_holdings
        )
        assert (
            self.initialization.agent_addr_to_eq_currency_holdings
            == self.agent_addr_to_eq_currency_holdings
        )

    def test_check_consistency_succeeds(self):
        """Test the _check_consistency of Configuration class which succeeds."""
        self.initialization._check_consistency()

    def test_check_consistency_fails_i(self):
        """Test the _check_consistency of Configuration class which fails because currency endowments are negative."""
        self.initialization._agent_addr_to_currency_endowments = {
            "agent_address_1": {"1": -1},
            "agent_address_2": {"1": 5},
        }
        with pytest.raises(
            AEAEnforceError, match="Currency endowments must be non-negative."
        ):
            assert self.initialization._check_consistency()

    def test_check_consistency_fails_ii(self):
        """Test the _check_consistency of Configuration class which fails because ExchangeParams are not strictly positive."""
        self.initialization._agent_addr_to_exchange_params = {
            "agent_address_1": {"1": 0.0},
            "agent_address_2": {"1": -1.2},
        }
        with pytest.raises(
            AEAEnforceError, match="ExchangeParams must be strictly positive."
        ):
            assert self.initialization._check_consistency()

    def test_check_consistency_fails_iii(self):
        """Test the _check_consistency of Configuration class which fails because Good endowments are not strictly positive."""
        self.initialization._agent_addr_to_good_endowments = {
            "agent_address_1": {"2": 0, "3": -1},
            "agent_address_2": {"2": -7, "3": 0},
        }
        with pytest.raises(
            AEAEnforceError, match="Good endowments must be strictly positive."
        ):
            assert self.initialization._check_consistency()

    def test_check_consistency_fails_iv(self):
        """Test the _check_consistency of Configuration class which fails because UtilityParams are not strictly positive."""
        self.initialization._agent_addr_to_utility_params = {
            "agent_address_1": {"2": 0, "3": -7},
            "agent_address_2": {"2": -4, "3": 0},
        }
        with pytest.raises(
            AEAEnforceError, match="UtilityParams must be strictly positive."
        ):
            assert self.initialization._check_consistency()

    def test_check_consistency_fails_v(self):
        """Test the _check_consistency of Configuration class which fails because lengths of endowments are not the same."""
        self.initialization._agent_addr_to_currency_endowments = {
            "agent_address_1": {"1": 10},
        }
        with pytest.raises(
            AEAEnforceError, match="Length of endowments must be the same."
        ):
            assert self.initialization._check_consistency()

    def test_check_consistency_fails_vi(self):
        """Test the _check_consistency of Configuration class which fails because lengths of params are not the same."""
        self.initialization._agent_addr_to_exchange_params = {
            "agent_address_1": {"1": 1.0},
        }
        with pytest.raises(AEAEnforceError, match="Length of params must be the same."):
            assert self.initialization._check_consistency()

    def test_check_consistency_fails_vii(self):
        """Test the _check_consistency of Configuration class which fails because length of eq_prices and elements of eq_good_holdings are not the same."""
        self.initialization._good_id_to_eq_prices = {"2": 1.7}
        with pytest.raises(
            AEAEnforceError,
            match="Length of eq_prices and an element of eq_good_holdings must be the same.",
        ):
            assert self.initialization._check_consistency()

    def test_check_consistency_fails_viii(self):
        """Test the _check_consistency of Configuration class which fails because length of eq_good_holdings and eq_currency_holdings are not the same."""
        self.initialization._agent_addr_to_eq_currency_holdings = {
            "agent_address_1": {"1": 1.1},
        }
        with pytest.raises(
            AEAEnforceError,
            match="Length of eq_good_holdings and eq_currency_holdings must be the same.",
        ):
            assert self.initialization._check_consistency()

    def test_check_consistency_fails_ix(self):
        """Test the _check_consistency of Configuration class which fails because exchange_params and currency_endowments have different number of rows."""
        self.initialization._agent_addr_to_currency_endowments = {
            "agent_address_1": {"1": 10, "2": 11},
            "agent_address_2": {"1": 5},
        }
        with pytest.raises(
            AEAEnforceError,
            match="Dimensions for exchange_params and currency_endowments rows must be the same.",
        ):
            assert self.initialization._check_consistency()

    def test_check_consistency_fails_x(self):
        """Test the _check_consistency of Configuration class which fails because utility_params and rows have different number of rows."""
        self.initialization._agent_addr_to_good_endowments = {
            "agent_address_1": {"2": 5, "3": 7, "4": 8},
            "agent_address_2": {"2": 4, "3": 6},
        }
        with pytest.raises(
            AEAEnforceError,
            match="Dimensions for utility_params and good_endowments rows must be the same.",
        ):
            assert self.initialization._check_consistency()


class TestTransaction:
    """Test Initialization class of tac control."""

    @classmethod
    def setup(cls):
        """Setup the test class."""
        cls.ledger_id = "ethereum"
        cls.sender_address = "some_sender_address"
        cls.counterparty_address = "some_counterparty_address"
        cls.amount_by_currency_id = {"1": 10}
        cls.quantities_by_good_id = {"2": 5, "5": 10}
        cls.is_sender_payable_tx_fee = True
        cls.nonce = "some_nonce"
        cls.fee_by_currency_id = {"1": 1}
        cls.sender_signature = "some_sender_signature"
        cls.counterparty_signature = "some_counterparty_signature"

        cls.transaction = Transaction(
            cls.ledger_id,
            cls.sender_address,
            cls.counterparty_address,
            cls.amount_by_currency_id,
            cls.quantities_by_good_id,
            cls.is_sender_payable_tx_fee,
            cls.nonce,
            cls.fee_by_currency_id,
            cls.sender_signature,
            cls.counterparty_signature,
        )

    def test_simple_properties(self):
        """Test the properties of Game class."""
        assert self.transaction.sender_signature == self.sender_signature
        assert self.transaction.counterparty_signature == self.counterparty_signature

    def test_has_matching_signatures_succeeds(self):
        """Test the has_matching_signatures method of Transaction class where the two addresses appear in the hash."""
        with patch.object(
            LedgerApis,
            "recover_message",
            return_value=(self.sender_address, self.counterparty_address),
        ):
            assert self.transaction.has_matching_signatures() is True

    def test_has_matching_signatures_fails_sender_not_in_hash(self):
        """Test the has_matching_signatures method of Transaction class where the sender address does not appear in the hash."""
        with patch.object(
            LedgerApis, "recover_message", return_value=(self.counterparty_address,)
        ):
            assert self.transaction.has_matching_signatures() is False

    def test_has_matching_signatures_fails_counterparty_not_in_hash(self):
        """Test the has_matching_signatures method of Transaction class where the counterparty addresses does not appear in the hash."""
        with patch.object(
            LedgerApis, "recover_message", return_value=(self.sender_address,)
        ):
            assert self.transaction.has_matching_signatures() is False

    def test_has_matching_signatures_fails_sender_and_counterparty_not_in_hash(self):
        """Test the has_matching_signatures method of Transaction class where the sender and counterparty addresses do not appear in the hash."""
        with patch.object(LedgerApis, "recover_message", return_value=tuple()):
            assert self.transaction.has_matching_signatures() is False

    def test_from_message(self):
        """Test the from_message method of Transaction class."""
        ledger_id = "some_ledger_id"
        sender_address = "some_sender_address"
        counterparty_address = "some_counterparty_address"
        amount_by_currency_id = {"FET": 10}
        fee_by_currency_id = {"FET": 2}
        quantities_by_good_id = {"G1": -1}
        nonce = "some_nonce"
        sender_signature = "some_signature"
        counterparty_signature = "some_other_signature"

        tx_id = Transaction.get_hash(
            ledger_id,
            sender_address=sender_address,
            counterparty_address=counterparty_address,
            good_ids=["G1"],
            sender_supplied_quantities=[0],
            counterparty_supplied_quantities=[1],
            sender_payable_amount=0,
            counterparty_payable_amount=10,
            nonce=nonce,
        )

        tx = Transaction.from_message(
            TacMessage(
                performative=TacMessage.Performative.TRANSACTION,
                transaction_id=tx_id,
                ledger_id=ledger_id,
                sender_address=sender_address,
                counterparty_address=counterparty_address,
                amount_by_currency_id=amount_by_currency_id,
                fee_by_currency_id=fee_by_currency_id,
                quantities_by_good_id=quantities_by_good_id,
                nonce=nonce,
                sender_signature=sender_signature,
                counterparty_signature=counterparty_signature,
            )
        )

        assert tx.ledger_id == ledger_id
        assert tx.sender_address == sender_address
        assert tx.counterparty_address == counterparty_address
        assert tx.amount_by_currency_id == amount_by_currency_id
        assert tx.fee_by_currency_id == fee_by_currency_id
        assert tx.quantities_by_good_id == quantities_by_good_id
        assert tx.nonce == nonce
        assert tx.sender_signature == sender_signature
        assert tx.counterparty_signature == counterparty_signature

    def test__eq__(self):
        """Test the __eq__ method of Transaction class."""
        equal_transaction = Transaction(
            self.ledger_id,
            self.sender_address,
            self.counterparty_address,
            self.amount_by_currency_id,
            self.quantities_by_good_id,
            self.is_sender_payable_tx_fee,
            self.nonce,
            self.fee_by_currency_id,
            self.sender_signature,
            self.counterparty_signature,
        )
        assert self.transaction.__eq__(equal_transaction) is True

        not_equal_transaction = Transaction(
            self.ledger_id,
            "some_different_sender_address",
            self.counterparty_address,
            self.amount_by_currency_id,
            self.quantities_by_good_id,
            self.is_sender_payable_tx_fee,
            self.nonce,
            self.fee_by_currency_id,
            self.sender_signature,
            self.counterparty_signature,
        )
        assert self.transaction.__eq__(not_equal_transaction) is False


class TestAgentState:
    """Test AgentState class of tac control."""

    @classmethod
    def setup(cls):
        """Setup the test class."""
        cls.agent_address = "sender_address"
        cls.amount_by_currency_id = {"1": 10}
        cls.quantities_by_good_id = {"2": 1, "3": 2}
        cls.exchange_params_by_currency_id = {"1": 1.0}
        cls.utility_params_by_good_id = {"2": 1.0, "3": 1.5}

        cls.agent_state = AgentState(
            cls.agent_address,
            cls.amount_by_currency_id,
            cls.exchange_params_by_currency_id,
            cls.quantities_by_good_id,
            cls.utility_params_by_good_id,
        )

        cls.ledger_id = "ethereum"
        cls.sender_address = cls.agent_address
        cls.counterparty_address = "some_counterparty_address"
        cls.tx_amount_by_currency_id = {"1": 10}
        cls.tx_quantities_by_good_id = {"2": -1, "3": -2}
        cls.is_sender_payable_tx_fee = True
        cls.nonce = "some_nonce"
        cls.fee_by_currency_id = {"1": 1}
        cls.sender_signature = "some_sender_signature"
        cls.counterparty_signature = "some_counterparty_signature"
        cls.transaction_1 = Transaction(
            cls.ledger_id,
            cls.sender_address,
            cls.counterparty_address,
            cls.tx_amount_by_currency_id,
            cls.tx_quantities_by_good_id,
            cls.is_sender_payable_tx_fee,
            cls.nonce,
            cls.fee_by_currency_id,
            cls.sender_signature,
            cls.counterparty_signature,
        )

        cls.amount_by_currency_id_2 = {"1": -9}
        cls.quantities_by_good_id_2 = {"2": 1, "3": 2}
        cls.transaction_2 = Transaction(
            cls.ledger_id,
            cls.sender_address,
            cls.counterparty_address,
            cls.amount_by_currency_id_2,
            cls.quantities_by_good_id_2,
            cls.is_sender_payable_tx_fee,
            cls.nonce,
            cls.fee_by_currency_id,
            cls.sender_signature,
            cls.counterparty_signature,
        )

    def test_simple_properties(self):
        """Test the properties of AgentState class."""
        assert self.agent_state.agent_address == self.agent_address
        assert self.agent_state.amount_by_currency_id == self.amount_by_currency_id
        assert (
            self.agent_state.exchange_params_by_currency_id
            == self.exchange_params_by_currency_id
        )
        assert self.agent_state.quantities_by_good_id == self.quantities_by_good_id
        assert (
            self.agent_state.utility_params_by_good_id == self.utility_params_by_good_id
        )

    def test_get_score(self):
        """Test the get_score of AgentState class."""
        assert self.agent_state.get_score() == logarithmic_utility(
            self.utility_params_by_good_id, self.quantities_by_good_id
        ) + linear_utility(
            self.exchange_params_by_currency_id, self.amount_by_currency_id
        )

    def test_is_consistent_transaction_succeeds(self):
        """Test the is_consistent_transaction of AgentState class where it returns True."""
        assert self.agent_state.is_consistent_transaction(self.transaction_1) is True

    def test_is_consistent_transaction_fails_i(self):
        """Test the is_consistent_transaction of AgentState class where it fails because agent address is not sender/counterparty."""
        self.transaction_1._sender_address = "some_sender_address"
        assert self.agent_state.is_consistent_transaction(self.transaction_1) is False

    def test_is_consistent_transaction_fails_ii(self):
        """Test the is_consistent_transaction of AgentState class where it fails because tx is not single currency."""
        self.transaction_1._amount_by_currency_id = {"1": 10, "2": 20}
        assert self.agent_state.is_consistent_transaction(self.transaction_1) is False

    def test_is_consistent_transaction_fails_iii(self):
        """Test the is_consistent_transaction of AgentState class where it fails because there is no exchange of wealth."""
        self.transaction_1._amount_by_currency_id = {"1": 0}
        self.transaction_1._quantities_by_good_id = {"2": 0, "3": 0}
        assert self.agent_state.is_consistent_transaction(self.transaction_1) is False

    def test_is_consistent_transaction_fails_iv(self):
        """Test the is_consistent_transaction of AgentState class where it fails because sender does not have enough funds."""
        self.transaction_1._amount_by_currency_id = {"1": -11}
        self.transaction_1._quantities_by_good_id = {"2": 1, "3": 0}
        assert self.agent_state.is_consistent_transaction(self.transaction_1) is False

    def test_is_consistent_transaction_succeeds_iv(self):
        """Test the is_consistent_transaction of AgentState class where it succeeds and sender does have enough funds."""
        self.transaction_1._amount_by_currency_id = {"1": -9}
        self.transaction_1._quantities_by_good_id = {"2": 1, "3": 0}
        assert self.agent_state.is_consistent_transaction(self.transaction_1) is True

    def test_is_consistent_transaction_fails_v(self):
        """Test the is_consistent_transaction of AgentState class where it fails because counterparty does not have enough goods."""
        self.transaction_1._counterparty_address = self.agent_address
        self.transaction_1._sender_address = "some_sender_address"

        self.transaction_1._amount_by_currency_id = {"1": -10}
        self.transaction_1._quantities_by_good_id = {"2": 2, "3": 2}
        assert self.agent_state.is_consistent_transaction(self.transaction_1) is False

    def test_is_consistent_transaction_succeeds_v(self):
        """Test the is_consistent_transaction of AgentState class where it succeeds and counterparty does have enough goods."""
        self.transaction_1._counterparty_address = self.agent_address
        self.transaction_1._sender_address = "some_sender_address"

        self.transaction_1._amount_by_currency_id = {"1": -10}
        self.transaction_1._quantities_by_good_id = {"2": 1, "3": 2}
        assert self.agent_state.is_consistent_transaction(self.transaction_1) is True

    def test_is_consistent_transaction_fails_vi(self):
        """Test the is_consistent_transaction of AgentState class where it fails because sender does not have enough goods."""
        self.transaction_1._amount_by_currency_id = {"1": 10}
        self.transaction_1._quantities_by_good_id = {"2": -2, "3": -2}
        assert self.agent_state.is_consistent_transaction(self.transaction_1) is False

    def test_is_consistent_transaction_succeeds_vi(self):
        """Test the is_consistent_transaction of AgentState class where it succeeds and sender does have enough goods."""
        self.transaction_1._amount_by_currency_id = {"1": 10}
        self.transaction_1._quantities_by_good_id = {"2": -1, "3": -2}
        assert self.agent_state.is_consistent_transaction(self.transaction_1) is True

    def test_is_consistent_transaction_fails_vii(self):
        """Test the is_consistent_transaction of AgentState class where it fails because counterparty does not have enough funds."""
        self.transaction_1._counterparty_address = self.agent_address
        self.transaction_1._sender_address = "some_sender_address"

        self.transaction_1._amount_by_currency_id = {"1": 11}
        self.transaction_1._quantities_by_good_id = {"2": -1, "3": -2}
        assert self.agent_state.is_consistent_transaction(self.transaction_1) is False

    def test_is_consistent_transaction_succeeds_vii(self):
        """Test the is_consistent_transaction of AgentState class where it succeeds and counterparty does have enough funds."""
        self.transaction_1._counterparty_address = self.agent_address
        self.transaction_1._sender_address = "some_sender_address"

        self.transaction_1._amount_by_currency_id = {"1": 9}
        self.transaction_1._quantities_by_good_id = {"2": -1, "3": -2}
        assert self.agent_state.is_consistent_transaction(self.transaction_1) is True

    def test_is_consistent_transaction_fails_viii(self):
        """Test the is_consistent_transaction of AgentState class where it fails because inconsistent values."""
        self.transaction_1._amount_by_currency_id = {"1": -11}
        self.transaction_1._quantities_by_good_id = {"2": -1, "3": -2}
        assert self.agent_state.is_consistent_transaction(self.transaction_1) is False

    def test_apply(self):
        """Test the apply of AgentState class."""
        new_agent_state = self.agent_state.apply(
            [self.transaction_1, self.transaction_2]
        )
        assert new_agent_state.amount_by_currency_id == {"1": 11}
        assert new_agent_state.quantities_by_good_id == {"2": 1, "3": 2}

    def test_update_sender_i(self):
        """Test the update of AgentState class where agent is tx sender."""
        self.agent_state.update(self.transaction_1)
        assert self.agent_state.amount_by_currency_id == {"1": 20}
        assert self.agent_state.quantities_by_good_id == {"2": 0, "3": 0}

    def test_update_sender_ii(self):
        """Test the update of AgentState class where agent is tx sender."""
        self.agent_state.update(self.transaction_2)
        assert self.agent_state.amount_by_currency_id == {"1": 1}
        assert self.agent_state.quantities_by_good_id == {"2": 2, "3": 4}

    def test_update_counterparty_i(self):
        """Test the update of AgentState class where agent is tx counterparty."""
        # setup
        self.transaction_1._sender_address = "some_sender_address"
        self.transaction_1._counterparty_address = self.agent_address

        # operation
        self.agent_state.update(self.transaction_1)

        # after
        assert self.agent_state.amount_by_currency_id == {"1": 0}
        assert self.agent_state.quantities_by_good_id == {"2": 2, "3": 4}

    def test_update_counterparty_ii(self):
        """Test the update of AgentState class where agent is tx counterparty."""
        # setup
        self.transaction_2._sender_address = "some_sender_address"
        self.transaction_2._counterparty_address = self.agent_address

        # operation
        self.agent_state.update(self.transaction_2)

        # after
        assert self.agent_state.amount_by_currency_id == {"1": 19}
        assert self.agent_state.quantities_by_good_id == {"2": 0, "3": 0}

    def test__copy__(self):
        """Test the __copy__ of AgentState class."""
        new_agent_state = self.agent_state.__copy__()
        assert new_agent_state == self.agent_state

    def test__str__(self):
        """Test the __str__ of AgentState class."""
        agent_state_str = self.agent_state.__str__()
        assert agent_state_str == "AgentState{}".format(
            pprint.pformat(
                {
                    "agent_address": self.agent_state.agent_address,
                    "amount_by_currency_id": self.agent_state.amount_by_currency_id,
                    "exchange_params_by_currency_id": self.agent_state.exchange_params_by_currency_id,
                    "quantities_by_good_id": self.agent_state.quantities_by_good_id,
                    "utility_params_by_good_id": self.agent_state.utility_params_by_good_id,
                }
            )
        )

    def test__eq__(self):
        """Test the __eq__ of AgentState class."""
        another_agent_state = AgentState(
            self.agent_address,
            self.amount_by_currency_id,
            self.exchange_params_by_currency_id,
            self.quantities_by_good_id,
            self.utility_params_by_good_id,
        )

        assert self.agent_state.__eq__(another_agent_state) is True


class TestTransactions:
    """Test Initialization class of tac control."""

    @classmethod
    def setup(cls):
        """Setup the test class."""
        cls.transactions = Transactions()

    def test_simple_properties(self):
        """Test the properties of Game class."""
        assert self.transactions.confirmed == {}
        assert self.transactions.confirmed_per_agent == {}

    def test_add(self):
        """Test the add of Transactions class which succeeds."""
        ledger_id = "ethereum"
        sender_address = "some_agent_address"
        counterparty_address = "some_counterparty_address"
        tx_amount_by_currency_id = {"1": 10}
        tx_quantities_by_good_id = {"2": -1, "3": -2}
        is_sender_payable_tx_fee = True
        nonce = "some_nonce"
        fee_by_currency_id = {"1": 1}
        sender_signature = "some_sender_signature"
        counterparty_signature = "some_counterparty_signature"
        transaction = Transaction(
            ledger_id,
            sender_address,
            counterparty_address,
            tx_amount_by_currency_id,
            tx_quantities_by_good_id,
            is_sender_payable_tx_fee,
            nonce,
            fee_by_currency_id,
            sender_signature,
            counterparty_signature,
        )

        mocked_now = datetime.datetime.strptime("01 01 2020  00:01", "%d %m %Y %H:%M")

        datetime_mock = Mock(wraps=datetime.datetime)
        datetime_mock.now.return_value = mocked_now

        with patch("datetime.datetime", new=datetime_mock):
            self.transactions.add(transaction)

        assert self.transactions.confirmed[mocked_now] == transaction
        assert (
            self.transactions.confirmed_per_agent[sender_address][mocked_now]
            == transaction
        )
        assert (
            self.transactions.confirmed_per_agent[counterparty_address][mocked_now]
            == transaction
        )


class TestRegistration:
    """Test Registration class of tac control."""

    @classmethod
    def setup(cls):
        """Setup the test class."""
        cls.registration = Registration()

    def test_simple_properties(self):
        """Test the properties of Game class."""
        assert self.registration.agent_addr_to_name == {}
        assert self.registration.nb_agents == 0

    def test_register_agent(self):
        """Test the register_agent of Registration class which succeeds."""
        agent_addr = "some_agent_address"
        agent_name = "some_agent_name"

        self.registration.register_agent(agent_addr, agent_name)

        assert self.registration.agent_addr_to_name == {agent_addr: agent_name}
        assert self.registration.nb_agents == 1

    def test_unregister_agent(self):
        """Test the unregister_agent of Registration class which succeeds."""
        agent_addr = "some_agent_address"
        agent_name = "some_agent_name"

        self.registration.register_agent(agent_addr, agent_name)
        assert self.registration.agent_addr_to_name == {agent_addr: agent_name}
        assert self.registration.nb_agents == 1

        self.registration.unregister_agent(agent_addr)
        assert self.registration.agent_addr_to_name == {}
        assert self.registration.nb_agents == 0


class TestGame(BaseSkillTestCase):
    """Test Game class of tac control."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "tac_control")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.amount_by_currency_id = {"FET": 10}
        cls.exchange_params_by_currency_id = {"FET": 1.0}
        cls.quantities_by_good_id = {"G1": 1, "G2": 2}
        cls.utility_params_by_good_id = {"G1": 1.0, "G2": 1.5}
        cls.game = Game(name="Game", skill_context=cls._skill.skill_context)
        cls._skill.skill_context.parameters = Parameters(
            ledger_id="",
            contract_address=None,
            good_ids=[],
            currency_ids=[],
            min_nb_agents=2,
            money_endowment=200,
            nb_goods=9,
            nb_currencies=1,
            tx_fee=1,
            base_good_endowment=2,
            lower_bound_factor=1,
            upper_bound_factor=1,
            registration_start_time="01 01 2020  00:01",
            registration_timeout=60,
            item_setup_timeout=60,
            competition_timeout=300,
            inactivity_timeout=30,
            whitelist=[],
            location={"longitude": 0.1270, "latitude": 51.5194},
            service_data={"key": "tac", "value": "v1"},
            name="parameters",
            skill_context=cls._skill.skill_context,
        )
        cls.game._conf = "stub"

    def test_simple_properties(self):
        """Test the properties of Game class."""
        self.game._conf = None
        # phase
        assert self.game.phase == Phase.PRE_GAME

        with patch.object(self.game.context.logger, "log") as mock_logger:
            self.game.phase = Phase.GAME
        mock_logger.assert_any_call(logging.DEBUG, f"Game phase set to: {Phase.GAME}")
        assert self.game.phase == Phase.GAME

        # registration
        assert self.game.registration.nb_agents == 0
        assert self.game.registration.agent_addr_to_name == {}

        # conf
        with pytest.raises(
            AEAEnforceError, match="Call create before calling configuration."
        ):
            assert self.game.conf
        conf = Configuration(
            "some_version_id",
            1,
            {"ag_1_add": "ag_1", "ag_2_add": "ag_2"},
            {"FET": "fetch"},
            {"G_1": "good_1", "G_2": "good_2"},
        )
        self.game._conf = conf
        assert self.game.conf == conf

        # initialization
        with pytest.raises(
            AEAEnforceError, match="Call create before calling initialization."
        ):
            assert self.game.initialization
        init = Initialization({}, {}, {}, {}, {}, {}, {})
        self.game._initialization = init
        assert self.game.initialization == init

        # initial_agent_states
        with pytest.raises(
            AEAEnforceError, match="Call create before calling initial_agent_states."
        ):
            assert self.game.initial_agent_states
        ias = {}
        self.game._initial_agent_states = ias
        assert self.game.initial_agent_states == ias

        # current_agent_states
        with pytest.raises(
            AEAEnforceError, match="Call create before calling current_agent_states."
        ):
            assert self.game.current_agent_states
        cas = {}
        self.game._current_agent_states = cas
        assert self.game.current_agent_states == cas

        # transactions
        tx = Transactions()
        self.game._transactions = tx
        assert self.game.transactions == tx

        # is_allowed_to_mint
        assert self.game.is_allowed_to_mint is True
        self.game.is_allowed_to_mint = False
        assert self.game.is_allowed_to_mint is False

    def test_create_succeeds(self):
        """Test the create method of the Game class which succeeds."""
        self.game.phase = Phase.PRE_GAME
        with patch.object(self.game, "_generate") as mock_generate:
            self.game.create()

        assert self.game.phase == Phase.GAME_SETUP
        mock_generate.assert_called_once()

    def test_create_fails(self):
        """Test the create method of the Game class which fails because phase is Game."""
        self.game.phase = Phase.GAME
        with pytest.raises(AEAEnforceError, match="A game phase is already active."):
            with patch.object(self.game, "_generate"):
                self.game.create()

        assert self.game.phase == Phase.GAME

    def test_get_next_agent_state_for_minting(self):
        """Test the get_next_agent_state_for_minting method of the Game class."""
        agent_state = AgentState(
            "some_address_1",
            self.amount_by_currency_id,
            self.exchange_params_by_currency_id,
            self.quantities_by_good_id,
            self.utility_params_by_good_id,
        )
        self.game._initial_agent_states = {"ag1": agent_state}
        self.game._already_minted_agents = []

        actual_agent_state = self.game.get_next_agent_state_for_minting()
        assert actual_agent_state == agent_state

        self.game._already_minted_agents = ["ag1"]
        actual_agent_state = self.game.get_next_agent_state_for_minting()
        assert actual_agent_state is None

    def test_create_generate(self):
        """Test the _generate method of the Game class."""
        # before
        assert self.game._conf == "stub"
        assert self.game._initialization is None
        assert self.game._initial_agent_states is None
        assert self.game._current_agent_states is None

        agent_addr_1 = "some_agent_address_1"
        agent_name_1 = "some_agent_name_1"
        agent_addr_2 = "some_agent_address_2"
        agent_name_2 = "some_agent_name_2"
        self.game.registration.register_agent(agent_addr_1, agent_name_1)
        self.game.registration.register_agent(agent_addr_2, agent_name_2)

        # operation
        self.game._generate()

        # after
        assert self.game._conf != "stub"
        assert self.game.initialization is not None
        assert self.game._initial_agent_states is not None
        assert self.game._current_agent_states is not None

    def test_holdings_summary(self):
        """Test the holdings_summary method of the Game class."""
        # before
        agent_address_1 = "agent_address_1"
        agent_address_2 = "agent_address_2"

        self.game._conf = Configuration(
            "some_version_id",
            1,
            {agent_address_1: "agent_name_1", agent_address_2: "agent_name_2"},
            {"1": "currency_1"},
            {"2": "good_1", "3": "good_2"},
        )
        agent_state_1 = AgentState(
            agent_address_1,
            {"1": 10},
            {"1": 1.0},
            {"2": 1, "3": 2},
            {"2": 1.0, "3": 1.5},
        )
        agent_state_2 = AgentState(
            agent_address_2,
            {"1": 10},
            {"1": 1.0},
            {"2": 1, "3": 2},
            {"2": 1.0, "3": 1.5},
        )

        self.game._current_agent_states = {
            agent_address_1: agent_state_1,
            agent_address_2: agent_state_2,
        }
        expected_holding_summary = (
            "\nCurrent good & money allocation & score: \n"
            "- agent_name_1:\n"
            "    good_1: 1\n"
            "    good_2: 2\n"
            "    currency_1: 10\n"
            "    score: 21.55\n"
            "- agent_name_2:\n"
            "    good_1: 1\n"
            "    good_2: 2\n"
            "    currency_1: 10\n"
            "    score: 21.55\n\n"
        )

        # operation
        holding_summary = self.game.holdings_summary

        # after
        assert holding_summary == expected_holding_summary

    def test_equilibrium_summary(self):
        """Test the equilibrium_summary method of the Game class."""
        # before
        agent_address_1 = "agent_address_1"
        agent_address_2 = "agent_address_2"

        self.game._conf = Configuration(
            "some_version_id",
            1,
            {agent_address_1: "agent_name_1", agent_address_2: "agent_name_2"},
            {"1": "currency_1"},
            {"2": "good_1", "3": "good_2"},
        )

        self.game._initialization = Initialization(
            {agent_address_1: {"1": 10}, agent_address_2: {"1": 5}},
            {agent_address_1: {"1": 1.0}, agent_address_2: {"1": 1.5}},
            {agent_address_1: {"2": 5, "3": 7}, agent_address_2: {"2": 4, "3": 6}},
            {
                agent_address_1: {"2": 1.0, "3": 1.1},
                agent_address_2: {"2": 1.3, "3": 1.5},
            },
            {"2": 1.7, "3": 1.3},
            {
                agent_address_1: {"2": 1.2, "3": 1.1},
                agent_address_2: {"2": 1.1, "3": 1.4},
            },
            {agent_address_1: {"1": 1.1}, agent_address_2: {"1": 1.2}},
        )
        expected_equilibrium_summary = (
            "\nEquilibrium prices: \n"
            "good_1 1.7\n"
            "good_2 1.3\n\n"
            "Equilibrium good allocation: \n"
            "- agent_name_1:\n"
            "    good_1: 1.2\n"
            "    good_2: 1.1\n"
            "- agent_name_2:\n"
            "    good_1: 1.1\n"
            "    good_2: 1.4\n\n"
            "Equilibrium money allocation: \n"
            "- agent_name_1:\n"
            "    currency_1: 1.1\n"
            "- agent_name_2:\n"
            "    currency_1: 1.2\n\n"
        )
        # operation
        equilibrium_summary = self.game.equilibrium_summary

        # after
        assert equilibrium_summary == expected_equilibrium_summary

    def test_is_transaction_valid_succeeds(self):
        """Test the is_transaction_valid method of the Game class which succeeds."""
        # before
        agent_address_1 = "agent_address_1"
        agent_address_2 = "agent_address_2"

        tx = Transaction(
            "ethereum",
            agent_address_1,
            agent_address_2,
            {"1": 10},
            {"2": 5, "5": 10},
            True,
            "some_nonce",
            {"1": 1},
            "some_sender_signature",
            "some_counterparty_signature",
        )

        agent_state_1 = AgentState(
            agent_address_1,
            {"1": 10},
            {"1": 1.0},
            {"2": 1, "3": 2},
            {"2": 1.0, "3": 1.5},
        )
        agent_state_2 = AgentState(
            agent_address_2,
            {"1": 10},
            {"1": 1.0},
            {"2": 1, "3": 2},
            {"2": 1.0, "3": 1.5},
        )

        self.game._current_agent_states = {
            agent_address_1: agent_state_1,
            agent_address_2: agent_state_2,
        }

        # operation
        with patch.object(Transaction, "has_matching_signatures", return_value=True):
            with patch.object(
                AgentState, "is_consistent_transaction", return_value=True
            ):
                assert self.game.is_transaction_valid(tx) is True

    def test_is_transaction_valid_fails_not_matching_signatures(self):
        """Test the is_transaction_valid method of the Game class which fails because the signatures do no match."""
        # before
        agent_address_1 = "agent_address_1"
        agent_address_2 = "agent_address_2"

        tx = Transaction(
            "ethereum",
            agent_address_1,
            agent_address_2,
            {"1": 10},
            {"2": 5, "5": 10},
            True,
            "some_nonce",
            {"1": 1},
            "some_sender_signature",
            "some_counterparty_signature",
        )

        agent_state_1 = AgentState(
            agent_address_1,
            {"1": 10},
            {"1": 1.0},
            {"2": 1, "3": 2},
            {"2": 1.0, "3": 1.5},
        )
        agent_state_2 = AgentState(
            agent_address_2,
            {"1": 10},
            {"1": 1.0},
            {"2": 1, "3": 2},
            {"2": 1.0, "3": 1.5},
        )

        self.game._current_agent_states = {
            agent_address_1: agent_state_1,
            agent_address_2: agent_state_2,
        }

        # operation
        with patch.object(Transaction, "has_matching_signatures", return_value=False):
            with patch.object(
                AgentState, "is_consistent_transaction", return_value=True
            ):
                assert self.game.is_transaction_valid(tx) is False

    def test_is_transaction_valid_fails_tx_inconsistent(self):
        """Test the is_transaction_valid method of the Game class which fails because transactions are inconsistent."""
        # before
        agent_address_1 = "agent_address_1"
        agent_address_2 = "agent_address_2"

        tx = Transaction(
            "ethereum",
            agent_address_1,
            agent_address_2,
            {"1": 10},
            {"2": 5, "5": 10},
            True,
            "some_nonce",
            {"1": 1},
            "some_sender_signature",
            "some_counterparty_signature",
        )

        agent_state_1 = AgentState(
            agent_address_1,
            {"1": 10},
            {"1": 1.0},
            {"2": 1, "3": 2},
            {"2": 1.0, "3": 1.5},
        )
        agent_state_2 = AgentState(
            agent_address_2,
            {"1": 10},
            {"1": 1.0},
            {"2": 1, "3": 2},
            {"2": 1.0, "3": 1.5},
        )

        self.game._current_agent_states = {
            agent_address_1: agent_state_1,
            agent_address_2: agent_state_2,
        }

        # operation
        with patch.object(Transaction, "has_matching_signatures", return_value=True):
            with patch.object(
                AgentState, "is_consistent_transaction", return_value=False
            ):
                assert self.game.is_transaction_valid(tx) is False

    def test_settle_transaction_succeeds(self):
        """Test the settle_transaction method of the Game class which succeeds."""
        # setup
        agent_address_1 = "agent_address_1"
        agent_address_2 = "agent_address_2"

        tx = Transaction(
            "ethereum",
            agent_address_1,
            agent_address_2,
            {"1": 10},
            {"2": -1, "3": 0},
            True,
            "some_nonce",
            {"1": 1},
            "some_sender_signature",
            "some_counterparty_signature",
        )
        agent_state_1 = AgentState(
            agent_address_1,
            {"1": 10},
            {"1": 1.0},
            {"2": 1, "3": 2},
            {"2": 1.0, "3": 1.5},
        )
        agent_state_2 = AgentState(
            agent_address_2,
            {"1": 10},
            {"1": 1.0},
            {"2": 1, "3": 2},
            {"2": 1.0, "3": 1.5},
        )

        self.game._current_agent_states = {
            agent_address_1: agent_state_1,
            agent_address_2: agent_state_2,
        }

        expected_agent_state_1 = AgentState(
            agent_address_1,
            {"1": 20},
            {"1": 1.0},
            {"2": 0, "3": 2},
            {"2": 1.0, "3": 1.5},
        )
        expected_agent_state_2 = AgentState(
            agent_address_2,
            {"1": 0},
            {"1": 1.0},
            {"2": 2, "3": 2},
            {"2": 1.0, "3": 1.5},
        )

        # before
        assert self.game._current_agent_states[agent_address_1] == agent_state_1
        assert self.game._current_agent_states[agent_address_2] == agent_state_2

        # operation
        with patch.object(Transaction, "has_matching_signatures", return_value=True):
            self.game.settle_transaction(tx)

        # after
        assert (
            self.game._current_agent_states[agent_address_1] == expected_agent_state_1
        )
        assert (
            self.game._current_agent_states[agent_address_2] == expected_agent_state_2
        )

    def test_settle_transaction_fails_current_agent_states_is_none(self):
        """Test the settle_transaction method of the Game class which fails because current_agent_states is None."""
        # before
        agent_address_1 = "agent_address_1"
        agent_address_2 = "agent_address_2"

        tx = Transaction(
            "ethereum",
            agent_address_1,
            agent_address_2,
            {"1": 10},
            {"2": 5, "5": 10},
            True,
            "some_nonce",
            {"1": 1},
            "some_sender_signature",
            "some_counterparty_signature",
        )

        # operation
        with pytest.raises(
            AEAEnforceError, match="Call create before calling current_agent_states."
        ):
            assert self.game.settle_transaction(tx)

    def test_settle_transaction_fails_tx_invalid(self):
        """Test the settle_transaction method of the Game class which fails because transaction is invalid."""
        # before
        agent_address_1 = "agent_address_1"
        agent_address_2 = "agent_address_2"

        tx = Transaction(
            "ethereum",
            agent_address_1,
            agent_address_2,
            {"1": 10},
            {"2": 5, "5": 10},
            True,
            "some_nonce",
            {"1": 1},
            "some_sender_signature",
            "some_counterparty_signature",
        )
        self.game._current_agent_states = "some_current_agent_states"

        # operation
        with patch.object(self.game, "is_transaction_valid", return_value=False):
            with pytest.raises(AEAEnforceError, match="Transaction is not valid."):
                assert self.game.settle_transaction(tx)

    def test_get_location_description(self):
        """Test the get_location_description method of the Game class."""
        description = self.game.get_location_description()

        assert type(description) == Description
        assert description.data_model is AGENT_LOCATION_MODEL
        assert description.values.get("location", "") == Location(
            longitude=0.1270, latitude=51.5194
        )

    def test_get_register_tac_description(self):
        """Test the get_register_tac_description method of the Game class."""
        description = self.game.get_register_tac_description()

        assert type(description) == Description
        assert description.data_model is AGENT_SET_SERVICE_MODEL
        assert description.values.get("key", "") == "tac"
        assert description.values.get("value", "") == "v1"

    def test_get_register_personality_description(self):
        """Test the get_register_personality_description method of the GenericStrategy class."""
        description = self.game.get_register_personality_description()

        assert type(description) == Description
        assert description.data_model is AGENT_PERSONALITY_MODEL
        assert description.values.get("piece", "") == "genus"
        assert description.values.get("value", "") == "service"

    def test_get_register_classification_description(self):
        """Test the get_register_classification_description method of the GenericStrategy class."""
        description = self.game.get_register_classification_description()

        assert type(description) == Description
        assert description.data_model is AGENT_PERSONALITY_MODEL
        assert description.values.get("piece", "") == "classification"
        assert description.values.get("value", "") == "tac.controller"

    def test_get_unregister_tac_description(self):
        """Test the get_unregister_tac_description method of the Game class."""
        description = self.game.get_unregister_tac_description()

        assert type(description) == Description
        assert description.data_model is AGENT_REMOVE_SERVICE_MODEL
        assert description.values.get("key", "") == "tac"
