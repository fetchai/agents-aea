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

import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from aea.exceptions import AEAEnforceError
from aea.helpers.search.models import Description, Location
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.skills.tac_control.game import (
    AGENT_LOCATION_MODEL,
    AGENT_REMOVE_SERVICE_MODEL,
    AGENT_SET_SERVICE_MODEL,
    AgentState,
    Configuration,
    Game,
    Initialization,
    Phase,
    Transactions,
)
from packages.fetchai.skills.tac_control.parameters import Parameters

from tests.conftest import ROOT_DIR


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
            location={"longitude": 51.5194, "latitude": 0.1270},
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

    def test_get_location_description(self):
        """Test the get_location_description method of the Game class."""
        description = self.game.get_location_description()

        assert type(description) == Description
        assert description.data_model is AGENT_LOCATION_MODEL
        assert description.values.get("location", "") == Location(0.1270, 51.5194)

    def test_get_register_tac_description(self):
        """Test the get_register_tac_description method of the Game class."""
        description = self.game.get_register_tac_description()

        assert type(description) == Description
        assert description.data_model is AGENT_SET_SERVICE_MODEL
        assert description.values.get("key", "") == "tac"
        assert description.values.get("value", "") == "v1"

    def test_get_unregister_tac_description(self):
        """Test the get_unregister_tac_description method of the Game class."""
        description = self.game.get_unregister_tac_description()

        assert type(description) == Description
        assert description.data_model is AGENT_REMOVE_SERVICE_MODEL
        assert description.values.get("key", "") == "tac"
