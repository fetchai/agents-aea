# HTTP client connection

This connection wraps an HTTP client. It consumes messages from the AEA, translates them into HTTP requests, then sends the HTTP response as a message back to the AEA.

## Usage

First, add the connection to your AEA project (`aea add connection fetchai/http_client:0.23.0`). Then, update the `config` in `connection.yaml` by providing a `host` and `port` of the server.
