# Webhook connection

An HTTP webhook connection which registers a webhook and waits for incoming requests. It generates messages based on webhook requests received and forwards them to the agent.

## Usage

First, add the connection to your AEA project: `aea add connection fetchai/webhook:0.19.0`. Then ensure the `config` in `connection.yaml` matches your need. In particular, set `webhook_address`, `webhook_port` and `webhook_url_path` appropriately.
