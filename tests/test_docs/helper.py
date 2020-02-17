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

import re


def extract_code_blocks(file, filter=None):
    """Extract code blocks from .md files."""
    code_blocks = []
    with open(file, "r") as f:
        while True:
            line = f.readline()
            if not line:
                # EOF
                break

            out = re.match("[^`]*```(.*)$", line)
            if out:
                if filter and filter.strip() != out.group(1).strip():
                    continue
                code_block = [f.readline()]
                while re.search("```", code_block[-1]) is None:
                    code_block.append(f.readline())
                code_blocks.append("".join(code_block[:-1]))
    return code_blocks
