# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
"""This test module contains the tests for aea.cli.utils module."""
from builtins import FileNotFoundError
from copy import deepcopy
from tempfile import TemporaryDirectory
from typing import cast
from unittest import TestCase, mock
from unittest.mock import MagicMock, patch
from uuid import uuid4

import click
import pytest
from aea_ledger_fetchai import FetchAICrypto
from click import BadParameter, ClickException
from click.testing import CliRunner
from jsonschema import ValidationError
from yaml import YAMLError

from aea.cli.utils.click_utils import PublicIdParameter, password_option
from aea.cli.utils.config import (
    _init_cli_config,
    get_or_create_cli_config,
    set_cli_author,
    update_cli_config,
)
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import _validate_config_consistency, clean_after
from aea.cli.utils.formatting import format_items
from aea.cli.utils.generic import is_readme_present
from aea.cli.utils.package_utils import (
    _override_ledger_configurations,
    find_item_in_distribution,
    find_item_locally,
    get_dotted_package_path_unified,
    get_package_path_unified,
    get_wallet_from_context,
    is_distributed_item,
    is_fingerprint_correct,
    is_item_present_unified,
    try_get_balance,
    try_get_item_source_path,
    try_get_item_target_path,
    validate_author_name,
    validate_package_name,
)
from aea.configurations.base import ComponentId, ComponentType, PublicId
from aea.configurations.constants import DEFAULT_LEDGER
from aea.crypto.ledger_apis import ETHEREUM_DEFAULT_CHAIN_ID, LedgerApis
from aea.crypto.wallet import Wallet
from aea.helpers.base import cd
from aea.test_tools.test_cases import AEATestCaseEmpty

from packages.fetchai.protocols.default.message import DefaultMessage

from tests.test_cli.tools_for_testing import (
    ConfigLoaderMock,
    ContextMock,
    PublicIdMock,
    StopTest,
    raise_stoptest,
)


AUTHOR = "author"


class FormatItemsTestCase(TestCase):
    """Test case for format_items method."""

    def testformat_items_positive(self):
        """Test format_items positive result."""
        items = [
            {
                "public_id": "author/name:version",
                "name": "obj_name",
                "description": "Some description",
                "author": "author",
                "version": "1.0",
            }
        ]
        result = format_items(items)
        expected_result = (
            "------------------------------\n"
            "Public ID: author/name:version\n"
            "Name: obj_name\n"
            "Description: Some description\n"
            "Author: author\n"
            "Version: 1.0\n"
            "------------------------------\n"
        )
        self.assertEqual(result, expected_result)


@mock.patch("aea.cli.utils.package_utils.os.path.join", return_value="some-path")
class TryGetItemSourcePathTestCase(TestCase):
    """Test case for try_get_item_source_path method."""

    @mock.patch("aea.cli.utils.package_utils.os.path.exists", return_value=True)
    def test_get_item_source_path_positive(self, exists_mock, join_mock):
        """Test for get_item_source_path positive result."""
        result = try_get_item_source_path("cwd", AUTHOR, "skills", "skill_name")
        expected_result = "some-path"
        self.assertEqual(result, expected_result)
        join_mock.assert_called_once_with("cwd", AUTHOR, "skills", "skill_name")
        exists_mock.assert_called_once_with("some-path")

        result = try_get_item_source_path("cwd", None, "skills", "skill_name")
        self.assertEqual(result, expected_result)

    @mock.patch("aea.cli.utils.package_utils.os.path.exists", return_value=False)
    def test_get_item_source_path_not_exists(self, exists_mock, join_mock):
        """Test for get_item_source_path item already exists."""
        item_name = "skill_name"
        with pytest.raises(
            ClickException,
            match=f'Item "{AUTHOR}/{item_name}" not found in source folder "some-path"',
        ):
            try_get_item_source_path("cwd", AUTHOR, "skills", item_name)


@mock.patch("aea.cli.utils.package_utils.os.path.join", return_value="some-path")
class TryGetItemTargetPathTestCase(TestCase):
    """Test case for try_get_item_target_path method."""

    @mock.patch("aea.cli.utils.package_utils.os.path.exists", return_value=False)
    def test_get_item_target_path_positive(self, exists_mock, join_mock):
        """Test for get_item_source_path positive result."""
        result = try_get_item_target_path("packages", AUTHOR, "skills", "skill_name")
        expected_result = "some-path"
        self.assertEqual(result, expected_result)
        join_mock.assert_called_once_with("packages", AUTHOR, "skills", "skill_name")
        exists_mock.assert_called_once_with("some-path")

    @mock.patch("aea.cli.utils.package_utils.os.path.exists", return_value=True)
    def test_get_item_target_path_already_exists(self, exists_mock, join_mock):
        """Test for get_item_target_path item already exists."""
        with self.assertRaises(ClickException):
            try_get_item_target_path("skills", AUTHOR, "skill_name", "packages_path")


