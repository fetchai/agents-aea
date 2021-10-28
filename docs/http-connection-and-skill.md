## Description

The HTTP client and HTTP server connections enable an AEA to communicate with external servers, respectively clients, via HTTP. 

The HTTP client connection receives request envelops from an agent's skill, translates each into an HTTP request and sends it to a server external to the agent. If it receives an HTTP response from the server within a timeout window, it translates it into a response envelope, and sends this back to the relevant skill inside the agent.

The HTTP server connection allows you to run a server inside the connection itself which accepts requests from clients external to the agent. The HTTP server connection validates requests it receives against a provided OpenAPI file. It translates each valid request into an envelope and sends it to the skill specified in the connections configuration. If it receives a valid response envelope from the skill within a timeout window, the connection translates the response envelope into an HTTP response and serves it to the client.

## HTTP Client

The `fetchai/simple_data_request:0.13.0` skill demonstrates a simple use case of the HTTP Client connection.

The `HttpRequestBehaviour` in `behaviours.py` periodically sends HTTP envelops to the HTTP client connection. Its `act()` method, periodically called, simply calls `_generate_http_request` which contains the logic for enqueueing an HTTP request envelop.

The `HttpHandler` in `handler.py` is a basic handler for dealing with HTTP response envelops received from the HTTP client connection. In the `handle()` method, the responses are dealt with by the private `_handle_response` method which essentially logs the response and adds the body of the response into the skill's shared state. 

## HTTP Server

Create a new AEA:

``` bash
aea create my_aea
cd my_aea
```

Add the http server connection package:

``` bash
aea add connection fetchai/http_server:0.22.0
```

Update the default connection:

``` bash
aea config set agent.default_connection fetchai/http_server:0.22.0
```

Modify the `api_spec_path`:

``` bash
aea config set vendor.fetchai.connections.http_server.config.api_spec_path "../examples/http_ex/petstore.yaml"
```

Ensure the file exists under the specified path!

Create and add a private key:

``` bash
aea generate-key fetchai
aea add-key fetchai
```

Install the dependencies:

``` bash
aea install
```

Write and add your skill:

``` bash
aea scaffold skill http_echo
```

You can implement a simple http echo skill (modelled after the standard echo skill) which prints out the content of received messages and responds with success.


First, delete the `my_model.py` and `behaviour.py` files (in `my_aea/skills/http_echo/`). The server will be purely reactive, so you only need the `handlers.py` file, and the `dialogues.py` to record the state of the dialogues. Update `skill.yaml` accordingly, so set `models: {}` and `behaviours: {}`.

Next implement a basic handler which prints the received envelopes and responds.


Then, replace the content of `handlers.py` with the following code snippet,
after having replaced the placeholder `YOUR_USERNAME` with 
the author username (i.e. the output of `aea config get agent.author`):

