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

"""This module contains helper function to extract code from the .md files."""

from pathlib import Path

from tests.test_docs.helper import extract_code_blocks, read_md_file
from tests.conftest import ROOT_DIR

FILEPATH = Path(ROOT_DIR, "docs", "orm-integration-to-generic.md")
DESTINATION_PATH = Path(ROOT_DIR, "tests", "test_docs", "test_bash_yaml", "md_files", "bash-orm-integration-to-generic.md")

code_blocks = extract_code_blocks(file=FILEPATH, filter="bash")
file_to_write = ""
for blocks in code_blocks:
    file_to_write += "``` bash \n" + blocks + "``` \n"

code_blocks = extract_code_blocks(file=FILEPATH, filter="yaml")
for blocks in code_blocks:
    file_to_write += "``` yaml \n" + blocks + "``` \n"

with open(DESTINATION_PATH, "w+") as file:
    file.write(file_to_write)






