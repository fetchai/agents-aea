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

"""This package contains a model for the AdvancedDataRequest skill"""

from typing import Any

from aea.skills.base import Model


DEFAULT_URL = ""
DEFAULT_METHOD = "GET"
DEFAULT_BODY = ""
DEFAULT_OUTPUTS = None
DEFAULT_DECIMALS = 5
DEFAULT_USE_HTTP_SERVER = False

HTTP_REQUEST_METHODS = {"GET", "PUT", "POST", "PATCH", "DELETE"}


class AdvancedDataRequestModel(Model):
    """This class models the AdvancedDataRequest skill."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize dialogues.

        :param kwargs: keyword arguments
        """
        self.url = kwargs.pop("url", DEFAULT_URL)
        self.method = kwargs.pop("method", DEFAULT_METHOD)
        self.body = kwargs.pop("body", DEFAULT_BODY)
        self.outputs = kwargs.pop("outputs", DEFAULT_OUTPUTS)
        self.decimals = kwargs.pop("decimals", DEFAULT_DECIMALS)
        self.use_http_server = kwargs.pop("use_http_server", DEFAULT_USE_HTTP_SERVER)

        Model.__init__(self, **kwargs)

        self._validate_config()

    def _validate_config(self) -> None:  # pragma: nocover
        """Ensure the configuration settings are all valid."""
        msg = []
        if not isinstance(self.url, str):
            msg.append("'url' must be provided as a string")
        if self.method not in HTTP_REQUEST_METHODS:
            msg.append(f"'method' must be one of {HTTP_REQUEST_METHODS}")
        if not isinstance(self.body, str):
            msg.append("'body' must be provided as a string")
        if not isinstance(self.outputs, list):
            msg.append("outputs must be provided as a list")
        else:
            for (ind, output) in enumerate(self.outputs):
                if not isinstance(output, dict):
                    msg.append(f"output {ind} must be a dict")
                else:
                    if "name" not in output:
                        msg.append(f"output {ind} must include key 'name'")
                    if "json_path" not in output:
                        msg.append(f"output {ind} must include key 'json_path'")
        if not isinstance(self.decimals, int):
            msg.append("'decimals' must be provided as an integer")
        if not isinstance(self.use_http_server, bool):
            msg.append("'use_http_server' must be provided as a bool")

        if msg:
            raise ValueError("Invalid skill configuration: " + ",".join(msg))
