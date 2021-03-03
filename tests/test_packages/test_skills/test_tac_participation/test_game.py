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
"""This module contains the tests of the models of the tac participation skill."""

import logging
from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest

from aea.exceptions import AEAEnforceError
from aea.helpers.search.models import Constraint, ConstraintType, Location, Query
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.protocols.state_update.message import StateUpdateMessage
from packages.fetchai.protocols.tac.message import TacMessage
from packages.fetchai.skills.tac_participation.dialogues import (
    StateUpdateDialogues,
    TacDialogues,
)
from packages.fetchai.skills.tac_participation.game import Configuration, Game, Phase

from tests.conftest import ROOT_DIR


class TestConfiguration:
    """Test Configuration class of tac participation."""

    @classmethod
    def setup(cls):
        """Setup the test class."""
        cls.version_id = "some_version_id"
        cls.fee_by_currency_id = {"1": 1}
        cls.agent_addr_to_name = {
            "agent_address_1": "agent_name_1",
            "agent_address_2": "agent_name_2",
        }
        cls.good_id_to_name = {"3": "good_1", "4": "good_2"}
        cls.controller_addr = "some_controller_address"

        cls.configuration = Configuration(
            cls.version_id,
            cls.fee_by_currency_id,
            cls.agent_addr_to_name,
            cls.good_id_to_name,
            cls.controller_addr,
        )

    def test_simple_properties(self):
        """Test the properties of Game class."""
        assert self.configuration.version_id == self.version_id

        assert self.configuration.nb_agents == len(self.agent_addr_to_name)

        assert self.configuration.nb_goods == len(self.good_id_to_name)

        assert self.configuration.tx_fee == 1

        self.configuration._fee_by_currency_id = {"1": 1, "2": 2}
        with pytest.raises(AEAEnforceError, match="More than one currency id present!"):
            assert self.configuration.tx_fee
        self.configuration._fee_by_currency_id = self.fee_by_currency_id

        assert self.configuration.fee_by_currency_id == self.fee_by_currency_id

        assert self.configuration.agent_addr_to_name == self.agent_addr_to_name

        assert self.configuration.good_id_to_name == self.good_id_to_name

        assert self.configuration.agent_addresses == list(
            self.agent_addr_to_name.keys()
        )

        assert self.configuration.agent_names == list(self.agent_addr_to_name.values())

        assert self.configuration.good_ids == list(self.good_id_to_name.keys())

        assert self.configuration.good_names == list(self.good_id_to_name.values())

        assert self.configuration.controller_addr == self.controller_addr

    def test_check_consistency_succeeds(self):
        """Test the _check_consistency of Configuration class which succeeds."""
        self.configuration._check_consistency()

    def test_check_consistency_fails_i(self):
        """Test the _check_consistency of Configuration class which fails on version being None."""
        self.configuration._version_id = None
        with pytest.raises(AEAEnforceError, match="A version id must be set."):
            assert self.configuration._check_consistency()

    def test_check_consistency_fails_ii(self):
        """Test the _check_consistency of Configuration class which fails because _fee_by_currency_id has more than one currencies."""
        self.configuration._fee_by_currency_id = {"1": 1, "2": 2}
        with pytest.raises(AEAEnforceError, match="Tx fee must be non-negative."):
            assert self.configuration._check_consistency()

    def test_check_consistency_fails_iii(self):
        """Test the _check_consistency of Configuration class which fails because tx_fee < 0."""
        self.configuration._fee_by_currency_id = {"1": -5}
        with pytest.raises(AEAEnforceError, match="Tx fee must be non-negative."):
            assert self.configuration._check_consistency()

    def test_check_consistency_fails_iv(self):
        """Test the _check_consistency of Configuration class which fails because number of agents is less than 2."""
        incorrect_agent_addr_to_name = {"agent_address_1": "agent_name_1"}
        with pytest.raises(AEAEnforceError, match="Must have at least two agents."):
            Configuration(
                self.version_id,
                self.fee_by_currency_id,
                incorrect_agent_addr_to_name,
                self.good_id_to_name,
                self.controller_addr,
            )

    def test_check_consistency_fails_v(self):
        """Test the _check_consistency of Configuration class which fails because number of goods is less than 2."""
        incorrect_good_id_to_name = {"3": "good_1"}
        with pytest.raises(AEAEnforceError, match="Must have at least two goods."):
            Configuration(
                self.version_id,
                self.fee_by_currency_id,
                self.agent_addr_to_name,
                incorrect_good_id_to_name,
                self.controller_addr,
            )

    def test_check_consistency_fails_vi(self):
        """Test the _check_consistency of Configuration class which fails because number of goods is less than 2."""
        self.configuration._agent_addr_to_name = {"agent_address_1": "agent_name_1"}
        with pytest.raises(
            AEAEnforceError, match="There must be one address for each agent."
        ):
            self.configuration._check_consistency()

    def test_check_consistency_fails_vii(self):
        """Test the _check_consistency of Configuration class which fails because number of goods is less than 2."""
        incorrect_agent_addr_to_name = {
            "agent_address_1": "agent_name_1",
            "agent_address_2": "agent_name_1",
        }
        with pytest.raises(AEAEnforceError, match="Agents' names must be unique."):
            Configuration(
                self.version_id,
                self.fee_by_currency_id,
                incorrect_agent_addr_to_name,
                self.good_id_to_name,
                self.controller_addr,
            )

    def test_check_consistency_fails_viii(self):
        """Test the _check_consistency of Configuration class which fails because number of goods is less than 2."""
        self.configuration._good_id_to_name = {
            "3": "good_1",
            "4": "good_2",
            "5": "good_3",
        }
        with pytest.raises(
            AEAEnforceError, match="There must be one id for each good."
        ):
            self.configuration._check_consistency()

    def test_check_consistency_fails_ix(self):
        """Test the _check_consistency of Configuration class which fails because number of goods is less than 2."""
        incorrect_good_id_to_name = {"3": "good_1", "4": "good_1"}
        with pytest.raises(AEAEnforceError, match="Goods' names must be unique."):
            Configuration(
                self.version_id,
                self.fee_by_currency_id,
                self.agent_addr_to_name,
                incorrect_good_id_to_name,
                self.controller_addr,
            )


