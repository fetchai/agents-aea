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
"""Registry utils used for CLI login command."""

from typing import cast

from aea.cli.registry.utils import request_api
from aea.common import JSONLike


def registry_login(username: str, password: str) -> str:
    """
    Login into Registry account.

    :param username: str username.
    :param password: str password.

    :return: str token
    """
    resp = cast(
        JSONLike,
        request_api(
            "POST",
            "/rest-auth/login/",
            data={"username": username, "password": password},
        ),
    )
    return cast(str, resp["key"])


def registry_reset_password(email: str) -> None:
    """
    Request Registry to reset password.

    :param email: user email.
    """
    request_api("POST", "/rest-auth/password/reset/", data={"email": email})
