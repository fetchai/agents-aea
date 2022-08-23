# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""This module contains tests for the documentation tools."""

import re

from scripts.check_doc_ipfs_hashes import AEA_COMMAND_REGEX


def test_cmd_regex() -> None:
    """Test the command regex"""

    lines = [
        "aea fetch --remote open_aea/my_first_aea:bafybeibnjfr3sdg57ggyxbcfkh42yqkj6a3gftp55l26aaw2z2jvvc3tny",
        "aea fetch open_aea/my_first_aea:bafybeibnjfr3sdg57ggyxbcfkh42yqkj6a3gftp55l26aaw2z2jvvc3tny",
        "aea fetch --remote --other_flag open_aea/my_first_aea:bafybeibnjfr3sdg57ggyxbcfkh42yqkj6a3gftp55l26aaw2z2jvvc3tny",
    ]

    for line in lines:
        assert re.match(
            AEA_COMMAND_REGEX, line
        ), f"line '{line}' does not match AEA_COMMAND_REGEX"
