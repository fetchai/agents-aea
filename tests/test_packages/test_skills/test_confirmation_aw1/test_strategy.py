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
"""This module contains the tests of the strategy class of the confirmation aw1 skill."""

import logging
from pathlib import Path
from typing import cast
from unittest.mock import patch

from aea.crypto.ledger_apis import LedgerApis
from aea.helpers.transaction.base import Terms
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.skills.confirmation_aw1.registration_db import RegistrationDB
from packages.fetchai.skills.confirmation_aw1.strategy import (
    DEVELOPER_ONLY_REQUIRED_KEYS,
    PUBLIC_ID,
    REQUIRED_KEYS,
    Strategy,
)

from tests.conftest import ROOT_DIR


class TestStrategy(BaseSkillTestCase):
    """Test Strategy of confirmation aw1."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "confirmation_aw1")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.token_denomination = "atestfet"
        cls.token_dispense_amount = 100000
        cls.fetchai_staking_contract_address = (
            "0x351bac612b50e87b46e4b10a282f632d41397de2"
        )
        cls.override_staking_check = False
        cls.awx_aeas = []
        cls.strategy = Strategy(
            token_denomination=cls.token_denomination,
            token_dispense_amount=cls.token_dispense_amount,
            fetchai_staking_contract_address=cls.fetchai_staking_contract_address,
            override_staking_check=cls.override_staking_check,
            awx_aeas=cls.awx_aeas,
            name="strategy",
            skill_context=cls._skill.skill_context,
        )

        cls.address = "some_address"
        cls.info = {
            "ethereum_address": "some_value",
            "signature_of_ethereum_address": "some_signature_of_ethereum_address",
            "signature_of_fetchai_address": "some_signature_of_fetchai_address",
            "developer_handle": "some_developer_handle",
            "tweet": "some_tweet",
        }
        cls.logger = cls._skill.skill_context.logger
        cls.db = cast(RegistrationDB, cls._skill.skill_context.registration_db)

    def test__init__(self):
        """Test the __init__ of Strategy class."""
        assert self.strategy._is_ready_to_register is False
        assert self.strategy._is_registered is False
        assert self.strategy.is_registration_pending is False
        assert self.strategy.signature_of_ethereum_address is None
        assert self.strategy._ledger_id == self.skill.skill_context.default_ledger_id
        assert self.strategy._max_tx_fee == 100
        assert self.strategy._contract_ledger_id == "ethereum"
        assert self.strategy._contract_callable == "get_stake"
        assert self.strategy._contract_id == str(PUBLIC_ID)
        assert self.strategy._in_process_registrations == {}

    def test_properties(self):
        """Test the properties of Strategy class."""
        assert self.strategy.contract_id == self.strategy._contract_id
        assert self.strategy.contract_address == self.fetchai_staking_contract_address
        assert self.strategy.contract_ledger_id == self.strategy._contract_ledger_id
        assert self.strategy.contract_callable == self.strategy._contract_callable
        assert self.strategy.awx_aeas == self.awx_aeas
        assert self.strategy.all_registered_aeas == []

    def test_lock_registration_temporarily(self):
        """Test the lock_registration_temporarily method of the Strategy class."""
        # before
        assert self.address not in self.strategy._in_process_registrations

        # operation
        self.strategy.lock_registration_temporarily(self.address, self.info)

        # after
        assert self.strategy._in_process_registrations[self.address] == self.info

    def test_finalize_registration_i(self):
        """Test the finalize_registration method of the Strategy class where NOT developer_only_mode."""
        # setup
        self.strategy.developer_handle_only = False
        self.strategy.lock_registration_temporarily(self.address, self.info)

        # operation
        with patch.object(self.db, "set_registered") as mock_set:
            with patch.object(self.logger, "log") as mock_logger:
                self.strategy.finalize_registration(self.address)

        # after
        assert self.address not in self.strategy._in_process_registrations

        mock_logger.assert_any_call(
            logging.INFO,
            f"finalizing registration for address={self.address}, info={self.info}",
        )

        mock_set.assert_any_call(
            address=self.address,
            ethereum_address=self.info["ethereum_address"],
            ethereum_signature=self.info["signature_of_ethereum_address"],
            fetchai_signature=self.info["signature_of_fetchai_address"],
            developer_handle=self.info["developer_handle"],
            tweet=self.info.get("tweet", ""),
        )

    def test_finalize_registration_ii(self):
        """Test the finalize_registration method of the Strategy class where IS developer_only_mode."""
        # setup
        self.strategy.developer_handle_only = True
        self.strategy.lock_registration_temporarily(self.address, self.info)

        # operation
        with patch.object(self.db, "set_registered_developer_only") as mock_set:
            with patch.object(self.logger, "log") as mock_logger:
                self.strategy.finalize_registration(self.address)

        # after
        assert self.address not in self.strategy._in_process_registrations

        mock_logger.assert_any_call(
            logging.INFO,
            f"finalizing registration for address={self.address}, info={self.info}",
        )

        mock_set.assert_any_call(
            address=self.address, developer_handle=self.info["developer_handle"],
        )

    def test_unlock_registration(self):
        """Test the unlock_registration method of the Strategy class."""
        # setup
        self.strategy.lock_registration_temporarily(self.address, self.info)

        # before
        assert self.address in self.strategy._in_process_registrations

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.strategy.unlock_registration(self.address)

        # after
        assert self.address not in self.strategy._in_process_registrations

        mock_logger.assert_any_call(
            logging.INFO,
            f"registration info did not pass staking checks = {self.info}",
        )

    def test_get_developer_handle(self):
        """Test the get_developer_handle method of the Strategy class."""
        # operation
        with patch.object(self.db, "get_developer_handle") as mock_get:
            self.strategy.get_developer_handle(self.address)

        # after
        mock_get.assert_any_call(self.address)

    def test_valid_registration_succeeds(self):
        """Test the valid_registration method of the Strategy class which succeeds."""
        # setup
        registration_info = {
            "ethereum_address": "some_ethereum_address",
            "fetchai_address": self.address,
            "signature_of_ethereum_address": "some_signature_of_ethereum_address",
            "signature_of_fetchai_address": "some_signature_of_fetchai_address",
            "developer_handle": "some_developer_handle",
        }

        # operation
        with patch.object(
            self.strategy, "_valid_signature", return_value=True
        ) as mock_valid:
            with patch.object(self.db, "is_registered", return_value=False) as mock_is:
                is_valid, code, msg = self.strategy.valid_registration(
                    registration_info, self.address
                )

        # after
        mock_is.assert_called_once()
        mock_valid.assert_called()

        assert is_valid
        assert code == 0
        assert msg == "all good!"

    def test_valid_registration_fails_i(self):
        """Test the valid_registration method of the Strategy class which fails because some key is missing."""
        # setup
        incorrect_registration_info = {
            "ethereum_address": "some_ethereum_address",
            "fetchai_address": self.address,
            "signature_of_ethereum_address": "some_signature_of_ethereum_address",
            "signature_of_fetchai_address": "some_signature_of_fetchai_address",
        }

        # operation
        is_valid, code, msg = self.strategy.valid_registration(
            incorrect_registration_info, self.address
        )

        # after
        assert not is_valid
        assert code == 1
        assert msg == f"missing keys in registration info, required: {REQUIRED_KEYS}!"

    def test_valid_registration_fails_ii(self):
        """Test the valid_registration method of the Strategy class which fails because addresses do not match."""
        # setup
        different_addres = "some_other_address"
        incorrect_registration_info = {
            "ethereum_address": "some_ethereum_address",
            "fetchai_address": different_addres,
            "signature_of_ethereum_address": "some_signature_of_ethereum_address",
            "signature_of_fetchai_address": "some_signature_of_fetchai_address",
            "developer_handle": "some_developer_handle",
        }

        # operation
        is_valid, code, msg = self.strategy.valid_registration(
            incorrect_registration_info, self.address
        )

        # after
        assert not is_valid
        assert code == 1
        assert msg == "fetchai address of agent and registration info do not match!"

    def test_valid_registration_fails_iii(self):
        """Test the valid_registration method of the Strategy class which fails because _valid_signature returns False for first call."""
        # setup
        incorrect_registration_info = {
            "ethereum_address": "some_ethereum_address",
            "fetchai_address": self.address,
            "signature_of_ethereum_address": "some_signature_of_ethereum_address",
            "signature_of_fetchai_address": "some_signature_of_fetchai_address",
            "developer_handle": "some_developer_handle",
        }

        # operation
        with patch.object(
            self.strategy, "_valid_signature", return_value=False
        ) as mock_valid:
            is_valid, code, msg = self.strategy.valid_registration(
                incorrect_registration_info, self.address
            )

        # after
        mock_valid.assert_called_once()

        assert not is_valid
        assert code == 1
        assert msg == "fetchai address and signature do not match!"

    def test_valid_registration_fails_iv(self):
        """Test the valid_registration method of the Strategy class which fails because _valid_signature returns False for second call."""
        # setup
        incorrect_registration_info = {
            "ethereum_address": "some_ethereum_address",
            "fetchai_address": self.address,
            "signature_of_ethereum_address": "some_signature_of_ethereum_address",
            "signature_of_fetchai_address": "some_signature_of_fetchai_address",
            "developer_handle": "some_developer_handle",
        }

        # operation
        with patch.object(
            self.strategy, "_valid_signature", side_effect=[True, False]
        ) as mock_valid:
            is_valid, code, msg = self.strategy.valid_registration(
                incorrect_registration_info, self.address
            )

        # after
        mock_valid.assert_called()

        assert not is_valid
        assert code == 1
        assert msg == "ethereum address and signature do not match!"

    def test_valid_registration_fails_v(self):
        """Test the valid_registration method of the Strategy class which fails because no developer_handle was provided."""
        # setup
        incorrect_registration_info = {
            "ethereum_address": "some_ethereum_address",
            "fetchai_address": self.address,
            "signature_of_ethereum_address": "some_signature_of_ethereum_address",
            "signature_of_fetchai_address": "some_signature_of_fetchai_address",
            "developer_handle": "",
        }

        # operation
        is_valid, code, msg = self.strategy.valid_registration(
            incorrect_registration_info, self.address
        )

        # after
        assert not is_valid
        assert code == 1
        assert msg == "missing developer_handle!"

    def test_valid_registration_fails_vi(self):
        """Test the valid_registration method of the Strategy class which fails because agent registration is in progress."""
        # setup
        registration_info = {
            "ethereum_address": "some_ethereum_address",
            "fetchai_address": self.address,
            "signature_of_ethereum_address": "some_signature_of_ethereum_address",
            "signature_of_fetchai_address": "some_signature_of_fetchai_address",
            "developer_handle": "some_developer_handle",
        }
        self.strategy.lock_registration_temporarily(self.address, self.info)

        # operation
        is_valid, code, msg = self.strategy.valid_registration(
            registration_info, self.address
        )

        # after
        assert not is_valid
        assert code == 1
        assert msg == "registration in process for this address!"

    def test_valid_registration_fails_vii(self):
        """Test the valid_registration method of the Strategy class which fails because agent already registered."""
        # setup
        registration_info = {
            "ethereum_address": "some_ethereum_address",
            "fetchai_address": self.address,
            "signature_of_ethereum_address": "some_signature_of_ethereum_address",
            "signature_of_fetchai_address": "some_signature_of_fetchai_address",
            "developer_handle": "some_developer_handle",
        }

        # operation
        with patch.object(self.db, "is_registered", return_value=True) as mock_is:
            is_valid, code, msg = self.strategy.valid_registration(
                registration_info, self.address
            )

        # after
        mock_is.assert_called_once()

        assert not is_valid
        assert code == 1
        assert msg == "already registered!"

    def test_valid_registration_fails_developer_only_mode_i(self):
        """Test the valid_registration method of the Strategy class in developer_only_mode which fails because some key is missing."""
        # setup
        self.strategy.developer_handle_only = True
        incorrect_registration_info = {
            "fetchai_address": self.address,
        }

        # operation
        is_valid, code, msg = self.strategy.valid_registration(
            incorrect_registration_info, self.address
        )

        # after
        assert not is_valid
        assert code == 1
        assert (
            msg
            == f"missing keys in registration info, required: {DEVELOPER_ONLY_REQUIRED_KEYS}!"
        )

    def test_valid_registration_fails_developer_only_mode_ii(self):
        """Test the valid_registration method of the Strategy class which fails because addresses do not match."""
        # setup
        self.strategy.developer_handle_only = True
        different_addres = "some_other_address"
        incorrect_registration_info = {
            "fetchai_address": different_addres,
            "developer_handle": "some_developer_handle",
        }

        # operation
        is_valid, code, msg = self.strategy.valid_registration(
            incorrect_registration_info, self.address
        )

        # after
        assert not is_valid
        assert code == 1
        assert msg == "fetchai address of agent and registration info do not match!"

    def test__valid_signature_i(self):
        """Test the _valid_signature method of the Strategy class where result is True."""
        # setup
        expected_signer = "some_expected_signer"
        signature = "some_signature"
        message_str = "some_message_str"
        ledger_id = "some_ledger_id"

        # operation
        with patch.object(
            LedgerApis, "recover_message", return_value=(expected_signer,)
        ) as mock_recover:
            is_valid = self.strategy._valid_signature(
                expected_signer, signature, message_str, ledger_id
            )

        # after
        mock_recover.assert_called_once()
        assert is_valid

    def test__valid_signature_ii(self):
        """Test the _valid_signature method of the Strategy class where result is False."""
        # setup
        expected_signer = "some_expected_signer"
        signature = "some_signature"
        message_str = "some_message_str"
        ledger_id = "some_ledger_id"

        # operation
        with patch.object(
            LedgerApis, "recover_message", return_value=("some_other_signer",)
        ) as mock_recover:
            is_valid = self.strategy._valid_signature(
                expected_signer, signature, message_str, ledger_id
            )

        # after
        mock_recover.assert_called_once()
        assert not is_valid

    def test__valid_signature_iii(self):
        """Test the _valid_signature method of the Strategy class where an exception is raised."""
        # setup
        expected_signer = "some_expected_signer"
        signature = "some_signature"
        message_str = "some_message_str"
        ledger_id = "some_ledger_id"

        exception_message = "some_exception_message"

        # operation
        with patch.object(
            LedgerApis, "recover_message", side_effect=Exception(exception_message)
        ) as mock_recover:
            with patch.object(self.logger, "log") as mock_logger:
                is_valid = self.strategy._valid_signature(
                    expected_signer, signature, message_str, ledger_id
                )

        # after
        mock_recover.assert_called_once()
        mock_logger.assert_any_call(
            logging.WARNING, f"Signing exception: {exception_message}",
        )
        assert not is_valid

    def test_get_terms(self):
        """Test the get_terms method of the Strategy class."""
        # setup
        counterparty = "some_counterparty"
        expected_terms = Terms(
            ledger_id=self.strategy._ledger_id,
            sender_address=self.skill.skill_context.agent_address,
            counterparty_address=counterparty,
            amount_by_currency_id={
                self.token_denomination: -self.token_dispense_amount
            },
            quantities_by_good_id={},
            is_sender_payable_tx_fee=True,
            nonce="some",
            fee_by_currency_id={self.token_denomination: self.strategy._max_tx_fee},
        )

        # operation
        actual_terms = self.strategy.get_terms(counterparty)

        # after
        assert actual_terms == expected_terms

    def test_get_kwargs(self):
        """Test the get_kwargs method of the Strategy class."""
        # setup
        expected_kwargs = {"address": self.info["ethereum_address"]}

        # operation
        actual_kwargs = self.strategy.get_kwargs(self.info)

        # after
        assert actual_kwargs == expected_kwargs

    def test_has_staked_i(self):
        """Test the get_kwargs method of the Strategy class where _override_staking_check is False and stake value is greater than 0."""
        # setup
        state = {"stake": "100"}

        # operation
        has_staked = self.strategy.has_staked(state)

        # after
        assert has_staked is True

    def test_has_staked_ii(self):
        """Test the get_kwargs method of the Strategy class where _override_staking_check is False and stake value is 0."""
        # setup
        state = {"stake": "0"}

        # operation
        has_staked = self.strategy.has_staked(state)

        # after
        assert has_staked is False

    def test_has_staked_iii(self):
        """Test the get_kwargs method of the Strategy class where _override_staking_check is True."""
        # setup
        self.strategy._override_staking_check = True
        state = {"stake": "100"}

        # operation
        has_staked = self.strategy.has_staked(state)

        # after
        assert has_staked is True
