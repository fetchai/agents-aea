# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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

"""Test ipfs utils."""

import os
import re
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import ipfshttpclient
import pytest
import requests
from aea_cli_ipfs.ipfs_utils import (
    DownloadError,
    IPFSDaemon,
    IPFSTool,
    PinError,
    RemoveError,
    resolve_addr,
)
from aea_cli_ipfs.test_tools.fixture_helpers import ipfs_daemon  # noqa: F401

from aea.cli.registry.settings import DEFAULT_IPFS_URL, DEFAULT_IPFS_URL_LOCAL


def test_init_tool() -> None:
    """Test tool initialization."""

    tool = IPFSTool(DEFAULT_IPFS_URL)
    assert tool.is_remote is True

    tool = IPFSTool(DEFAULT_IPFS_URL_LOCAL)
    assert tool.is_remote is False


def test_hash_bytes() -> None:
    """Test hash bytes."""
    tool = IPFSTool(DEFAULT_IPFS_URL_LOCAL)
    tool.daemon.start()
    try:
        assert tool.is_remote is False
        some_bytes = b"there is some bytes"
        ipfs_hash = tool.add_bytes(some_bytes)
        assert (
            ipfs_hash == "QmPPFcK8uynDmceTDkDjHuDbR7gnqBfaMCTifs6oFKHn4E"
        )  # precalculated
    finally:
        tool.daemon.stop()


def test_resolve_addr() -> None:
    """Test resolve_addr function."""
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Address type should be one of the ('ip4', 'dns'), provided: 2"
        ),
    ):
        resolve_addr("1/2/3/4/5/6")

    with pytest.raises(
        ValueError,
        match=re.escape("Connection should be one of the ('tcp',), provided: 4"),
    ):
        resolve_addr("1/ip4/3/4/5/6")

    with pytest.raises(
        ValueError,
        match=re.escape("Protocol should be one of the ('http', 'https'), provided: 6"),
    ):
        resolve_addr("1/ip4/3/tcp/5/6")

    with pytest.raises(
        ValueError,
        match=re.escape(
            "Invalid multiaddr string provided, valid format: /{dns,dns4,dns6,ip4}/<host>/tcp/<port>/protocol. Provided: 1/ip4/3/tcp/5/https/1/2"
        ),
    ):
        resolve_addr("1/ip4/3/tcp/5/https/1/2")


def test_daemon_url_trim() -> None:
    """Test extra slash in addr url trimmed."""
    daemon = IPFSDaemon(is_remote=False, node_url="http://1.1.1.1:1/")
    assert daemon.node_url == "http://1.1.1.1:1"


def test_daemon_ipfs_not_found() -> None:
    """Test ipfs cli command avialable."""
    with patch("shutil.which", return_value=None):
        with pytest.raises(Exception, match="Please install IPFS first!"):
            IPFSDaemon._check_ipfs()

    with patch("subprocess.Popen.communicate", return_value=(b"", b"")):
        with pytest.raises(
            Exception,
            match=re.escape(
                "Please ensure you have version 0.6.0 of IPFS daemon installed."
            ),
        ):
            IPFSDaemon._check_ipfs()


def test_daemon_is_started_externally() -> None:
    """Test IPFSDaemon is started externally."""
    daemon = IPFSDaemon()
    response_mock = Mock()
    response_mock.status_code = 200
    with patch("requests.post", return_value=response_mock):
        assert daemon.is_started_externally()

    response_mock.status_code = 400
    with patch("requests.post", return_value=response_mock):
        assert not daemon.is_started_externally()

    with patch("requests.post", side_effect=requests.exceptions.ConnectionError()):
        assert not daemon.is_started_externally()

    assert not daemon.is_started()


def test_daemon_start() -> None:
    """Test IPFSDaemon start method."""
    daemon = IPFSDaemon()
    popen_mock = Mock()
    popen_mock.communicate = Mock(return_value=(b"0.6.0", b""))
    popen_mock.stdout = None
    with patch("subprocess.Popen", return_value=popen_mock):
        with pytest.raises(RuntimeError, match="Could not start IPFS daemon."):
            daemon.start()

        popen_mock.stdout = Mock()
        popen_mock.stdout.readline = Mock(side_effect=[b""] * 10)
        with pytest.raises(RuntimeError, match="Could not start IPFS daemon."):
            daemon.start()


def test_daemon_context() -> None:
    """Test IPFSDaemon context manager."""
    daemon = IPFSDaemon()
    with patch.object(daemon, "start") as start_mock, patch.object(
        daemon, "stop"
    ) as stop_mock:
        with daemon:
            pass

        start_mock.assert_called_once()
        stop_mock.assert_called_once()


def test_tool_all_pins() -> None:
    """Test IPFSTool.all_pins and is_a_package method."""
    ipfs_tool = IPFSTool()
    client_mock = Mock()
    client_mock.pin.ls = Mock(return_value={"Keys": [1, 2, 3, 4, 5]})
    with patch.object(ipfs_tool, "client", client_mock):
        assert ipfs_tool.all_pins() == {1, 2, 3, 4, 5}
        assert ipfs_tool.is_a_package(1)
        assert not ipfs_tool.is_a_package(6)


