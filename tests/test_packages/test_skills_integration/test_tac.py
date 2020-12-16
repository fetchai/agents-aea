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
"""This test module contains the integration test for the tac skills."""

import datetime
import uuid
from random import uniform

import pytest

from aea.test_tools.test_cases import AEATestCaseMany

from packages.fetchai.connections.p2p_libp2p.connection import LIBP2P_SUCCESS_MESSAGE

from tests.conftest import (
    COSMOS,
    COSMOS_PRIVATE_KEY_FILE_CONNECTION,
    ETHEREUM,
    ETHEREUM_PRIVATE_KEY_FILE,
    FETCHAI,
    FETCHAI_PRIVATE_KEY_FILE,
    FUNDED_ETH_PRIVATE_KEY_1,
    FUNDED_ETH_PRIVATE_KEY_2,
    FUNDED_ETH_PRIVATE_KEY_3,
    MAX_FLAKY_RERUNS_ETH,
    MAX_FLAKY_RERUNS_INTEGRATION,
    NON_FUNDED_COSMOS_PRIVATE_KEY_1,
    NON_GENESIS_CONFIG,
    NON_GENESIS_CONFIG_TWO,
    UseGanache,
)


MAX_FLAKY_RERUNS_ETH -= 1


class TestTacSkills(AEATestCaseMany):
    """Test that tac skills work."""

    capture_log = True

    @pytest.mark.integration
    @pytest.mark.flaky(
        reruns=MAX_FLAKY_RERUNS_INTEGRATION
    )  # cause possible network issues
    def test_tac(self):
        """Run the tac skills sequence."""
        tac_aea_one = "tac_participant_one"
        tac_aea_two = "tac_participant_two"
        tac_controller_name = "tac_controller"

        # create tac controller, agent one and agent two
        self.create_agents(
            tac_aea_one, tac_aea_two, tac_controller_name,
        )

        default_routing = {
            "fetchai/oef_search:0.11.0": "fetchai/soef:0.14.0",
        }

        # generate random location
        location = {
            "latitude": round(uniform(-90, 90), 2),  # nosec
            "longitude": round(uniform(-180, 180), 2),  # nosec
        }

        # tac name
        tac_id = uuid.uuid4().hex

        # prepare tac controller for test
        self.set_agent_context(tac_controller_name)
        self.add_item("connection", "fetchai/p2p_libp2p:0.13.0")
        self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.13.0")
        self.add_item("connection", "fetchai/soef:0.14.0")
        self.remove_item("connection", "fetchai/stub:0.13.0")
        self.add_item("skill", "fetchai/tac_control:0.13.0")
        self.set_config("agent.default_ledger", FETCHAI)
        setting_path = "agent.default_routing"
        self.nested_set_config(setting_path, default_routing)
        self.run_install()

        diff = self.difference_to_fetched_agent(
            "fetchai/tac_controller:0.16.0", tac_controller_name
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
            "vendor.fetchai.skills.tac_control.models.parameters.args.location"
        )
        self.nested_set_config(setting_path, location)

        # set tac id
        data = {"key": "tac", "value": tac_id}
        setting_path = (
            "vendor.fetchai.skills.tac_control.models.parameters.args.service_data"
        )
        self.nested_set_config(setting_path, data)

        default_routing = {
            "fetchai/ledger_api:0.8.0": "fetchai/ledger:0.11.0",
            "fetchai/oef_search:0.11.0": "fetchai/soef:0.14.0",
        }

        # prepare agents for test
        for agent_name, config in (
            (tac_aea_one, NON_GENESIS_CONFIG),
            (tac_aea_two, NON_GENESIS_CONFIG_TWO),
        ):
            self.set_agent_context(agent_name)
            self.add_item("connection", "fetchai/p2p_libp2p:0.13.0")
            self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.13.0")
            self.add_item("connection", "fetchai/soef:0.14.0")
            self.add_item("connection", "fetchai/ledger:0.11.0")
            self.remove_item("connection", "fetchai/stub:0.13.0")
            self.add_item("skill", "fetchai/tac_participation:0.14.0")
            self.add_item("skill", "fetchai/tac_negotiation:0.16.0")
            self.set_config("agent.default_ledger", FETCHAI)
            setting_path = "agent.default_routing"
            self.nested_set_config(setting_path, default_routing)
            self.run_install()
            diff = self.difference_to_fetched_agent(
                "fetchai/tac_participant:0.18.0", agent_name
            )
            assert (
                diff == []
            ), "Difference between created and fetched project for files={}".format(
                diff
            )

            # add keys
            self.generate_private_key(FETCHAI)
            self.generate_private_key(COSMOS, COSMOS_PRIVATE_KEY_FILE_CONNECTION)
            self.add_private_key(FETCHAI, FETCHAI_PRIVATE_KEY_FILE)
            self.add_private_key(
                COSMOS, COSMOS_PRIVATE_KEY_FILE_CONNECTION, connection=True
            )

            # set p2p configs
            setting_path = "vendor.fetchai.connections.p2p_libp2p.config"
            self.nested_set_config(setting_path, config)

            # replace location
            setting_path = (
                "vendor.fetchai.skills.tac_participation.models.game.args.location"
            )
            self.nested_set_config(setting_path, location)

            # set tac id
            data = {
                "search_key": "tac",
                "search_value": tac_id,
                "constraint_type": "==",
            }
            setting_path = (
                "vendor.fetchai.skills.tac_participation.models.game.args.search_query"
            )
            self.nested_set_config(setting_path, data)

        # run tac controller
        self.set_agent_context(tac_controller_name)
        now = datetime.datetime.now().strftime("%d %m %Y %H:%M")
        now_min = datetime.datetime.strptime(now, "%d %m %Y %H:%M")
        fut = now_min + datetime.timedelta(0, 60)
        start_time = fut.strftime("%d %m %Y %H:%M")
        setting_path = "vendor.fetchai.skills.tac_control.models.parameters.args.registration_start_time"
        self.set_config(setting_path, start_time)
        self.run_cli_command("build", cwd=self._get_cwd())
        tac_controller_process = self.run_agent()

        check_strings = (
            "Starting libp2p node...",
            "Connecting to libp2p node...",
            "Successfully connected to libp2p node!",
            LIBP2P_SUCCESS_MESSAGE,
        )
        missing_strings = self.missing_from_output(
            tac_controller_process, check_strings, timeout=240, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in tac_controller output.".format(missing_strings)

        # run two agents (participants)
        self.set_agent_context(tac_aea_one)
        self.run_cli_command("build", cwd=self._get_cwd())
        tac_aea_one_process = self.run_agent()

        self.set_agent_context(tac_aea_two)
        self.run_cli_command("build", cwd=self._get_cwd())
        tac_aea_two_process = self.run_agent()

        check_strings = (
            "Starting libp2p node...",
            "Connecting to libp2p node...",
            "Successfully connected to libp2p node!",
            LIBP2P_SUCCESS_MESSAGE,
        )
        missing_strings = self.missing_from_output(
            tac_aea_one_process, check_strings, timeout=240, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in tac_aea_one output.".format(missing_strings)

        check_strings = (
            "Starting libp2p node...",
            "Connecting to libp2p node...",
            "Successfully connected to libp2p node!",
            LIBP2P_SUCCESS_MESSAGE,
        )
        missing_strings = self.missing_from_output(
            tac_aea_two_process, check_strings, timeout=240, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in tac_aea_two output.".format(missing_strings)

        check_strings = (
            "registering agent on SOEF.",
            "registering TAC data model on SOEF.",
            "TAC open for registration until:",
            "agent registered: 'tac_participant_one'",
            "agent registered: 'tac_participant_two'",
            "started competition:",
            "unregistering TAC data model from SOEF.",
            "handling valid transaction:",
            "Current good & money allocation & score: ",
        )
        missing_strings = self.missing_from_output(
            tac_controller_process, check_strings, timeout=240, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in tac_controller output.".format(missing_strings)

        check_strings = (
            "searching for TAC, search_id=",
            "found the TAC controller. Registering...",
            "received start event from the controller. Starting to compete...",
            "registering agent on SOEF.",
            "searching for sellers, search_id=",
            "searching for buyers, search_id=",
            "found potential sellers agents=",
            "received cfp from",
            "received decline from",
            "received propose from",
            "received accept from",
            "received match_accept_w_inform from",
            "sending CFP to agent=",
            "sending propose to",
            "sending accept to",
            "requesting signature, sending sign_message to decision_maker, message=",
            "received signed_message from decision_maker, message=",
            "sending transaction to controller, tx=",
            "received transaction confirmation from the controller:",
            "Applying state update!",
            "found potential buyers agents=",
            "sending CFP to agent=",
        )
        missing_strings = self.missing_from_output(
            tac_aea_one_process, check_strings, timeout=240, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in tac_aea_one output.".format(missing_strings)

        # Note, we do not need to check std output of the other participant as it is implied

        self.terminate_agents(
            tac_controller_process, tac_aea_one_process, tac_aea_two_process
        )
        assert (
            self.is_successfully_terminated()
        ), "Agents weren't successfully terminated."


class TestTacSkillsContract(AEATestCaseMany, UseGanache):
    """Test that tac skills work."""

    capture_log = True

    @pytest.mark.integration
    @pytest.mark.ledger
    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS_ETH)  # cause possible network issues
    def test_tac(self):
        """Run the tac skills sequence."""
        tac_aea_one = "tac_participant_one"
        tac_aea_two = "tac_participant_two"
        tac_controller_name = "tac_controller_contract"

        # create tac controller, agent one and agent two
        self.create_agents(
            tac_aea_one, tac_aea_two, tac_controller_name,
        )

        default_routing = {
            "fetchai/contract_api:0.9.0": "fetchai/ledger:0.11.0",
            "fetchai/ledger_api:0.8.0": "fetchai/ledger:0.11.0",
            "fetchai/oef_search:0.11.0": "fetchai/soef:0.14.0",
        }

        # generate random location
        location = {
            "latitude": round(uniform(-90, 90), 2),  # nosec
            "longitude": round(uniform(-180, 180), 2),  # nosec
        }

        # tac name
        tac_id = uuid.uuid4().hex

        # prepare tac controller for test
        self.set_agent_context(tac_controller_name)
        self.add_item("connection", "fetchai/p2p_libp2p:0.13.0")
        self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.13.0")
        self.add_item("connection", "fetchai/soef:0.14.0")
        self.add_item("connection", "fetchai/ledger:0.11.0")
        self.remove_item("connection", "fetchai/stub:0.13.0")
        self.add_item("skill", "fetchai/tac_control_contract:0.15.0")
        self.set_config("agent.default_ledger", ETHEREUM)
        setting_path = "agent.default_routing"
        self.nested_set_config(setting_path, default_routing)
        self.run_install()

        diff = self.difference_to_fetched_agent(
            "fetchai/tac_controller_contract:0.18.0", tac_controller_name
        )
        assert (
            diff == []
        ), "Difference between created and fetched project for files={}".format(diff)

        # add keys
        self.generate_private_key(ETHEREUM)
        self.generate_private_key(COSMOS, COSMOS_PRIVATE_KEY_FILE_CONNECTION)
        self.add_private_key(ETHEREUM, ETHEREUM_PRIVATE_KEY_FILE)
        self.add_private_key(
            COSMOS, COSMOS_PRIVATE_KEY_FILE_CONNECTION, connection=True
        )
        self.replace_private_key_in_file(
            FUNDED_ETH_PRIVATE_KEY_1, ETHEREUM_PRIVATE_KEY_FILE
        )
        self.replace_private_key_in_file(
            NON_FUNDED_COSMOS_PRIVATE_KEY_1, COSMOS_PRIVATE_KEY_FILE_CONNECTION
        )
        setting_path = "vendor.fetchai.connections.p2p_libp2p.config.ledger_id"
        self.set_config(setting_path, COSMOS)
        setting_path = "vendor.fetchai.connections.soef.config.chain_identifier"
        self.set_config(setting_path, ETHEREUM)
        setting_path = "vendor.fetchai.skills.tac_control.is_abstract"
        self.set_config(setting_path, True, "bool")

        # replace location
        setting_path = (
            "vendor.fetchai.skills.tac_control_contract.models.parameters.args.location"
        )
        self.nested_set_config(setting_path, location)

        # set tac id
        data = {"key": "tac", "value": tac_id}
        setting_path = "vendor.fetchai.skills.tac_control_contract.models.parameters.args.service_data"
        self.nested_set_config(setting_path, data)

        default_routing = {
            "fetchai/contract_api:0.9.0": "fetchai/ledger:0.11.0",
            "fetchai/ledger_api:0.8.0": "fetchai/ledger:0.11.0",
            "fetchai/oef_search:0.11.0": "fetchai/soef:0.14.0",
        }

        # prepare agents for test
        for agent_name, config, private_key in (
            (tac_aea_one, NON_GENESIS_CONFIG, FUNDED_ETH_PRIVATE_KEY_2),
            (tac_aea_two, NON_GENESIS_CONFIG_TWO, FUNDED_ETH_PRIVATE_KEY_3),
        ):
            self.set_agent_context(agent_name)
            self.add_item("connection", "fetchai/p2p_libp2p:0.13.0")
            self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.13.0")
            self.add_item("connection", "fetchai/soef:0.14.0")
            self.add_item("connection", "fetchai/ledger:0.11.0")
            self.remove_item("connection", "fetchai/stub:0.13.0")
            self.add_item("skill", "fetchai/tac_participation:0.14.0")
            self.add_item("skill", "fetchai/tac_negotiation:0.16.0")
            self.set_config("agent.default_ledger", ETHEREUM)
            setting_path = "agent.default_routing"
            self.nested_set_config(setting_path, default_routing)
            self.set_config(
                "vendor.fetchai.skills.tac_participation.models.game.args.is_using_contract",
                True,
                "bool",
            )
            self.set_config(
                "vendor.fetchai.skills.tac_negotiation.models.strategy.args.is_contract_tx",
                True,
                "bool",
            )
            self.run_install()
            diff = self.difference_to_fetched_agent(
                "fetchai/tac_participant_contract:0.8.0", agent_name
            )
            assert (
                diff == []
            ), "Difference between created and fetched project for files={}".format(
                diff
            )

            # add keys
            self.generate_private_key(ETHEREUM)
            self.generate_private_key(COSMOS, COSMOS_PRIVATE_KEY_FILE_CONNECTION)
            self.add_private_key(ETHEREUM, ETHEREUM_PRIVATE_KEY_FILE)
            self.add_private_key(
                COSMOS, COSMOS_PRIVATE_KEY_FILE_CONNECTION, connection=True
            )
            self.replace_private_key_in_file(private_key, ETHEREUM_PRIVATE_KEY_FILE)

            # set p2p configs
            setting_path = "vendor.fetchai.connections.p2p_libp2p.config"
            self.nested_set_config(setting_path, config)
            setting_path = "vendor.fetchai.connections.p2p_libp2p.config.ledger_id"
            self.set_config(setting_path, COSMOS)
            setting_path = "vendor.fetchai.connections.soef.config.chain_identifier"
            self.set_config(setting_path, ETHEREUM)

            # replace location
            setting_path = (
                "vendor.fetchai.skills.tac_participation.models.game.args.location"
            )
            self.nested_set_config(setting_path, location)

            # set tac id
            data = {
                "search_key": "tac",
                "search_value": tac_id,
                "constraint_type": "==",
            }
            setting_path = (
                "vendor.fetchai.skills.tac_participation.models.game.args.search_query"
            )
            self.nested_set_config(setting_path, data)

        # run tac controller
        self.set_agent_context(tac_controller_name)
        now = datetime.datetime.now().strftime("%d %m %Y %H:%M")
        now_min = datetime.datetime.strptime(now, "%d %m %Y %H:%M")
        fut = now_min + datetime.timedelta(
            0, 180
        )  # we provide 3 minutes time for contract deployment
        start_time = fut.strftime("%d %m %Y %H:%M")
        setting_path = "vendor.fetchai.skills.tac_control_contract.models.parameters.args.registration_start_time"
        self.set_config(setting_path, start_time)
        self.run_cli_command("build", cwd=self._get_cwd())
        tac_controller_process = self.run_agent()

        check_strings = (
            "Starting libp2p node...",
            "Connecting to libp2p node...",
            "Successfully connected to libp2p node!",
            LIBP2P_SUCCESS_MESSAGE,
            "registering agent on SOEF.",
            "requesting contract deployment transaction...",
            "Start processing messages...",
            "received raw transaction=",
            "transaction signing was successful.",
            "sending transaction to ledger.",
            "transaction was successfully submitted. Transaction digest=",
            "requesting transaction receipt.",
            "transaction was successfully settled. Transaction receipt=",
            "contract deployed.",
            "registering TAC data model on SOEF.",
            "TAC open for registration until:",
        )
        missing_strings = self.missing_from_output(
            tac_controller_process, check_strings, timeout=240, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in tac_controller output.".format(missing_strings)

        # run two agents (participants)
        self.set_agent_context(tac_aea_one)
        self.run_cli_command("build", cwd=self._get_cwd())
        tac_aea_one_process = self.run_agent()

        self.set_agent_context(tac_aea_two)
        self.run_cli_command("build", cwd=self._get_cwd())
        tac_aea_two_process = self.run_agent()

        check_strings = (
            "Starting libp2p node...",
            "Connecting to libp2p node...",
            "Successfully connected to libp2p node!",
            LIBP2P_SUCCESS_MESSAGE,
            "Start processing messages...",
            "searching for TAC, search_id=",
            "found the TAC controller. Registering...",
        )
        missing_strings = self.missing_from_output(
            tac_aea_one_process, check_strings, timeout=240, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in tac_aea_one output.".format(missing_strings)

        check_strings = (
            "Starting libp2p node...",
            "Connecting to libp2p node...",
            "Successfully connected to libp2p node!",
            LIBP2P_SUCCESS_MESSAGE,
            "Start processing messages...",
            "searching for TAC, search_id=",
            "found the TAC controller. Registering...",
        )
        missing_strings = self.missing_from_output(
            tac_aea_two_process, check_strings, timeout=240, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in tac_aea_two output.".format(missing_strings)

        check_strings = (
            "agent registered:",
            "closing registration!",
            "unregistering TAC data model from SOEF.",
            "requesting create items transaction...",
            "received raw transaction=",
            "proposing the transaction to the decision maker. Waiting for confirmation ...",
            "transaction signing was successful.",
            "transaction was successfully submitted. Transaction digest=",
            "requesting transaction receipt.",
            "transaction was successfully settled. Transaction receipt=",
            "tokens created.",
            "requesting mint_items transactions for agent=",
            "tokens minted.",
            "requesting mint_items transactions for agent=",
            "tokens minted.",
            "all tokens minted.",
            "started competition:",
        )
        missing_strings = self.missing_from_output(
            tac_controller_process, check_strings, timeout=240, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in tac_controller output.".format(missing_strings)

        check_strings = (
            "received start event from the controller. Starting to compete...",
            "received a contract address:",
            "registering agent on SOEF.",
            "searching for sellers, search_id=",
            "searching for buyers, search_id=",
            "found potential sellers agents=",
            "found potential buyers agents=",
            "sending CFP to agent=",
            "received cfp from",
            "received propose from",
            "received decline from",
            "received accept from",
            "received match_accept_w_inform from",
            "sending propose to",
            "sending accept to",
            "requesting batch transaction hash, sending get_raw_message to fetchai/erc1155:0.13.0, message=",
            "requesting batch atomic swap transaction, sending get_raw_transaction to fetchai/erc1155:0.13.0, message=",
            "received raw transaction=",
            "received raw message=",
            "proposing the transaction to the decision maker. Waiting for confirmation ...",
            "proposing the message to the decision maker. Waiting for confirmation ...",
            "received signed_message from decision_maker, message=",
            "received signed_transaction from decision_maker, message=",
            "sending send_signed_transaction to ledger ethereum, message=",
        )
        missing_strings = self.missing_from_output(
            tac_aea_one_process, check_strings, timeout=300, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in tac_aea_one output.".format(missing_strings)

        check_strings = (
            "received start event from the controller. Starting to compete...",
            "received a contract address:",
            "registering agent on SOEF.",
            "searching for sellers, search_id=",
            "searching for buyers, search_id=",
            "found potential sellers agents=",
            "found potential buyers agents=",
            "sending CFP to agent=",
            "received cfp from",
            "received propose from",
            "received decline from",
            "received accept from",
            "received match_accept_w_inform from",
            "sending propose to",
            "sending accept to",
            "requesting batch transaction hash, sending get_raw_message to fetchai/erc1155:0.13.0, message=",
            "requesting batch atomic swap transaction, sending get_raw_transaction to fetchai/erc1155:0.13.0, message=",
            "received raw transaction=",
            "received raw message=",
            "proposing the transaction to the decision maker. Waiting for confirmation ...",
            "proposing the message to the decision maker. Waiting for confirmation ...",
            "received signed_message from decision_maker, message=",
            "received signed_transaction from decision_maker, message=",
            "sending send_signed_transaction to ledger ethereum, message=",
        )
        missing_strings = self.missing_from_output(
            tac_aea_two_process, check_strings, timeout=360, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in tac_aea_two output.".format(missing_strings)

        # Note, we do not need to check std output of the other participant as it is implied

        self.terminate_agents(
            tac_controller_process, tac_aea_one_process, tac_aea_two_process
        )
        assert (
            self.is_successfully_terminated()
        ), "Agents weren't successfully terminated."
