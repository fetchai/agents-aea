# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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
"""This test module contains tests for CLI Registry utils."""

import os
import tempfile
from json.decoder import JSONDecodeError
from pathlib import Path
from unittest import TestCase, mock
from unittest.mock import MagicMock, patch

import pytest
from click import ClickException
from requests.exceptions import ConnectionError

from aea.cli.registry.settings import AUTH_TOKEN_KEY
from aea.cli.registry.utils import (
    FILE_DOWNLOAD_TIMEOUT,
    _rm_tarfiles,
    check_is_author_logged_in,
    clean_tarfiles,
    download_file,
    extract,
    get_latest_public_id_mixed,
    get_latest_version_available_in_registry,
    get_package_meta,
    is_auth_token_present,
    list_missing_packages,
    request_api,
)
from aea.cli.utils.exceptions import AEAConfigException
from aea.configurations.base import PublicId
from aea.helpers.base import cd

from packages.fetchai.protocols.default import DefaultMessage


def _raise_connection_error(*args, **kwargs):
    raise ConnectionError()


def _raise_config_exception(*args):
    raise AEAConfigException()


def _raise_json_decode_error(*args):
    raise JSONDecodeError(None, "None", 1)  # args requied for JSONDecodeError raising


@pytest.mark.skip  # need remote registry
@mock.patch("aea.cli.registry.utils.requests.request")
class RequestAPITestCase(TestCase):
    """Test case for request_api method."""

    def test_request_api_positive(self, request_mock):
        """Test for request_api method positive result."""
        REGISTRY_API_URL = "https://agents-registry.prod.fetch-ai.com/api/v1"
        expected_result = {"correct": "json"}

        resp_mock = mock.Mock()
        resp_mock.json = lambda: expected_result
        resp_mock.status_code = 200
        request_mock.return_value = resp_mock

        result = request_api("GET", "/path")
        request_mock.assert_called_once_with(
            method="GET",
            params=None,
            data=None,
            files=None,
            headers={},
            url=REGISTRY_API_URL + "/path",
        )
        self.assertEqual(result, expected_result)

        result = request_api("GET", "/path", return_code=True)
        self.assertEqual(result, (expected_result, 200))

    def test_request_api_404(self, request_mock):
        """Test for request_api method 404 server response."""
        resp_mock = mock.Mock()
        resp_mock.status_code = 404
        request_mock.return_value = resp_mock
        with self.assertRaises(ClickException):
            request_api("GET", "/path")

    def test_request_api_500(self, request_mock):
        """Test for request_api method 500 server response."""
        resp_mock = mock.Mock()
        resp_mock.status_code = 500
        resp_mock.json.return_value = {"detail": "test"}
        request_mock.return_value = resp_mock
        with self.assertRaises(ClickException):
            request_api("GET", "/path")

    def test_request_api_201(self, request_mock):
        """Test for request_api method 201 server response."""
        expected_result = {"correct": "json"}

        resp_mock = mock.Mock()
        resp_mock.json = lambda: expected_result
        resp_mock.status_code = 201
        request_mock.return_value = resp_mock
        result = request_api("GET", "/path")
        self.assertEqual(result, expected_result)

    def test_request_api_403(self, request_mock):
        """Test for request_api method notauthorized server response."""
        resp_mock = mock.Mock()
        resp_mock.status_code = 403
        request_mock.return_value = resp_mock
        with self.assertRaises(ClickException):
            request_api("GET", "/path")

    def test_request_api_400(self, request_mock):
        """Test for request_api method 400 code server response."""
        resp_mock = mock.Mock()
        resp_mock.status_code = 400
        request_mock.return_value = resp_mock
        with self.assertRaises(ClickException):
            request_api("GET", "/path")

    def test_request_api_409(self, request_mock):
        """Test for request_api method conflict server response."""
        resp_mock = mock.Mock()
        resp_mock.status_code = 409
        resp_mock.json = lambda: {"detail": "some"}
        request_mock.return_value = resp_mock
        with self.assertRaises(ClickException):
            request_api("GET", "/path")

    def test_request_api_unexpected_response(self, request_mock):
        """Test for request_api method unexpected server response."""
        resp_mock = mock.Mock()
        status_code = 501
        resp_mock.status_code = status_code  # not implemented status
        resp_mock.json = _raise_json_decode_error
        request_mock.return_value = resp_mock
        with self.assertRaises(ClickException):
            request_api("GET", "/path")

        error_msg = "Error occured."
        resp_mock.json = mock.Mock(return_value={"detail": error_msg})
        with self.assertRaises(ClickException) as execinfo:
            request_api("GET", "/path")
        expected_exception = f"Wrong server response. Status code: {status_code}: Error detail: {error_msg}"
        self.assertEqual(str(execinfo.exception), expected_exception)

    @mock.patch("aea.cli.registry.utils.get_or_create_cli_config", return_value={})
    def test_request_api_no_auth_data(
        self, get_or_create_cli_config_mock, request_mock
    ):
        """Test for request_api method no auth data."""
        with self.assertRaises(ClickException):
            request_api("GET", "/path", is_auth=True)

    @mock.patch(
        "aea.cli.registry.utils.get_or_create_cli_config",
        return_value={AUTH_TOKEN_KEY: "key"},
    )
    def test_request_api_with_auth_positive(
        self, get_or_create_cli_config_mock, request_mock
    ):
        """Test for request_api method with auth positive result."""
        expected_result = {"correct": "json"}

        resp_mock = mock.Mock()
        resp_mock.json = lambda: expected_result
        resp_mock.status_code = 200
        request_mock.return_value = resp_mock

        result = request_api("GET", "/path", is_auth=True)
        self.assertEqual(result, expected_result)

    @mock.patch("builtins.open", mock.mock_open())
    def test_request_api_with_files_positive(self, request_mock):
        """Test for request_api method with file positive result."""
        expected_result = {"correct": "json"}

        resp_mock = mock.Mock()
        resp_mock.json = lambda: expected_result
        resp_mock.status_code = 200
        request_mock.return_value = resp_mock

        test_files = {
            "file": open("file.tar.gz", "rb"),
            "readme": open("file.md", "rb"),
        }
        result = request_api("GET", "/path", files=test_files)
        self.assertEqual(result, expected_result)


