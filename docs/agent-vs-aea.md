AEAs are more than just agents.

<img src="../assets/aea-vs-agent-vs-multiplexer.svg" alt="AEA vs Agent vs Multiplexer" class="center" style="display: block; margin-left: auto; margin-right: auto;width:100%;">

In this guide we show some of the differences in terms of code.

The <a href="../build-aea-programmatically">Build an AEA programmatically</a> guide shows how to programmatically build an AEA. We can build an agent of the <a href="../api/agent#agent-objects">`Agent`</a> class programmatically as well.

First, use an empty agent to get the stub connection and default protocol.
```bash
mkdir packages  # packages folder will contain the local package repository
aea create my_aea  # create an agent
cd my_aea
aea add connection fetchai/stub:0.21.0:bafybeihijtaawc2adyewb3g7kta7hw6jyhyhoi7cotkzgqilves5zz7smm --remote  # get a connection from the remote registry
aea push connection fetchai/stub --local  # push to local registry
aea add protocol fetchai/default:1.0.0:bafybeiazamq4mogosgmr77ipita5s6sq6rfowubxf5rybfxikc772befxy --remote
aea push protocol fetchai/default --local
cd ..
aea delete my_aea  # delete the agent
```

Then, in your script, import the python and application specific libraries.
``` python
import os
import time
from threading import Thread
from typing import List

from aea.agent import Agent
from aea.configurations.base import ConnectionConfig
from aea.connections.base import Connection
from aea.helpers.file_io import write_with_lock
from aea.identity.base import Identity
from aea.mail.base import Envelope

from packages.fetchai.connections.stub.connection import StubConnection
from packages.fetchai.protocols.default.message import DefaultMessage
```

Unlike an `AEA`, an `Agent` does not require a `Wallet`, `LedgerApis` or `Resources` module.

However, we need to implement 4 abstract methods:
- `setup()`
- `act()`
- `handle_envelope()`
- `teardown()`


When we run an agent, `start()` calls `setup()` and then the main agent loop. The main agent loop calls `act()`, `react()` and `update()` on each tick. When the agent is stopped via `stop()` then `teardown()` is called.

Such a lightweight agent can be used to implement simple logic.

## Code an `Agent`

We define our `Agent` which simply receives envelopes, prints the sender address and `protocol_id` and returns it unopened.
``` python
INPUT_FILE = "input_file"
OUTPUT_FILE = "output_file"


class MyAgent(Agent):
    """A simple agent."""

    def __init__(self, identity: Identity, connections: List[Connection]):
        """Initialise the agent."""
        super().__init__(identity, connections)

    def setup(self):
        """Setup the agent."""

    def act(self):
        """Act implementation."""
        print("Act called for tick {}".format(self.tick))

    def handle_envelope(self, envelope: Envelope) -> None:
        """
        Handle envelope.

        :param envelope: the envelope received
        :return: None
        """
        print("React called for tick {}".format(self.tick))
        if (
            envelope is not None
            and envelope.protocol_specification_id
            == DefaultMessage.protocol_specification_id
        ):
            sender = envelope.sender
            receiver = envelope.to
            envelope.to = sender
            envelope.sender = receiver
            envelope.message = DefaultMessage.serializer.decode(envelope.message_bytes)
            envelope.message.sender = receiver
            envelope.message.to = sender
            print(
                "Received envelope from {} with protocol_specification_id={}".format(
                    sender, envelope.protocol_specification_id
                )
            )
            self.outbox.put(envelope)

    def teardown(self):
        """Teardown the agent."""
```

## Instantiate an `Agent`

``` python
    # Ensure the input and output files do not exist initially
    if os.path.isfile(INPUT_FILE):
        os.remove(INPUT_FILE)
    if os.path.isfile(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    # Create an addresses identity:
    identity = Identity(
        name="my_agent", address="some_address", public_key="public_key"
    )

    # Set up the stub connection
    configuration = ConnectionConfig(
        input_file_path=INPUT_FILE,
        output_file_path=OUTPUT_FILE,
        connection_id=StubConnection.connection_id,
    )
    stub_connection = StubConnection(
        configuration=configuration, data_dir=".", identity=identity
    )

    # Create our Agent
    my_agent = MyAgent(identity, [stub_connection])
```