class TestGame(BaseSkillTestCase):
    """Test Game class of tac participation."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "tac_participation")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.expected_version_id = "v1"
        cls.expected_controller_addr = "some_controller_address"
        cls.search_query = {
            "search_key": "tac",
            "search_value": "v1",
            "constraint_type": "==",
        }
        cls.location = {"longitude": 0.1270, "latitude": 51.5194}
        cls.search_radius = 5.0
        cls.ledger_id = "some_ledger_id"
        cls.is_using_contract = False

        cls.game = Game(
            expected_version_id=cls.expected_version_id,
            expected_controller_addr=cls.expected_controller_addr,
            search_query=cls.search_query,
            location=cls.location,
            search_radius=cls.search_radius,
            ledger_id=cls.ledger_id,
            is_using_contract=cls.is_using_contract,
            name="game",
            skill_context=cls._skill.skill_context,
        )

    def test_simple_properties(self):
        """Test the properties of Game class."""
        assert self.game.ledger_id == self.ledger_id

        assert self.game.is_using_contract == self.is_using_contract

        assert self.game.expected_version_id == self.expected_version_id

        assert self.game.phase == Phase.PRE_GAME

        with pytest.raises(AEAEnforceError, match="Contract address not set!"):
            assert self.game.contract_address
        self.game.contract_address = "some_contract_address"
        assert self.game.contract_address == "some_contract_address"
        with pytest.raises(AEAEnforceError, match="Contract address already set!"):
            self.game.contract_address = "some_other_contract_address"

        with pytest.raises(AEAEnforceError, match="TacDialogue not set!"):
            assert self.game.tac_dialogue
        _, tac_dialogue = cast(
            TacDialogues, self.skill.skill_context.tac_dialogues
        ).create(
            counterparty="some_address",
            performative=TacMessage.Performative.REGISTER,
            agent_name="some_agent_name",
        )
        self.game.tac_dialogue = tac_dialogue
        assert self.game.tac_dialogue == tac_dialogue
        with pytest.raises(AEAEnforceError, match="TacDialogue already set!"):
            self.game.tac_dialogue = tac_dialogue

        with pytest.raises(AEAEnforceError, match="StateUpdateDialogue not set!"):
            assert self.game.state_update_dialogue
        _, state_update_dialogue = cast(
            StateUpdateDialogues, self.skill.skill_context.state_update_dialogues
        ).create(
            counterparty="some_address",
            performative=StateUpdateMessage.Performative.INITIALIZE,
            exchange_params_by_currency_id={"some_currency_id": 1.0},
            utility_params_by_good_id={"some_good_id": 2.0},
            amount_by_currency_id={"some_currency_id": 10},
            quantities_by_good_id={"some_good_id": 5},
        )
        self.game.state_update_dialogue = state_update_dialogue
        assert self.game.state_update_dialogue == state_update_dialogue
        with pytest.raises(AEAEnforceError, match="StateUpdateDialogue already set!"):
            self.game.state_update_dialogue = state_update_dialogue

        assert self.game.expected_controller_addr == self.expected_controller_addr
        self.game._expected_controller_addr = None
        with pytest.raises(
            AEAEnforceError, match="Expected controller address not assigned!"
        ):
            assert self.game.expected_controller_addr

        with pytest.raises(AEAEnforceError, match="Game configuration not assigned!"):
            assert self.game.conf
        configuration = Configuration(
            "some_version_id",
            {"1": 1},
            {"agent_address_1": "agent_name_1", "agent_address_2": "agent_name_2"},
            {"3": "good_1", "4": "good_2"},
            "some_controller_address",
        )
        self.game._conf = configuration
        assert self.game.conf == configuration

    def test_init_succeeds(self):
        """Test the init method of the Game class which succeeds."""
        fee_by_currency_id = {"1": 1}
        agent_addr_to_name = {
            "some_address_1": "some_name_1",
            "some_address_2": "some_name_2",
        }
        good_id_to_name = {"2": "good_2", "3": "good_3"}
        tac_message = cast(
            TacMessage,
            self.build_incoming_message(
                message_type=TacMessage,
                performative=TacMessage.Performative.GAME_DATA,
                amount_by_currency_id={"1": 10},
                exchange_params_by_currency_id={"1": 1.0},
                quantities_by_good_id={"2": 10, "3": 11},
                utility_params_by_good_id={"2": 1.2, "3": 1.1},
                fee_by_currency_id=fee_by_currency_id,
                agent_addr_to_name=agent_addr_to_name,
                currency_id_to_name={"1": "FETCH"},
                good_id_to_name=good_id_to_name,
                version_id=self.expected_version_id,
            ),
        )

        self.game.init(tac_message, self.expected_controller_addr)

        assert self.game.conf is not None
        assert self.game.conf.version_id == self.expected_version_id
        assert self.game.conf.fee_by_currency_id == fee_by_currency_id
        assert self.game.conf.agent_addr_to_name == agent_addr_to_name
        assert self.game.conf.good_id_to_name == good_id_to_name
        assert self.game.conf.controller_addr == self.expected_controller_addr

    def test_init_fails_i(self):
        """Test the init method of the Game class which fails because performative is NOT GAME_DATA."""
        tac_message = cast(
            TacMessage,
            self.build_incoming_message(
                message_type=TacMessage,
                performative=TacMessage.Performative.REGISTER,
                agent_name="some_agent_name",
            ),
        )

        with pytest.raises(
            AEAEnforceError, match="Wrong TacMessage for initialization of TAC game."
        ):
            self.game.init(tac_message, self.expected_controller_addr)

    def test_init_fails_ii(self):
        """Test the init method of the Game class which fails because controller address is incorrect."""
        fee_by_currency_id = {"1": 1}
        agent_addr_to_name = {
            "some_address_1": "some_name_1",
            "some_address_2": "some_name_2",
        }
        good_id_to_name = {"2": "good_2", "3": "good_3"}
        incorrect_controller_addr = "some_other_controller_address"
        tac_message = cast(
            TacMessage,
            self.build_incoming_message(
                message_type=TacMessage,
                performative=TacMessage.Performative.GAME_DATA,
                amount_by_currency_id={"1": 10},
                exchange_params_by_currency_id={"1": 1.0},
                quantities_by_good_id={"2": 10, "3": 11},
                utility_params_by_good_id={"2": 1.2, "3": 1.1},
                fee_by_currency_id=fee_by_currency_id,
                agent_addr_to_name=agent_addr_to_name,
                currency_id_to_name={"1": "FETCH"},
                good_id_to_name=good_id_to_name,
                version_id=self.expected_version_id,
            ),
        )

        with pytest.raises(
            AEAEnforceError, match="TacMessage from unexpected controller."
        ):
            self.game.init(tac_message, incorrect_controller_addr)

    def test_init_fails_iii(self):
        """Test the init method of the Game class which fails because version id is incorrect."""
        fee_by_currency_id = {"1": 1}
        agent_addr_to_name = {
            "some_address_1": "some_name_1",
            "some_address_2": "some_name_2",
        }
        good_id_to_name = {"2": "good_2", "3": "good_3"}
        incorrect_version_id = "some_other_version_id"
        tac_message = cast(
            TacMessage,
            self.build_incoming_message(
                message_type=TacMessage,
                performative=TacMessage.Performative.GAME_DATA,
                amount_by_currency_id={"1": 10},
                exchange_params_by_currency_id={"1": 1.0},
                quantities_by_good_id={"2": 10, "3": 11},
                utility_params_by_good_id={"2": 1.2, "3": 1.1},
                fee_by_currency_id=fee_by_currency_id,
                agent_addr_to_name=agent_addr_to_name,
                currency_id_to_name={"1": "FETCH"},
                good_id_to_name=good_id_to_name,
                version_id=incorrect_version_id,
            ),
        )

        with pytest.raises(AEAEnforceError, match="TacMessage for unexpected game."):
            self.game.init(tac_message, self.expected_controller_addr)

    def test_update_expected_controller_addr(self):
        """Test the update_expected_controller_addr method of the Game class."""
        new_contract_address = "some_different_controller_address"
        with patch.object(self.skill.skill_context.logger, "log") as mock_logger:
            self.game.update_expected_controller_addr(new_contract_address)

        mock_logger.assert_any_call(
            logging.WARNING,
            "TAKE CARE! Circumventing controller identity check! For added security provide the expected controller key as an argument to the Game instance "
            "and check against it.",
        )
        assert self.game.expected_controller_addr == new_contract_address

    def test_update_game_phase(self):
        """Test the update_game_phase method of the Game class."""
        assert self.game.phase == Phase.PRE_GAME
        self.game.update_game_phase(Phase.GAME)
        assert self.game.phase == Phase.GAME

    def test_get_game_query(self):
        """Test the get_game_query method of the Game class."""
        expected_location = Location(
            latitude=self.location["latitude"], longitude=self.location["longitude"]
        )
        expected_query = Query(
            [
                Constraint(
                    "location",
                    ConstraintType("distance", (expected_location, self.search_radius)),
                ),
                Constraint(
                    self.search_query["search_key"],
                    ConstraintType(
                        self.search_query["constraint_type"],
                        self.search_query["search_value"],
                    ),
                ),
            ],
        )

        actual_query = self.game.get_game_query()
        assert actual_query == expected_query