class PublicIdParameterTestCase(TestCase):
    """Test case for PublicIdParameter class."""

    def test_get_metavar_positive(self):
        """Test for get_metavar positive result."""
        result = PublicIdParameter.get_metavar("obj", "param")
        expected_result = "PUBLIC_ID_OR_HASH"
        self.assertEqual(result, expected_result)


@mock.patch("aea.cli.utils.config.os.path.dirname", return_value="dir-name")
@mock.patch("aea.cli.utils.config.os.path.exists", return_value=False)
@mock.patch("aea.cli.utils.config.os.makedirs")
@mock.patch("aea.cli.utils.click_utils.open_file")
class InitConfigFolderTestCase(TestCase):
    """Test case for _init_cli_config method."""

    def test_init_cli_config_positive(
        self, open_mock, makedirs_mock, exists_mock, dirname_mock
    ):
        """Test for _init_cli_config method positive result."""
        _init_cli_config()
        dirname_mock.assert_called_once()
        exists_mock.assert_called_once_with("dir-name")
        makedirs_mock.assert_called_once_with("dir-name")


@mock.patch("aea.cli.utils.config.get_or_create_cli_config")
@mock.patch("aea.cli.utils.config.validate_cli_config")
@mock.patch("yaml.dump")
@mock.patch("aea.cli.utils.config.open_file", mock.mock_open())
class UpdateCLIConfigTestCase(TestCase):
    """Test case for update_cli_config method."""

    def testupdate_cli_config_positive(self, icf_mock, validate_mock, yaml_dump):
        """Test for update_cli_config method positive result."""
        update_cli_config({"some": "config"})
        icf_mock.assert_called_once()
        validate_mock.assert_called_once()
        yaml_dump.assert_called_once()


def _raise_yamlerror(*args):
    raise YAMLError()


def _raise_file_not_found_error(*args):
    raise FileNotFoundError()


@mock.patch("aea.cli.utils.click_utils.open_file", mock.mock_open())
@mock.patch("aea.cli.utils.config.validate_cli_config")
class GetOrCreateCLIConfigTestCase(TestCase):
    """Test case for read_cli_config method."""

    @mock.patch(
        "aea.cli.utils.generic.yaml.safe_load", return_value={"correct": "output"}
    )
    def testget_or_create_cli_config_positive(self, safe_load_mock, validate_mock):
        """Test for get_or_create_cli_config method positive result."""
        result = get_or_create_cli_config()
        expected_result = {"correct": "output"}
        self.assertEqual(result, expected_result)
        safe_load_mock.assert_called_once()
        validate_mock.assert_called_once()

    @mock.patch("aea.cli.utils.generic.yaml.safe_load", _raise_yamlerror)
    def testget_or_create_cli_config_bad_yaml(self, validate_mock):
        """Test for rget_or_create_cli_config method bad yaml behavior."""
        with self.assertRaises(ClickException):
            get_or_create_cli_config()


class CleanAfterTestCase(TestCase):
    """Test case for clean_after decorator method."""

    @mock.patch("aea.cli.utils.decorators.os.path.exists", return_value=True)
    @mock.patch("aea.cli.utils.decorators._cast_ctx", lambda x: x)
    @mock.patch("aea.cli.utils.decorators.shutil.rmtree")
    def test_clean_after_positive(self, rmtree_mock, *mocks):
        """Test clean_after decorator method for positive result."""

        @clean_after
        def func(click_context):
            ctx = cast(Context, click_context.obj)
            ctx.clean_paths.append("clean/path")
            raise ClickException("Message")

        with self.assertRaises(ClickException):
            func(ContextMock())
            rmtree_mock.assert_called_once_with("clean/path")