def test_tool_add_pin() -> None:
    """Test IPFSTool.pin method."""
    ipfs_tool = IPFSTool()
    client_mock = Mock()
    client_mock.pin.add = Mock(return_value={"Keys": [1]})
    with patch.object(ipfs_tool, "client", client_mock):
        assert ipfs_tool.pin("some")

        with pytest.raises(PinError):
            client_mock.pin.add = Mock(
                side_effect=ipfshttpclient.exceptions.ErrorResponse(Mock(), Mock())
            )
            ipfs_tool.pin("some")


def test_tool_remove_unpinned_files() -> None:
    """Test IPFSTool.remove_unpinned_files method."""
    ipfs_tool = IPFSTool()
    client_mock = Mock()
    client_mock.repo.gc = Mock(return_value={"Keys": [1]})
    with patch.object(ipfs_tool, "client", client_mock):
        ipfs_tool.remove_unpinned_files()

        with pytest.raises(RemoveError):
            client_mock.repo.gc = Mock(
                side_effect=ipfshttpclient.exceptions.ErrorResponse(Mock(), Mock())
            )
            ipfs_tool.remove_unpinned_files()


def test_tool_download() -> None:
    """Test IPFSTool.download method."""
    ipfs_tool = IPFSTool()
    client_mock = Mock()
    client_mock.get = Mock(
        side_effect=ipfshttpclient.exceptions.StatusError(Mock(), Mock())
    )
    with patch.object(
        ipfs_tool, "client", client_mock
    ), TemporaryDirectory() as tmp_dir, patch(
        "pathlib.Path.is_file", return_value=True
    ), patch(
        "shutil.copy"
    ), patch(
        "os.listdir", return_value=["1"]
    ), patch(
        "pathlib.Path.iterdir", return_value=[]
    ), patch(
        "shutil.rmtree"
    ), patch(
        "shutil.move"
    ):
        with pytest.raises(DownloadError, match="Failed to download: some"):
            with patch("time.sleep"):
                ipfs_tool.download("some", tmp_dir, attempts=5)
        assert client_mock.get.call_count == 5

        client_mock.get = Mock()

        assert ipfs_tool.download("some", tmp_dir, attempts=5) == tmp_dir


def test_tool_download_fix_path_works() -> None:
    """Test IPFSTool.download method."""
    ipfs_tool = IPFSTool()
    client_mock = Mock()
    sub_file_name = "some1"
    hash_id = "some_hash"

    def make_files(hash_, download_dir):
        os.mkdir(Path(download_dir) / hash_)
        os.mkdir(Path(download_dir) / hash_ / sub_file_name)

    client_mock.get = make_files
    with patch.object(ipfs_tool, "client", client_mock), patch(
        "pathlib.Path.is_file", return_value=False
    ), patch("shutil.copy"), patch("os.listdir", return_value=["1"]), patch(
        "pathlib.Path.iterdir", return_value=[]
    ), patch(
        "shutil.rmtree"
    ):
        with TemporaryDirectory() as target_tmp_dir:
            assert ipfs_tool.download(hash_id, target_tmp_dir, fix_path=True) == str(
                Path(target_tmp_dir, sub_file_name)
            )
            assert [i.name for i in Path(target_tmp_dir).glob("*")] == [sub_file_name]

        with TemporaryDirectory() as target_tmp_dir:
            assert ipfs_tool.download(hash_id, target_tmp_dir, fix_path=False) == str(
                Path(target_tmp_dir) / hash_id
            )
            assert [i.name for i in Path(target_tmp_dir).glob("*")] == [hash_id]


def test_wrap_directory_flag_file() -> None:
    """Test `wrap_directory` flag"""

    tool = IPFSTool(DEFAULT_IPFS_URL_LOCAL)
    tool.daemon.start()
    try:
        with TemporaryDirectory() as temp_dir:
            temp_file = Path(temp_dir, "txt")
            temp_file.write_text("Hello, World")

            _, file_hash, _ = tool.add(dir_path=str(temp_file))
            assert file_hash == "QmWVQQhQ5Qxzb1jLk1SW4Etsn6rMWHtjdELTNEmA1J1gRx"

            _, file_hash, _ = tool.add(
                dir_path=str(temp_file), wrap_with_directory=False
            )
            assert file_hash == "QmTev1ZgJkHgFYiCX7MgELEDJuMygPNGcinqBa2RmfnGFu"
    finally:
        tool.daemon.stop()


def test_wrap_directory_flag_dir() -> None:
    """Test `wrap_directory` flag"""
    tool = IPFSTool(DEFAULT_IPFS_URL_LOCAL)
    tool.daemon.start()
    try:
        with TemporaryDirectory() as _temp_dir:
            temp_dir = Path(_temp_dir, "some_dir")
            temp_dir.mkdir()

            temp_file = temp_dir / "txt"
            temp_file.write_text("Hello, World")

            _, file_hash, _ = tool.add(dir_path=str(temp_dir))
            assert file_hash == "Qmb7LSaArLheRjnvVZ2vhhnBun8EWsF9Z5TdL8NgLgyhJL"

            _, file_hash, _ = tool.add(
                dir_path=str(temp_dir), wrap_with_directory=False
            )
            assert file_hash == "QmWVQQhQ5Qxzb1jLk1SW4Etsn6rMWHtjdELTNEmA1J1gRx"
    finally:
        tool.daemon.stop()
