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

"""This module contains the tests for the content of quickstart.md file."""
from pathlib import Path

from packages.fetchai.protocols.default.message import DefaultMessage

from tests.conftest import ROOT_DIR
from tests.test_docs.helper import BasePythonMarkdownDocs, extract_code_blocks


class TestQuickstartTest(BasePythonMarkdownDocs):
    """Test the quickstart test."""

    DOC_PATH = Path(ROOT_DIR, "docs", "quickstart.md")


def test_correct_echo_string():
    """Test the echo string in the quickstart is using the correct protocol specification id."""
    file_path = Path(ROOT_DIR, "docs", "quickstart.md")
    bash_code_blocks = extract_code_blocks(filepath=file_path, filter_="bash")
    echo_bloc = bash_code_blocks[19]
    default_protocol_spec_id = echo_bloc.split(",")[2]
    assert (
        str(DefaultMessage.protocol_specification_id) == default_protocol_spec_id
    ), "Spec ids not matching!"