@mock.patch("aea.cli.utils.package_utils.click.echo", raise_stoptest)
class ValidateAuthorNameTestCase(TestCase):
    """Test case for validate_author_name method."""

    @mock.patch(
        "aea.cli.utils.package_utils.click.prompt", return_value="correct_author"
    )
    def test_validate_author_name_positive(self, prompt_mock):
        """Test validate_author_name for positive result."""
        author = "valid_author"
        result = validate_author_name(author=author)
        self.assertEqual(result, author)

        result = validate_author_name()
        self.assertEqual(result, "correct_author")
        prompt_mock.assert_called_once()

    @mock.patch(
        "aea.cli.utils.package_utils.click.prompt", return_value="inv@l1d_@uth&r"
    )
    def test_validate_author_name_negative(self, prompt_mock):
        """Test validate_author_name for negative result."""
        with self.assertRaises(StopTest):
            validate_author_name()

        prompt_mock.return_value = "skills"
        with self.assertRaises(StopTest):
            validate_author_name()


class ValidatePackageNameTestCase(TestCase):
    """Test case for validate_package_name method."""

    def test_validate_package_name_positive(self):
        """Test validate_package_name for positive result."""
        validate_package_name("correct_name")

    def test_validate_package_name_negative(self):
        """Test validate_package_name for negative result."""
        with self.assertRaises(BadParameter):
            validate_package_name("incorrect-name")


def _raise_validation_error(*args, **kwargs):
    raise ValidationError("Message.")


class FindItemLocallyTestCase(TestCase):
    """Test case for find_item_locally method."""

    @mock.patch("aea.cli.utils.package_utils.Path.exists", return_value=True)
    @mock.patch(
        "aea.cli.utils.package_utils.ConfigLoader.from_configuration_type",
        _raise_validation_error,
    )
    def test_find_item_locally_bad_config(self, *mocks):
        """Test find_item_locally for bad config result."""
        public_id = PublicIdMock.from_str("fetchai/echo:0.19.0")
        with self.assertRaises(ClickException) as cm:
            find_item_locally(ContextMock(), "skill", public_id)

        self.assertIn("configuration file not valid", cm.exception.message)

    @mock.patch("aea.cli.utils.package_utils.Path.exists", return_value=True)
    @mock.patch("aea.cli.utils.package_utils.open_file", mock.mock_open())
    @mock.patch(
        "aea.cli.utils.package_utils.ConfigLoader.from_configuration_type",
        return_value=ConfigLoaderMock(),
    )
    def test_find_item_locally_cant_find(self, from_conftype_mock, *mocks):
        """Test find_item_locally for can't find result."""
        public_id = PublicIdMock.from_str("fetchai/echo:0.19.0")
        with self.assertRaises(ClickException) as cm:
            find_item_locally(ContextMock(), "skill", public_id)

        self.assertEqual(
            cm.exception.message, "Cannot find skill with author and version specified."
        )


class FindItemInDistributionTestCase(TestCase):
    """Test case for find_item_in_distribution method."""

    @mock.patch("aea.cli.utils.package_utils.Path.exists", return_value=True)
    @mock.patch(
        "aea.cli.utils.package_utils.ConfigLoader.from_configuration_type",
        _raise_validation_error,
    )
    def testfind_item_in_distribution_bad_config(self, *mocks):
        """Test find_item_in_distribution for bad config result."""
        public_id = PublicIdMock.from_str("fetchai/echo:0.19.0")
        with self.assertRaises(ClickException) as cm:
            find_item_in_distribution(ContextMock(), "skill", public_id)

        self.assertIn("configuration file not valid", cm.exception.message)

    @mock.patch("aea.cli.utils.package_utils.Path.exists", return_value=False)
    def testfind_item_in_distribution_not_found(self, *mocks):
        """Test find_item_in_distribution for not found result."""
        public_id = PublicIdMock.from_str("fetchai/echo:0.19.0")
        with self.assertRaises(ClickException) as cm:
            find_item_in_distribution(ContextMock(), "skill", public_id)

        self.assertIn("Cannot find skill", cm.exception.message)

    @mock.patch("aea.cli.utils.package_utils.Path.exists", return_value=True)
    @mock.patch("aea.cli.utils.package_utils.open_file", mock.mock_open())
    @mock.patch(
        "aea.cli.utils.package_utils.ConfigLoader.from_configuration_type",
        return_value=ConfigLoaderMock(),
    )
    def testfind_item_in_distribution_cant_find(self, from_conftype_mock, *mocks):
        """Test find_item_locally for can't find result."""
        public_id = PublicIdMock.from_str("fetchai/echo:0.19.0")
        with self.assertRaises(ClickException) as cm:
            find_item_in_distribution(ContextMock(), "skill", public_id)

        self.assertEqual(
            cm.exception.message, "Cannot find skill with author and version specified."
        )


