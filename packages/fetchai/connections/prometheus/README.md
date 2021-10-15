# Prometheus connection
AEAs can create and update prometheus metrics for remote monitoring by sending messages to the prometheus connection.

## Usage

First, add the connection to your AEA project (`aea add connection fetchai/prometheus:0.8.0`). Then, add the protocol (`aea add protocol fetchai/prometheus:1.0.0`) to your project. The default port (`9090`) to expose metrics can be changed to `PORT` by updating the `config` at the agent level (`aea config set --type=int vendor.fetchai.connections.prometheus.config.port PORT`).
