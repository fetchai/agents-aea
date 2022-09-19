# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""This test module contains the tests for the `aea scaffold` sub-command."""

from pathlib import Path


def files_outside_copyright_are_identical(*files: Path) -> bool:
    """Check files are identical outside copyright author / year"""

    def remove_copyright_author_year_lines(s: str) -> str:
        """Filter copyright author and year for file comparison"""
        lines, prefix = s.splitlines(), "#   Copyright"
        return "/n".join(line for line in lines if not line.startswith(prefix))

    lines = (f.read_text() for f in files)
    cleaned_lines = set(map(remove_copyright_author_year_lines, lines))
    return len(set(cleaned_lines)) == 1
