
These instructions detail the Python code you need for running an AEA outside the `cli` tool, using the code interface.

## Preparation

Get the packages directory from the AEA repository:

``` bash
svn export https://github.com/fetchai/agents-aea.git/trunk/packages
```

Also, install `aea-ledger-fetchai` plug-in:
```bash
pip install aea-ledger-fetchai
```

## Imports

First, import the necessary common Python libraries and classes.

``` python
import os
import time
from threading import Thread
```

Then, import the application specific libraries.

``` python
from aea_ledger_fetchai import FetchAICrypto

from aea.aea_builder import AEABuilder
from aea.configurations.base import SkillConfig
from aea.crypto.helpers import PRIVATE_KEY_PATH_SCHEMA, create_private_key
from aea.helpers.file_io import write_with_lock
from aea.skills.base import Skill
```

Set up a variable pointing to where the packages directory is located - this should be our current directory - and where the input and output files are located.
``` python
ROOT_DIR = "./"
INPUT_FILE = "input_file"
OUTPUT_FILE = "output_file"
FETCHAI_PRIVATE_KEY_FILE = PRIVATE_KEY_PATH_SCHEMA.format(FetchAICrypto.identifier)
```

## Create a private key
We need a private key to populate the AEA's wallet.
``` python
    # Create a private key
    create_private_key(FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_FILE)
```

## Clearing the input and output files
We will use the stub connection to pass envelopes in and out of the AEA. Ensure that any input and output text files are removed before we start.
``` python
    # Ensure the input and output files do not exist initially
    if os.path.isfile(INPUT_FILE):
        os.remove(INPUT_FILE)
    if os.path.isfile(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
```

## Initialise the AEA
We use the <a href="../api/aea_builder#aeabuilder-objects">`AEABuilder`</a> to readily build an AEA. By default, the `AEABuilder` adds the `fetchai/default:1.0.0`, `fetchai/state_update:1.0.0` and `fetchai/signing:1.0.0` protocols.
``` python
    # Instantiate the builder and build the AEA
    # By default, the default protocol, error skill and stub connection are added
    builder = AEABuilder()
```

We set the name, add the private key for the AEA to use and set the ledger configurations for the AEA to use.
``` python
    builder.set_name("my_aea")

    builder.add_private_key(FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_FILE)
```

Next, we add the `fetchai/stub:0.15.0` connection which will read/write messages from file:
``` python
    # Add the stub connection (assuming it is present in the local directory 'packages')
    builder.add_connection("./packages/fetchai/connections/stub")
```

Next, we add the echo skill which will bounce our messages back to us. We first need to place the echo skill into a relevant directory (see path), either by downloading the `packages` directory from the AEA repo or by getting the package from the registry.
``` python
    # Add the echo skill (assuming it is present in the local directory 'packages')
    builder.add_skill("./packages/fetchai/skills/echo")
```

Also, we can add a component that was instantiated programmatically. :
``` python
    # create skill and handler manually
    from aea.protocols.base import Message
    from aea.skills.base import Handler

    from packages.fetchai.protocols.default.message import DefaultMessage

    class DummyHandler(Handler):
        """Dummy handler to handle messages."""

        SUPPORTED_PROTOCOL = DefaultMessage.protocol_id

        def setup(self) -> None:
            """Noop setup."""

        def teardown(self) -> None:
            """Noop teardown."""

        def handle(self, message: Message) -> None:
            """Handle incoming message."""
            self.context.logger.info("You got a message: {}".format(str(message)))

    config = SkillConfig(name="test_skill", author="fetchai")
    skill = Skill(configuration=config)
    dummy_handler = DummyHandler(
        name="dummy_handler", skill_context=skill.skill_context
    )
    skill.handlers.update({dummy_handler.name: dummy_handler})
    builder.add_component_instance(skill)
```

Finally, we can build our AEA:
``` python
    # Create our AEA
    my_aea = builder.build()
```

## Start the AEA
We run the AEA from a different thread so that we can still use the main thread to pass it messages.
``` python
    # Set the AEA running in a different thread
    try:
        t = Thread(target=my_aea.start)
        t.start()

        # Wait for everything to start up
        time.sleep(4)
```

