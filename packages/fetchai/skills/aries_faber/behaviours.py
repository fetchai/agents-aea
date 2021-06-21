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

"""This package contains the behaviour for the aries_faber skill."""

import json
from typing import Any, Dict, cast

from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.connections.http_client.connection import (
    PUBLIC_ID as HTTP_CLIENT_PUBLIC_ID,
)
from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.aries_faber.dialogues import (
    HttpDialogues,
    OefSearchDialogues,
)
from packages.fetchai.skills.aries_faber.strategy import Strategy


DEFAULT_SEARCH_INTERVAL = 5.0


class FaberBehaviour(TickerBehaviour):
    """This class represents the behaviour of faber."""

    def __init__(self, **kwargs: Any):
        """Initialize the handler."""
        search_interval = cast(
            float, kwargs.pop("search_interval", DEFAULT_SEARCH_INTERVAL)
        )
        super().__init__(tick_interval=search_interval, **kwargs)

    def send_http_request_message(
        self, method: str, url: str, content: Dict = None
    ) -> None:
        """
        Send an http request message.

        :param method: the http request method (i.e. 'GET' or 'POST').
        :param url: the url to send the message to.
        :param content: the payload.
        """
        # context
        http_dialogues = cast(HttpDialogues, self.context.http_dialogues)

        # http request message
        request_http_message, _ = http_dialogues.create(
            counterparty=str(HTTP_CLIENT_PUBLIC_ID),
            performative=HttpMessage.Performative.REQUEST,
            method=method,
            url=url,
            headers="",
            version="",
            body=b"" if content is None else json.dumps(content).encode("utf-8"),
        )
        # send
        self.context.outbox.put_message(message=request_http_message)

    def setup(self) -> None:
        """Implement the setup."""
        strategy = cast(Strategy, self.context.strategy)
        strategy.is_searching = True

    def act(self) -> None:
        """Implement the act."""
        strategy = cast(Strategy, self.context.strategy)
        if strategy.is_searching:
            query = strategy.get_location_and_service_query()
            oef_search_dialogues = cast(
                OefSearchDialogues, self.context.oef_search_dialogues
            )
            oef_search_msg, _ = oef_search_dialogues.create(
                counterparty=self.context.search_service_address,
                performative=OefSearchMessage.Performative.SEARCH_SERVICES,
                query=query,
            )
            self.context.outbox.put_message(message=oef_search_msg)
            self.context.logger.info("Searching for Alice on SOEF...")

    def teardown(self) -> None:
        """Implement the task teardown."""
