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
"""This module contains the tests of the parameters module of the tac control skill."""

import datetime
import logging
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from aea.exceptions import AEAEnforceError
from aea.helpers.search.models import Location
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.skills.tac_control.parameters import Parameters

from tests.conftest import ROOT_DIR


class TestParameters(BaseSkillTestCase):
    """Test Parameters module of tac control."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "tac_control")

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

    @staticmethod
    def _time(date_time: str):
        return datetime.datetime.strptime(date_time, "%d %m %Y %H:%M")

    def test_init_now_after_start(self):
        """Test the init of Parameters where now is after the registration_start_time."""
        mocked_start_time = self._time("01 01 2020 00:01")
        mocked_now_time = self._time("01 01 2020 00:02")

        datetime_mock = Mock(wraps=datetime.datetime)
        datetime_mock.now.return_value = mocked_now_time

        with patch("datetime.datetime", new=datetime_mock):
            with patch.object(self.parameters.context.logger, "log") as mocked_logger:
                Parameters(**self.kwargs)
        mocked_logger.assert_any_call(
            logging.WARNING,
            f"TAC registration start time {mocked_start_time} is in the past! Deregistering skill.",
        )
        assert self.skill.skill_context.is_active is False

    def test_init_now_before_start(self):
        """Test the init of Parameters where now is before the registration_start_time."""
        mocked_start_time_str = "01 01 2020  00:03"

        mocked_start_time = self._time(mocked_start_time_str)
        mocked_now_time = self._time("01 01 2020  00:02")

        datetime_mock = Mock(wraps=datetime.datetime)
        datetime_mock.now.return_value = mocked_now_time

        self.kwargs["registration_start_time"] = mocked_start_time_str

        with patch("datetime.datetime", new=datetime_mock):
            with patch.object(self.parameters.context.logger, "log") as mocked_logger:
                par = Parameters(**self.kwargs)
        mocked_logger.assert_any_call(
            logging.INFO,
            f"TAC registation start time: {mocked_start_time}, and registration end time: {par.registration_end_time}, and start time: "
            f"{par.start_time}, "
            f"and end time: {par.end_time}",
        )

    def test_simple_properties(self):
        """Test the properties of Parameters class."""
        # phase
        assert self.parameters.ledger_id == "some_ledger_id"

        self.parameters._contract_address = None
        with pytest.raises(AEAEnforceError, match="No contract address provided."):
            assert self.parameters.contract_address

        self.parameters.contract_address = "some_contract_address"
        assert self.parameters.contract_address == "some_contract_address"

        with pytest.raises(AEAEnforceError, match="Contract address already provided."):
            self.parameters.contract_address = "some_contract_address"

        assert self.parameters.contract_id == self.parameters._contract_id

        assert self.parameters.is_contract_deployed is True
        self.parameters._contract_address = None
        assert self.parameters.is_contract_deployed is False

        assert self.parameters.registration_end_time == datetime.datetime.strptime(
            "01 01 2020  00:02", "%d %m %Y %H:%M"
        )

        assert self.parameters.inactivity_timeout == 30

        assert self.parameters.agent_location == {
            "location": Location(latitude=51.5194, longitude=0.1270)
        }
        assert self.parameters.set_service_data == {"key": "tac", "value": "v1"}
        assert self.parameters.set_personality_data == {
            "piece": "genus",
            "value": "service",
        }
        assert self.parameters.set_classification == {
            "piece": "classification",
            "value": "tac.controller",
        }
        assert self.parameters.remove_service_data == {"key": "tac"}
        assert self.parameters.simple_service_data == {"tac": "v1"}

    def test_init_inconsistent(self):
        """Test the __init__ of the Parameters class where _check_consistency raises an exception."""
        self.kwargs["contract_address"] = "some_contract_address"
        error_message = "If the contract address is set, then good ids and currency id must be provided and consistent."

        with pytest.raises(ValueError, match=error_message):
            assert Parameters(**self.kwargs,)
