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

"""This test module contains the integration test for the weather skills."""

import sys

import pytest

from aea.test_tools.test_cases import AEATestCaseMany, UseOef


class TestMLSkills(AEATestCaseMany, UseOef):
    """Test that ml skills work."""

    @pytest.mark.skipif(
        sys.version_info >= (3, 8),
        reason="cannot run on 3.8 as tensorflow not installable",
    )
    def test_ml_skills(self, pytestconfig):
        """Run the ml skills sequence."""
        data_provider_aea_name = "ml_data_provider"
        model_trainer_aea_name = "ml_model_trainer"
        self.create_agents(data_provider_aea_name, model_trainer_aea_name)

        # prepare data provider agent
        self.set_agent_context(data_provider_aea_name)
        self.add_item("connection", "fetchai/oef:0.2.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/ml_data_provider:0.3.0")
        self.run_install()

        # prepare model trainer agent
        self.set_agent_context(model_trainer_aea_name)
        self.add_item("connection", "fetchai/oef:0.2.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/ml_train:0.3.0")
        self.run_install()

        self.set_agent_context(data_provider_aea_name)
        data_provider_aea_process = self.run_agent("--connections", "fetchai/oef:0.2.0")

        self.set_agent_context(model_trainer_aea_name)
        model_trainer_aea_process = self.run_agent("--connections", "fetchai/oef:0.2.0")

        check_strings = ("Got a Call for Terms", "Got an Accept", "a Data message:")
        missing_strings = self.missing_from_output(
            data_provider_aea_process, check_strings, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in data_provider_aea output.".format(
            missing_strings
        )

        check_strings = (
            "found agents=",
            "sending CFT to agent=",
            "Received terms message",
            "Received data message",
            "Loss:",
        )
        missing_strings = self.missing_from_output(
            model_trainer_aea_process, check_strings, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in model_trainer_aea output.".format(
            missing_strings
        )

        self.terminate_agents(data_provider_aea_process, model_trainer_aea_process)
        assert (
            self.is_successfully_terminated()
        ), "Agents weren't successfully terminated."


class TestMLSkillsFetchaiLedger(AEATestCaseMany, UseOef):
    """Test that ml skills work."""

    @pytest.mark.skipif(
        sys.version_info >= (3, 8),
        reason="cannot run on 3.8 as tensorflow not installable",
    )
    def test_ml_skills(self, pytestconfig):
        """Run the ml skills sequence."""
        data_provider_aea_name = "ml_data_provider"
        model_trainer_aea_name = "ml_model_trainer"
        self.create_agents(data_provider_aea_name, model_trainer_aea_name)

        ledger_apis = {"fetchai": {"network": "testnet"}}

        # prepare data provider agent
        self.set_agent_context(data_provider_aea_name)
        self.add_item("connection", "fetchai/oef:0.2.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/ml_data_provider:0.3.0")
        setting_path = "agent.ledger_apis"
        self.force_set_config(setting_path, ledger_apis)
        self.run_install()

        # prepare model trainer agent
        self.set_agent_context(model_trainer_aea_name)
        self.add_item("connection", "fetchai/oef:0.2.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/ml_train:0.3.0")
        setting_path = (
            "vendor.fetchai.skills.ml_train.models.strategy.args.is_ledger_tx"
        )
        self.set_config(setting_path, True, "bool")
        setting_path = "agent.ledger_apis"
        self.force_set_config(setting_path, ledger_apis)
        self.run_install()

        self.set_agent_context(data_provider_aea_name)
        data_provider_aea_process = self.run_agent("--connections", "fetchai/oef:0.2.0")

        self.set_agent_context(model_trainer_aea_name)
        model_trainer_aea_process = self.run_agent("--connections", "fetchai/oef:0.2.0")

        # TODO: finish test
        check_strings = ()  # "Got a Call for Terms",)  # "Got an Accept", "a Data message:")
        missing_strings = self.missing_from_output(
            data_provider_aea_process, check_strings, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in data_provider_aea output.".format(
            missing_strings
        )

        check_strings = (
            # "found agents=",
            # "sending CFT to agent=",
            # "Received terms message",
            # "Received data message",
            # "Loss:",
        )
        missing_strings = self.missing_from_output(
            model_trainer_aea_process, check_strings, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in model_trainer_aea output.".format(
            missing_strings
        )

        self.terminate_agents(data_provider_aea_process, model_trainer_aea_process)
        assert (
            self.is_successfully_terminated()
        ), "Agents weren't successfully terminated."
