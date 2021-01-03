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

"""This module contains the tests for the content of data-models.md file."""
from pathlib import Path

from aea.helpers.search.models import Attribute, DataModel, Description

from tests.conftest import ROOT_DIR
from tests.test_docs.helper import BasePythonMarkdownDocs


class TestDataModel(BasePythonMarkdownDocs):
    """Test the data models code snippets."""

    DOC_PATH = Path(ROOT_DIR, "docs", "defining-data-models.md")

    def _assert(self, locals_, *_mocks):
        attribute = locals_["attr_title"]
        assert isinstance(attribute, Attribute)

        data_model = locals_["book_model"]
        assert isinstance(data_model, DataModel)

        description = locals_["It"]
        assert isinstance(description, Description)