@mock.patch("aea.cli.registry.utils.requests.request", _raise_connection_error)
class RequestAPINoResponseTestCase(TestCase):
    """Test case for request_api method no server response."""

    def test_request_api_server_not_responding(self):
        """Test for request_api method no server response."""
        with self.assertRaises(ClickException):
            request_api("GET", "/path")


@mock.patch("aea.cli.registry.utils.requests.get")
class DownloadFileTestCase(TestCase):
    """Test case for download_file method."""

    @mock.patch("builtins.open", mock.mock_open())
    def test_download_file_positive(self, get_mock):
        """Test for download_file method positive result."""
        filename = "filename.tar.gz"
        url = "url/{}".format(filename)
        cwd = "cwd"
        filepath = os.path.join(cwd, filename)

        resp_mock = mock.Mock()
        raw_mock = mock.Mock()
        raw_mock.read = lambda: "file content"

        resp_mock.raw = raw_mock
        resp_mock.status_code = 200
        get_mock.return_value = resp_mock

        result = download_file(url, cwd)
        expected_result = filepath
        self.assertEqual(result, expected_result)
        get_mock.assert_called_once_with(
            url, stream=True, timeout=FILE_DOWNLOAD_TIMEOUT
        )

    def test_download_file_wrong_response(self, get_mock):
        """Test for download_file method wrong response from file server."""
        resp_mock = mock.Mock()
        resp_mock.status_code = 404
        get_mock.return_value = resp_mock

        with self.assertRaises(ClickException):
            download_file("url", "cwd")


class ExtractTestCase(TestCase):
    """Test case for extract method."""

    @mock.patch("aea.cli.registry.utils.os.remove")
    @mock.patch("aea.cli.registry.utils.tarfile.open")
    def test_extract_positive(self, tarfile_open_mock, os_remove_mock):
        """Test for extract method positive result."""
        source = "file.tar.gz"
        target = "target-folder"

        tar_mock = mock.Mock()
        tar_mock.extractall = lambda path: None
        tar_mock.close = lambda: None
        tarfile_open_mock.return_value = tar_mock

        extract(source, target)
        tarfile_open_mock.assert_called_once_with(source, "r:gz")
        os_remove_mock.assert_called_once_with(source)

    def test_extract_wrong_file_type(self):
        """Test for extract method wrong file type."""
        source = "file.wrong"
        target = "target-folder"
        with self.assertRaises(Exception):
            extract(source, target)


@mock.patch(
    "aea.cli.registry.utils.request_api", return_value={"username": "current-user"}
)
class CheckIsAuthorLoggedInTestCase(TestCase):
    """Test case for check_is_author_logged_in method."""

    def test_check_is_author_logged_in_positive(self, request_api_mock):
        """Test for check_is_author_logged_in method positive result."""
        check_is_author_logged_in("current-user")

    def test_check_is_author_logged_in_negative(self, request_api_mock):
        """Test for check_is_author_logged_in method negative result."""
        with self.assertRaises(ClickException):
            check_is_author_logged_in("not-current-user")


