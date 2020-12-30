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

"""This module contains the tests for the content of language-agnostic-definition.md file."""
from pathlib import Path
from typing import Dict

import mistune

from aea import AEA_DIR
from aea.configurations.data_types import PublicId

from tests.conftest import ROOT_DIR


MAIL_BASE_PROTO = Path(AEA_DIR) / "mail" / "base.proto"
DEFAULT_MESSAGE_PROTO = (
    Path(ROOT_DIR) / "packages" / "fetchai" / "protocols" / "default" / "default.proto"
)


class TestLanguageAgnosticDocs:
    """Test the integrity of the language agnostic definitions in docs."""

    @classmethod
    def _proto_snippet_selector(cls, block: Dict) -> bool:
        return block["type"] == "block_code" and block["info"].strip() == "proto"

    @classmethod
    def setup_class(cls):
        """Set up the test."""
        markdown_parser = mistune.create_markdown(renderer=mistune.AstRenderer())

        cls.spec_doc_file = Path(ROOT_DIR, "docs", "language-agnostic-definition.md")
        cls.spec_doc_content = cls.spec_doc_file.read_text()
        doc = markdown_parser(cls.spec_doc_content)
        # get only code blocks
        cls.code_blocks = list(filter(cls._proto_snippet_selector, doc))

        cls.actual_mail_base_file_content = MAIL_BASE_PROTO.read_text()
        cls.actual_default_message_file_content = DEFAULT_MESSAGE_PROTO.read_text()

    def test_envelope_code_snippet(self):
        """
        Test the Envelope protobuf code snippet.

        It requires treating the preamble lines separately,
        because aea/mail/base.proto doesn't follow
        the same order of language-agnostic-definition.md file.
        """
        block = self.code_blocks[0]
        assert block["info"].strip() == "proto"

        lines = block["text"].splitlines()
        first_part, second_part = "\n".join(lines[:3]), "\n".join(lines[3:])

        assert first_part in self.actual_mail_base_file_content
        assert second_part in self.actual_mail_base_file_content

    def test_dialogue_message_code_snippet(self):
        """
        Test the DialogueMessage protobuf code snippet.

        It requires treating the preamble lines separately,
        because aea/mail/base.proto doesn't follow
        the same order of language-agnostic-definition.md file.
        """
        block = self.code_blocks[1]
        assert block["info"].strip() == "proto"
        assert block["text"] in self.actual_mail_base_file_content

    def test_public_id_regular_expression(self):
        """Test public id regular expression is the same."""
        expected_regex = PublicId.PUBLIC_ID_REGEX
        assert expected_regex in self.spec_doc_content

    def test_default_message_code_snippet(self):
        """Test DefaultMessage protobuf code snippet."""
        block = self.code_blocks[2]
        assert block["info"].strip() == "proto"
        assert block["text"] in self.actual_default_message_file_content
