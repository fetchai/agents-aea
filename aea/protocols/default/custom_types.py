# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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

"""This module contains class representations corresponding to every custom type in the protocol specification."""


class ErrorCode:
    """This class represents an instance of ErrorCode."""

    def __init__(self):
        """Initialise an instance of ErrorCode."""
        raise NotImplementedError

    @classmethod
    def serialise(cls, error_code: "ErrorCode") -> bytes:
        """Serialise an instance of this class."""
        raise NotImplementedError

    @classmethod
    def deserialise(cls, obj: bytes) -> "ErrorCode":
        """Deserialise an instance of this class that has been serialised."""
        raise NotImplementedError
