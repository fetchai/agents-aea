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
"""This test module contains the integration test for the generic buyer and seller skills."""
import json
import os

import pytest
from aea_ledger_ethereum import EthereumCrypto
from aea_ledger_fetchai import FetchAICrypto

from aea.test_tools.test_cases import AEATestCaseManyFlaky

from packages.fetchai.connections.p2p_libp2p.connection import LIBP2P_SUCCESS_MESSAGE

from tests.conftest import (
    CUR_PATH,
    DEFAULT_FETCH_LEDGER_ADDR,
    DEFAULT_FETCH_LEDGER_REST_PORT,
    ETHEREUM_PRIVATE_KEY_FILE,
    FETCHAI_PRIVATE_KEY_FILE,
    FETCHAI_PRIVATE_KEY_FILE_CONNECTION,
    FUNDED_ETH_PRIVATE_KEY_2,
    FUNDED_ETH_PRIVATE_KEY_3,
    FUNDED_FETCHAI_PRIVATE_KEY_1,
    FUNDED_FETCHAI_PRIVATE_KEY_2,
    MAX_FLAKY_RERUNS_ETH,
    UseGanache,
    UseLocalFetchNode,
)


ORACLE_CONTRACT_ADDRESS_FILE = os.path.join(CUR_PATH, "oracle_contract_address.txt")


