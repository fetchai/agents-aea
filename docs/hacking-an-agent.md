## Preliminaries

These instructions detail the Python code you need for running an AEA outside the `cli` tool.

!!!	Note
	You have already coded up your agent. See the <a href="../aea/skill-guide/" target=_blank>build your own skill guide</a> for a reminder.


## Imports

First, import the necessary common Python libraries and classes.

``` python
import os
import tempfile
import time	
from pathlib import Path
from threading import Thread
import yaml
```

Then, import the application specific libraries.

``` python
from aea import AEA_DIR
from aea.aea import AEA	
from aea.configurations.base import ProtocolConfig
from aea.connections.local.connection import LocalNode, OEFLocalConnection
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import Wallet
from aea.mail.base import MailBox, Envelope
from aea.protocols.base import Protocol
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.protocols.fipa.message import FIPAMessage
from aea.protocols.fipa.serialization import FIPASerializer
from aea.registries.base import Resources
from aea.skills.base import Skill
from .conftest import CUR_PATH, DummyConnection
```



## Initialise the agent

Create a node.

``` python
node = LocalNode()
```

Initialise a `MailBox` object with a public key and grab the private key and add it to a wallet.

``` python
public_key_1 = "mailbox1"
mailbox1 = MailBox(OEFLocalConnection(public_key_1, node))
private_key_pem_path = os.path.join(CUR_PATH, "data", "priv.pem")
wallet = Wallet({'default': private_key_pem_path})
```

Using a variable for accessing running ledgers, initialise the agent. 

``` python
ledger_apis = LedgerApis({})
my_AEA = AEA("Agent0", mailbox1, wallet, ledger_apis, resources=Resources(str(Path(CUR_PATH, "aea"))))
```


## Run the agent

Running the agent invokes the `act()` function in a `Behaviour` object.

Initialise the agent as above and add a mailbox to it.

``` python
mailbox = MailBox(OEFLocalConnection(public_key, node))
```

Create a thread and add the agent to it.

``` python
t = Thread(target=my_AEA.start)
```

Start the agent and sleep it.

``` python
t.start()
time.sleep(1)
```

Make sure the `act()` function was called by grabbing the agent's `Behaviour` object and running an assert on it.

``` python
behaviour = agent.resources.behaviour_registry.fetch("dummy")
assert behaviour[0].nb_act_called > 0, "Act() wasn't called"
```

Finalise the agent thread.

``` python
finally:
	agent.stop()
	t.join()
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


## Ensure receipt of envelope messages

Start up the agent thread as in all previous steps then add the envelope you just created in to the message queue.

``` python
t.start()
agent.mailbox.inbox._queue.put(envelope)
time.sleep(1)
```

Grab a `Handler` from the agent `handler_registry` to make sure messages are coming in.

``` python
handler = agent.resources.handler_registry.fetch_by_skill('default', "dummy")
assert msg in handler.handled_messages, "The message is not inside the handled_messages."
```


## Test the `handle()` method

Initialise and start the agent as in previous steps but this time create a `DummyConnection` object to add to the `MailBox` so you have a variable name for accessing the `Connection`.

``` python
connection = DummyConnection()
mailbox = MailBox(connection)
```

Create the message envelope as before then start the agent in a `try` clause and add the envelope to the `DummyConnection`.

``` python
t.start()
time.sleep(1.0)
connection.in_queue.put(envelope)
```

Check the out queue is functioning correctly.

``` python
env = connection.out_queue.get(block=True, timeout=5.0)
assert env.protocol_id == "default"
```

``` python
#   DECODING ERROR
msg = "hello".encode("utf-8")
envelope = Envelope(
	to=public_key,
    sender=public_key,
    protocol_id='default',
    message=msg)
connection.in_queue.put(envelope)
env = connection.out_queue.get(block=True, timeout=5.0)
assert env.protocol_id == "default"
```

``` python
#   UNSUPPORTED SKILL
msg = FIPASerializer().encode(
	FIPAMessage(performative=FIPAMessage.Performative.ACCEPT,
		message_id=0,
       	dialogue_id=0,
   		destination=public_key,
		target=1))
envelope = Envelope(
        to=public_key,
		sender=public_key,
        protocol_id="fipa",
        message=msg)
connection.in_queue.put(envelope)
env = connection.out_queue.get(block=True, timeout=5.0)
assert env.protocol_id == "default"
```


<br />