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

"""This test module contains the tests for aea.cli.utils module."""

from builtins import FileNotFoundError
from typing import cast
from unittest import TestCase, mock

from click import BadParameter, ClickException

from jsonschema import ValidationError

from yaml import YAMLError

from aea.cli.utils.click_utils import AEAJsonPathType, PublicIdParameter
from aea.cli.utils.config import (
    _init_cli_config,
    get_or_create_cli_config,
    update_cli_config,
)
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import _validate_config_consistency, clean_after
from aea.cli.utils.formatting import format_items
from aea.cli.utils.generic import is_readme_present
from aea.cli.utils.package_utils import (
    find_item_in_distribution,
    find_item_locally,
    is_fingerprint_correct,
    try_get_balance,
    try_get_item_source_path,
    try_get_item_target_path,
    validate_author_name,
    validate_package_name,
)

from tests.conftest import FETCHAI
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
                "name": "obj-name",
                "description": "Some description",
                "author": "author",
                "version": "1.0",
            }
        ]
        result = format_items(items)
        expected_result = (
            "------------------------------\n"
            "Public ID: author/name:version\n"
            "Name: obj-name\n"
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
        result = try_get_item_source_path("cwd", AUTHOR, "skills", "skill-name")
        expected_result = "some-path"
        self.assertEqual(result, expected_result)
        join_mock.assert_called_once_with("cwd", AUTHOR, "skills", "skill-name")
        exists_mock.assert_called_once_with("some-path")

        result = try_get_item_source_path("cwd", None, "skills", "skill-name")
        self.assertEqual(result, expected_result)

    @mock.patch("aea.cli.utils.package_utils.os.path.exists", return_value=False)
    def test_get_item_source_path_not_exists(self, exists_mock, join_mock):
        """Test for get_item_source_path item already exists."""
        with self.assertRaises(ClickException):
            try_get_item_source_path("cwd", AUTHOR, "skills", "skill-name")


@mock.patch("aea.cli.utils.package_utils.os.path.join", return_value="some-path")
class TryGetItemTargetPathTestCase(TestCase):
    """Test case for try_get_item_target_path method."""

    @mock.patch("aea.cli.utils.package_utils.os.path.exists", return_value=False)
    def test_get_item_target_path_positive(self, exists_mock, join_mock):
        """Test for get_item_source_path positive result."""
        result = try_get_item_target_path("packages", AUTHOR, "skills", "skill-name")
        expected_result = "some-path"
        self.assertEqual(result, expected_result)
        join_mock.assert_called_once_with("packages", AUTHOR, "skills", "skill-name")
        exists_mock.assert_called_once_with("some-path")

    @mock.patch("aea.cli.utils.package_utils.os.path.exists", return_value=True)
    def test_get_item_target_path_already_exists(self, exists_mock, join_mock):
        """Test for get_item_target_path item already exists."""
        with self.assertRaises(ClickException):
            try_get_item_target_path("skills", AUTHOR, "skill-name", "packages_path")


class PublicIdParameterTestCase(TestCase):
    """Test case for PublicIdParameter class."""

    def test_get_metavar_positive(self):
        """Test for get_metavar positive result."""
        result = PublicIdParameter.get_metavar("obj", "param")
        expected_result = "PUBLIC_ID"
        self.assertEqual(result, expected_result)


@mock.patch("aea.cli.utils.config.os.path.dirname", return_value="dir-name")
@mock.patch("aea.cli.utils.config.os.path.exists", return_value=False)
@mock.patch("aea.cli.utils.config.os.makedirs")
class InitConfigFolderTestCase(TestCase):
    """Test case for _init_cli_config method."""

    def test_init_cli_config_positive(self, makedirs_mock, exists_mock, dirname_mock):
        """Test for _init_cli_config method positive result."""
        _init_cli_config()
        dirname_mock.assert_called_once()
        exists_mock.assert_called_once_with("dir-name")
        makedirs_mock.assert_called_once_with("dir-name")


@mock.patch("aea.cli.utils.config.get_or_create_cli_config")
@mock.patch("aea.cli.utils.generic.yaml.dump")
@mock.patch("builtins.open", mock.mock_open())
class UpdateCLIConfigTestCase(TestCase):
    """Test case for update_cli_config method."""

    def testupdate_cli_config_positive(self, dump_mock, icf_mock):
        """Test for update_cli_config method positive result."""
        update_cli_config({"some": "config"})
        icf_mock.assert_called_once()
        dump_mock.assert_called_once()


def _raise_yamlerror(*args):
    raise YAMLError()


def _raise_file_not_found_error(*args):
    raise FileNotFoundError()


@mock.patch("builtins.open", mock.mock_open())
class GetOrCreateCLIConfigTestCase(TestCase):
    """Test case for read_cli_config method."""

    @mock.patch(
        "aea.cli.utils.generic.yaml.safe_load", return_value={"correct": "output"}
    )
    def testget_or_create_cli_config_positive(self, safe_load_mock):
        """Test for get_or_create_cli_config method positive result."""
        result = get_or_create_cli_config()
        expected_result = {"correct": "output"}
        self.assertEqual(result, expected_result)
        safe_load_mock.assert_called_once()

    @mock.patch("aea.cli.utils.generic.yaml.safe_load", _raise_yamlerror)
    def testget_or_create_cli_config_bad_yaml(self):
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
        public_id = PublicIdMock.from_str("fetchai/echo:0.3.0")
        with self.assertRaises(ClickException) as cm:
            find_item_locally(ContextMock(), "skill", public_id)

        self.assertIn("configuration file not valid", cm.exception.message)

    @mock.patch("aea.cli.utils.package_utils.Path.exists", return_value=True)
    @mock.patch("aea.cli.utils.package_utils.Path.open", mock.mock_open())
    @mock.patch(
        "aea.cli.utils.package_utils.ConfigLoader.from_configuration_type",
        return_value=ConfigLoaderMock(),
    )
    def test_find_item_locally_cant_find(self, from_conftype_mock, *mocks):
        """Test find_item_locally for can't find result."""
        public_id = PublicIdMock.from_str("fetchai/echo:0.3.0")
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
        public_id = PublicIdMock.from_str("fetchai/echo:0.3.0")
        with self.assertRaises(ClickException) as cm:
            find_item_in_distribution(ContextMock(), "skill", public_id)

        self.assertIn("configuration file not valid", cm.exception.message)

    @mock.patch("aea.cli.utils.package_utils.Path.exists", return_value=False)
    def testfind_item_in_distribution_not_found(self, *mocks):
        """Test find_item_in_distribution for not found result."""
        public_id = PublicIdMock.from_str("fetchai/echo:0.3.0")
        with self.assertRaises(ClickException) as cm:
            find_item_in_distribution(ContextMock(), "skill", public_id)

        self.assertIn("Cannot find skill", cm.exception.message)

    @mock.patch("aea.cli.utils.package_utils.Path.exists", return_value=True)
    @mock.patch("aea.cli.utils.package_utils.Path.open", mock.mock_open())
    @mock.patch(
        "aea.cli.utils.package_utils.ConfigLoader.from_configuration_type",
        return_value=ConfigLoaderMock(),
    )
    def testfind_item_in_distribution_cant_find(self, from_conftype_mock, *mocks):
        """Test find_item_locally for can't find result."""
        public_id = PublicIdMock.from_str("fetchai/echo:0.3.0")
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


@mock.patch("aea.cli.config.click.ParamType")
class AEAJsonPathTypeTestCase(TestCase):
    """Test case for AEAJsonPathType class."""

    @mock.patch("aea.cli.utils.click_utils.Path.exists", return_value=True)
    def test_convert_root_vendor_positive(self, *mocks):
        """Test for convert method with root "vendor" positive result."""
        value = "vendor.author.protocols.package_name.attribute_name"
        ctx_mock = ContextMock()
        ctx_mock.obj = mock.Mock()
        ctx_mock.obj.set_config = mock.Mock()
        obj = AEAJsonPathType()
        obj.convert(value, "param", ctx_mock)

    @mock.patch("aea.cli.utils.click_utils.Path.exists", return_value=False)
    def test_convert_root_vendor_path_not_exists(self, *mocks):
        """Test for convert method with root "vendor" path not exists."""
        value = "vendor.author.protocols.package_name.attribute_name"
        obj = AEAJsonPathType()
        with self.assertRaises(BadParameter):
            obj.convert(value, "param", "ctx")


@mock.patch("aea.cli.utils.package_utils.LedgerApis", mock.MagicMock())
class TryGetBalanceTestCase(TestCase):
    """Test case for try_get_balance method."""

    def test_try_get_balance_positive(self):
        """Test for try_get_balance method positive result."""
        agent_config = mock.Mock()
        agent_config.default_ledger_config = FETCHAI

        wallet_mock = mock.Mock()
        wallet_mock.addresses = {FETCHAI: "some-adress"}
        try_get_balance(agent_config, wallet_mock, FETCHAI)


@mock.patch("aea.cli.utils.generic.os.path.exists", return_value=True)
class IsReadmePresentTestCase(TestCase):
    """Test case for is_readme_present method."""

    def test_is_readme_present_positive(self, *mocks):
        """Test is_readme_present for positive result."""
        self.assertTrue(is_readme_present("readme/path"))