class ValidateConfigConsistencyTestCase(TestCase):
    """Test case for _validate_config_consistency method."""

    @mock.patch("aea.cli.utils.config.Path.exists", _raise_validation_error)
    def test__validate_config_consistency_cant_find(self, *mocks):
        """Test _validate_config_consistency can't find result"""
        with self.assertRaises(ValueError) as cm:
            _validate_config_consistency(ContextMock(protocols=["some"]))

        self.assertIn("Cannot find", str(cm.exception))


@mock.patch(
    "aea.cli.utils.package_utils._compute_fingerprint",
    return_value={"correct": "fingerprint"},
)
class IsFingerprintCorrectTestCase(TestCase):
    """Test case for adding skill with invalid fingerprint."""

    def test_is_fingerprint_correct_positive(self, *mocks):
        """Test is_fingerprint_correct method for positive result."""
        item_config = mock.Mock()
        item_config.fingerprint = {"correct": "fingerprint"}
        item_config.fingerprint_ignore_patterns = []
        result = is_fingerprint_correct("package_path", item_config)
        self.assertTrue(result)

    def test_is_fingerprint_correct_negative(self, *mocks):
        """Test is_fingerprint_correct method for negative result."""
        item_config = mock.Mock()
        item_config.fingerprint = {"incorrect": "fingerprint"}
        item_config.fingerprint_ignore_patterns = []
        package_path = "package_dir"
        result = is_fingerprint_correct(package_path, item_config)
        self.assertFalse(result)


@mock.patch("aea.cli.utils.package_utils.LedgerApis", mock.MagicMock())
class TryGetBalanceTestCase(TestCase):
    """Test case for try_get_balance method."""

    def test_try_get_balance_positive(self):
        """Test for try_get_balance method positive result."""
        agent_config = mock.Mock()
        agent_config.default_ledger_config = FetchAICrypto.identifier

        wallet_mock = mock.Mock()
        wallet_mock.addresses = {FetchAICrypto.identifier: "some-adress"}
        try_get_balance(agent_config, wallet_mock, FetchAICrypto.identifier)


@mock.patch("aea.cli.utils.generic.os.path.exists", return_value=True)
class IsReadmePresentTestCase(TestCase):
    """Test case for is_readme_present method."""

    def test_is_readme_present_positive(self, *mocks):
        """Test is_readme_present for positive result."""
        self.assertTrue(is_readme_present("readme/path"))


@mock.patch("aea.cli.utils.package_utils.get_package_path", return_value="some_path")
@mock.patch("aea.cli.utils.package_utils.is_item_present")
@pytest.mark.parametrize("vendor", [True, False])
def test_get_package_path_unified(mock_present, mock_path, vendor):
    """Test 'get_package_path_unified'."""
    contex_mock = mock.MagicMock()
    contex_mock.agent_config.author = "some_author" if vendor else "another_author"
    mock_present.return_value = vendor
    public_id_mock = mock.MagicMock(author="some_author")
    result = get_package_path_unified(
        ".", contex_mock.agent_config, "some_component_type", public_id_mock
    )
    assert result == "some_path"


@mock.patch("aea.cli.utils.package_utils.get_package_path", return_value="some_path")
@mock.patch("aea.cli.utils.package_utils.is_item_present")
@pytest.mark.parametrize("vendor", [True, False])
def test_get_dotted_package_path_unified(mock_present, mock_path, vendor):
    """Test 'get_package_path_unified'."""
    contex_mock = mock.MagicMock()
    contex_mock.cwd = "."
    contex_mock.agent_config.author = "some_author" if vendor else "another_author"
    mock_present.return_value = vendor
    public_id_mock = mock.MagicMock(author="some_author")
    result = get_dotted_package_path_unified(
        ".", contex_mock.agent_config, "some_component_type", public_id_mock
    )
    assert result == "some_path"


@mock.patch("aea.cli.utils.package_utils.is_item_present", return_value=False)
@pytest.mark.parametrize("vendor", [True, False])
def test_is_item_present_unified(mock_, vendor):
    """Test 'is_item_present_unified'."""
    contex_mock = mock.MagicMock()
    contex_mock.agent_config.author = "some_author" if vendor else "another_author"
    public_id_mock = mock.MagicMock(author="some_author")
    result = is_item_present_unified(contex_mock, "some_component_type", public_id_mock)
    assert not result


@pytest.mark.parametrize(
    ["public_id", "expected_outcome"],
    [
        (PublicId.from_str("author/package:0.1.0"), False),
        (PublicId.from_str("author/package:latest"), False),
        (PublicId.from_str("fetchai/oef:0.1.0"), False),
        (PublicId.from_str("fetchai/oef:latest"), False),
        (PublicId.from_str("fetchai/stub:latest"), False),
        (DefaultMessage.protocol_id, False),
    ],
)
def test_is_distributed_item(public_id, expected_outcome):
    """Test the 'is_distributed_item' CLI utility function."""
    assert is_distributed_item(public_id) is expected_outcome


