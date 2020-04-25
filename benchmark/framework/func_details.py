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
"""Helper module for details about function being tested."""
import inspect
from inspect import Parameter
from typing import Any, Callable, List


class BaseFuncDetails:
    """Class to introspect some callable details: name, docstring, arguments."""

    def __init__(self, func: Callable):
        """
        Create an instance.

        :param func: Function or another callable to get details.
        """
        self.func = func

    @property
    def doc(self) -> str:
        """
        Return docstring for function.

        :return: str. docstring for function
        """
        return self.func.__doc__ or ""

    @property
    def name(self) -> str:
        """
        Return function definition name.

        :return: str
        """
        return self.func.__name__ or ""

    @property
    def _arguments(self) -> List[Parameter]:
        """
        Get list of arguments defined in function.

        :return: list of function parameters
        """
        sig = inspect.signature(self.func)
        return list(sig.parameters.values())

    @property
    def argument_names(self) -> List[str]:
        """
        Get list of argument names in function.

        :return: list of function argument names
        """
        return [i.name for i in self._arguments]

    @property
    def default_argument_values(self) -> List[Any]:
        """
        Get list of argument default values.

        :return: list of default values for funcion arguments
        """
        default_args = []
        for arg in self._arguments:
            default_args.append(arg.default)
        return default_args

    @property
    def default_argument_values_as_string(self) -> str:
        """
        Get list of argument default values as a string.

        :return: str
        """
        return ",".join(map(repr, self.default_argument_values))


class BenchmarkFuncDetails(BaseFuncDetails):
    """
    Special benchmarked function details.

    With check of function definition.

    :param CONTROL_ARG_NAME: Name of the special argument name, placed first.
    """

    CONTROL_ARG_NAME: str = "benchmark"

    def check(self) -> None:
        """
        Check for docstring and arguments have default values set.

        Raises exception if function definition does not contain docstring or default values.

        :return: None
        """
        if not self.doc:
            raise ValueError("Function docstring is missing")

        if super()._arguments[0].name != self.CONTROL_ARG_NAME:
            raise ValueError(
                f"first function argument must be named `{self.CONTROL_ARG_NAME}`!"
            )

        for arg in self._arguments:
            if arg.default == inspect._empty:  # type: ignore
                raise ValueError(
                    "function should have default values for every param except first one"
                )

    @property
    def _arguments(self) -> List[Parameter]:
        """
        Skip first argument, cause it special.

        :return: list of function arguments except the first one named `benchmark`
        """
        return super()._arguments[1:]
