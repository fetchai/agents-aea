# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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

import traceback
from typing import Optional, Type


class AEAException(Exception):
    """User-defined exception for the AEA framework."""


class AEAPackageLoadingError(AEAException):
    """Class for exceptions that are raised for loading errors of AEA packages."""


class AEASetupError(AEAException):
    """Class for exceptions that are raised for setup errors of AEA packages."""


class AEATeardownError(AEAException):
    """Class for exceptions that are raised for teardown errors of AEA packages."""


class AEAActException(AEAException):
    """Class for exceptions that are raised for act errors of AEA packages."""


class AEAHandleException(AEAException):
    """Class for exceptions that are raised for handler errors of AEA packages."""


class AEAInstantiationException(AEAException):
    """Class for exceptions that are raised for instantiation errors of AEA packages."""


class AEAPluginError(AEAException):
    """Class for exceptions that are raised for wrong plugin setup of the working set."""


class AEAEnforceError(AEAException):
    """Class for enforcement errors."""


class AEAValidationError(AEAException):
    """Class for validation errors of an AEA."""


class AEAComponentLoadException(AEAException):
    """Class for component loading errors of an AEA."""


class AEAWalletNoAddressException(AEAException):
    """Class for attempts to instantiate a wallet without addresses."""


class _StopRuntime(Exception):
    """
    Exception to stop runtime.

    For internal usage only!
    Used to perform asyncio call from sync callbacks.
    """

    def __init__(self, reraise: Optional[Exception] = None) -> None:
        """
        Init _StopRuntime exception.

        :param reraise: exception to reraise.
        """
        self.reraise = reraise
        super().__init__("Stop runtime exception.")


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


def parse_exception(exception: Exception, limit: int = -1) -> str:
    """
    Parse an exception to get the relevant lines.

    :param exception: the exception to be parsed
    :param limit: the limit
    :return: exception as string
    """
    if isinstance(exception, AEAEnforceError):
        limit = -2
    msgs = traceback.format_exception(
        type(exception), exception, exception.__traceback__, limit=limit
    )
    e_str = "\n".join(msgs)
    return e_str
