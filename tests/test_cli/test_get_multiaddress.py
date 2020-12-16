# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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
"""This test module contains the tests for commands in aea.cli.get_multiaddress module."""
from unittest import mock

import base58
import pytest

from aea.test_tools.test_cases import AEATestCaseEmpty

from packages.fetchai.connections.stub.connection import (
    PUBLIC_ID as STUB_CONNECTION_PUBLIC_ID,
)

from tests.conftest import FETCHAI


class TestGetMultiAddressCommandPositive(AEATestCaseEmpty):
    """Test case for CLI get-multiaddress command."""

    def test_run(self, *mocks):
        """Run the test."""
        self.generate_private_key(FETCHAI)
        self.add_private_key(FETCHAI, connection=False)

        result = self.run_cli_command(
            "get-multiaddress", FETCHAI, cwd=self.current_agent_context
        )

        assert result.exit_code == 0
        # test we can decode the output
        base58.b58decode(result.stdout)


class TestGetMultiAddressCommandConnectionPositive(AEATestCaseEmpty):
    """Test case for CLI get-multiaddress command with --connection flag."""

    def test_run(self, *mocks):
        """Run the test."""
        self.generate_private_key(FETCHAI)
        self.add_private_key(FETCHAI, connection=True)

        result = self.run_cli_command(
            "get-multiaddress", FETCHAI, "--connection", cwd=self.current_agent_context
        )

        assert result.exit_code == 0
        # test we can decode the output
        base58.b58decode(result.stdout)


class TestGetMultiAddressCommandConnectionIdPositive(AEATestCaseEmpty):
    """Test case for CLI get-multiaddress command with --connection flag."""

    def test_run(self, *mocks):
        """Run the test."""
        self.generate_private_key(FETCHAI)
        self.add_private_key(FETCHAI, connection=True)

        self.nested_set_config(
            "vendor.fetchai.connections.stub.config",
            {"host": "127.0.0.1", "port": 10000},
        )

        result = self.run_cli_command(
            "get-multiaddress",
            FETCHAI,
            "--connection",
            "--connection-id",
            str(STUB_CONNECTION_PUBLIC_ID),
            "--host-field",
            "host",
            "--port-field",
            "port",
            cwd=self.current_agent_context,
        )

        assert result.exit_code == 0
        # multiaddr test
        expected_multiaddr_prefix = "/dns4/127.0.0.1/tcp/10000/p2p/"
        assert expected_multiaddr_prefix in result.stdout
        base58_addr = str(result.stdout).replace(expected_multiaddr_prefix, "")
        base58.b58decode(base58_addr)


class TestGetMultiAddressCommandConnectionIdURIPositive(AEATestCaseEmpty):
    """Test case for CLI get-multiaddress command with --connection flag and --uri."""

    def test_run(self, *mocks):
        """Run the test."""
        self.generate_private_key(FETCHAI)
        self.add_private_key(FETCHAI, connection=True)

        self.nested_set_config(
            "vendor.fetchai.connections.stub.config", {"public_uri": "127.0.0.1:10000"}
        )

        result = self.run_cli_command(
            "get-multiaddress",
            FETCHAI,
            "--connection",
            "--connection-id",
            str(STUB_CONNECTION_PUBLIC_ID),
            "--uri-field",
            "public_uri",
            cwd=self.current_agent_context,
        )

        assert result.exit_code == 0
        # multiaddr test
        expected_multiaddr_prefix = "/dns4/127.0.0.1/tcp/10000/p2p/"
        assert expected_multiaddr_prefix in result.stdout
        base58_addr = str(result.stdout).replace(expected_multiaddr_prefix, "")
        base58.b58decode(base58_addr)


class TestGetMultiAddressCommandConnectionNegative(AEATestCaseEmpty):
    """Test case for CLI get-multiaddress command with --connection flag."""

    def test_run(self, *mocks):
        """Run the test."""
        self.generate_private_key(FETCHAI)
        self.add_private_key(FETCHAI, connection=True)

        result = self.run_cli_command(
            "get-multiaddress", FETCHAI, "--connection", cwd=self.current_agent_context
        )

        assert result.exit_code == 0
        # test we can decode the output
        base58.b58decode(result.stdout)


class TestGetMultiAddressCommandNegativeMissingKey(AEATestCaseEmpty):
    """Test case for CLI get-multiaddress when the key is missing."""

    def test_run(self, *mocks):
        """Run the test."""
        # this will cause exception because no key is added to the AEA project.
        with pytest.raises(
            Exception,
            match="Cannot find '{}'. Please check private_key_path.".format(FETCHAI),
        ):
            self.run_cli_command(
                "get-multiaddress", FETCHAI, cwd=self.current_agent_context
            )


class TestGetMultiAddressCommandNegativePeerId(AEATestCaseEmpty):
    """Test case for CLI get-multiaddress when the peer id computation raises an error."""

    @mock.patch(
        "aea.cli.get_multiaddress.MultiAddr.__init__",
        side_effect=Exception("test error"),
    )
    def test_run(self, *mocks):
        """Run the test."""
        self.generate_private_key(FETCHAI)
        self.add_private_key(FETCHAI, connection=False)

        # this will cause exception because no key is added to the AEA project.
        with pytest.raises(Exception, match="test error"):
            self.run_cli_command(
                "get-multiaddress", FETCHAI, cwd=self.current_agent_context
            )


