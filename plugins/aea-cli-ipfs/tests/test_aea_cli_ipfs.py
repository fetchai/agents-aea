# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
"""Tests for aea cli ipfs plugin."""

import os
import re
import sys
from pathlib import Path
from unittest import mock
from unittest.mock import patch

import click
import ipfshttpclient  # type: ignore
import pytest
from aea_cli_ipfs.ipfs_utils import addr_to_url, resolve_addr
from click.testing import CliRunner
from urllib3.exceptions import NewConnectionError as ConnectionError

from aea.cli.core import cli
from aea.test_tools.click_testing import CliTest


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from aea_cli_ipfs.core import (  # noqa # type: ignore  # pylint: disable=wrong-import-position
    PublishError,
    ipfs,
)


DUMMY_HASH = "QmbWqxBEKC3P8tqsKc98xmWNzrzDtRLMiMPL8wBuTGsMnR"

cli.add_command(ipfs)


def test_addr_helpers():
    """Test `resolve_addr` method."""

    addr_scheme, host, conn_type, port, protocol = resolve_addr(
        "/ip4/127.0.0.1/tcp/5001/http"
    )

    assert addr_scheme == "ip4"
    assert host == "127.0.0.1"
    assert conn_type == "tcp"
    assert port == "5001"
    assert protocol == "http"

    *_, port, protocol = resolve_addr("/ip4/127.0.0.1/tcp")

    assert port == "5001"
    assert protocol == "http"

    with pytest.raises(
        ValueError,
        match=re.escape(
            "Address type should be one of the ('ip4', 'dns'), provided: ip6"
        ),
    ):
        resolve_addr("/ip6/127.0.0.1/tcp")

    with pytest.raises(
        ValueError,
        match=re.escape("Connection should be one of the ('tcp',), provided: udp"),
    ):
        resolve_addr("/ip4/127.0.0.1/udp")

    with pytest.raises(
        ValueError,
        match=re.escape(
            "Protocol should be one of the ('http', 'https'), provided: wss"
        ),
    ):
        resolve_addr("/ip4/127.0.0.1/tcp/5001/wss")

    assert addr_to_url("/ip4/127.0.0.1/tcp/5001/http") == "http://127.0.0.1:5001"


def test_ipfs():
    """Test aea ipfs command itself."""
    runner = CliRunner()
    with patch("ipfshttpclient.Client.id"):
        r = runner.invoke(cli, ["ipfs"], catch_exceptions=False, standalone_mode=False)
    assert r.exit_code == 0


def test_ipfs_add():
    """Test aea ipfs add."""
    runner = CliRunner()
    with patch("ipfshttpclient.Client.name.publish") as ipfs_publish, patch(
        "ipfshttpclient.Client.id"
    ) as ipfs_id, patch(
        "ipfshttpclient.Client.add",
        return_value=[{"Name": "name", "Hash": DUMMY_HASH}] * 2,
    ) as ipfs_add, patch(
        "aea_cli_ipfs.ipfs_utils.IPFSDaemon._check_ipfs", new=lambda *_: None
    ):
        r = runner.invoke(cli, ["ipfs", "add", "-p"], catch_exceptions=False)
    assert r.exit_code == 0
    ipfs_id.assert_called()
    ipfs_add.assert_called()
    ipfs_publish.assert_called()

    with patch(
        "ipfshttpclient.Client.name.publish", side_effect=PublishError("oops")
    ) as ipfs_publish, patch("ipfshttpclient.Client.id") as ipfs_id, patch(
        "ipfshttpclient.Client.add",
        return_value=[{"Name": "name", "Hash": DUMMY_HASH}] * 2,
    ) as ipfs_add, patch(
        "aea_cli_ipfs.ipfs_utils.IPFSDaemon._check_ipfs", new=lambda *_: None
    ):
        with pytest.raises(click.ClickException, match="Publish failed.*oops"):
            runner.invoke(
                cli,
                ["ipfs", "add", "-p"],
                catch_exceptions=False,
                standalone_mode=False,
            )


def test_node_not_alive_can_not_be_started():
    """Test error on node connection failed"""
    runner = CliRunner()
    with patch(
        "ipfshttpclient.Client.id",
        side_effect=ipfshttpclient.exceptions.CommunicationError(
            original=Exception("oops")
        ),
    ), patch("time.sleep"), patch("subprocess.Popen"), patch(
        "aea_cli_ipfs.ipfs_utils.IPFSDaemon._check_ipfs"
    ), patch(
        "aea_cli_ipfs.ipfs_utils.IPFSDaemon.start"
    ), patch(
        "aea_cli_ipfs.ipfs_utils.IPFSDaemon._check_ipfs", new=lambda *_: None
    ):
        env = os.environ.copy()
        env["OPEN_AEA_IPFS_ADDR"] = "/ip4/127.0.0.1/tcp/5001"
        with pytest.raises(ConnectionError):
            runner.invoke(
                cli,
                ["ipfs", "add", "-p"],
                catch_exceptions=False,
                standalone_mode=False,
                env=env,
            )


