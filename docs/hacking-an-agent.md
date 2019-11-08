## Preliminaries

These instructions detail the Python code you need for running an AEA outside the `cli` tool.

!!! Note
    You have already coded up your agent. See the <a href="../aea/skill-guide/" target=_blank>build your own skill guide</a> for a reminder.


## Imports

First, import the necessary common Python libraries and classes.

``` python
import os
import time
from threading import Thread
```

Then, import the application specific libraries.

``` python
from aea.aea import AEA 
from aea.connections.stub.connection import StubConnection
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import Wallet
from aea.mail.base import MailBox, Envelope
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.protocols.fipa.message import FIPAMessage
from aea.protocols.fipa.serialization import FIPASerializer
from aea.registries.base import Resources
```



## Initialise the agent

Create a private key.
``` bash
python scripts/generate_private_key.py my_key
```

Create a wallet object with a private key.
``` python
wallet = Wallet({'default': 'my_key'})
    ```

Create a `Connection` and a `MailBox`.
``` python
stub_connection = StubConnection(input_file_path='input.txt', output_file_path='output.txt')
mailbox = MailBox(stub_connection)
```

For ledger APIs, we simply feed the agent an empty dictionary (meaning we do not require any). 
``` python
ledger_apis = LedgerApis({})
```

Create the resources.
``` python
resources = Resources('')
```

Now we have everything we need for initialisation.
``` python
my_AEA = AEA("my_agent", mailbox, wallet, ledger_apis, resources)
```

## Add skills and protocols

We can add the echo skill as follows...

## Run the agent

Create a thread and add the agent to it.

``` python
t = Thread(target=my_AEA.start)
```

Start the agent and sleep it.

``` python
t.start()
```

## Create an envelope

An envelope carries an encoded message. Create the message object with contents then serialise it.

After that, add the serialised message to an envelope object.

``` python
msg = DefaultMessage(type=DefaultMessage.Type.BYTES, content=b"hello")
message_bytes = DefaultSerializer().encode(msg)

envelope = Envelope(
        to="Agent1",
        sender=public_key,
        protocol_id="default",
        message=message_bytes)
```


## Terminate the agent

Finalise the agent thread.

``` python
agent.stop()
t.join()
t = None
```

<br />