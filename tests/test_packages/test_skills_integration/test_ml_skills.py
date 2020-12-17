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
from random import uniform

import pytest

from aea.test_tools.test_cases import AEATestCaseMany

from packages.fetchai.connections.p2p_libp2p.connection import LIBP2P_SUCCESS_MESSAGE

from tests.conftest import (
    COSMOS,
    COSMOS_PRIVATE_KEY_FILE_CONNECTION,
    FETCHAI,
    FETCHAI_PRIVATE_KEY_FILE,
    MAX_FLAKY_RERUNS_INTEGRATION,
    NON_FUNDED_COSMOS_PRIVATE_KEY_1,
    NON_GENESIS_CONFIG,
    wait_for_localhost_ports_to_close,
)


def _is_not_tensorflow_installed():
    try:
        import tensorflow  # noqa

        return False
    except ImportError:
        return True


@pytest.mark.integration
class TestMLSkills(AEATestCaseMany):
    """Test that ml skills work."""

    @pytest.mark.flaky(
        reruns=MAX_FLAKY_RERUNS_INTEGRATION
    )  # cause possible network issues
    @pytest.mark.skipif(
        _is_not_tensorflow_installed(), reason="This test requires Tensorflow.",
    )
    def test_ml_skills(self, pytestconfig):
        """Run the ml skills sequence."""
        data_provider_aea_name = "ml_data_provider"
        model_trainer_aea_name = "ml_model_trainer"
        self.create_agents(data_provider_aea_name, model_trainer_aea_name)

        default_routing = {
            "fetchai/ledger_api:0.8.0": "fetchai/ledger:0.11.0",
            "fetchai/oef_search:0.11.0": "fetchai/soef:0.14.0",
        }

        # generate random location
        location = {
            "latitude": round(uniform(-90, 90), 2),  # nosec
            "longitude": round(uniform(-180, 180), 2),  # nosec
        }

        # prepare data provider agent
        self.set_agent_context(data_provider_aea_name)
        self.add_item("connection", "fetchai/p2p_libp2p:0.13.0")
        self.add_item("connection", "fetchai/soef:0.14.0")
        self.remove_item("connection", "fetchai/stub:0.13.0")
        self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.13.0")
        self.add_item("connection", "fetchai/ledger:0.11.0")
        self.add_item("skill", "fetchai/ml_data_provider:0.17.0")
        setting_path = (
            "vendor.fetchai.skills.ml_data_provider.models.strategy.args.is_ledger_tx"
        )
        self.set_config(setting_path, False, "bool")
        setting_path = "agent.default_routing"
        self.nested_set_config(setting_path, default_routing)
        self.run_install()

        # add keys
        self.generate_private_key(FETCHAI)
        self.generate_private_key(COSMOS, COSMOS_PRIVATE_KEY_FILE_CONNECTION)
        self.add_private_key(FETCHAI, FETCHAI_PRIVATE_KEY_FILE)
        self.add_private_key(
            COSMOS, COSMOS_PRIVATE_KEY_FILE_CONNECTION, connection=True
        )
        self.replace_private_key_in_file(
            NON_FUNDED_COSMOS_PRIVATE_KEY_1, COSMOS_PRIVATE_KEY_FILE_CONNECTION
        )

        setting_path = "vendor.fetchai.connections.p2p_libp2p.config.ledger_id"
        self.set_config(setting_path, COSMOS)

        # replace location
        setting_path = (
            "vendor.fetchai.skills.ml_data_provider.models.strategy.args.location"
        )
        self.nested_set_config(setting_path, location)

        # prepare model trainer agent
        self.set_agent_context(model_trainer_aea_name)
        self.add_item("connection", "fetchai/p2p_libp2p:0.13.0")
        self.add_item("connection", "fetchai/soef:0.14.0")
        self.remove_item("connection", "fetchai/stub:0.13.0")
        self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.13.0")
        self.add_item("connection", "fetchai/ledger:0.11.0")
        self.add_item("skill", "fetchai/ml_train:0.18.0")
        setting_path = (
            "vendor.fetchai.skills.ml_train.models.strategy.args.is_ledger_tx"
        )
        self.set_config(setting_path, False, "bool")
        setting_path = "agent.default_routing"
        self.nested_set_config(setting_path, default_routing)
        self.run_install()

        # add keys
        self.generate_private_key(FETCHAI)
        self.generate_private_key(COSMOS, COSMOS_PRIVATE_KEY_FILE_CONNECTION)
        self.add_private_key(FETCHAI, FETCHAI_PRIVATE_KEY_FILE)
        self.add_private_key(
            COSMOS, COSMOS_PRIVATE_KEY_FILE_CONNECTION, connection=True
        )

        # set p2p configs
        setting_path = "vendor.fetchai.connections.p2p_libp2p.config"
        self.nested_set_config(setting_path, NON_GENESIS_CONFIG)

        # replace location
        setting_path = "vendor.fetchai.skills.ml_train.models.strategy.args.location"
        self.nested_set_config(setting_path, location)

        self.set_agent_context(data_provider_aea_name)
        self.run_cli_command("build", cwd=self._get_cwd())
        data_provider_aea_process = self.run_agent()

        check_strings = (
            "Starting libp2p node...",
            "Connecting to libp2p node...",
            "Successfully connected to libp2p node!",
            LIBP2P_SUCCESS_MESSAGE,
        )
        missing_strings = self.missing_from_output(
            data_provider_aea_process, check_strings, timeout=240, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in data_provider_aea output.".format(
            missing_strings
        )

        self.set_agent_context(model_trainer_aea_name)
        self.run_cli_command("build", cwd=self._get_cwd())
        model_trainer_aea_process = self.run_agent()

        check_strings = (
            "Starting libp2p node...",
            "Connecting to libp2p node...",
            "Successfully connected to libp2p node!",
            LIBP2P_SUCCESS_MESSAGE,
        )
        missing_strings = self.missing_from_output(
            model_trainer_aea_process, check_strings, timeout=240, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in model_trainer_aea output.".format(
            missing_strings
        )

        check_strings = (
            "registering agent on SOEF.",
            "registering service on SOEF.",
            "got a Call for Terms from",
            "a Terms message:",
            "got an Accept from",
            "a Data message:",
        )
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
            "received terms message from",
            "sending dummy transaction digest ...",
            "received data message from",
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
        wait_for_localhost_ports_to_close([9000, 9001])