@pytest.mark.skip
def test_version_did_not_match():
    """Test error on node connection failed"""
    runner = CliRunner()
    with patch(
        "ipfshttpclient.Client.id",
        side_effect=ipfshttpclient.exceptions.CommunicationError(
            original=Exception("oops")
        ),
    ), patch("time.sleep"), patch(
        "subprocess.Popen.communicate", new_callable=lambda: lambda _: (b"", None)
    ), patch(
        "aea_cli_ipfs.ipfs_utils.IPFSDaemon._check_ipfs", new=lambda *_: None
    ):
        with pytest.raises(
            Exception,
            match="Please ensure you have version 0.6.0 of IPFS daemon installed.",
        ):
            runner.invoke(
                cli,
                ["ipfs", "add", "-p"],
                catch_exceptions=False,
                standalone_mode=False,
            )


class TestIPFSToolDownload(CliTest):
    """Test IPFSTool.download"""

    # we download either a file or a directory
    # if a file: the original name is not preserved, and will be the hash
    #   e.g. <filename> --> <some_ipfs_hash>
    # if a dir : the original name is preserved, as a nested directory
    #   e.g. <directory>/ --> <some_ipfs_hash>/<directory>/

    cli_options = ("ipfs", "download")

    def setup(self) -> None:
        """Setup"""

        super().setup()
        self.some_ipfs_hash = "not_a_real_ipfs_hash"
        self.target_dir = self.t / "target_dir"
        self.args = self.some_ipfs_hash, str(self.target_dir)

    @staticmethod
    def mock_client_get_success(is_dir: bool) -> mock._patch:
        """Mock IPFSTool.client.get"""

        # self.client.get(hash_id, tmp_dir) creates tmp_dir/hash_id

        def new_callable(_, hash_id, tmp_dir) -> None:
            if is_dir:  # <ipfs_hash>/<dir_name>/...
                some_dir = Path(tmp_dir) / hash_id / "some_dir"
                some_dir.mkdir(parents=True)
                (some_dir / "some_file").touch()
                (some_dir / "some_nested_dir").mkdir()
                (some_dir / "some_nested_dir" / "some_nested_file").touch()
            else:  # <ipfs_hash>
                (Path(tmp_dir) / hash_id).touch()

        # we need a nested lambda to mock a method on the class instead of instance
        return patch("ipfshttpclient.Client.get", new_callable=lambda: new_callable)

    @property
    def mock_client_get_failure(self) -> mock._patch:
        """Mock IPFSTool.client.get failure"""

        def new_callable(*_, **__) -> None:
            exception = Exception("DummyError for testing")
            raise ipfshttpclient.exceptions.StatusError(exception)

        return patch("ipfshttpclient.Client.get", new_callable=lambda: new_callable)

    @pytest.mark.parametrize("is_dir", [False, True])
    def test_ipfs_download_success(self, is_dir: bool) -> None:
        """Test aea ipfs download."""

        with self.mock_client_get_success(is_dir=is_dir):
            result = self.run_cli(*self.args, catch_exceptions=False)

        assert result.exit_code == 0, result.stdout
        assert f"Download {self.some_ipfs_hash} to {self.target_dir}" in result.stdout
        assert "Download complete!" in result.stdout

        all_new_paths = list(self.target_dir.rglob("*"))

        if is_dir:
            assert len(all_new_paths) == 4
            assert not any(self.some_ipfs_hash in str(p) for p in all_new_paths)
        else:
            assert len(all_new_paths) == 1
            assert all_new_paths[0].is_file()
            assert all_new_paths[0].name == self.some_ipfs_hash

    def test_ipfs_download_failure(self) -> None:
        """Test aea ipfs download failure."""

        with self.mock_client_get_failure:
            with mock.patch("time.sleep"):
                result = self.run_cli(
                    *self.args, catch_exceptions=True, standalone_mode=False
                )

        assert result.exit_code == 1, result.stdout
        assert isinstance(result.exception, click.ClickException)
        assert f"Failed to download: {self.some_ipfs_hash}" in result.exception.message
        assert not any(self.target_dir.rglob("*"))


@patch("ipfshttpclient.Client.id")
def test_ipfs_remove(*_):
    """Test aea ipfs remove."""
    runner = CliRunner()
    with patch("ipfshttpclient.Client.pin.rm") as ipfs_rm, patch(
        "aea_cli_ipfs.ipfs_utils.IPFSDaemon._check_ipfs", new=lambda *_: None
    ):
        r = runner.invoke(cli, ["ipfs", "remove", "some_hash"], catch_exceptions=False)
    assert r.exit_code == 0
    ipfs_rm.assert_called()

    with patch(
        "ipfshttpclient.Client.pin.rm",
        side_effect=ipfshttpclient.exceptions.ErrorResponse(
            "oops", original=Exception()
        ),
    ) as ipfs_rm, patch(
        "aea_cli_ipfs.ipfs_utils.IPFSDaemon._check_ipfs", new=lambda *_: None
    ):
        with pytest.raises(click.ClickException, match="Remove error:.*oops"):
            runner.invoke(
                cli,
                ["ipfs", "remove", "some_hash"],
                catch_exceptions=False,
                standalone_mode=False,
            )


if __name__ == "__main__":
    pytest.main([__file__])
