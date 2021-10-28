AEAs can create and update prometheus metrics for remote monitoring by sending messages to the prometheus connection `fetchai/prometheus:0.8.0`.

To see this working in an agent, fetch and run the `coin_price_feed` agent and check `localhost:9090/metrics` to see the latest values of the metrics `num_retrievals` and `num_requests`:
``` bash
aea fetch fetchai/coin_price_feed:0.14.0
cd coin_price_feed
aea install
aea build
aea run
```
You can then instruct a prometheus server running on the same computing cluster as a deployed agent to scrape these metrics for remote monitoring and visualisation with the Prometheus/Grafana toolset.

To use this connection, add a model `prometheus_dialogues` to your skill to handle the metrics configuration and messages to the prometheus connection.

<details><summary>Click here for example</summary>


``` python
class PrometheusDialogues(Model, BasePrometheusDialogues):
    """The dialogues class keeps track of all prometheus dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """

        self.enabled = kwargs.pop("enabled", False)
        self.metrics = kwargs.pop("metrics", [])

        Model.__init__(self, **kwargs)

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return PrometheusDialogue.Role.AGENT

        BasePrometheusDialogues.__init__(
            self,
            self_address=str(self.skill_id),
            role_from_first_message=role_from_first_message,
        )
```
</details>

Then configure your metrics in the `skill.yaml` file. For example (from the `advanced_data_request` skill):
``` yaml
models:
  prometheus_dialogues:
    args:
      enabled: true
      metrics:
      - name: num_retrievals
        type: Gauge
        description: Number of price quotes retrieved
        labels: {}
      - name: num_requests
        type: Gauge
        description: Number of price quote requests served
        labels: {}
    class_name: PrometheusDialogues
```

Add a metric `metric_name` of type `metric_type` {`Gauge`, `Counter`, ...} and description `description` by sending a message with performative `ADD_METRIC` to the prometheus connection:
``` python
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
    self.context.outbox.put_message(message=message)
```
where `PROM_CONNECTION_ID` should be imported to your skill as follows:
``` python
from packages.fetchai.connections.prometheus.connection import (
    PUBLIC_ID as PROM_CONNECTION_ID,
)
```

Update metric `metric_name` with update function `update_func` {`inc`, `set`, `observe`, ...} and value `value` by sending a message with performative `UPDATE_METRIC` to the prometheus connection:
``` python
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
    self.context.outbox.put_message(message=message)
```

Initialize the metrics from the configuration file in the behaviour setup:
``` python
def setup(self) -> None:
    """Implement the setup of the behaviour"""
    prom_dialogues = cast(PrometheusDialogues, self.context.prometheus_dialogues)

    if prom_dialogues.enabled:
        for metric in prom_dialogues.metrics:
            self.context.logger.info("Adding Prometheus metric: " + metric["name"])
            self.add_prometheus_metric(
                metric["name"], metric["type"], metric["description"], dict(metric["labels"]),
```

Then call the `update_prometheus_metric` function from the appropriate places.
For example, the following code in `handlers.py` for the `advanced_data_request` skill updates the number of http requests served:
``` python
if self.context.prometheus_dialogues.enabled:
    self.context.behaviours.advanced_data_request_behaviour.update_prometheus_metric(
        "num_requests", "inc", 1.0, {}
    )
```

Finally, you can add a `PrometheusHandler` to your skill to process response messages from the prometheus connection.

<details><summary>Click here for example</summary>


``` python
class PrometheusHandler(Handler):
    """This class handles responses from the prometheus server."""

    SUPPORTED_PROTOCOL = PrometheusMessage.protocol_id

    def __init__(self, **kwargs):
        """Initialize the handler."""
        super().__init__(**kwargs)

        self.handled_message = None

    def setup(self) -> None:
        """Set up the handler."""
        if self.context.prometheus_dialogues.enabled:
            self.context.logger.info("setting up PrometheusHandler")

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """

        message = cast(PrometheusMessage, message)

        # recover dialogue
        prometheus_dialogues = cast(
            PrometheusDialogues, self.context.prometheus_dialogues
        )
        prometheus_dialogue = cast(
            PrometheusDialogue, prometheus_dialogues.update(message)
        )
        if prometheus_dialogue is None:
            self._handle_unidentified_dialogue(message)
            return

        self.handled_message = message
        if message.performative == PrometheusMessage.Performative.RESPONSE:
            self.context.logger.debug(
                f"Prometheus response ({message.code}): {message.message}"
            )
        else:
            self.context.logger.debug(
                f"got unexpected prometheus message: Performative = {PrometheusMessage.Performative}"
            )

    def _handle_unidentified_dialogue(self, msg: Message) -> None:
        """
        Handle an unidentified dialogue.

        :param msg: the unidentified message to be handled
        :return: None
        """

        self.context.logger.info(
            "received invalid message={}, unidentified dialogue.".format(msg)
        )

    def teardown(self) -> None:
        """
        Teardown the handler.

        :return: None
        """
```
