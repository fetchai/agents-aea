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
"""Module with methods for new user registration."""

from typing import Dict, List, cast

from click import ClickException

from aea.cli.registry.utils import request_api


def register(
    username: str, email: str, password: str, password_confirmation: str
) -> str:
    """
    Register new Registry account and automatically login if successful.

    :param username: str username.
    :param email: str email.
    :param password: str password.
    :param password_confirmation: str password confirmation.

    :return: str auth token.
    """
    data = {
        "username": username,
        "email": email,
        "password1": password,
        "password2": password_confirmation,
    }
    resp_json, status_code = request_api(
        "POST",
        "/rest-auth/registration/",
        data=data,
        handle_400=False,
        return_code=True,
    )
    resp_json = cast(Dict, resp_json)
    if status_code == 400:
        errors: List[str] = []
        for key in ("username", "email", "password1", "password2"):
            param_errors = cast(str, resp_json.get(key))
            if param_errors:
                errors.extend(param_errors)

        raise ClickException(
            "Errors occured during registration.\n" + "\n".join(errors)
        )
    return cast(str, resp_json["key"])