class TestGetMultiAddressCommandNegativeBadHostField(AEATestCaseEmpty):
    """Test case for CLI get-multiaddress when the host field is missing."""

    def test_run(self, *mocks):
        """Run the test."""
        self.generate_private_key(FETCHAI)
        self.add_private_key(FETCHAI, connection=True)

        # this will cause exception because no host configuration is in stub connection by default.
        with pytest.raises(
            Exception,
            match="Host field 'some_host' not present in connection configuration fetchai/stub:0.13.0",
        ):
            self.run_cli_command(
                "get-multiaddress",
                FETCHAI,
                "--connection",
                "--connection-id",
                str(STUB_CONNECTION_PUBLIC_ID),
                "--host-field",
                "some_host",
                "--port-field",
                "some_port",
                cwd=self.current_agent_context,
            )


class TestGetMultiAddressCommandNegativeBadPortField(AEATestCaseEmpty):
    """Test case for CLI get-multiaddress when the port field is missing."""

    def test_run(self, *mocks):
        """Run the test."""
        self.generate_private_key(FETCHAI)
        self.add_private_key(FETCHAI, connection=True)

        self.nested_set_config(
            "vendor.fetchai.connections.stub.config", {"host": "127.0.0.1"}
        )

        # this will cause exception because no port configuration is in stub connection by default.
        with pytest.raises(
            Exception,
            match="Port field 'some_port' not present in connection configuration fetchai/stub:0.13.0",
        ):
            self.run_cli_command(
                "get-multiaddress",
                FETCHAI,
                "--connection",
                "--connection-id",
                str(STUB_CONNECTION_PUBLIC_ID),
                "--host-field",
                "host",
                "--port-field",
                "some_port",
                cwd=self.current_agent_context,
            )


class TestGetMultiAddressCommandNegativeBadConnectionId(AEATestCaseEmpty):
    """Test case for CLI get-multiaddress when the connection id is missing."""

    def test_run(self, *mocks):
        """Run the test."""
        self.generate_private_key(FETCHAI)
        self.add_private_key(FETCHAI, connection=True)

        # this will cause exception because a bad public id is provided.
        connection_id = "some_author/some_connection:0.1.0"
        with pytest.raises(
            Exception,
            match=f"Cannot find connection with the public id {connection_id}",
        ):
            self.run_cli_command(
                "get-multiaddress",
                FETCHAI,
                "--connection",
                "--connection-id",
                connection_id,
                cwd=self.current_agent_context,
            )


class TestGetMultiAddressCommandNegativeFullMultiaddrComputation(AEATestCaseEmpty):
    """Test case for CLI get-multiaddress when an error occurs in the computation of the full multiaddr."""

    @mock.patch(
        "aea.cli.get_multiaddress.MultiAddr.__init__",
        side_effect=Exception("test error"),
    )
    def test_run(self, *mocks):
        """Run the test."""
        self.generate_private_key(FETCHAI)
        self.add_private_key(FETCHAI, connection=True)

        self.nested_set_config(
            "vendor.fetchai.connections.stub.config",
            {"host": "127.0.0.1", "port": 10000},
        )

        # this will cause exception due to the mocking.
        with pytest.raises(
            Exception,
            match="An error occurred while creating the multiaddress: test error",
        ):
            self.run_cli_command(
                "get-multiaddress",
                FETCHAI,
                "--connection",
                "--connection-id",
                str(STUB_CONNECTION_PUBLIC_ID),
                "--host-field",
                "host",
                "--port-field",
                "port",
                cwd=self.current_agent_context,
            )


class TestGetMultiAddressCommandNegativeOnlyHostSpecified(AEATestCaseEmpty):
    """Test case for CLI get-multiaddress when only the host field is specified."""

    def test_run(self, *mocks):
        """Run the test."""
        self.generate_private_key(FETCHAI)
        self.add_private_key(FETCHAI, connection=True)

        # this will cause exception because only the host, and not the port, are specified.
        with pytest.raises(
            Exception,
            match="-h/--host-field and -p/--port-field must be specified together.",
        ):
            self.run_cli_command(
                "get-multiaddress",
                FETCHAI,
                "--connection",
                "--connection-id",
                str(STUB_CONNECTION_PUBLIC_ID),
                "--host-field",
                "some_host",
                cwd=self.current_agent_context,
            )


class TestGetMultiAddressCommandNegativeUriNotExisting(AEATestCaseEmpty):
    """Test case for CLI get-multiaddress when the URI field doesn't exists."""

    def test_run(self, *mocks):
        """Run the test."""
        self.generate_private_key(FETCHAI)
        self.add_private_key(FETCHAI, connection=True)

        # this will cause exception because only the host, and not the port, are specified.
        with pytest.raises(
            Exception,
            match="URI field 'some_uri' not present in connection configuration fetchai/stub:0.13.0",
        ):
            self.run_cli_command(
                "get-multiaddress",
                FETCHAI,
                "--connection",
                "--connection-id",
                str(STUB_CONNECTION_PUBLIC_ID),
                "--uri-field",
                "some_uri",
                cwd=self.current_agent_context,
            )


class TestGetMultiAddressCommandNegativeBadUri(AEATestCaseEmpty):
    """Test case for CLI get-multiaddress when we cannot parse the URI field."""

    def test_run(self, *mocks):
        """Run the test."""
        self.generate_private_key(FETCHAI)
        self.add_private_key(FETCHAI, connection=True)

        self.nested_set_config(
            "vendor.fetchai.connections.stub.config",
            {"some_uri": "some-unparsable_URI"},
        )

        # this will cause exception because only the host, and not the port, are specified.
        with pytest.raises(
            Exception,
            match=r"Cannot extract host and port from some_uri: 'some-unparsable_URI'. Reason: URI Doesn't match regex '",
        ):
            self.run_cli_command(
                "get-multiaddress",
                FETCHAI,
                "--connection",
                "--connection-id",
                str(STUB_CONNECTION_PUBLIC_ID),
                "--uri-field",
                "some_uri",
                cwd=self.current_agent_context,
            )