@mock.patch("aea.cli.registry.utils.os.remove")
@mock.patch("aea.cli.registry.utils.os.listdir", return_value=["file1.tar.gz", "file2"])
@mock.patch("aea.cli.registry.utils.os.getcwd", return_value="cwd")
class RmTarfilesTestCase(TestCase):
    """Test case for _rm_tarfiles method."""

    def test__rm_tarfiles_positive(self, getcwd_mock, listdir_mock, remove_mock):
        """Test for _rm_tarfiles method positive result."""
        _rm_tarfiles()
        listdir_mock.assert_called_once_with("cwd")
        remove_mock.assert_called_once()


@mock.patch("aea.cli.registry.utils.get_auth_token", return_value="token")
class IsAuthTokenPresentTestCase(TestCase):
    """Test case for is_auth_token_present method."""

    def test_is_auth_token_present_positive(self, get_auth_token_mock):
        """Test for is_auth_token_present method positive result."""
        result = is_auth_token_present()
        self.assertTrue(result)


@mock.patch(
    "aea.cli.registry.utils.find_item_locally", side_effect=ClickException("some error")
)
@mock.patch(
    "aea.cli.registry.utils.get_package_meta",
    return_value=dict(public_id="author/name:0.1.0"),
)
def test_get_latest_public_id_mixed_negative(*_mocks):
    """Test 'get_latest_public_id_mixed', when local fetch fails."""
    get_latest_public_id_mixed(
        MagicMock(), "protocol", PublicId.from_str("author/name:0.1.0")
    )


def test_clean_tarfiles():
    """Test clean tarfiles wrapper."""

    expected_result = "result"

    def func() -> str:
        """The function being wrapped."""
        return expected_result

    wrapped = clean_tarfiles(func)
    with tempfile.TemporaryDirectory() as tempdir:
        with cd(tempdir):
            tarfile_path = Path(tempdir, "tarfile.tar.gz")
            tarfile_path.touch()

            result = wrapped()

            assert not tarfile_path.exists()
            assert result == expected_result


def test_clean_tarfiles_error():
    """Test clean tarfiles wrapper in case of error."""

    expected_message = "some exception"

    def func() -> str:
        """The function being wrapped."""
        raise Exception(expected_message)

    wrapped = clean_tarfiles(func)
    with tempfile.TemporaryDirectory() as tempdir:
        with cd(tempdir):
            tarfile_path = Path(tempdir, "tarfile.tar.gz")
            tarfile_path.touch()

            with pytest.raises(Exception, match=expected_message):
                wrapped()

            assert not tarfile_path.exists()


@pytest.mark.skip  # need remote registry
@pytest.mark.integration
def test_get_package_meta():
    """Test get package meta."""
    package_meta = get_package_meta("protocol", DefaultMessage.protocol_id.to_latest())
    assert isinstance(package_meta, dict)
    assert package_meta["name"] == DefaultMessage.protocol_id.name


@mock.patch(
    "aea.cli.registry.utils.find_item_locally",
    return_value=(None, MagicMock(public_id=DefaultMessage.protocol_id)),
)
def test_get_latest_public_id_mixed(*_mock):
    """Test 'get_latest_public_id_mixed', in case of success."""
    result = get_latest_public_id_mixed(
        MagicMock(), "protocol", DefaultMessage.protocol_id
    )
    assert result == DefaultMessage.protocol_id


@mock.patch(
    "aea.cli.registry.utils.get_package_meta",
    return_value=dict(public_id=str(DefaultMessage.protocol_id)),
)
def test_get_latest_version_available_in_registry_remote_mode(*_mocks):
    """Test 'get_latest_version_available_in_registry', remote mode."""
    context_mock = MagicMock(config=dict(is_local=False, is_mixed=False))
    result = get_latest_version_available_in_registry(
        context_mock, "protocol", DefaultMessage.protocol_id
    )
    assert result == DefaultMessage.protocol_id


def test_list_missing_packages():
    """Test 'list_missing_packages'."""
    packages = [("connection", PublicId.from_str("test/test:0.1.2"))]

    resp_ok = MagicMock()
    resp_ok.status_code = 200
    with patch(
        "aea.cli.registry.utils._perform_registry_request", return_value=resp_ok
    ):
        assert list_missing_packages(packages) == []

    resp_404 = MagicMock()
    resp_404.status_code = 404
    with patch(
        "aea.cli.registry.utils._perform_registry_request", return_value=resp_404
    ):
        assert list_missing_packages(packages) == packages
