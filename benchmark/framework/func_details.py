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


class FuncDetails:
    """Class to introspect some callable details."""

    def __init__(self, func: Callable):
        """Create an instance."""
        self.func = func

    def check(self) -> None:
        """Check for docstring and arguments have default values set."""
        if not self.doc:
            raise ValueError("Function docstring is missing")

        if self._arguments[0].name != "control":
            raise ValueError("first function argument must be named `control`!")

    @property
    def doc(self) -> str:
        """Return docstring for function."""
        return self.func.__doc__ or ""

    @property
    def _arguments(self) -> List[Parameter]:
        """Get list of arguments defined in function."""
        sig = inspect.signature(self.func)
        return list(sig.parameters.values())

    @property
    def argument_names(self) -> List[str]:
        """Get list of argument names in function."""
        return [i.name for i in self._arguments[1:]]

    @property
    def default_argument_values(self) -> List[Any]:
        """Get list of argument default values."""
        default_args = []
        for arg in self._arguments[1:]:
            if arg.default == inspect._empty:  # type: ignore
                raise ValueError(
                    "function should have default values for every param except control"
                )
            default_args.append(arg.default)
        return default_args

    @property
    def default_argument_values_as_string(self) -> str:
        """Get list of argument default values as a string."""
        return ",".join(map(repr, self.default_argument_values))