## Start the agent
We run the agent from a different thread so that we can still use the main thread to pass it messages.
``` python
    # Set the agent running in a different thread
    try:
        t = Thread(target=my_agent.start)
        t.start()

        # Wait for everything to start up
        time.sleep(3)
```

## Send and receive an envelope
We use the input and output text files to send an envelope to our agent and receive a response
``` python
        # Create a message inside an envelope and get the stub connection to pass it into the agent
        message_text = b"my_agent,other_agent,fetchai/default:1.0.0,\x12\r\x08\x01*\t*\x07\n\x05hello,"

        with open(INPUT_FILE, "wb") as f:
            write_with_lock(f, message_text)

        # Wait for the envelope to get processed
        time.sleep(2)

        # Read the output envelope generated by the agent
        with open(OUTPUT_FILE, "rb") as f:
            print("output message: " + f.readline().decode("utf-8"))
```

## Shutdown
Finally stop our agent and wait for it to finish
``` python
    finally:
        # Shut down the agent
        my_agent.stop()
        t.join()
```

## Your turn

Now it is your turn to develop a simple agent with the `Agent` class.

## Entire code listing
If you just want to copy and paste the entire script in you can find it here:

<details><summary>Click here to see full listing</summary>
<p>

``` python
import os
import time
from threading import Thread
from typing import List

from aea.agent import Agent
from aea.configurations.base import ConnectionConfig
from aea.connections.base import Connection
from aea.helpers.file_io import write_with_lock
from aea.identity.base import Identity
from aea.mail.base import Envelope

from packages.fetchai.connections.stub.connection import StubConnection
from packages.fetchai.protocols.default.message import DefaultMessage


INPUT_FILE = "input_file"
OUTPUT_FILE = "output_file"


class MyAgent(Agent):
    """A simple agent."""

    def __init__(self, identity: Identity, connections: List[Connection]):
        """Initialise the agent."""
        super().__init__(identity, connections)

    def setup(self):
        """Setup the agent."""

    def act(self):
        """Act implementation."""
        print("Act called for tick {}".format(self.tick))

    def handle_envelope(self, envelope: Envelope) -> None:
        """
        Handle envelope.

        :param envelope: the envelope received
        :return: None
        """
        print("React called for tick {}".format(self.tick))
        if (
            envelope is not None
            and envelope.protocol_specification_id
            == DefaultMessage.protocol_specification_id
        ):
            sender = envelope.sender
            receiver = envelope.to
            envelope.to = sender
            envelope.sender = receiver
            envelope.message = DefaultMessage.serializer.decode(envelope.message_bytes)
            envelope.message.sender = receiver
            envelope.message.to = sender
            print(
                "Received envelope from {} with protocol_specification_id={}".format(
                    sender, envelope.protocol_specification_id
                )
            )
            self.outbox.put(envelope)

    def teardown(self):
        """Teardown the agent."""


def run():
    """Run demo."""

    # Ensure the input and output files do not exist initially
    if os.path.isfile(INPUT_FILE):
        os.remove(INPUT_FILE)
    if os.path.isfile(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    # Create an addresses identity:
    identity = Identity(
        name="my_agent", address="some_address", public_key="public_key"
    )

    # Set up the stub connection
    configuration = ConnectionConfig(
        input_file_path=INPUT_FILE,
        output_file_path=OUTPUT_FILE,
        connection_id=StubConnection.connection_id,
    )
    stub_connection = StubConnection(
        configuration=configuration, data_dir=".", identity=identity
    )

    # Create our Agent
    my_agent = MyAgent(identity, [stub_connection])

    # Set the agent running in a different thread
    try:
        t = Thread(target=my_agent.start)
        t.start()

        # Wait for everything to start up
        time.sleep(3)

        # Create a message inside an envelope and get the stub connection to pass it into the agent
        message_text = b"my_agent,other_agent,fetchai/default:1.0.0,\x12\r\x08\x01*\t*\x07\n\x05hello,"

        with open(INPUT_FILE, "wb") as f:
            write_with_lock(f, message_text)

        # Wait for the envelope to get processed
        time.sleep(2)

        # Read the output envelope generated by the agent
        with open(OUTPUT_FILE, "rb") as f:
            print("output message: " + f.readline().decode("utf-8"))
    finally:
        # Shut down the agent
        my_agent.stop()
        t.join()


if __name__ == "__main__":
    run()
```
</p>
</details>

<br />
