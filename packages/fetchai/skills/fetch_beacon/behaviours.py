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

"""This package contains the behaviour to get the Fetch random beacon."""

import json
from typing import Dict, Optional, cast

from aea.mail.base import EnvelopeContext
from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.connections.http_client.connection import PUBLIC_ID
from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.skills.fetch_beacon.dialogues import HttpDialogues


DEFAULT_URL = ""
DEFAULT_PUBLISH_INTERVAL = 3600


class FetchBeaconBehaviour(TickerBehaviour):
    """This class provides a simple beacon fetch behaviour."""

    def __init__(self, **kwargs):
        """Initialize the beacon fetch behaviour."""

        super().__init__(**kwargs)
        self.beacon_url = kwargs.pop("beacon_url", DEFAULT_URL)

    def send_http_request_message(
        self, method: str, url: str, content: Optional[Dict] = None
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

        counterparty_address = str(PUBLIC_ID)

        # http request message
        request_http_message, _ = http_dialogues.create(
            counterparty=counterparty_address,
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
        self.context.logger.info("setting up FetchBeaconBehaviour")

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """

        self.send_http_request_message("GET", self.beacon_url)
        self.context.logger.info(
            "Fetching random beacon from {}...".format(self.beacon_url)
        )

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        self.context.logger.info("tearing down FetchBeaconBehaviour")
