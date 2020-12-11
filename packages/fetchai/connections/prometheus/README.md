# Prometheus connection
The prometheus connection allows agents to create and update prometheus metrics.

## Usage

First, add the connection to your AEA project (`aea add connection fetchai/prometheus:0.1.0`). The default port (`8080`) to expose metrics can be changed by updating the `config` in `connection.yaml`. Then, add the protocol (`aea add protocol fetchai/prometheus:0.1.0`) to your project. 

It may be convenient to add a model `prometheus_dialogues` to your skill, to handle the metrics configuration and messages to the prometheus connection.

Add a metric `METRIC_NAME` of type `METRIC_TYPE` {`Gauge`, `Counter`, ...} and description `METRIC_DESCRIPTION` by sending a message with performative `ADD_METRIC` to the prometheus connection:
```python
message, _ = prometheus_dialogues.create(
    counterparty=str(PROM_CONNECTION_ID),
    performative=PrometheusMessage.Performative.ADD_METRIC,
    type=METRIC_TYPE,
    title=METRIC_NAME,
    description=METRIC_DESCRIPTION,
    labels=(),
)
```
where `PROM_CONNECTION_ID` should be imported to your skill as follows:
```python
from packages.fetchai.connections.prometheus.connection import (
    PUBLIC_ID as PROM_CONNECTION_ID,
)
```

Update metric `METRIC_NAME` with update function `UPDATE_FUNCTION` {`inc`, `set`, `observe`, ...} and value `VALUE` by sending a message with performative `UPDATE_METRIC` to the prometheus connection:
```python
message, _ = prometheus_dialogues.create(
    counterparty=str(PROM_CONNECTION_ID),
    performative=PrometheusMessage.Performative.UPDATE_METRIC,
    title=METRIC_NAME,
    callable=UPDATE_FUNCTION,
    value=VALUE,
)
```