class TestGetWalletFromtx(AEATestCaseEmpty):
    """Test get_wallet_from_context."""

    def test_get_wallet_from_ctx(self):
        """Test get_wallet_from_context."""
        ctx = mock.Mock()
        with cd(self._get_cwd()):
            assert isinstance(get_wallet_from_context(ctx), Wallet)


def test_override_ledger_configurations_negative():
    """Test override ledger configurations function util when nothing to override."""
    agent_config = MagicMock()
    agent_config.component_configurations = {}
    expected_configurations = deepcopy(LedgerApis.ledger_api_configs)
    _override_ledger_configurations(agent_config)
    actual_configurations = LedgerApis.ledger_api_configs
    assert expected_configurations == actual_configurations


def test_override_ledger_configurations_positive():
    """Test override ledger configurations function util with fields to override."""
    new_chain_id = 134
    agent_config = MagicMock()
    agent_config.component_configurations = {
        ComponentId(
            ComponentType.CONNECTION, PublicId.from_str("fetchai/ledger:latest")
        ): {"config": {"ledger_apis": {DEFAULT_LEDGER: {"chain_id": new_chain_id}}}}
    }
    old_configurations = deepcopy(LedgerApis.ledger_api_configs)

    expected_configurations = deepcopy(old_configurations[DEFAULT_LEDGER])
    expected_configurations["chain_id"] = new_chain_id
    try:
        _override_ledger_configurations(agent_config)
        actual_configurations = LedgerApis.ledger_api_configs.get(DEFAULT_LEDGER)
        assert expected_configurations == actual_configurations
    finally:
        # this is important - _ovveride_ledger_configurations does
        # side-effect to LedgerApis.ledger_api_configs
        LedgerApis.ledger_api_configs = old_configurations
        assert (
            LedgerApis.ledger_api_configs[DEFAULT_LEDGER]["chain_id"]
            == ETHEREUM_DEFAULT_CHAIN_ID
        )


@mock.patch("aea.cli.utils.config.get_or_create_cli_config", return_value={})
def test_set_cli_author_negative(*_mocks):
    """Test set_cli_author, negative case."""
    with pytest.raises(
        ClickException,
        match="The AEA configurations are not initialized. Use `aea init` before continuing.",
    ):
        set_cli_author(MagicMock())


@mock.patch(
    "aea.cli.utils.config.get_or_create_cli_config",
    return_value=dict(author="some_author"),
)
def test_set_cli_author_positive(*_mocks):
    """Test set_cli_author, positive case."""
    context_mock = MagicMock()
    set_cli_author(context_mock)
    context_mock.obj.set_config.assert_called_with("cli_author", "some_author")


def test_password_option():
    """Test password option."""

    @click.command()
    @password_option()
    def cmd(password):
        raise ValueError(password)

    # no password specified
    with pytest.raises(ValueError, match="None"):
        CliRunner().invoke(cmd, [], catch_exceptions=False, standalone_mode=False)

    # --password specified
    password = uuid4().hex
    with pytest.raises(ValueError, match=password):
        CliRunner().invoke(
            cmd, ["--password", password], catch_exceptions=False, standalone_mode=False
        )

    # -p to ask with click.prompt
    with pytest.raises(ValueError, match=password):
        with patch("click.prompt", return_value=password):
            CliRunner().invoke(
                cmd, ["-p"], catch_exceptions=False, standalone_mode=False
            )
    # -p and --password togehter, -p in priority
    with pytest.raises(ValueError, match=password):
        with patch("click.prompt", return_value="prompted_password"):
            CliRunner().invoke(
                cmd,
                ["-p", "--password", password],
                catch_exceptions=False,
                standalone_mode=False,
            )


def test_context_registry_path_does_not_exist():
    """Test context registry path specified but not found."""
    with pytest.raises(
        ValueError, match="Registry path directory provided .* can not be found."
    ):
        Context(
            cwd=".", verbosity="", registry_path="some_path_does_not_exist"
        ).registry_path

    with TemporaryDirectory() as tmp_dir:
        with cd(tmp_dir):
            with pytest.raises(
                ValueError,
                match="Registry path not provided and local registry `packages` not found",
            ):
                Context(cwd=".", verbosity="", registry_path=None).registry_path
