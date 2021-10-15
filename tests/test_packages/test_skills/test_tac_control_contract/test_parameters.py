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
"""This module contains the tests of the parameters module of the tac control contract skill."""

from pathlib import Path

from aea_ledger_ethereum import EthereumApi
from aea_ledger_fetchai import FetchAIApi

from aea.helpers.transaction.base import Terms
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.skills.tac_control_contract.parameters import Parameters

from tests.conftest import ROOT_DIR


class TestParameters(BaseSkillTestCase):
    """Test Parameters module of tac control contract."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "fetchai", "skills", "tac_control_contract"
    )

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.kwargs = {
            "ledger_id": "some_ledger_id",
            "contract_address": None,
            "good_ids": [],
            "currency_ids": [],
            "min_nb_agents": 2,
            "money_endowment": 200,
            "nb_goods": 9,
            "nb_currencies": 1,
            "tx_fee": 1,
            "base_good_endowment": 2,
            "lower_bound_factor": 1,
            "upper_bound_factor": 1,
            "registration_start_time": "01 01 2020  00:01",
            "registration_timeout": 60,
            "item_setup_timeout": 60,
            "competition_timeout": 300,
            "inactivity_timeout": 30,
            "whitelist": [],
            "location": {"longitude": 0.1270, "latitude": 51.5194},
            "service_data": {"key": "tac", "value": "v1"},
            "name": "parameters",
            "skill_context": cls._skill.skill_context,
        }
        cls.parameters = Parameters(**cls.kwargs)

    def test__init__(self):
        """Test the __init__ of Parameters."""
        assert self.parameters.nb_completed_minting == 0

    def test_get_deploy_terms(self):
        """Test the get_deploy_terms of Parameters."""
        self.parameters._ledger_id = FetchAIApi.identifier
        assert self.parameters.get_deploy_terms() == Terms(
            FetchAIApi.identifier,
            self.skill.skill_context.agent_address,
            self.skill.skill_context.agent_address,
            {},
            {},
            "",
            label="store",
        )

        self.parameters._ledger_id = FetchAIApi.identifier
        assert self.parameters.get_deploy_terms(True) == Terms(
            FetchAIApi.identifier,
            self.skill.skill_context.agent_address,
            self.skill.skill_context.agent_address,
            {},
            {},
            "",
            label="init",
        )

        self.parameters._ledger_id = EthereumApi.identifier
        assert self.parameters.get_deploy_terms() == Terms(
            EthereumApi.identifier,
            self.skill.skill_context.agent_address,
            self.skill.skill_context.agent_address,
            {},
            {},
            "",
            label="deploy",
        )

    def test_get_create_token_terms(self):
        """Test the get_create_token_terms of Parameters."""
        assert self.parameters.get_create_token_terms() == Terms(
            "some_ledger_id",
            self.skill.skill_context.agent_address,
            self.skill.skill_context.agent_address,
            {},
            {},
            "",
        )

    def test_get_mint_token_terms(self):
        """Test the get_mint_token_terms of Parameters."""
        assert self.parameters.get_mint_token_terms() == Terms(
            "some_ledger_id",
            self.skill.skill_context.agent_address,
            self.skill.skill_context.agent_address,
            {},
            {},
            "",
        )
