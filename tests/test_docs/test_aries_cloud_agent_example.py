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

"""Test that the documentation of the Aries Cloud agent example is consistent."""
from pathlib import Path

import mistune

import pytest

from tests.conftest import ROOT_DIR


def test_code_blocks_all_present():
    """
    Test that all the code blocks in the docs (aries-cloud-agent-example.md)
    are present in the Aries test module
    (tests/test_examples/test_http_client_connection_to_aries_cloud_agent.py).
    """

    markdown_parser = mistune.create_markdown(renderer=mistune.AstRenderer())

    skill_doc_file = Path(ROOT_DIR, "docs", "aries-cloud-agent-example.md")
    doc = markdown_parser(skill_doc_file.read_text())
    # get only code blocks
    offset = 1
    code_blocks = list(filter(lambda x: x["type"] == "block_code", doc))[offset:]

    expected_code_path = Path(
        ROOT_DIR,
        "tests",
        "test_examples",
        "test_http_client_connection_to_aries_cloud_agent.py",
    )
    expected_code = expected_code_path.read_text()

    # all code blocks must be present in the expected code
    for code_block in code_blocks:
        text = code_block["text"]
        if text.strip() not in expected_code:
            pytest.fail(
                "The following code cannot be found in {}:\n{}".format(
                    expected_code_path, text
                )
            )
