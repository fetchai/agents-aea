# HTTP server connection

This connection wraps an HTTP server. It consumes requests from clients, translates them into messages for the AEA, waits for a response message from the AEA, then serves the response to the client.

## Usage

First, add the connection to your AEA project (`aea add connection fetchai/http_server:0.22.0`). Then, update the `config` in `connection.yaml` by providing a `host` and `port` of the server. Optionally, provide a path to an [OpenAPI specification](https://swagger.io/docs/specification/about/) for request validation.