@pytest.mark.integration
class TestOracleSkillsFetchAI(AEATestCaseManyFlaky, UseLocalFetchNode):
    """Test that oracle skills work."""

    @pytest.mark.ledger
    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS_ETH)  # cause possible network issues
    def test_oracle(
        self, fund_fetchai_accounts,
    ):
        """Run the oracle skills sequence."""
        oracle_agent_name = "oracle_aea"
        client_agent_name = "client_aea"
        processes = []
        try:

            ledger_id = "fetchai"
            private_key_file = FETCHAI_PRIVATE_KEY_FILE
            funded_private_key_1 = FUNDED_FETCHAI_PRIVATE_KEY_1
            funded_private_key_2 = FUNDED_FETCHAI_PRIVATE_KEY_2
            update_function = "update_oracle_value"
            query_function = "query_oracle_value"

            self.create_agents(oracle_agent_name, client_agent_name)

            default_routing = {
                "fetchai/ledger_api:1.0.0": "fetchai/ledger:0.19.0",
                "fetchai/contract_api:1.0.0": "fetchai/ledger:0.19.0",
                "fetchai/http:1.0.0": "fetchai/http_client:0.23.0",
                "fetchai/prometheus:1.0.0": "fetchai/prometheus:0.8.0",
            }

            # add packages for oracle agent
            self.set_agent_context(oracle_agent_name)
            self.add_item("connection", "fetchai/p2p_libp2p:0.25.0")
            self.add_item("connection", "fetchai/ledger:0.19.0")
            self.add_item("connection", "fetchai/http_client:0.23.0")
            self.add_item("connection", "fetchai/prometheus:0.8.0")
            self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.25.0")
            self.set_config("agent.default_ledger", ledger_id)
            self.nested_set_config(
                "agent.required_ledgers", [FetchAICrypto.identifier],
            )
            setting_path = "agent.default_routing"
            self.nested_set_config(setting_path, default_routing)
            self.add_item("skill", "fetchai/advanced_data_request:0.6.0")
            self.add_item("contract", "fetchai/oracle:0.11.0")
            self.add_item("skill", "fetchai/simple_oracle:0.14.0")

            # set up data request skill to fetch coin price
            self.set_config(
                "vendor.fetchai.skills.advanced_data_request.models.advanced_data_request_model.args.url",
                "https://api.coingecko.com/api/v3/simple/price?ids=fetch-ai&vs_currencies=usd",
                type_="str",
            )
            self.set_config(
                "vendor.fetchai.skills.advanced_data_request.models.advanced_data_request_model.args.outputs",
                '[{"name": "price", "json_path": "fetch-ai.usd"}]',
                type_="list",
            )

            setting_path = (
                "vendor.fetchai.skills.simple_oracle.models.strategy.args.ledger_id"
            )
            self.set_config(setting_path, ledger_id)
            setting_path = "vendor.fetchai.skills.simple_oracle.models.strategy.args.update_function"
            self.set_config(setting_path, update_function)
            setting_path = "vendor.fetchai.skills.simple_oracle.models.strategy.args.oracle_value_name"
            self.set_config(setting_path, "price")

            self.generate_private_key(ledger_id)
            self.add_private_key(ledger_id, private_key_file)
            self.replace_private_key_in_file(funded_private_key_1, private_key_file)
            self.generate_private_key(
                FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_FILE_CONNECTION
            )
            self.add_private_key(
                FetchAICrypto.identifier,
                FETCHAI_PRIVATE_KEY_FILE_CONNECTION,
                connection=True,
            )
            setting_path = "vendor.fetchai.connections.p2p_libp2p.cert_requests"
            settings = json.dumps(
                [
                    {
                        "identifier": "acn",
                        "ledger_id": ledger_id,
                        "not_after": "2022-01-01",
                        "not_before": "2021-01-01",
                        "public_key": FetchAICrypto.identifier,
                        "message_format": "{public_key}",
                        "save_path": ".certs/conn_cert.txt",
                    }
                ]
            )
            self.set_config(setting_path, settings, type_="list")
            self.run_install()

            # redirect fetchai ledger address to local test node
            setting_path = (
                "vendor.fetchai.connections.ledger.config.ledger_apis.fetchai.address"
            )
            self.set_config(
                setting_path,
                f"{DEFAULT_FETCH_LEDGER_ADDR}:{DEFAULT_FETCH_LEDGER_REST_PORT}",
            )

            # use alternate port for prometheus connection
            setting_path = "vendor.fetchai.connections.prometheus.config.port"
            self.set_config(setting_path, 9091, type_="int")

            setting_path = "vendor.fetchai.skills.simple_oracle.models.strategy.args.contract_address_file"
            self.set_config(setting_path, ORACLE_CONTRACT_ADDRESS_FILE)

            # add packages for oracle client agent
            self.set_agent_context(client_agent_name)
            self.add_item("connection", "fetchai/ledger:0.19.0")
            self.add_item("connection", "fetchai/http_client:0.23.0")
            self.set_config("agent.default_connection", "fetchai/ledger:0.19.0")
            self.set_config("agent.default_ledger", ledger_id)
            self.nested_set_config(
                "agent.required_ledgers", [FetchAICrypto.identifier],
            )

            default_routing = {
                "fetchai/ledger_api:1.0.0": "fetchai/ledger:0.19.0",
                "fetchai/contract_api:1.0.0": "fetchai/ledger:0.19.0",
                "fetchai/http:1.0.0": "fetchai/http_client:0.23.0",
            }
            setting_path = "agent.default_routing"
            self.nested_set_config(setting_path, default_routing)
            self.add_item("contract", "fetchai/oracle_client:0.10.0")
            self.add_item("contract", "fetchai/fet_erc20:0.9.0")
            self.add_item("skill", "fetchai/simple_oracle_client:0.11.0")

            self.generate_private_key(ledger_id)
            self.add_private_key(ledger_id, private_key_file)
            self.replace_private_key_in_file(funded_private_key_2, private_key_file)
            setting_path = "vendor.fetchai.skills.simple_oracle_client.models.strategy.args.ledger_id"
            self.set_config(setting_path, ledger_id)
            setting_path = "vendor.fetchai.skills.simple_oracle_client.models.strategy.args.query_function"
            self.set_config(setting_path, query_function)

            # redirect fetchai ledger address to local test node
            setting_path = (
                "vendor.fetchai.connections.ledger.config.ledger_apis.fetchai.address"
            )
            self.set_config(
                setting_path,
                f"{DEFAULT_FETCH_LEDGER_ADDR}:{DEFAULT_FETCH_LEDGER_REST_PORT}",
            )

            # run oracle agent
            self.set_agent_context(oracle_agent_name)
            self.run_cli_command("build", cwd=self._get_cwd())
            self.run_cli_command("issue-certificates", cwd=self._get_cwd())
            oracle_aea_process = self.run_agent()
            processes.append(oracle_aea_process)

            check_strings = (
                "Starting libp2p node...",
                "Connecting to libp2p node...",
                "Successfully connected to libp2p node!",
                LIBP2P_SUCCESS_MESSAGE,
            )
            missing_strings = self.missing_from_output(
                oracle_aea_process, check_strings, timeout=60, is_terminating=False,
            )
            assert (
                missing_strings == []
            ), "Strings {} didn't appear in aea output: \n{}".format(
                missing_strings, self.stdout[oracle_aea_process.pid]
            )

            check_strings = (
                "setting up HttpHandler",
                "setting up AdvancedDataRequestBehaviour",
                "Setting up Fetch oracle contract...",
                "Fetching data from https://api.coingecko.com/api/v3/simple/price?ids=fetch-ai&vs_currencies=usd",
                "received raw transaction=",
                "Observation: {'price': {'value': ",
                "transaction was successfully submitted. Transaction digest=",
                "requesting transaction receipt.",
                "transaction was successfully settled. Transaction receipt=",
                "Oracle value successfully updated!",
            )
            missing_strings = self.missing_from_output(
                oracle_aea_process, check_strings, timeout=60, is_terminating=False,
            )
            assert (
                missing_strings == []
            ), "Strings {} didn't appear in aea output: \n{}".format(
                missing_strings, self.stdout[oracle_aea_process.pid]
            )

            # Get oracle contract address from file
            with open(ORACLE_CONTRACT_ADDRESS_FILE) as file:
                oracle_address = file.read()

            # run oracle client agent
            self.set_agent_context(client_agent_name)

            # set oracle contract address in oracle client
            setting_path = "vendor.fetchai.skills.simple_oracle_client.models.strategy.args.oracle_contract_address"
            self.set_config(setting_path, oracle_address)

            client_aea_process = self.run_agent()
            processes.append(client_aea_process)

            check_strings = (
                "requesting contract deployment transaction...",
                "received raw transaction=",
                "transaction was successfully submitted. Transaction digest=",
                "requesting transaction receipt.",
                "transaction was successfully settled. Transaction receipt=",
                "Oracle value successfully requested!",
            )
            missing_strings = self.missing_from_output(
                client_aea_process, check_strings, timeout=60, is_terminating=False,
            )
            assert (
                missing_strings == []
            ), "Strings {} didn't appear in aea output: \n{}".format(
                missing_strings, self.stdout[client_aea_process.pid]
            )
        finally:
            if processes:
                self.terminate_agents(*processes)
            assert (
                self.is_successfully_terminated()
            ), "Agents weren't successfully terminated."


