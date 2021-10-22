The AEA framework supports flexible logging capabilities with the standard <a href="https://docs.python.org/3/library/logging.html" target="_blank">Python logging library</a>.

In this tutorial, we configure logging for an AEA.

First of all, create your AEA.


``` bash
aea create my_aea
cd my_aea
```

The `aea-config.yaml` file should look like this.

``` yaml
agent_name: my_aea
author: fetchai
version: 0.1.0
description: ''
license: Apache-2.0
aea_version: 0.6.0
fingerprint: {}
fingerprint_ignore_patterns: []
connections:
- fetchai/stub:0.21.0
contracts: []
protocols:
- fetchai/default:1.0.0
skills:
- fetchai/error:0.17.0
default_connection: fetchai/stub:0.21.0
default_ledger: fetchai
required_ledgers:
- fetchai
logging_config:
  disable_existing_loggers: false
  version: 1
private_key_paths: {}
```

By updating the `logging_config` section, you can configure the loggers of your application.

The format of this section is specified in the <a href="https://docs.python.org/3/library/logging.config.html" target="_blank">`logging.config`</a> module.

At <a href="https://docs.python.org/3/library/logging.config.html#configuration-dictionary-schema" target="_blank">this section</a>
you'll find the definition of the configuration dictionary schema.

Below is an example of the `logging_config` value.

``` yaml
logging_config:
  version: 1
  disable_existing_loggers: False
  formatters:
    standard:
      format: '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
  handlers:
    logfile:
      class: logging.FileHandler
      formatter: standard
      level: DEBUG
      filename: logconfig.log
    console:
      class: logging.StreamHandler
      formatter: standard
      level: DEBUG
  loggers:
    aea:
      handlers:
      - logfile
      - console
      level: DEBUG
      propagate: False
```

This configuration will set up a logger with name `aea`. It prints both on console and on file with a format specified by the `standard` formatter.


## Streaming to browser

It is possible to configure the AEA to stream logs to a browser.

First, add the following configuration to your AEA:

``` yaml
logging_config:
  version: 1
  disable_existing_loggers: false
  formatters:
    standard:
      format: '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
  handlers:
    http:
      class: logging.handlers.HTTPHandler
      formatter: standard
      level: INFO
      host: localhost:5000
      url: /stream
      method: POST
  loggers:
    aea:
      handlers:
      - http
      level: INFO
      propagate: false
```

Second, create a log server:

``` python
# -*- coding: utf-8 -*-
"""A simple flask server to serve logs."""

import datetime
import itertools
import queue

from flask import Flask, Response, request, stream_with_context


def format_log(log_dict):
    """Format a log record."""
    date = datetime.datetime.fromtimestamp(float(log_dict["created"]))
    formatted_log = f"[{date.isoformat()}] [{log_dict['levelname']}] {log_dict['name']}: {log_dict['msg']}"
    return formatted_log


def create_app():
    """Create Flask app for streaming logs."""
    all_logs = []
    unread_logs = queue.Queue()
    app = Flask(__name__)

    @app.route("/")
    def index():
        """Stream logs to client."""
        def generate():
            # stream old logs
            div = "<div>{}</div>"
            for old_row in all_logs:
                yield div.format(old_row)

            # stream unread logs
            while True:
                row = unread_logs.get()
                all_logs.append(row)
                yield f"<div>{row}</div>"

        rows = generate()
        title = "<p>Waiting for logs...</p>"
        return Response(stream_with_context(itertools.chain([title], rows)))

    @app.route("/stream", methods=["POST"])
    def stream():
        """Save log record from AEA."""
        log_record_formatted = format_log(dict(request.form))
        unread_logs.put(log_record_formatted)
        return {}, 200

    app.run()


if __name__ == "__main__":
    create_app()
```

Save the script in a file called `server.py`, install flask with `pip install flask` and run the server with `python server.py`.

Third, run your AEA and visit `localhost:5000` in your browser.

<br />
