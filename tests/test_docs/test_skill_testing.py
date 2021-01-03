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

"""This module contains the tests for the content of skill-testing.md file."""
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock

from tests.conftest import ROOT_DIR
from tests.test_docs.helper import BasePythonMarkdownDocs


@mock.patch("unittest.mock.MagicMock.assert_any_call")
class TestSkillTesting(BasePythonMarkdownDocs):
    """Test the skill testing code snippets."""

    DOC_PATH = Path(ROOT_DIR, "docs", "skill-testing.md")

    @classmethod
    def setup_class(cls):
        """Set up the test."""
        super().setup_class()
        # without this, it fails at the first block
        # with: "NameError: name 'Path' is not defined"
        cls.globals.update(globals())

        cls.locals.update(dict(cls=MagicMock(), self=MagicMock()))
