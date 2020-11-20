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

"""This package contains a behaviour for fetching a coin price from an API."""

import json
from typing import Dict, cast

from aea.mail.base import EnvelopeContext
from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.connections.http_client.connection import PUBLIC_ID
from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.skills.coin_price.dialogues import HttpDialogues


class CoinPriceBehaviour(TickerBehaviour):
    """This class provides a simple behaviour to fetch a coin price."""

    def __init__(self, **kwargs):
        """Initialize the coin price behaviour."""

        super().__init__(**kwargs)

    def send_http_request_message(
        self, method: str, url: str, content: Dict = None
    ) -> None:
        """
        Send an http request message.

        :param method: the http request method (i.e. 'GET' or 'POST').
        :param url: the url to send the message to.
        :param content: the payload.

        :return: None
        """

        # context
        http_dialogues = cast(HttpDialogues, self.context.http_dialogues)

        # http request message
        request_http_message, _ = http_dialogues.create(
            counterparty=str(PUBLIC_ID),
            performative=HttpMessage.Performative.REQUEST,
            method=method,
            url=url,
            headers="",
            version="",
            body=b"" if content is None else json.dumps(content).encode("utf-8"),
        )

        # send message
        envelope_context = EnvelopeContext(skill_id=self.context.skill_id)
        self.context.outbox.put_message(
            message=request_http_message, context=envelope_context
        )

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        self.context.logger.info("setting up CoinPriceBehaviour")

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """

        model = self.context.coin_price_model

        url = model.url
        coin_id = model.coin_id
        currency = model.currency

        self.context.logger.info(
            f"Fetching price of {coin_id} in {currency} from CoinPrice"
        )

        query = f"simple/price?ids={coin_id}&vs_currencies={currency}"

        self.send_http_request_message("GET", url + query)

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        self.context.logger.info("tearing down CoinPriceBehaviour")
