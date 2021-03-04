## Description

The HTTP server connection allows you to run a server inside a connection which accepts requests from clients. The HTTP server connection validates requests it receives against a provided OpenAPI file. It translates each valid request into an envelope and sends it to the agent. If it receives a valid response envelope from the agent within a timeout window, the connection translates the response envelope into an HTTP response and serves it to the client.

## Steps

Create a new AEA:

``` bash
aea create my_aea
cd my_aea
```

Add the http server connection package:

``` bash
aea add connection fetchai/http_server:0.17.0
```

Update the default connection:

``` bash
aea config set agent.default_connection fetchai/http_server:0.17.0
```

Modify the `api_spec_path`:

``` bash
aea config set vendor.fetchai.connections.http_server.config.api_spec_path "../examples/http_ex/petstore.yaml"
```

Ensure the file exists under the specified path!

Install the dependencies:

``` bash
aea install
```

Write and add your skill:

``` bash
aea scaffold skill http_echo
```

You can implement a simple http echo skill (modelled after the standard echo skill) which prints out the content of received messages and responds with success.


First, delete the `my_model.py` and `behaviour.py` files (in `my_aea/skills/http_echo/`). The server will be purely reactive, so you only need the `handlers.py` file. Update `skill.yaml` accordingly, so set `models: {}` and `behaviours: {}`.

Next implement a basic handler which prints the received envelopes and responds:

``` python
import json
from typing import cast

from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.protocols.http.message import HttpMessage


class HttpHandler(Handler):
    """This implements the echo handler."""

    SUPPORTED_PROTOCOL = HttpMessage.protocol_id

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to an envelope.

        :param message: the message
        :return: None
        """
        http_msg = cast(HttpMessage, message)
        if http_msg.performative == HttpMessage.Performative.REQUEST:
            self.context.logger.info(
                "received http request with method={}, url={} and body={}".format(
                    http_msg.method,
                    http_msg.url,
                    http_msg.bodyy,
                )
            )
            if http_msg.method == "get":
                self._handle_get(http_msg)
            elif http_msg.method == "post":
                self._handle_post(http_msg)
        else:
            self.context.logger.info(
                "received response ({}) unexpectedly!".format(http_msg)
            )

    def _handle_get(self, http_msg: HttpMessage) -> None:
        """
        Handle a Http request of verb GET.

        :param http_msg: the http message
        :return: None
        """
        http_response = HttpMessage(
            dialogue_reference=http_msg.dialogue_reference,
            target=http_msg.message_id,
            message_id=http_msg.message_id + 1,
            performative=HttpMessage.Performative.RESPONSE,
            version=http_msg.version,
            status_code=200,
            status_text="Success",
            headers=http_msg.headers,
            bodyy=json.dumps({"tom": {"type": "cat", "age": 10}}).encode("utf-8"),
        )
        self.context.logger.info(
            "responding with: {}".format(http_response)
        )
        http_response.counterparty = http_msg.counterparty
        self.context.outbox.put_message(message=http_response)

    def _handle_post(self, http_msg: HttpMessage) -> None:
        """
        Handle a Http request of verb POST.

        :param http_msg: the http message
        :return: None
        """
        http_response = HttpMessage(
            dialogue_reference=http_msg.dialogue_reference,
            target=http_msg.message_id,
            message_id=http_msg.message_id + 1,
            performative=HttpMessage.Performative.RESPONSE,
            version=http_msg.version,
            status_code=200,
            status_text="Success",
            headers=http_msg.headers,
            bodyy=b"",
        )
        self.context.logger.info(
            "responding with: {}".format(http_response)
        )
        http_response.counterparty = http_msg.counterparty
        self.context.outbox.put_message(message=http_response)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass
```

And update the `skill.yaml` accordingly:

``` yaml
handlers:
  http_handler:
    args: {}
    class_name: HttpHandler
```

Finally, run the fingerprinter (note, you will have to replace the author name with your author handle):
``` bash
aea fingerprint skill fetchai/http_echo:0.15.0
```

You can now run the AEA:
``` bash
aea run
```

In a separate terminal, you can create a client and communicate with the server:
``` python
import requests

response = requests.get('http://127.0.0.1:8000')
response.status_code
# >>> 404
# we receive a not found since the path is not available in the api spec

response = requests.get('http://127.0.0.1:8000/pets')
response.status_code
# >>> 200
response.content
# >>> b'{"tom": {"type": "cat", "age": 10}}'

response = requests.post('http://127.0.0.1:8000/pets')
response.status_code
# >>> 200
response.content
# >>> b''
```