``` python
import json
from typing import cast

from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.protocols.default import DefaultMessage
from packages.fetchai.protocols.http.message import HttpMessage
from packages.YOUR_USERNAME.skills.http_echo.dialogues import (
    DefaultDialogues,
    HttpDialogue,
    HttpDialogues,
)


class HttpHandler(Handler):
    """This implements the echo handler."""

    SUPPORTED_PROTOCOL = HttpMessage.protocol_id

    def setup(self) -> None:
        """Implement the setup."""

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to an envelope.

        :param message: the message
        """
        http_msg = cast(HttpMessage, message)

        # recover dialogue
        http_dialogues = cast(HttpDialogues, self.context.http_dialogues)
        http_dialogue = cast(HttpDialogue, http_dialogues.update(http_msg))
        if http_dialogue is None:
            self._handle_unidentified_dialogue(http_msg)
            return

        # handle message
        if http_msg.performative == HttpMessage.Performative.REQUEST:
            self._handle_request(http_msg, http_dialogue)
        else:
            self._handle_invalid(http_msg, http_dialogue)

    def _handle_unidentified_dialogue(self, http_msg: HttpMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param http_msg: the message
        """
        self.context.logger.info(
            "received invalid http message={}, unidentified dialogue.".format(http_msg)
        )
        default_dialogues = cast(DefaultDialogues, self.context.default_dialogues)
        default_msg, _ = default_dialogues.create(
            counterparty=http_msg.sender,
            performative=DefaultMessage.Performative.ERROR,
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
            error_msg="Invalid dialogue.",
            error_data={"http_message": http_msg.encode()},
        )
        self.context.outbox.put_message(message=default_msg)

    def _handle_request(
        self, http_msg: HttpMessage, http_dialogue: HttpDialogue
    ) -> None:
        """
        Handle a Http request.

        :param http_msg: the http message
        :param http_dialogue: the http dialogue
        """
        self.context.logger.info(
            "received http request with method={}, url={} and body={!r}".format(
                http_msg.method, http_msg.url, http_msg.body,
            )
        )
        if http_msg.method == "get":
            self._handle_get(http_msg, http_dialogue)
        elif http_msg.method == "post":
            self._handle_post(http_msg, http_dialogue)

    def _handle_get(self, http_msg: HttpMessage, http_dialogue: HttpDialogue) -> None:
        """
        Handle a Http request of verb GET.

        :param http_msg: the http message
        :param http_dialogue: the http dialogue
        """
        http_response = http_dialogue.reply(
            performative=HttpMessage.Performative.RESPONSE,
            target_message=http_msg,
            version=http_msg.version,
            status_code=200,
            status_text="Success",
            headers=http_msg.headers,
            body=json.dumps({"tom": {"type": "cat", "age": 10}}).encode("utf-8"),
        )
        self.context.logger.info("responding with: {}".format(http_response))
        self.context.outbox.put_message(message=http_response)

    def _handle_post(self, http_msg: HttpMessage, http_dialogue: HttpDialogue) -> None:
        """
        Handle a Http request of verb POST.

        :param http_msg: the http message
        :param http_dialogue: the http dialogue
        """
        http_response = http_dialogue.reply(
            performative=HttpMessage.Performative.RESPONSE,
            target_message=http_msg,
            version=http_msg.version,
            status_code=200,
            status_text="Success",
            headers=http_msg.headers,
            body=http_msg.body,
        )
        self.context.logger.info("responding with: {}".format(http_response))
        self.context.outbox.put_message(message=http_response)

    def _handle_invalid(
        self, http_msg: HttpMessage, http_dialogue: HttpDialogue
    ) -> None:
        """
        Handle an invalid http message.

        :param http_msg: the http message
        :param http_dialogue: the http dialogue
        """
        self.context.logger.warning(
            "cannot handle http message of performative={} in dialogue={}.".format(
                http_msg.performative, http_dialogue
            )
        )

    def teardown(self) -> None:
        """Implement the handler teardown."""
```

Moreover, add a `dialogues.py` file with the following code:
``` python
from typing import Any

from aea.protocols.base import Address, Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.skills.base import Model

from packages.fetchai.protocols.default.dialogues import (
    DefaultDialogue as BaseDefaultDialogue,
)
from packages.fetchai.protocols.default.dialogues import (
    DefaultDialogues as BaseDefaultDialogues,
)
from packages.fetchai.protocols.http.dialogues import HttpDialogue as BaseHttpDialogue
from packages.fetchai.protocols.http.dialogues import HttpDialogues as BaseHttpDialogues


DefaultDialogue = BaseDefaultDialogue


class DefaultDialogues(Model, BaseDefaultDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize dialogues.

        :param kwargs: keyword arguments
        """
        Model.__init__(self, **kwargs)

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return DefaultDialogue.Role.AGENT

        BaseDefaultDialogues.__init__(
            self,
            self_address=self.context.agent_address,
            role_from_first_message=role_from_first_message,
        )


HttpDialogue = BaseHttpDialogue


class HttpDialogues(Model, BaseHttpDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize dialogues.

        :param kwargs: keyword arguments
        """
        Model.__init__(self, **kwargs)

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return BaseHttpDialogue.Role.SERVER

        BaseHttpDialogues.__init__(
            self,
            self_address=str(self.skill_id),
            role_from_first_message=role_from_first_message,
        )
```

Then, update the `skill.yaml` accordingly:

``` yaml
handlers:
  http_handler:
    args: {}
    class_name: HttpHandler
models:
  default_dialogues:
    args: {}
    class_name: DefaultDialogues
  http_dialogues:
    args: {}
    class_name: HttpDialogues
```


Run the fingerprinter (note, you will have to replace the author name with your author handle):
``` bash
aea fingerprint skill fetchai/http_echo:0.20.0
```


Moreover, we need to tell to the `http_server` connection to what skill
the HTTP requests should be forwarded.
In our case, this is the `http_echo` that you have just scaffolded.
Its public id will be `<your-author-name>/http_echo:0.1.0`.

``` bash
aea config set vendor.fetchai.connections.http_server.config.target_skill_id "$(aea config get agent.author)/http_echo:0.1.0" 
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
