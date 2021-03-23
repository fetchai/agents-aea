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
"""This test module contains the tests for the `aea launch` sub-command."""
import json
import os
import sqlite3
import sys
import uuid

import pytest
from aea_ledger_fetchai import FetchAICrypto

from aea.test_tools.test_cases import AEATestCaseMany

from tests.common.pexpect_popen import PexpectWrapper
from tests.conftest import FETCHAI_PRIVATE_KEY_FILE_CONNECTION


class TestLaunchEndToEnd(AEATestCaseMany):
    """Perform aea launch end to end test."""

    key = "seller_service"
    value = None

    registration_agent_connection = {
        "delegate_uri": "127.0.0.1:11011",
        "entry_peers": [],
        "ledger_id": "fetchai",
        "local_uri": "127.0.0.1:9011",
        "log_file": "libp2p_node.log",
        "public_uri": "127.0.0.1:9011",
    }

    search_agent_connection = {
        "delegate_uri": "127.0.0.1:11012",
        "entry_peers": [],
        "ledger_id": "fetchai",
        "local_uri": "127.0.0.1:9012",
        "log_file": "libp2p_node.log",
        "public_uri": "127.0.0.1:9012",
    }

    @pytest.mark.integration
    def test_end_to_end(self):
        """Perform end to end test with simple register/search agents."""
        registration_agent_name = "registration_agent"
        self.value = uuid.uuid4().hex
        self.fetch_agent(
            "fetchai/simple_service_registration",
            agent_name=registration_agent_name,
            is_local=True,
        )

        self.run_cli_command(
            "config",
            "set",
            "vendor.fetchai.connections.p2p_libp2p.config",
            "--type",
            "dict",
            json.dumps(self.registration_agent_connection),
            cwd=registration_agent_name,
        )
        self.run_cli_command(
            "config",
            "set",
            "vendor.fetchai.skills.simple_service_registration.models.strategy.args.service_data",
            "--type",
            "dict",
            json.dumps({"key": self.key, "value": self.value}),
            cwd=registration_agent_name,
        )
        self.run_cli_command(
            "config",
            "set",
            "vendor.fetchai.connections.soef.config.token_storage_path",
            os.path.join(self.t, registration_agent_name, "soef_key.txt"),
            cwd=registration_agent_name,
        )

        storage_file_name = os.path.abspath(
            os.path.join(registration_agent_name, "test.db")
        )
        self.run_cli_command(
            "config",
            "set",
            "agent.storage_uri",
            f"sqlite://{storage_file_name}",
            cwd=registration_agent_name,
        )

        search_agent_name = "search_agent"
        self.fetch_agent(
            "fetchai/simple_service_search",
            agent_name=search_agent_name,
            is_local=True,
        )
        self.run_cli_command(
            "config",
            "set",
            "vendor.fetchai.connections.p2p_libp2p.config",
            "--type",
            "dict",
            json.dumps(self.search_agent_connection),
            cwd=search_agent_name,
        )
        self.run_cli_command(
            "config",
            "set",
            "vendor.fetchai.skills.simple_service_search.models.strategy.args.search_query",
            "--type",
            "dict",
            json.dumps(
                {
                    "constraint_type": "==",
                    "search_key": self.key,
                    "search_value": self.value,
                }
            ),
            cwd=search_agent_name,
        )
        self.run_cli_command(
            "config",
            "set",
            "vendor.fetchai.skills.simple_service_search.behaviours.service_search.args.tick_interval",
            "--type",
            "int",
            "2",
            cwd=search_agent_name,
        )
        self.run_cli_command(
            "config",
            "set",
            "vendor.fetchai.connections.soef.config.token_storage_path",
            os.path.join(self.t, search_agent_name, "soef_key.txt"),
            cwd=search_agent_name,
        )
        self.run_cli_command(
            "build", cwd=registration_agent_name,
        )
        self.run_cli_command(
            "build", cwd=search_agent_name,
        )
        self.set_agent_context(registration_agent_name)
        self.generate_private_key(
            FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_FILE_CONNECTION
        )
        self.add_private_key(
            FetchAICrypto.identifier,
            FETCHAI_PRIVATE_KEY_FILE_CONNECTION,
            connection=True,
        )
        self.generate_private_key()
        self.add_private_key()
        self.unset_agent_context()
        self.run_cli_command(
            "issue-certificates", cwd=registration_agent_name,
        )
        self.set_agent_context(search_agent_name)
        self.generate_private_key(
            FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_FILE_CONNECTION
        )
        self.add_private_key(
            FetchAICrypto.identifier,
            FETCHAI_PRIVATE_KEY_FILE_CONNECTION,
            connection=True,
        )
        self.generate_private_key()
        self.add_private_key()
        self.unset_agent_context()
        self.run_cli_command(
            "issue-certificates", cwd=search_agent_name,
        )

        proc = PexpectWrapper(  # nosec
            [
                sys.executable,
                "-m",
                "aea.cli",
                "-v",
                "DEBUG",
                "launch",
                registration_agent_name,
                search_agent_name,
            ],
            env=os.environ,
            maxread=10000,
            encoding="utf-8",
            logfile=sys.stdout,
        )
        try:
            proc.expect_all(
                [f"[{search_agent_name}] found number of agents=1, search_response"],
                timeout=30,
            )
        finally:
            proc.control_c()
            proc.expect("Exit cli. code: 0", timeout=30)

        assert os.path.exists(storage_file_name)
        con = sqlite3.connect(storage_file_name)
        try:
            cursor = con.cursor()
            tables = cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table';"
            ).fetchall()
            assert tables
            table_name = tables[0][0]
            num_of_records = cursor.execute(  # nosec
                f"SELECT count(*) FROM {table_name};"
            ).fetchone()[0]
            assert num_of_records > 0
        finally:
            con.close
