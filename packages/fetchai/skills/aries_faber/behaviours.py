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
from typing import Dict, cast

from aea.mail.base import Address
from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.aries_faber.dialogues import OefSearchDialogues
from packages.fetchai.skills.aries_faber.strategy import FaberStrategy

DEFAULT_ADMIN_HOST = "127.0.0.1"
DEFAULT_ADMIN_PORT = 8021

DEFAULT_SEARCH_INTERVAL = 5.0


class FaberBehaviour(TickerBehaviour):
    """This class represents the behaviour of faber."""

    def __init__(self, **kwargs):
        """Initialize the handler."""
        self._admin_host = kwargs.pop("admin_host", DEFAULT_ADMIN_HOST)
        self._admin_port = kwargs.pop("admin_port", DEFAULT_ADMIN_PORT)
        self._admin_url = "http://{}:{}".format(self.admin_host, self.admin_port)
        self._alice_address = ""

        search_interval = cast(
            float, kwargs.pop("search_interval", DEFAULT_SEARCH_INTERVAL)
        )
        super().__init__(tick_interval=search_interval, **kwargs)

    @property
    def admin_host(self) -> str:
        return self._admin_host

    @property
    def admin_port(self) -> str:
        return self._admin_port

    @property
    def admin_url(self) -> str:
        return self._admin_url

    @property
    def alice_address(self) -> Address:
        return self._alice_address

    @alice_address.setter
    def alice_address(self, address: Address) -> None:
        self._alice_address = address

    def admin_get(self, path: str, content: Dict = None) -> None:
        """
        Get from admin.

        :param path: the path
        :param content: the payload
        :return: None
        """
        # Request message & envelope
        request_http_message = HttpMessage(
            performative=HttpMessage.Performative.REQUEST,
            method="GET",
            url=self.admin_url + path,
            headers="",
            version="",
            bodyy=b"" if content is None else json.dumps(content).encode("utf-8"),
        )
        request_http_message.counterparty = self.admin_url
        self.context.outbox.put_message(message=request_http_message)

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        strategy = cast(FaberStrategy, self.context.strategy)
        strategy.is_searching = True

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        strategy = cast(FaberStrategy, self.context.strategy)
        if strategy.is_searching:
            query = strategy.get_location_and_service_query()
            oef_search_dialogues = cast(
                OefSearchDialogues, self.context.oef_search_dialogues
            )
            oef_search_msg = OefSearchMessage(
                performative=OefSearchMessage.Performative.SEARCH_SERVICES,
                dialogue_reference=oef_search_dialogues.new_self_initiated_dialogue_reference(),
                query=query,
            )
            oef_search_msg.counterparty = self.context.search_service_address
            oef_search_dialogues.update(oef_search_msg)
            self.context.outbox.put_message(message=oef_search_msg)
            self.context.logger.info("Searching for Alice on SOEF...")

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        pass