@pytest.mark.integration
class TestMLSkillsFetchaiLedger(AEATestCaseMany):
    """Test that ml skills work."""

    @pytest.mark.flaky(
        reruns=MAX_FLAKY_RERUNS_INTEGRATION
    )  # cause possible network issues
    @pytest.mark.skipif(
        sys.version_info >= (3, 8),
        reason="cannot run on 3.8 as tensorflow not installable",
    )
    def test_ml_skills(self, pytestconfig):
        """Run the ml skills sequence."""
        data_provider_aea_name = "ml_data_provider"
        model_trainer_aea_name = "ml_model_trainer"
        self.create_agents(data_provider_aea_name, model_trainer_aea_name)

        default_routing = {
            "fetchai/ledger_api:0.8.0": "fetchai/ledger:0.11.0",
            "fetchai/oef_search:0.11.0": "fetchai/soef:0.14.0",
        }

        # generate random location
        location = {
            "latitude": round(uniform(-90, 90), 2),  # nosec
            "longitude": round(uniform(-180, 180), 2),  # nosec
        }

        # prepare data provider agent
        self.set_agent_context(data_provider_aea_name)
        self.add_item("connection", "fetchai/p2p_libp2p:0.13.0")
        self.add_item("connection", "fetchai/soef:0.14.0")
        self.remove_item("connection", "fetchai/stub:0.13.0")
        self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.13.0")
        self.add_item("connection", "fetchai/ledger:0.11.0")
        self.add_item("skill", "fetchai/ml_data_provider:0.17.0")
        setting_path = "agent.default_routing"
        self.nested_set_config(setting_path, default_routing)
        self.run_install()

        diff = self.difference_to_fetched_agent(
            "fetchai/ml_data_provider:0.19.0", data_provider_aea_name
        )
        assert (
            diff == []
        ), "Difference between created and fetched project for files={}".format(diff)

        # add keys
        self.generate_private_key(FETCHAI)
        self.generate_private_key(COSMOS, COSMOS_PRIVATE_KEY_FILE_CONNECTION)
        self.add_private_key(FETCHAI, FETCHAI_PRIVATE_KEY_FILE)
        self.add_private_key(
            COSMOS, COSMOS_PRIVATE_KEY_FILE_CONNECTION, connection=True
        )
        self.replace_private_key_in_file(
            NON_FUNDED_COSMOS_PRIVATE_KEY_1, COSMOS_PRIVATE_KEY_FILE_CONNECTION
        )

        setting_path = "vendor.fetchai.connections.p2p_libp2p.config.ledger_id"
        self.set_config(setting_path, COSMOS)

        # replace location
        setting_path = (
            "vendor.fetchai.skills.ml_data_provider.models.strategy.args.location"
        )
        self.nested_set_config(setting_path, location)

        # prepare model trainer agent
        self.set_agent_context(model_trainer_aea_name)
        self.add_item("connection", "fetchai/p2p_libp2p:0.13.0")
        self.add_item("connection", "fetchai/soef:0.14.0")
        self.remove_item("connection", "fetchai/stub:0.13.0")
        self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.13.0")
        self.add_item("connection", "fetchai/ledger:0.11.0")
        self.add_item("skill", "fetchai/ml_train:0.18.0")
        setting_path = "agent.default_routing"
        self.nested_set_config(setting_path, default_routing)
        self.run_install()

        diff = self.difference_to_fetched_agent(
            "fetchai/ml_model_trainer:0.20.0", model_trainer_aea_name
        )
        assert (
            diff == []
        ), "Difference between created and fetched project for files={}".format(diff)

        # add keys
        self.generate_private_key(FETCHAI)
        self.generate_private_key(COSMOS, COSMOS_PRIVATE_KEY_FILE_CONNECTION)
        self.add_private_key(FETCHAI, FETCHAI_PRIVATE_KEY_FILE)
        self.add_private_key(
            COSMOS, COSMOS_PRIVATE_KEY_FILE_CONNECTION, connection=True
        )

        # fund key
        self.generate_wealth(FETCHAI)

        # set p2p configs
        setting_path = "vendor.fetchai.connections.p2p_libp2p.config"
        self.nested_set_config(setting_path, NON_GENESIS_CONFIG)

        # replace location
        setting_path = "vendor.fetchai.skills.ml_train.models.strategy.args.location"
        self.nested_set_config(setting_path, location)

        self.set_agent_context(data_provider_aea_name)
        self.run_cli_command("build", cwd=self._get_cwd())
        data_provider_aea_process = self.run_agent()

        check_strings = (
            "Starting libp2p node...",
            "Connecting to libp2p node...",
            "Successfully connected to libp2p node!",
            LIBP2P_SUCCESS_MESSAGE,
        )
        missing_strings = self.missing_from_output(
            data_provider_aea_process, check_strings, timeout=240, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in data_provider_aea output.".format(
            missing_strings
        )

        self.set_agent_context(model_trainer_aea_name)
        self.run_cli_command("build", cwd=self._get_cwd())
        model_trainer_aea_process = self.run_agent()

        check_strings = (
            "Starting libp2p node...",
            "Connecting to libp2p node...",
            "Successfully connected to libp2p node!",
            LIBP2P_SUCCESS_MESSAGE,
        )
        missing_strings = self.missing_from_output(
            model_trainer_aea_process, check_strings, timeout=240, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in model_trainer_aea output.".format(
            missing_strings
        )

        check_strings = (
            "registering agent on SOEF.",
            "registering service on SOEF.",
            "got a Call for Terms from",
            "a Terms message:",
            "got an Accept from",
            "a Data message:",
        )
        missing_strings = self.missing_from_output(
            data_provider_aea_process, check_strings, timeout=240, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in data_provider_aea output.".format(
            missing_strings
        )

        check_strings = (
            "found agents=",
            "sending CFT to agent=",
            "received terms message from",
            "requesting transfer transaction from ledger api for message=",
            "received raw transaction=",
            "proposing the transaction to the decision maker. Waiting for confirmation ...",
            "transaction signing was successful.",
            "sending transaction to ledger.",
            "transaction was successfully submitted. Transaction digest=",
            "informing counterparty=",
            "received data message from",
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
        wait_for_localhost_ports_to_close([9000, 9001])
