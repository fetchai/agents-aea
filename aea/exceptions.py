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

"""Exceptions for the AEA package."""

from typing import Type


class AEAException(Exception):
    """User-defined exception for the AEA framework."""


class AEAPackageLoadingError(AEAException):
    """Class for exceptions that are raised for loading errors of AEA packages."""


class AEAEnforceError(AEAException):
    """Class for enforcement errors."""


def enforce(
    is_valid_condition: bool,
    exception_text: str,
    exception_class: Type[Exception] = AEAEnforceError,
) -> None:
    """
    Evaluate a condition and raise an exception with the provided text if it is not satisfied.

    :param is_valid_condition: the valid condition
    :param exception_text: the exception to be raised
    :param exception_class: the class of exception
    """
    if not is_valid_condition:
        raise exception_class(exception_text)