@pytest.mark.integration
class TestOracleSkillsETH(AEATestCaseManyFlaky, UseGanache):
    """Test that oracle skills work."""

    @pytest.mark.ledger
    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS_ETH)  # cause possible network issues
    def test_oracle(
        self, erc20_contract, oracle_contract,
    ):
        """Run the oracle skills sequence."""
        oracle_agent_name = "oracle_aea"
        client_agent_name = "client_aea"
        processes = []
        try:

            _, erc20_address = erc20_contract
            _, oracle_address = oracle_contract

            ledger_id = "ethereum"
            private_key_file = ETHEREUM_PRIVATE_KEY_FILE
            funded_private_key_1 = FUNDED_ETH_PRIVATE_KEY_3
            funded_private_key_2 = FUNDED_ETH_PRIVATE_KEY_2
            update_function = "updateOracleValue"
            query_function = "queryOracleValue"

            self.create_agents(oracle_agent_name, client_agent_name)

            default_routing = {
                "fetchai/ledger_api:1.0.0": "fetchai/ledger:0.19.0",
                "fetchai/contract_api:1.0.0": "fetchai/ledger:0.19.0",
                "fetchai/http:1.0.0": "fetchai/http_client:0.23.0",
                "fetchai/prometheus:1.0.0": "fetchai/prometheus:0.8.0",
            }

            # add packages for oracle agent
            self.set_agent_context(oracle_agent_name)
            self.add_item("connection", "fetchai/p2p_libp2p:0.25.0")
            self.add_item("connection", "fetchai/ledger:0.19.0")
            self.add_item("connection", "fetchai/http_client:0.23.0")
            self.add_item("connection", "fetchai/prometheus:0.8.0")
            self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.25.0")
            self.set_config("agent.default_ledger", ledger_id)
            self.nested_set_config(
                "agent.required_ledgers",
                [FetchAICrypto.identifier, EthereumCrypto.identifier],
            )
            setting_path = "agent.default_routing"
            self.nested_set_config(setting_path, default_routing)
            self.add_item("skill", "fetchai/advanced_data_request:0.6.0")
            self.add_item("contract", "fetchai/oracle:0.11.0")
            self.add_item("skill", "fetchai/simple_oracle:0.14.0")

            # set up data request skill to fetch coin price
            self.set_config(
                "vendor.fetchai.skills.advanced_data_request.models.advanced_data_request_model.args.url",
                "https://api.coingecko.com/api/v3/simple/price?ids=fetch-ai&vs_currencies=usd",
                type_="str",
            )
            self.set_config(
                "vendor.fetchai.skills.advanced_data_request.models.advanced_data_request_model.args.outputs",
                '[{"name": "price", "json_path": "fetch-ai.usd"}]',
                type_="list",
            )

            setting_path = (
                "vendor.fetchai.skills.simple_oracle.models.strategy.args.ledger_id"
            )
            self.set_config(setting_path, ledger_id)
            setting_path = "vendor.fetchai.skills.simple_oracle.models.strategy.args.update_function"
            self.set_config(setting_path, update_function)
            setting_path = "vendor.fetchai.skills.simple_oracle.models.strategy.args.oracle_value_name"
            self.set_config(setting_path, "price")

            self.generate_private_key(ledger_id)
            self.add_private_key(ledger_id, private_key_file)
            self.replace_private_key_in_file(funded_private_key_1, private_key_file)
            self.generate_private_key(
                FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_FILE_CONNECTION
            )
            self.add_private_key(
                FetchAICrypto.identifier,
                FETCHAI_PRIVATE_KEY_FILE_CONNECTION,
                connection=True,
            )
            setting_path = "vendor.fetchai.connections.p2p_libp2p.cert_requests"
            settings = json.dumps(
                [
                    {
                        "identifier": "acn",
                        "ledger_id": ledger_id,
                        "not_after": "2022-01-01",
                        "not_before": "2021-01-01",
                        "public_key": FetchAICrypto.identifier,
                        "message_format": "{public_key}",
                        "save_path": ".certs/conn_cert.txt",
                    }
                ]
            )
            self.set_config(setting_path, settings, type_="list")
            self.run_install()

            diff = self.difference_to_fetched_agent(
                "fetchai/coin_price_oracle:0.16.0", oracle_agent_name
            )
            assert (
                diff == []
            ), "Difference between created and fetched project for files={}".format(
                diff
            )

            # set erc20 address
            setting_path = (
                "vendor.fetchai.skills.simple_oracle.models.strategy.args.erc20_address"
            )
            self.set_config(setting_path, erc20_address)
            setting_path = "vendor.fetchai.skills.simple_oracle.models.strategy.args.contract_address"
            self.set_config(setting_path, oracle_address)

            setting_path = "vendor.fetchai.skills.simple_oracle.models.strategy.args.contract_address_file"
            self.set_config(setting_path, ORACLE_CONTRACT_ADDRESS_FILE)

            # add packages for oracle client agent
            self.set_agent_context(client_agent_name)
            self.add_item("connection", "fetchai/ledger:0.19.0")
            self.add_item("connection", "fetchai/http_client:0.23.0")
            self.set_config("agent.default_connection", "fetchai/ledger:0.19.0")
            self.set_config("agent.default_ledger", ledger_id)
            self.nested_set_config(
                "agent.required_ledgers",
                [FetchAICrypto.identifier, EthereumCrypto.identifier],
            )

            default_routing = {
                "fetchai/ledger_api:1.0.0": "fetchai/ledger:0.19.0",
                "fetchai/contract_api:1.0.0": "fetchai/ledger:0.19.0",
                "fetchai/http:1.0.0": "fetchai/http_client:0.23.0",
            }
            setting_path = "agent.default_routing"
            self.nested_set_config(setting_path, default_routing)
            self.add_item("contract", "fetchai/oracle_client:0.10.0")
            self.add_item("contract", "fetchai/fet_erc20:0.9.0")
            self.add_item("skill", "fetchai/simple_oracle_client:0.11.0")

            self.generate_private_key(ledger_id)
            self.add_private_key(ledger_id, private_key_file)
            self.replace_private_key_in_file(funded_private_key_2, private_key_file)
            setting_path = "vendor.fetchai.skills.simple_oracle_client.models.strategy.args.ledger_id"
            self.set_config(setting_path, ledger_id)
            setting_path = "vendor.fetchai.skills.simple_oracle_client.models.strategy.args.query_function"
            self.set_config(setting_path, query_function)

            diff = self.difference_to_fetched_agent(
                "fetchai/coin_price_oracle_client:0.11.0", client_agent_name
            )
            assert (
                diff == []
            ), "Difference between created and fetched project for files={}".format(
                diff
            )

            # set addresses *after* comparison with fetched agent!
            setting_path = "vendor.fetchai.skills.simple_oracle_client.models.strategy.args.erc20_address"
            self.set_config(setting_path, erc20_address)

            # run oracle agent
            self.set_agent_context(oracle_agent_name)
            self.run_cli_command("build", cwd=self._get_cwd())
            self.run_cli_command("issue-certificates", cwd=self._get_cwd())
            oracle_aea_process = self.run_agent()
            processes.append(oracle_aea_process)

            check_strings = (
                "Starting libp2p node...",
                "Connecting to libp2p node...",
                "Successfully connected to libp2p node!",
                LIBP2P_SUCCESS_MESSAGE,
            )
            missing_strings = self.missing_from_output(
                oracle_aea_process, check_strings, timeout=60, is_terminating=False,
            )
            assert (
                missing_strings == []
            ), "Strings {} didn't appear in aea output: \n{}".format(
                missing_strings, self.stdout[oracle_aea_process.pid]
            )

            check_strings = (
                "setting up HttpHandler",
                "setting up AdvancedDataRequestBehaviour",
                "Setting up Fetch oracle contract...",
                "Fetching data from https://api.coingecko.com/api/v3/simple/price?ids=fetch-ai&vs_currencies=usd",
                "received raw transaction=",
                "Observation: {'price': {'value': ",
                "transaction was successfully submitted. Transaction digest=",
                "requesting transaction receipt.",
                "transaction was successfully settled. Transaction receipt=",
                "Oracle value successfully updated!",
            )
            missing_strings = self.missing_from_output(
                oracle_aea_process, check_strings, timeout=60, is_terminating=False,
            )
            assert (
                missing_strings == []
            ), "Strings {} didn't appear in aea output: \n{}".format(
                missing_strings, self.stdout[oracle_aea_process.pid]
            )

            if ledger_id == FetchAICrypto.identifier:
                # Get oracle contract address from file
                with open(ORACLE_CONTRACT_ADDRESS_FILE) as file:
                    oracle_address = file.read()

            # run oracle client agent
            self.set_agent_context(client_agent_name)

            # set oracle contract address in oracle client
            setting_path = "vendor.fetchai.skills.simple_oracle_client.models.strategy.args.oracle_contract_address"
            self.set_config(setting_path, oracle_address)

            client_aea_process = self.run_agent()
            processes.append(client_aea_process)

            check_strings = (
                "requesting contract deployment transaction...",
                "received raw transaction=",
                "transaction was successfully submitted. Transaction digest=",
                "requesting transaction receipt.",
                "transaction was successfully settled. Transaction receipt=",
                "Oracle value successfully requested!",
            )
            missing_strings = self.missing_from_output(
                client_aea_process, check_strings, timeout=60, is_terminating=False,
            )
            assert (
                missing_strings == []
            ), "Strings {} didn't appear in aea output: \n{}".format(
                missing_strings, self.stdout[client_aea_process.pid]
            )
        finally:
            if processes:
                self.terminate_agents(*processes)
            assert (
                self.is_successfully_terminated()
            ), "Agents weren't successfully terminated."
