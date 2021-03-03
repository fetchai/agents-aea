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
DEFAULT_BODY = None
DEFAULT_OUTPUTS = None
DEFAULT_DECIMALS = 5
DEFAULT_USE_HTTP_SERVER = False

class AdvancedDataRequestModel(Model):
    """This class models the AdvancedDataRequest skill."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize dialogues.

        :return: None
        """

        self.url = kwargs.pop("url", DEFAULT_URL)
        self.method = kwargs.pop("method", DEFAULT_METHOD)
        self.body = kwargs.pop("body", DEFAULT_BODY)
        self.outputs = kwargs.pop("outputs", DEFAULT_OUTPUTS)
        self.decimals = kwargs.pop("decimals", DEFAULT_DECIMALS)
        self.use_http_server = kwargs.pop("use_http_server", DEFAULT_USE_HTTP_SERVER)

        Model.__init__(self, **kwargs)
