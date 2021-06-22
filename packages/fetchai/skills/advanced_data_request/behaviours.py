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

"""This package contains a behaviour for fetching data from an API."""

import json
from typing import Any, Dict, cast

from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.connections.http_client.connection import (
    PUBLIC_ID as HTTP_CLIENT_ID,
)
from packages.fetchai.connections.prometheus.connection import (
    PUBLIC_ID as PROM_CONNECTION_ID,
)
from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.prometheus.message import PrometheusMessage
from packages.fetchai.skills.advanced_data_request.dialogues import (
    HttpDialogues,
    PrometheusDialogues,
)
from packages.fetchai.skills.advanced_data_request.models import (
    AdvancedDataRequestModel,
)


class AdvancedDataRequestBehaviour(TickerBehaviour):
    """This class provides a simple behaviour to fetch data."""

    def __init__(self, **kwargs: Any):
        """Initialize the advanced data request behaviour."""

        super().__init__(**kwargs)

    def send_http_request_message(self) -> None:
        """Send an http request message."""

        # context
        http_dialogues = cast(HttpDialogues, self.context.http_dialogues)
        model = cast(AdvancedDataRequestModel, self.context.advanced_data_request_model)
        content = model.body

        # http request message
        request_http_message, _ = http_dialogues.create(
            counterparty=str(HTTP_CLIENT_ID),
            performative=HttpMessage.Performative.REQUEST,
            method=model.method,
            url=model.url,
            headers="",
            version="",
            body=b"" if content is None else json.dumps(content).encode("utf-8"),
        )

        # send message
        self.context.outbox.put_message(message=request_http_message)

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
        :param metric_type: the type of the metric.
        :param description: a description of the metric.
        :param labels: the metric labels.
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
        self.context.outbox.put_message(message=message)

    def update_prometheus_metric(
        self, metric_name: str, update_func: str, value: float, labels: Dict[str, str],
    ) -> None:
        """
        Update a prometheus metric.

        :param metric_name: the name of the metric.
        :param update_func: the name of the update function (e.g. inc, dec, set, ...).
        :param value: the value to provide to the update function.
        :param labels: the metric labels.
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
        self.context.outbox.put_message(message=message)

    def setup(self) -> None:
        """Implement the setup."""
        self.context.logger.info("setting up AdvancedDataRequestBehaviour")

        prom_dialogues = cast(PrometheusDialogues, self.context.prometheus_dialogues)

        if prom_dialogues.enabled:
            for metric in prom_dialogues.metrics:
                metric_name = metric["name"]
                self.context.logger.info("Adding Prometheus metric: " + metric_name)
                self.add_prometheus_metric(
                    metric_name,
                    metric["type"],
                    metric["description"],
                    dict(metric["labels"]),
                )

    def act(self) -> None:
        """Implement the act."""
        model = cast(AdvancedDataRequestModel, self.context.advanced_data_request_model)
        self.context.logger.info(f"Fetching data from {model.url}")
        self.send_http_request_message()

    def teardown(self) -> None:
        """Implement the task teardown."""
        self.context.logger.info("tearing down AdvancedDataRequestBehaviour")
