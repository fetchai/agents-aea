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

"""This package contains the behaviour of a generic seller AEA."""

import json
from typing import Any, Dict, Optional, cast

from aea.helpers.search.models import Description
from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.connections.http_client.connection import (
    PUBLIC_ID as HTTP_CLIENT_PUBLIC_ID,
)
from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.aries_alice.dialogues import (
    HttpDialogues,
    OefSearchDialogues,
)
from packages.fetchai.skills.aries_alice.strategy import Strategy


DEFAULT_MAX_SOEF_REGISTRATION_RETRIES = 5
DEFAULT_SERVICES_INTERVAL = 60.0


class AliceBehaviour(TickerBehaviour):
    """This class implements a behaviour."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialise the behaviour."""

        services_interval = kwargs.pop(
            "services_interval", DEFAULT_SERVICES_INTERVAL
        )  # type: int
        self._max_soef_registration_retries = kwargs.pop(
            "max_soef_registration_retries", DEFAULT_MAX_SOEF_REGISTRATION_RETRIES
        )  # type: int
        super().__init__(tick_interval=services_interval, **kwargs)
        self.failed_registration_msg = None  # type: Optional[OefSearchMessage]
        self._nb_retries = 0

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
        """
        Implement the setup.

        :return: None
        """
        self.context.logger.info("My address is: " + self.context.agent_address)
        self._register_agent()

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        self._retry_failed_registration()

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        self._unregister_service()
        self._unregister_agent()

    def _retry_failed_registration(self) -> None:
        """
        Retry a failed registration.

        :return: None
        """
        if self.failed_registration_msg is not None:
            self._nb_retries += 1
            if self._nb_retries > self._max_soef_registration_retries:
                self.context.is_active = False
                return

            oef_search_dialogues = cast(
                OefSearchDialogues, self.context.oef_search_dialogues
            )
            oef_search_msg, _ = oef_search_dialogues.create(
                counterparty=self.failed_registration_msg.to,
                performative=self.failed_registration_msg.performative,
                service_description=self.failed_registration_msg.service_description,
            )
            self.context.outbox.put_message(message=oef_search_msg)
            self.context.logger.info(
                f"Retrying registration on SOEF. Retry {self._nb_retries} out of {self._max_soef_registration_retries}."
            )

            self.failed_registration_msg = None

    def _register(self, description: Description, logger_msg: str) -> None:
        """
        Register something on the SOEF.

        :param description: the description of what is being registered
        :param logger_msg: the logger message to print after the registration

        :return: None
        """
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_msg, _ = oef_search_dialogues.create(
            counterparty=self.context.search_service_address,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            service_description=description,
        )
        self.context.outbox.put_message(message=oef_search_msg)
        self.context.logger.info(logger_msg)

    def _register_agent(self) -> None:
        """
        Register the agent's location.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        description = strategy.get_location_description()
        self._register(description, "registering agent on SOEF.")

    def register_service(self) -> None:
        """
        Register the agent's service.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        description = strategy.get_register_service_description()
        self._register(description, "registering agent's service on the SOEF.")

    def register_genus(self) -> None:
        """
        Register the agent's personality genus.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        description = strategy.get_register_personality_description()
        self._register(
            description, "registering agent's personality genus on the SOEF."
        )

    def register_classification(self) -> None:
        """
        Register the agent's personality classification.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        description = strategy.get_register_classification_description()
        self._register(
            description, "registering agent's personality classification on the SOEF."
        )

    def _unregister_service(self) -> None:
        """
        Unregister service from the SOEF.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        description = strategy.get_unregister_service_description()
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_msg, _ = oef_search_dialogues.create(
            counterparty=self.context.search_service_address,
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            service_description=description,
        )
        self.context.outbox.put_message(message=oef_search_msg)
        self.context.logger.info("unregistering service from SOEF.")

    def _unregister_agent(self) -> None:
        """
        Unregister agent from the SOEF.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        description = strategy.get_location_description()
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_msg, _ = oef_search_dialogues.create(
            counterparty=self.context.search_service_address,
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            service_description=description,
        )
        self.context.outbox.put_message(message=oef_search_msg)
        self.context.logger.info("unregistering agent from SOEF.")
