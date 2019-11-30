## Preliminaries

These instructions detail the Python code you need for running an AEA outside the `cli` tool.

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>You have already coded up your agent. See the <a href="../aea/skill-guide/" target=_blank>build your own skill guide</a> for a reminder.</p>
</div>


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
from aea.mail.base import Envelope
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.registries.base import Resources
```



## Initialise the agent

Create a private key.
``` bash
python scripts/generate_private_key.py my_key.txt
```

Create a wallet object with a private key.
``` python
wallet = Wallet({'default': 'my_key.txt'})
```

Create a `Connection`.
``` python
stub_connection = StubConnection(input_file_path='input.txt', output_file_path='output.txt')
```

For ledger APIs, we simply feed the agent an empty dictionary (meaning we do not require any). 
``` python
ledger_apis = LedgerApis({})
```

Create the resources pointing to the working directory.
``` python
resources = Resources('')
```

Now we have everything we need for initialisation.
``` python
my_agent = AEA("my_agent", stub_connection, wallet, ledger_apis, resources)
```

## Add skills and protocols

We can add the echo skill as follows...

!!! Note
    Work in progress.

## Run the agent

Create a thread and add the agent to it.

``` python
t = Thread(target=my_agent.start)
```

Start the agent.

``` python
t.start()
```

## Terminate the agent

Finalise the agent thread.

``` python
my_agent.stop()
t.join()
t = None
```

<br />