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

"""This package contains a model for the CoinPrice skill"""

from aea.skills.base import Model


DEFAULT_URL = ""
DEFAULT_COIN_ID = "fetch-ai"
DEFAULT_CURRENCY = "usd"
DEFAULT_DECIMALS = 5
DEFAULT_USE_HTTP_SERVER = False


class CoinPriceModel(Model):
    """This class models the CoinPrice skill."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """

        self.url = kwargs.pop("url", DEFAULT_URL)
        self.coin_id = kwargs.pop("coin_id", DEFAULT_COIN_ID)
        self.currency = kwargs.pop("currency", DEFAULT_CURRENCY)
        self.decimals = kwargs.pop("decimals", DEFAULT_DECIMALS)
        self.use_http_server = kwargs.pop("use_http_server", DEFAULT_USE_HTTP_SERVER)

        Model.__init__(self, **kwargs)
