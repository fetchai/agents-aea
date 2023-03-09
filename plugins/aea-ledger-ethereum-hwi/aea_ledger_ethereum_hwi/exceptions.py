# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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

"""Custom exceptions for hardware wallet interface"""


class HWIError(Exception):
    """Hardware wallet interface error"""

    def __init__(self, message: str, sw: int, data=None) -> None:
        """Initialize object."""

        self.message = message
        self.sw = sw
        self.data = data

    def __str__(self) -> str:
        """Serialize message to string"""

        return self.message
