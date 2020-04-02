## Description

The HTTP server connection allows you to run a server inside a connection which accepts requests from clients. The HTTP server connection validates requests it receives against the provided OpenAPI file. It translates each valid request into an envelope, sends the envelope to the agent and if it receives, within a timeout window, a valid response envelope, serves the response to the client.

## Steps

Create a new AEA:

``` bash
aea create my_aea
```

Add the http server connection package

``` bash
aea add connection fetchai/http_server:0.1.0
```

Modify the `api_spec_path`:

``` bash
aea config set vendor.fetchai.connections.http_server.config.api_spec_path "examples/http_ex/petstore.yaml"
```

Install the dependencies:

``` bash
aea install
```

Write and add your skill:

``` bash
aea scaffold skill http_echo
```

We leave it to you to implement a simple http echo skill (modelled after the standard echo skill) which prints out the content of received envelopes.
