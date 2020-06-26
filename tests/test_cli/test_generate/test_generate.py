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

"""This test module contains the tests for the aea.cli.generate sub-module."""

from unittest import TestCase, mock

from click import ClickException

from aea.cli.generate import _generate_item
from aea.configurations.base import ProtocolSpecificationParseError

from tests.test_cli.tools_for_testing import ContextMock


def _raise_file_exists(*args, **kwargs):
    raise FileExistsError()


def _which_mock(arg):
    if arg == "protoc":
        return True
    else:
        return None


def _raise_psperror(*args, **kwargs):
    raise ProtocolSpecificationParseError()


@mock.patch("builtins.open", mock.mock_open())
@mock.patch("aea.protocols.generator.common.ConfigLoader")
@mock.patch("aea.cli.generate.os.path.join", return_value="joined-path")
@mock.patch("aea.cli.utils.decorators._cast_ctx")
class GenerateItemTestCase(TestCase):
    """Test case for fetch_agent_locally method."""

    def test__generate_item_file_exists(self, *mocks):
        """Test for fetch_agent_locally method file exists result."""
        ctx_mock = ContextMock()
        with self.assertRaises(ClickException):
            _generate_item(ctx_mock, "protocol", "path")

    @mock.patch("aea.protocols.generator.base.shutil.which", _which_mock)
    def test__generate_item_no_res(self, *mocks):
        """Test for fetch_agent_locally method no black."""
        ctx_mock = ContextMock()
        with self.assertRaises(ClickException) as cm:
            _generate_item(ctx_mock, "protocol", "path")
        expected_msg = (
            "Protocol is NOT generated. The following error happened while generating the protocol:\n"
            "Cannot find black code formatter! To install, please follow this link: "
            "https://black.readthedocs.io/en/stable/installation_and_usage.html"
        )
        self.assertEqual(cm.exception.message, expected_msg)

    @mock.patch("aea.cli.generate.os.path.exists", return_value=False)
    @mock.patch("aea.protocols.generator.base.shutil.which", return_value="some")
    @mock.patch("aea.cli.generate.ProtocolGenerator.generate", _raise_psperror)
    def test__generate_item_parsing_specs_fail(self, *mocks):
        """Test for fetch_agent_locally method parsing specs fail."""
        ctx_mock = ContextMock()
        with self.assertRaises(ClickException) as cm:
            _generate_item(ctx_mock, "protocol", "path")
        expected_msg = (
            "The following error happened while parsing the protocol specification"
        )
        self.assertIn(expected_msg, cm.exception.message)

    # @mock.patch("aea.cli.generate.os.path.exists", return_value=False)
    # @mock.patch("aea.cli.generate.shutil.which", return_value="some")
    # @mock.patch("aea.cli.generate.ProtocolGenerator.generate", _raise_file_exists)
    # def test__generate_item_protocol_exists(self, *mocks):
    #     """Test for fetch_agent_locally method protocol exists result."""
    #     ctx_mock = ContextMock()
    #     with self.assertRaises(ClickException) as cm:
    #         _generate_item(ctx_mock, "protocol", "path")
    #     expected_msg = (
    #         "A protocol with this name already exists. "
    #         "Please choose a different name and try again."
    #     )
    #     self.assertEqual(expected_msg, cm.exception.message)
