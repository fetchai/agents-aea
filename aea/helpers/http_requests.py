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
"""Wrapper over requests library."""
from functools import wraps
from typing import Any, Callable

import requests

from aea.helpers.constants import NETWORK_REQUEST_DEFAULT_TIMEOUT


DEFAULT_TIMEOUT = NETWORK_REQUEST_DEFAULT_TIMEOUT


# requests can use one of these
try:
    from simplejson.errors import (  # type: ignore  # pylint: disable=unused-import
        JSONDecodeError,
    )
except ModuleNotFoundError:  # pragma: nocover
    from json.decoder import JSONDecodeError  # noqa  # pylint: disable=unused-import


def add_default_timeout(fn: Callable, timeout: float) -> Callable:
    """Add default timeout for requests methods."""

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Callable:  # pragma: nocover
        kwargs["timeout"] = kwargs.get("timeout", timeout)
        return fn(*args, **kwargs)

    return wrapper


get = add_default_timeout(requests.get, DEFAULT_TIMEOUT)
post = add_default_timeout(requests.post, DEFAULT_TIMEOUT)
request = add_default_timeout(requests.request, DEFAULT_TIMEOUT)
head = add_default_timeout(requests.head, DEFAULT_TIMEOUT)

exceptions = requests.exceptions

Response = requests.Response
ConnectionError = requests.ConnectionError  # pylint: disable=redefined-builtin
