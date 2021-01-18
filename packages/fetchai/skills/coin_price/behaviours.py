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

from packages.fetchai.connections.http_client.connection import (
    PUBLIC_ID as HTTP_CLIENT_ID,
)
from packages.fetchai.connections.prometheus.connection import (
    PUBLIC_ID as PROM_CONNECTION_ID,
)
from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.prometheus.message import PrometheusMessage
from packages.fetchai.skills.coin_price.dialogues import (
    HttpDialogues,
    PrometheusDialogues,
)
from packages.fetchai.skills.coin_price.models import CoinPriceModel


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
            counterparty=str(HTTP_CLIENT_ID),
            performative=HttpMessage.Performative.REQUEST,
            method=method,
            url=url,
            headers="",
            version="",
            body=b"" if content is None else json.dumps(content).encode("utf-8"),
        )

        # send message
        envelope_context = EnvelopeContext(
            skill_id=self.context.skill_id, connection_id=HTTP_CLIENT_ID
        )
        self.context.outbox.put_message(
            message=request_http_message, context=envelope_context
        )

    def add_prometheus_metric(
        self,
        metric_name: str,
        metric_type: str,
        description: str,
        labels: Dict[str, str],
    ) -> None:
        """
        Add a prometheus metric.

        :param metric_name: the name of the metric to add.
        :param type: the type of the metric.
        :param description: a description of the metric.
        :param labels: the metric labels.
        :return: None
        """

        # context
        prom_dialogues = cast(PrometheusDialogues, self.context.prometheus_dialogues)

        # prometheus update message
        message, _ = prom_dialogues.create(
            counterparty=str(PROM_CONNECTION_ID),
            performative=PrometheusMessage.Performative.ADD_METRIC,
            type=metric_type,
            title=metric_name,
            description=description,
            labels=labels,
        )

        # send message
        envelope_context = EnvelopeContext(
            skill_id=self.context.skill_id, connection_id=PROM_CONNECTION_ID
        )
        self.context.outbox.put_message(message=message, context=envelope_context)

    def update_prometheus_metric(
        self, metric_name: str, update_func: str, value: float, labels: Dict[str, str],
    ) -> None:
        """
        Update a prometheus metric.

        :param metric_name: the name of the metric.
        :param update_func: the name of the update function (e.g. inc, dec, set, ...).
        :param value: the value to provide to the update function.
        :param labels: the metric labels.
        :return: None
        """

        # context
        prom_dialogues = cast(PrometheusDialogues, self.context.prometheus_dialogues)

        # prometheus update message
        message, _ = prom_dialogues.create(
            counterparty=str(PROM_CONNECTION_ID),
            performative=PrometheusMessage.Performative.UPDATE_METRIC,
            title=metric_name,
            callable=update_func,
            value=value,
            labels=labels,
        )

        # send message
        envelope_context = EnvelopeContext(
            skill_id=self.context.skill_id, connection_id=PROM_CONNECTION_ID
        )
        self.context.outbox.put_message(message=message, context=envelope_context)

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        self.context.logger.info("setting up CoinPriceBehaviour")

        prom_dialogues = cast(PrometheusDialogues, self.context.prometheus_dialogues)

        if prom_dialogues.enabled:
            for metric in prom_dialogues.metrics:
                self.context.logger.info("Adding Prometheus metric: " + metric["name"])
                self.add_prometheus_metric(
                    metric["name"],
                    metric["type"],
                    metric["description"],
                    dict(metric["labels"]),
                )

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        model = cast(CoinPriceModel, self.context.coin_price_model)

        self.context.logger.info(
            f"Fetching price of {model.coin_id} in {model.currency} from {model.url}"
        )

        url = f"{model.url}simple/price?ids={model.coin_id}&vs_currencies={model.currency}"

        self.send_http_request_message("GET", url)

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        self.context.logger.info("tearing down CoinPriceBehaviour")
