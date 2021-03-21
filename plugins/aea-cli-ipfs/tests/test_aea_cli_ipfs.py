# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
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
import sys
from unittest.mock import patch

import click
import ipfshttpclient  # type: ignore
import pytest
from click.testing import CliRunner

from aea.cli.core import cli


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from aea_cli_ipfs.core import (  # noqa # type: ignore  # pylint: disable=wrong-import-position
    PublishError,
    ipfs,
)


cli.add_command("ipfs", ipfs)


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
        "ipfshttpclient.Client.add", return_value=[{"Name": "name", "Hash": "hash"}] * 2
    ) as ipfs_add:
        r = runner.invoke(cli, ["ipfs", "add", "-p"], catch_exceptions=False)
    assert r.exit_code == 0
    ipfs_id.assert_called()
    ipfs_add.assert_called()
    ipfs_publish.assert_called()

    with patch(
        "ipfshttpclient.Client.name.publish", side_effect=PublishError("oops")
    ) as ipfs_publish, patch("ipfshttpclient.Client.id") as ipfs_id, patch(
        "ipfshttpclient.Client.add", return_value=[{"Name": "name", "Hash": "hash"}] * 2
    ) as ipfs_add:
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
    ), patch("time.sleep"), patch("subprocess.Popen"):

        with pytest.raises(
            click.ClickException,
            match="Failed to connect or start ipfs node! Please check ipfs is installed or launched!",
        ):
            runner.invoke(
                cli,
                ["ipfs", "add", "-p"],
                catch_exceptions=False,
                standalone_mode=False,
            )


@patch("ipfshttpclient.Client.id")
def test_ipfs_download(*_):
    """Test aea ipfs download."""
    runner = CliRunner()
    with patch("ipfshttpclient.Client.get") as ipfs_get, patch("os.rmdir"), patch(
        "pathlib.Path.iterdir", return_value=[1]
    ), patch("shutil.move"):
        r = runner.invoke(
            cli, ["ipfs", "download", "some_hash"], catch_exceptions=False
        )
    assert r.exit_code == 0
    ipfs_get.assert_called()


@patch("ipfshttpclient.Client.id")
def test_ipfs_remove(*_):
    """Test aea ipfs remove."""
    runner = CliRunner()
    with patch("ipfshttpclient.Client.pin.rm") as ipfs_rm:
        r = runner.invoke(cli, ["ipfs", "remove", "some_hash"], catch_exceptions=False)
    assert r.exit_code == 0
    ipfs_rm.assert_called()

    with patch(
        "ipfshttpclient.Client.pin.rm",
        side_effect=ipfshttpclient.exceptions.ErrorResponse(
            "oops", original=Exception()
        ),
    ) as ipfs_rm:
        with pytest.raises(click.ClickException, match="Remove error:.*oops"):
            runner.invoke(
                cli,
                ["ipfs", "remove", "some_hash"],
                catch_exceptions=False,
                standalone_mode=False,
            )


if __name__ == "__main__":
    pytest.main([__file__])
