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

"""This package contains a a behaviour to request data from a HTTP endpoint."""

import json
from typing import Any, cast

from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.connections.http_client.connection import (
    PUBLIC_ID as HTTP_CLIENT_PUBLIC_ID,
)
from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.skills.simple_data_request.dialogues import HttpDialogues


DEFAULT_REQUEST_INTERVAL = 20.0


class HttpRequestBehaviour(TickerBehaviour):
    """This class defines an http request behaviour."""

    def __init__(self, **kwargs: Any):
        """Initialise the behaviour."""
        request_interval = kwargs.pop(
            "request_interval", DEFAULT_REQUEST_INTERVAL
        )  # type: int
        self.url = kwargs.pop("url", None)
        self.method = kwargs.pop("method", None)
        self.body = kwargs.pop("body", None)
        self.lookup_termination_key = kwargs.pop("lookup_termination_key", None)
        if self.url is None or self.method is None or self.body is None:
            raise ValueError("Url, method and body must be provided.")
        super().__init__(tick_interval=request_interval, **kwargs)

    def setup(self) -> None:
        """Implement the setup."""

    def act(self) -> None:
        """Implement the act."""
        if self.lookup_termination_key is not None:
            prerequisite_satisfied = self.context.shared_state.get(
                self.lookup_termination_key, False
            )
            if not prerequisite_satisfied:
                return

        self._generate_http_request()

    def _generate_http_request(self) -> None:
        """Generate http request to provided url with provided body and method."""
        http_dialogues = cast(HttpDialogues, self.context.http_dialogues)
        request_http_message, _ = http_dialogues.create(
            counterparty=str(HTTP_CLIENT_PUBLIC_ID),
            performative=HttpMessage.Performative.REQUEST,
            method=self.method,
            url=self.url,
            headers="",
            version="",
            body=json.dumps(self.body).encode("utf-8"),
        )
        self.context.outbox.put_message(message=request_http_message)

    def teardown(self) -> None:
        """Implement the task teardown."""
