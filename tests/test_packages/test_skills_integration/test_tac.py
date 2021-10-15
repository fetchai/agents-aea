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
import json
import uuid
from random import uniform

import pytest
from aea_ledger_ethereum import EthereumCrypto
from aea_ledger_fetchai import FetchAICrypto

from aea.test_tools.test_cases import AEATestCaseManyFlaky

from packages.fetchai.connections.p2p_libp2p.connection import LIBP2P_SUCCESS_MESSAGE

from tests.conftest import (
    DEFAULT_DENOMINATION,
    DEFAULT_FETCH_LEDGER_ADDR,
    DEFAULT_FETCH_LEDGER_REST_PORT,
    ETHEREUM_PRIVATE_KEY_FILE,
    FETCHAI_PRIVATE_KEY_FILE,
    FETCHAI_PRIVATE_KEY_FILE_CONNECTION,
    FUNDED_ETH_PRIVATE_KEY_1,
    FUNDED_ETH_PRIVATE_KEY_2,
    FUNDED_ETH_PRIVATE_KEY_3,
    MAX_FLAKY_RERUNS_ETH,
    MAX_FLAKY_RERUNS_INTEGRATION,
    NON_FUNDED_FETCHAI_PRIVATE_KEY_1,
    NON_GENESIS_CONFIG,
    NON_GENESIS_CONFIG_TWO,
    UseGanache,
    UseLocalFetchNode,
    UseSOEF,
    fund_accounts_from_local_validator,
)


MAX_FLAKY_RERUNS_ETH -= 1