## Send and receive an envelope
We use the input and output text files to send an envelope to our AEA and receive a response (from the echo skill)
``` python
        # Create a message inside an envelope and get the stub connection to pass it on to the echo skill
        message_text = b"my_aea,other_agent,fetchai/default:1.0.0,\x12\x10\x08\x01\x12\x011*\t*\x07\n\x05hello,"
        with open(INPUT_FILE, "wb") as f:
            write_with_lock(f, message_text)
            print(b"input message: " + message_text)

        # Wait for the envelope to get processed
        time.sleep(4)

        # Read the output envelope generated by the echo skill
        with open(OUTPUT_FILE, "rb") as f:
            print(b"output message: " + f.readline())
```

## Shutdown
Finally stop our AEA and wait for it to finish
``` python
    finally:
        # Shut down the AEA
        my_aea.stop()
        t.join()
        t = None
```

## Running the AEA
If you now run this python script file, you should see this output:

    input message: my_aea,other_agent,fetchai/default:1.0.0,\x12\x10\x08\x01\x12\x011*\t*\x07\n\x05hello,
    output message: other_agent,my_aea,fetchai/default:1.0.0,...\x05hello


## Entire code listing
If you just want to copy and past the entire script in you can find it here:

<details><summary>Click here to see full listing</summary>
<p>

``` python
import os
import time
from threading import Thread

from aea_ledger_fetchai import FetchAICrypto

from aea.aea_builder import AEABuilder
from aea.configurations.base import SkillConfig
from aea.crypto.helpers import PRIVATE_KEY_PATH_SCHEMA, create_private_key
from aea.helpers.file_io import write_with_lock
from aea.skills.base import Skill


ROOT_DIR = "./"
INPUT_FILE = "input_file"
OUTPUT_FILE = "output_file"
FETCHAI_PRIVATE_KEY_FILE = PRIVATE_KEY_PATH_SCHEMA.format(FetchAICrypto.identifier)


def run():
    """Run demo."""

    # Create a private key
    create_private_key(FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_FILE)

    # Ensure the input and output files do not exist initially
    if os.path.isfile(INPUT_FILE):
        os.remove(INPUT_FILE)
    if os.path.isfile(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    # Instantiate the builder and build the AEA
    # By default, the default protocol, error skill and stub connection are added
    builder = AEABuilder()

    builder.set_name("my_aea")

    builder.add_private_key(FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_FILE)

    # Add the stub connection (assuming it is present in the local directory 'packages')
    builder.add_connection("./packages/fetchai/connections/stub")

    # Add the echo skill (assuming it is present in the local directory 'packages')
    builder.add_skill("./packages/fetchai/skills/echo")

    # create skill and handler manually
    from aea.protocols.base import Message
    from aea.skills.base import Handler

    from packages.fetchai.protocols.default.message import DefaultMessage

    class DummyHandler(Handler):
        """Dummy handler to handle messages."""

        SUPPORTED_PROTOCOL = DefaultMessage.protocol_id

        def setup(self) -> None:
            """Noop setup."""

        def teardown(self) -> None:
            """Noop teardown."""

        def handle(self, message: Message) -> None:
            """Handle incoming message."""
            self.context.logger.info("You got a message: {}".format(str(message)))

    config = SkillConfig(name="test_skill", author="fetchai")
    skill = Skill(configuration=config)
    dummy_handler = DummyHandler(
        name="dummy_handler", skill_context=skill.skill_context
    )
    skill.handlers.update({dummy_handler.name: dummy_handler})
    builder.add_component_instance(skill)

    # Create our AEA
    my_aea = builder.build()

    # Set the AEA running in a different thread
    try:
        t = Thread(target=my_aea.start)
        t.start()

        # Wait for everything to start up
        time.sleep(4)

        # Create a message inside an envelope and get the stub connection to pass it on to the echo skill
        message_text = b"my_aea,other_agent,fetchai/default:1.0.0,\x12\x10\x08\x01\x12\x011*\t*\x07\n\x05hello,"
        with open(INPUT_FILE, "wb") as f:
            write_with_lock(f, message_text)
            print(b"input message: " + message_text)

        # Wait for the envelope to get processed
        time.sleep(4)

        # Read the output envelope generated by the echo skill
        with open(OUTPUT_FILE, "rb") as f:
            print(b"output message: " + f.readline())
    finally:
        # Shut down the AEA
        my_aea.stop()
        t.join()
        t = None


if __name__ == "__main__":
    run()
```
</p>
</details>

<br />
