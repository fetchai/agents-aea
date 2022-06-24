# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""
This module contain the test for the HTTP connection and skill documentation page.

The testing strategy is to just check that the Python code reported in
the documentation is contained in the http_echo skill.

Moreover, test that the code is compilable/executable.
"""
from pathlib import Path
from unittest import mock

from tests.conftest import ROOT_DIR
from tests.test_docs.helper import BaseTestMarkdownDocs


class TestHttpConnectionAndSkill(BaseTestMarkdownDocs):
    """Test the skill testing code snippets."""

    DOC_PATH = Path(ROOT_DIR, "docs", "http-connection-and-skill.md")
    HTTP_ECHO_PATH = Path(ROOT_DIR, "packages", "fetchai", "skills", "http_echo")

    @classmethod
    def setup_class(cls):
        """Set up the test."""
        super().setup_class()

        assert (
            len(cls.python_blocks) == 3
        ), "this test expected exactly 3 Python blocks."

        # read the content of 'handlers.py' and 'dialogues.py' of skill
        cls.http_echo_handlers_module = (cls.HTTP_ECHO_PATH / "handlers.py").read_text()
        cls.http_echo_dialogues = (cls.HTTP_ECHO_PATH / "dialogues.py").read_text()

    def test_handlers_code_snippet(self):
        """Test the 'handlers.py' code snippet."""
        handlers_code_snippet = self.python_blocks[0]["text"]

        # the handlers code snippet contains the YOUR_USERNAME placeholder
        # to be replaced by the user. We need to replace it with 'fetchai'
        # in order to compare it with the skill 'fetchai/http_echo'.
        replacement = "from packages.YOUR_USERNAME.skills.http_echo.dialogues import"
        to_be_replaced = "from packages.fetchai.skills.http_echo.dialogues import"
        expected_handlers_code = self.http_echo_handlers_module.replace(
            to_be_replaced, replacement
        )

        assert handlers_code_snippet in expected_handlers_code

    def test_dialogues_code_snippet(self):
        """Test the 'dialogues.py' code snippet."""
        dialogues_code_snippet = self.python_blocks[1]["text"]

        expected_dialogues_code = self.http_echo_dialogues
        assert dialogues_code_snippet in expected_dialogues_code

    @mock.patch("requests.get")
    @mock.patch("requests.post")
    def test_requests_code_snippet(self, *_mocks):
        """Test the 'requests' code snippet."""
        _globals, locals_ = {}, {}
        requests_code_snippet = self.python_blocks[2]["text"]
        exec(requests_code_snippet, _globals, locals_)  # nosec

        assert "requests" in locals_
        assert "response" in locals_