class TestTacSkills(AEATestCaseManyFlaky):
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
            "fetchai/oef_search:1.0.0": "fetchai/soef:0.26.0",
        }

        # generate random location
        location = {
            "latitude": round(uniform(-90, 90), 2),  # nosec
            "longitude": round(uniform(-180, 180), 2),  # nosec
        }

        # tac name
        tac_id = uuid.uuid4().hex
        tac_service = f"tac_service_{tac_id[:5]}"

        # prepare tac controller for test
        self.set_agent_context(tac_controller_name)
        self.add_item("connection", "fetchai/p2p_libp2p:0.25.0")
        self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.25.0")
        self.add_item("connection", "fetchai/soef:0.26.0")
        self.add_item("skill", "fetchai/tac_control:0.24.0")
        self.set_config("agent.default_ledger", FetchAICrypto.identifier)
        setting_path = "agent.default_routing"
        self.nested_set_config(setting_path, default_routing)
        self.run_install()

        diff = self.difference_to_fetched_agent(
            "fetchai/tac_controller:0.29.0", tac_controller_name
        )
        assert (
            diff == []
        ), "Difference between created and fetched project for files={}".format(diff)

        # add keys
        self.generate_private_key(FetchAICrypto.identifier)
        self.generate_private_key(
            FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_FILE_CONNECTION
        )
        self.add_private_key(FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_FILE)
        self.add_private_key(
            FetchAICrypto.identifier,
            FETCHAI_PRIVATE_KEY_FILE_CONNECTION,
            connection=True,
        )
        self.replace_private_key_in_file(
            NON_FUNDED_FETCHAI_PRIVATE_KEY_1, FETCHAI_PRIVATE_KEY_FILE_CONNECTION
        )
        setting_path = "vendor.fetchai.connections.p2p_libp2p.config.ledger_id"
        self.set_config(setting_path, FetchAICrypto.identifier)

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
            "fetchai/ledger_api:1.0.0": "fetchai/ledger:0.19.0",
            "fetchai/oef_search:1.0.0": "fetchai/soef:0.26.0",
        }

        self.run_cli_command("build", cwd=self._get_cwd())
        self.run_cli_command("issue-certificates", cwd=self._get_cwd())

        # prepare agents for test
        for agent_name, config in (
            (tac_aea_one, NON_GENESIS_CONFIG),
            (tac_aea_two, NON_GENESIS_CONFIG_TWO),
        ):
            self.set_agent_context(agent_name)
            self.add_item("connection", "fetchai/p2p_libp2p:0.25.0")
            self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.25.0")
            self.add_item("connection", "fetchai/soef:0.26.0")
            self.add_item("connection", "fetchai/ledger:0.19.0")
            self.add_item("skill", "fetchai/tac_participation:0.24.0")
            self.add_item("skill", "fetchai/tac_negotiation:0.28.0")
            self.set_config("agent.default_ledger", FetchAICrypto.identifier)
            setting_path = "agent.default_routing"
            self.nested_set_config(setting_path, default_routing)
            data = {
                "dotted_path": "aea.decision_maker.gop:DecisionMakerHandler",
                "file_path": None,
                "config": {},
            }
            setting_path = "agent.decision_maker_handler"
            self.nested_set_config(setting_path, data)
            self.run_install()
            diff = self.difference_to_fetched_agent(
                "fetchai/tac_participant:0.31.0", agent_name
            )
            assert (
                diff == []
            ), "Difference between created and fetched project for files={}".format(
                diff
            )

            # add keys
            self.generate_private_key(FetchAICrypto.identifier)
            self.generate_private_key(
                FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_FILE_CONNECTION
            )
            self.add_private_key(FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_FILE)
            self.add_private_key(
                FetchAICrypto.identifier,
                FETCHAI_PRIVATE_KEY_FILE_CONNECTION,
                connection=True,
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
            self.set_config(
                "vendor.fetchai.skills.tac_negotiation.models.strategy.args.service_key",
                tac_service,
            )

            self.run_cli_command("build", cwd=self._get_cwd())
            self.run_cli_command("issue-certificates", cwd=self._get_cwd())

        # run tac controller
        self.set_agent_context(tac_controller_name)
        now = datetime.datetime.now().strftime("%d %m %Y %H:%M")
        now_min = datetime.datetime.strptime(now, "%d %m %Y %H:%M")
        fut = now_min + datetime.timedelta(0, 60)
        start_time = fut.strftime("%d %m %Y %H:%M")
        setting_path = "vendor.fetchai.skills.tac_control.models.parameters.args.registration_start_time"
        self.set_config(setting_path, start_time)
        tac_controller_process = self.run_agent()

        check_strings = (
            "Starting libp2p node...",
            "Connecting to libp2p node...",
            "Successfully connected to libp2p node!",
            LIBP2P_SUCCESS_MESSAGE,
        )
        missing_strings = self.missing_from_output(
            tac_controller_process, check_strings, timeout=30, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in tac_controller output.".format(missing_strings)

        # run two agents (participants)
        self.set_agent_context(tac_aea_one)
        tac_aea_one_process = self.run_agent()

        self.set_agent_context(tac_aea_two)
        tac_aea_two_process = self.run_agent()

        check_strings = (
            "Starting libp2p node...",
            "Connecting to libp2p node...",
            "Successfully connected to libp2p node!",
            LIBP2P_SUCCESS_MESSAGE,
        )
        missing_strings = self.missing_from_output(
            tac_aea_one_process, check_strings, timeout=30, is_terminating=False
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
            tac_aea_two_process, check_strings, timeout=30, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in tac_aea_two output.".format(missing_strings)

        check_strings = (
            "registering agent on SOEF.",
            "registering TAC data model on SOEF.",
            "TAC open for registration until:",
            "registered as 'tac_participant_one'",
            "registered as 'tac_participant_two'",
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


class TestTacSkillsContractEthereum(AEATestCaseManyFlaky, UseGanache, UseSOEF):
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

        # default routing (both for controller and participants)
        default_routing = {
            "fetchai/contract_api:1.0.0": "fetchai/ledger:0.19.0",
            "fetchai/ledger_api:1.0.0": "fetchai/ledger:0.19.0",
            "fetchai/oef_search:1.0.0": "fetchai/soef:0.26.0",
        }

        # generate random location
        location = {
            "latitude": round(uniform(-90, 90), 2),  # nosec
            "longitude": round(uniform(-180, 180), 2),  # nosec
        }

        # tac name
        tac_id = uuid.uuid4().hex
        tac_service = f"tac_service_{tac_id[:5]}"

        # prepare tac controller for test
        self.set_agent_context(tac_controller_name)
        self.add_item("connection", "fetchai/p2p_libp2p:0.25.0")
        self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.25.0")
        self.add_item("connection", "fetchai/soef:0.26.0")
        self.add_item("connection", "fetchai/ledger:0.19.0")
        self.add_item("skill", "fetchai/tac_control_contract:0.26.0")
        self.set_config("agent.default_ledger", FetchAICrypto.identifier)
        self.nested_set_config(
            "agent.required_ledgers",
            [FetchAICrypto.identifier, EthereumCrypto.identifier],
        )
        setting_path = "agent.default_routing"
        self.nested_set_config(setting_path, default_routing)
        self.run_install()

        # add keys
        self.generate_private_key(EthereumCrypto.identifier)
        self.generate_private_key(
            FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_FILE_CONNECTION
        )
        self.add_private_key(EthereumCrypto.identifier, ETHEREUM_PRIVATE_KEY_FILE)
        self.add_private_key(
            FetchAICrypto.identifier,
            FETCHAI_PRIVATE_KEY_FILE_CONNECTION,
            connection=True,
        )
        self.replace_private_key_in_file(
            FUNDED_ETH_PRIVATE_KEY_1, ETHEREUM_PRIVATE_KEY_FILE
        )
        self.replace_private_key_in_file(
            NON_FUNDED_FETCHAI_PRIVATE_KEY_1, FETCHAI_PRIVATE_KEY_FILE_CONNECTION
        )
        setting_path = "vendor.fetchai.connections.p2p_libp2p.cert_requests"
        settings = json.dumps(
            [
                {
                    "identifier": "acn",
                    "ledger_id": EthereumCrypto.identifier,
                    "not_after": "2022-01-01",
                    "not_before": "2021-01-01",
                    "public_key": FetchAICrypto.identifier,
                    "message_format": "{public_key}",
                    "save_path": ".certs/conn_cert.txt",
                }
            ]
        )
        self.set_config(setting_path, settings, type_="list")
        settings = json.dumps(
            [
                {
                    "identifier": "acn",
                    "ledger_id": FetchAICrypto.identifier,
                    "not_after": "2022-01-01",
                    "not_before": "2021-01-01",
                    "public_key": FetchAICrypto.identifier,
                    "message_format": "{public_key}",
                    "save_path": ".certs/conn_cert.txt",
                }
            ]
        )
        self.set_config(setting_path, settings, type_="list")

        # set SOEF configuration
        setting_path = "vendor.fetchai.connections.soef.config.chain_identifier"
        self.set_config(setting_path, "fetchai_v2_misc")

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

        # check manually built agent is the same as the fetched one
        diff = self.difference_to_fetched_agent(
            "fetchai/tac_controller_contract:0.31.0", tac_controller_name
        )
        assert (
            diff == []
        ), "Difference between created and fetched project for files={}".format(diff)

        # change default ledger to Ethereum
        self.set_config("agent.default_ledger", EthereumCrypto.identifier)

        # set SOEF connection configuration
        setting_path = "vendor.fetchai.connections.soef.config.chain_identifier"
        self.set_config(setting_path, EthereumCrypto.identifier)

        # set p2p_libp2p connection config
        setting_path = "vendor.fetchai.connections.p2p_libp2p.cert_requests"
        settings = json.dumps(
            [
                {
                    "identifier": "acn",
                    "ledger_id": EthereumCrypto.identifier,
                    "not_after": "2022-01-01",
                    "not_before": "2021-01-01",
                    "public_key": FetchAICrypto.identifier,
                    "message_format": "{public_key}",
                    "save_path": ".certs/conn_cert.txt",
                }
            ]
        )
        self.set_config(setting_path, settings, type_="list")

        # change SOEF configuration to local
        setting_path = "vendor.fetchai.connections.soef.config.is_https"
        self.set_config(setting_path, False)
        setting_path = "vendor.fetchai.connections.soef.config.soef_addr"
        self.set_config(setting_path, "127.0.0.1")
        setting_path = "vendor.fetchai.connections.soef.config.soef_port"
        self.set_config(setting_path, 12002)

        # prepare agents for test
        for agent_name, config, private_key in (
            (tac_aea_one, NON_GENESIS_CONFIG, FUNDED_ETH_PRIVATE_KEY_2),
            (tac_aea_two, NON_GENESIS_CONFIG_TWO, FUNDED_ETH_PRIVATE_KEY_3),
        ):
            self.set_agent_context(agent_name)

            # add items
            self.add_item("connection", "fetchai/p2p_libp2p:0.25.0")
            self.add_item("connection", "fetchai/soef:0.26.0")
            self.add_item("connection", "fetchai/ledger:0.19.0")
            self.add_item("skill", "fetchai/tac_participation:0.24.0")
            self.add_item("skill", "fetchai/tac_negotiation:0.28.0")

            # set AEA config (no component overrides)
            self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.25.0")
            self.set_config("agent.default_ledger", FetchAICrypto.identifier)
            self.nested_set_config(
                "agent.required_ledgers",
                [FetchAICrypto.identifier, EthereumCrypto.identifier],
            )
            setting_path = "agent.default_routing"
            self.nested_set_config(setting_path, default_routing)
            data = {
                "dotted_path": "aea.decision_maker.gop:DecisionMakerHandler",
                "file_path": None,
                "config": {},
            }
            setting_path = "agent.decision_maker_handler"
            self.nested_set_config(setting_path, data)

            # install PyPI dependencies
            self.run_install()

            # add keys
            self.generate_private_key(EthereumCrypto.identifier)
            self.generate_private_key(
                FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_FILE_CONNECTION
            )
            self.add_private_key(EthereumCrypto.identifier, ETHEREUM_PRIVATE_KEY_FILE)
            self.add_private_key(
                FetchAICrypto.identifier,
                FETCHAI_PRIVATE_KEY_FILE_CONNECTION,
                connection=True,
            )
            self.replace_private_key_in_file(private_key, ETHEREUM_PRIVATE_KEY_FILE)

            # set p2p configs
            setting_path = "vendor.fetchai.connections.p2p_libp2p.config"
            self.nested_set_config(setting_path, config)
            setting_path = "vendor.fetchai.connections.p2p_libp2p.cert_requests"
            settings = json.dumps(
                [
                    {
                        "identifier": "acn",
                        "ledger_id": EthereumCrypto.identifier,
                        "not_after": "2022-01-01",
                        "not_before": "2021-01-01",
                        "public_key": FetchAICrypto.identifier,
                        "message_format": "{public_key}",
                        "save_path": ".certs/conn_cert.txt",
                    }
                ]
            )
            self.set_config(setting_path, settings, type_="list")
            settings = json.dumps(
                [
                    {
                        "identifier": "acn",
                        "ledger_id": FetchAICrypto.identifier,
                        "not_after": "2022-01-01",
                        "not_before": "2021-01-01",
                        "public_key": FetchAICrypto.identifier,
                        "message_format": "{public_key}",
                        "save_path": ".certs/conn_cert.txt",
                    }
                ]
            )
            self.set_config(setting_path, settings, type_="list")

            # set SOEF configuration
            setting_path = "vendor.fetchai.connections.soef.config.chain_identifier"
            self.set_config(setting_path, "fetchai_v2_misc")

            # set tac participant configuration
            self.set_config(
                "vendor.fetchai.skills.tac_participation.models.game.args.is_using_contract",
                True,
                "bool",
            )

            # set tac negotiation configuration
            self.set_config(
                "vendor.fetchai.skills.tac_negotiation.models.strategy.args.is_contract_tx",
                True,
                "bool",
            )

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

            diff = self.difference_to_fetched_agent(
                "fetchai/tac_participant_contract:0.21.0", agent_name
            )
            assert (
                diff == []
            ), "Difference between created and fetched project for files={}".format(
                diff
            )

            # change default ledger to Ethereum
            self.set_config("agent.default_ledger", EthereumCrypto.identifier)

            # set SOEF connection configuration
            setting_path = "vendor.fetchai.connections.soef.config.chain_identifier"
            self.set_config(setting_path, EthereumCrypto.identifier)

            # set p2p_libp2p connection config
            setting_path = "vendor.fetchai.connections.p2p_libp2p.cert_requests"
            settings = json.dumps(
                [
                    {
                        "identifier": "acn",
                        "ledger_id": EthereumCrypto.identifier,
                        "not_after": "2022-01-01",
                        "not_before": "2021-01-01",
                        "public_key": FetchAICrypto.identifier,
                        "message_format": "{public_key}",
                        "save_path": ".certs/conn_cert.txt",
                    }
                ]
            )
            self.set_config(setting_path, settings, type_="list")

            # change SOEF configuration to local
            setting_path = "vendor.fetchai.connections.soef.config.is_https"
            self.set_config(setting_path, False)
            setting_path = "vendor.fetchai.connections.soef.config.soef_addr"
            self.set_config(setting_path, "127.0.0.1")
            setting_path = "vendor.fetchai.connections.soef.config.soef_port"
            self.set_config(setting_path, 12002)

            self.set_config(
                "vendor.fetchai.skills.tac_negotiation.models.strategy.args.service_key",
                tac_service,
            )

        # run tac controller
        self.set_agent_context(tac_controller_name)
        self.run_cli_command("build", cwd=self._get_cwd())
        self.run_cli_command("issue-certificates", cwd=self._get_cwd())
        now = datetime.datetime.now().strftime("%d %m %Y %H:%M")
        now_min = datetime.datetime.strptime(now, "%d %m %Y %H:%M")
        fut = now_min + datetime.timedelta(
            0, 120
        )  # we provide 2 minutes time for contract deployment
        start_time = fut.strftime("%d %m %Y %H:%M")
        setting_path = "vendor.fetchai.skills.tac_control_contract.models.parameters.args.registration_start_time"
        self.set_config(setting_path, start_time)
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
            tac_controller_process, check_strings, timeout=180, is_terminating=False
        )  # we need to wait sufficiently long (at least 2 minutes - see above for deployment)
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in tac_controller output.".format(missing_strings)

        # run two agents (participants)
        self.set_agent_context(tac_aea_one)
        self.run_cli_command("build", cwd=self._get_cwd())
        self.run_cli_command("issue-certificates", cwd=self._get_cwd())
        tac_aea_one_process = self.run_agent()

        self.set_agent_context(tac_aea_two)
        self.run_cli_command("build", cwd=self._get_cwd())
        self.run_cli_command("issue-certificates", cwd=self._get_cwd())
        tac_aea_two_process = self.run_agent()

        check_strings = (
            "Starting libp2p node...",
            "Connecting to libp2p node...",
            "Successfully connected to libp2p node!",
            LIBP2P_SUCCESS_MESSAGE,
            "Start processing messages...",
            "searching for TAC, search_id=",
        )
        missing_strings = self.missing_from_output(
            tac_aea_one_process, check_strings, timeout=30, is_terminating=False
        )
        check_strings = ("found the TAC controller. Registering...",)
        missing_strings = self.missing_from_output(
            tac_aea_one_process, check_strings, timeout=60, is_terminating=False
        )  # we need to wait sufficiently long (at least 1 minutes - for registration)
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
            tac_aea_two_process, check_strings, timeout=30, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in tac_aea_two output.".format(missing_strings)

        check_strings = (
            "registered as 'tac_participant_one'",
            "registered as 'tac_participant_two'",
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
            "requesting batch transaction hash, sending get_raw_message to fetchai/erc1155:0.22.0, message=",
            "requesting batch atomic swap transaction, sending get_raw_transaction to fetchai/erc1155:0.22.0, message=",
            "received raw transaction=",
            "received raw message=",
            "proposing the transaction to the decision maker. Waiting for confirmation ...",
            "proposing the message to the decision maker. Waiting for confirmation ...",
            "received signed_message from decision_maker, message=",
            "received signed_transaction from decision_maker, message=",
            "sending send_signed_transaction to ledger ethereum, message=",
            "transaction was successfully submitted. Transaction digest=",
            "transaction was successfully settled. Transaction receipt=",
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
            "requesting batch transaction hash, sending get_raw_message to fetchai/erc1155:0.22.0, message=",
            "requesting batch atomic swap transaction, sending get_raw_transaction to fetchai/erc1155:0.22.0, message=",
            "received raw transaction=",
            "received raw message=",
            "proposing the transaction to the decision maker. Waiting for confirmation ...",
            "proposing the message to the decision maker. Waiting for confirmation ...",
            "received signed_message from decision_maker, message=",
            "received signed_transaction from decision_maker, message=",
            "sending send_signed_transaction to ledger ethereum, message=",
            "transaction was successfully submitted. Transaction digest=",
            "transaction was successfully settled. Transaction receipt=",
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


class TestTacSkillsContractFetchai(AEATestCaseManyFlaky, UseLocalFetchNode, UseSOEF):
    """Test that tac skills work."""

    capture_log = True
    LOCAL_TESTNET_CHAIN_ID = "stargateworld-3"

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

        # default routing (both for controller and participants)
        default_routing = {
            "fetchai/contract_api:1.0.0": "fetchai/ledger:0.19.0",
            "fetchai/ledger_api:1.0.0": "fetchai/ledger:0.19.0",
            "fetchai/oef_search:1.0.0": "fetchai/soef:0.26.0",
        }

        # generate random location
        location = {
            "latitude": round(uniform(-90, 90), 2),  # nosec
            "longitude": round(uniform(-180, 180), 2),  # nosec
        }

        # tac name
        tac_id = uuid.uuid4().hex
        tac_service = f"tac_service_{tac_id[:5]}"

        # prepare tac controller for test
        self.set_agent_context(tac_controller_name)
        self.add_item("connection", "fetchai/p2p_libp2p:0.25.0")
        self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.25.0")
        self.add_item("connection", "fetchai/soef:0.26.0")
        self.add_item("connection", "fetchai/ledger:0.19.0")
        self.add_item("skill", "fetchai/tac_control_contract:0.26.0")
        self.set_config("agent.default_ledger", FetchAICrypto.identifier)
        self.nested_set_config(
            "agent.required_ledgers",
            [FetchAICrypto.identifier, EthereumCrypto.identifier],
        )
        setting_path = "agent.default_routing"
        self.nested_set_config(setting_path, default_routing)
        self.run_install()

        # add keys
        self.generate_private_key(FetchAICrypto.identifier)
        self.generate_private_key(
            FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_FILE_CONNECTION
        )
        self.add_private_key(FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_FILE)
        self.add_private_key(
            FetchAICrypto.identifier,
            FETCHAI_PRIVATE_KEY_FILE_CONNECTION,
            connection=True,
        )

        # fund controller account
        controller_address = self.get_address(FetchAICrypto.identifier)
        fund_accounts_from_local_validator([controller_address], 10000000000000000000)

        self.replace_private_key_in_file(
            NON_FUNDED_FETCHAI_PRIVATE_KEY_1, FETCHAI_PRIVATE_KEY_FILE_CONNECTION
        )

        setting_path = "vendor.fetchai.connections.p2p_libp2p.cert_requests"
        settings = json.dumps(
            [
                {
                    "identifier": "acn",
                    "ledger_id": EthereumCrypto.identifier,
                    "not_after": "2022-01-01",
                    "not_before": "2021-01-01",
                    "public_key": FetchAICrypto.identifier,
                    "message_format": "{public_key}",
                    "save_path": ".certs/conn_cert.txt",
                }
            ]
        )
        self.set_config(setting_path, settings, type_="list")
        settings = json.dumps(
            [
                {
                    "identifier": "acn",
                    "ledger_id": FetchAICrypto.identifier,
                    "not_after": "2022-01-01",
                    "not_before": "2021-01-01",
                    "public_key": FetchAICrypto.identifier,
                    "message_format": "{public_key}",
                    "save_path": ".certs/conn_cert.txt",
                }
            ]
        )
        self.set_config(setting_path, settings, type_="list")

        # set SOEF configuration
        setting_path = "vendor.fetchai.connections.soef.config.chain_identifier"
        self.set_config(setting_path, "fetchai_v2_misc")

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

        # check manually built agent is the same as the fetched one
        diff = self.difference_to_fetched_agent(
            "fetchai/tac_controller_contract:0.31.0", tac_controller_name
        )
        assert (
            diff == []
        ), "Difference between created and fetched project for files={}".format(diff)

        # use local test-net
        setting_path = (
            "vendor.fetchai.connections.ledger.config.ledger_apis.fetchai.address"
        )
        self.set_config(
            setting_path,
            f"{DEFAULT_FETCH_LEDGER_ADDR}:{DEFAULT_FETCH_LEDGER_REST_PORT}",
        )
        setting_path = (
            "vendor.fetchai.connections.ledger.config.ledger_apis.fetchai.denom"
        )
        self.set_config(setting_path, DEFAULT_DENOMINATION)
        setting_path = (
            "vendor.fetchai.connections.ledger.config.ledger_apis.fetchai.chain_id"
        )
        self.set_config(setting_path, self.LOCAL_TESTNET_CHAIN_ID)

        # change SOEF configuration to local
        setting_path = "vendor.fetchai.connections.soef.config.is_https"
        self.set_config(setting_path, False)
        setting_path = "vendor.fetchai.connections.soef.config.soef_addr"
        self.set_config(setting_path, "127.0.0.1")
        setting_path = "vendor.fetchai.connections.soef.config.soef_port"
        self.set_config(setting_path, 12002)

        # prepare agents for test
        for agent_name, config in (
            (tac_aea_one, NON_GENESIS_CONFIG),
            (tac_aea_two, NON_GENESIS_CONFIG_TWO),
        ):
            self.set_agent_context(agent_name)

            # add items
            self.add_item("connection", "fetchai/p2p_libp2p:0.25.0")
            self.add_item("connection", "fetchai/soef:0.26.0")
            self.add_item("connection", "fetchai/ledger:0.19.0")
            self.add_item("skill", "fetchai/tac_participation:0.24.0")
            self.add_item("skill", "fetchai/tac_negotiation:0.28.0")

            # set AEA config (no component overrides)
            self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.25.0")
            self.set_config("agent.default_ledger", FetchAICrypto.identifier)
            self.nested_set_config(
                "agent.required_ledgers",
                [FetchAICrypto.identifier, EthereumCrypto.identifier],
            )
            setting_path = "agent.default_routing"
            self.nested_set_config(setting_path, default_routing)
            data = {
                "dotted_path": "aea.decision_maker.gop:DecisionMakerHandler",
                "file_path": None,
                "config": {},
            }
            setting_path = "agent.decision_maker_handler"
            self.nested_set_config(setting_path, data)

            # install PyPI dependencies
            self.run_install()

            # add keys
            self.generate_private_key(FetchAICrypto.identifier)
            self.generate_private_key(
                FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_FILE_CONNECTION
            )
            self.add_private_key(FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_FILE)
            self.add_private_key(
                FetchAICrypto.identifier,
                FETCHAI_PRIVATE_KEY_FILE_CONNECTION,
                connection=True,
            )

            # fund participant account
            participant_address = self.get_address(FetchAICrypto.identifier)
            fund_accounts_from_local_validator(
                [participant_address], 10000000000000000000
            )

            # set p2p configs
            setting_path = "vendor.fetchai.connections.p2p_libp2p.config"
            self.nested_set_config(setting_path, config)
            setting_path = "vendor.fetchai.connections.p2p_libp2p.cert_requests"
            settings = json.dumps(
                [
                    {
                        "identifier": "acn",
                        "ledger_id": EthereumCrypto.identifier,
                        "not_after": "2022-01-01",
                        "not_before": "2021-01-01",
                        "public_key": FetchAICrypto.identifier,
                        "message_format": "{public_key}",
                        "save_path": ".certs/conn_cert.txt",
                    }
                ]
            )
            self.set_config(setting_path, settings, type_="list")
            settings = json.dumps(
                [
                    {
                        "identifier": "acn",
                        "ledger_id": FetchAICrypto.identifier,
                        "not_after": "2022-01-01",
                        "not_before": "2021-01-01",
                        "public_key": FetchAICrypto.identifier,
                        "message_format": "{public_key}",
                        "save_path": ".certs/conn_cert.txt",
                    }
                ]
            )
            self.set_config(setting_path, settings, type_="list")

            # set SOEF configuration
            setting_path = "vendor.fetchai.connections.soef.config.chain_identifier"
            self.set_config(setting_path, "fetchai_v2_misc")

            # set tac participant configuration
            self.set_config(
                "vendor.fetchai.skills.tac_participation.models.game.args.is_using_contract",
                True,
                "bool",
            )

            # set tac negotiation configuration
            self.set_config(
                "vendor.fetchai.skills.tac_negotiation.models.strategy.args.is_contract_tx",
                True,
                "bool",
            )

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

            diff = self.difference_to_fetched_agent(
                "fetchai/tac_participant_contract:0.21.0", agent_name
            )
            assert (
                diff == []
            ), "Difference between created and fetched project for files={}".format(
                diff
            )

            # use local test-net
            setting_path = (
                "vendor.fetchai.connections.ledger.config.ledger_apis.fetchai.address"
            )
            self.set_config(
                setting_path,
                f"{DEFAULT_FETCH_LEDGER_ADDR}:{DEFAULT_FETCH_LEDGER_REST_PORT}",
            )
            setting_path = (
                "vendor.fetchai.connections.ledger.config.ledger_apis.fetchai.denom"
            )
            self.set_config(setting_path, DEFAULT_DENOMINATION)
            setting_path = (
                "vendor.fetchai.connections.ledger.config.ledger_apis.fetchai.chain_id"
            )
            self.set_config(setting_path, self.LOCAL_TESTNET_CHAIN_ID)

            # change SOEF configuration to local
            setting_path = "vendor.fetchai.connections.soef.config.is_https"
            self.set_config(setting_path, False)
            setting_path = "vendor.fetchai.connections.soef.config.soef_addr"
            self.set_config(setting_path, "127.0.0.1")
            setting_path = "vendor.fetchai.connections.soef.config.soef_port"
            self.set_config(setting_path, 12002)

            self.set_config(
                "vendor.fetchai.skills.tac_negotiation.models.strategy.args.service_key",
                tac_service,
            )

        # run tac controller
        self.set_agent_context(tac_controller_name)
        self.run_cli_command("build", cwd=self._get_cwd())
        self.run_cli_command("issue-certificates", cwd=self._get_cwd())
        now = datetime.datetime.now().strftime("%d %m %Y %H:%M")
        now_min = datetime.datetime.strptime(now, "%d %m %Y %H:%M")
        fut = now_min + datetime.timedelta(
            0, 120
        )  # we provide 2 minutes time for contract deployment
        start_time = fut.strftime("%d %m %Y %H:%M")
        setting_path = "vendor.fetchai.skills.tac_control_contract.models.parameters.args.registration_start_time"
        self.set_config(setting_path, start_time)
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
            "requesting contract initialisation transaction...",
            "contract deployed.",
            "registering TAC data model on SOEF.",
            "TAC open for registration until:",
        )
        missing_strings = self.missing_from_output(
            tac_controller_process, check_strings, timeout=180, is_terminating=False
        )  # we need to wait sufficiently long (at least 2 minutes - see above for deployment)
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in tac_controller output.".format(missing_strings)

        # run two agents (participants)
        self.set_agent_context(tac_aea_one)
        self.run_cli_command("build", cwd=self._get_cwd())
        self.run_cli_command("issue-certificates", cwd=self._get_cwd())
        tac_aea_one_process = self.run_agent()

        self.set_agent_context(tac_aea_two)
        self.run_cli_command("build", cwd=self._get_cwd())
        self.run_cli_command("issue-certificates", cwd=self._get_cwd())
        tac_aea_two_process = self.run_agent()

        check_strings = (
            "Starting libp2p node...",
            "Connecting to libp2p node...",
            "Successfully connected to libp2p node!",
            LIBP2P_SUCCESS_MESSAGE,
            "Start processing messages...",
            "searching for TAC, search_id=",
        )
        missing_strings = self.missing_from_output(
            tac_aea_one_process, check_strings, timeout=30, is_terminating=False
        )
        check_strings = ("found the TAC controller. Registering...",)
        missing_strings = self.missing_from_output(
            tac_aea_one_process, check_strings, timeout=60, is_terminating=False
        )  # we need to wait sufficiently long (at least 1 minutes - for registration)
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
            tac_aea_two_process, check_strings, timeout=30, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in tac_aea_two output.".format(missing_strings)

        check_strings = (
            "registered as 'tac_participant_one'",
            "registered as 'tac_participant_two'",
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
            "sending match_accept_w_inform to",
            "requesting batch atomic swap transaction, sending get_raw_transaction to fetchai/erc1155:0.22.0, message=",
            "received raw transaction=",
            "proposing the transaction to the decision maker. Waiting for confirmation ...",
            "received signed_transaction from decision_maker, message=",
            "sending inform_signed_transaction to",
            "received inform_signed_transaction from",
            "sending send_signed_transaction to ledger fetchai, message=",
            "transaction was successfully submitted. Transaction digest=",
            "transaction was successfully settled. Transaction receipt=",
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
            "sending match_accept_w_inform to",
            "requesting batch atomic swap transaction, sending get_raw_transaction to fetchai/erc1155:0.22.0, message=",
            "received raw transaction=",
            "proposing the transaction to the decision maker. Waiting for confirmation ...",
            "received signed_transaction from decision_maker, message=",
            "sending inform_signed_transaction to",
            "received inform_signed_transaction from",
            "sending send_signed_transaction to ledger fetchai, message=",
            "transaction was successfully submitted. Transaction digest=",
            "transaction was successfully settled. Transaction receipt=",
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
