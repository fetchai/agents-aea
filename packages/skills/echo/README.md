# Echo skill

This tutorial explains how to set up an AEA with the echo skill.

## What it does?

The Echo skill handles messages of the protocol `"default"` and
replies to the sender with the same message.

## Set up

- Create the agent:

```
aea create myagent & cd myagent
```

- Add the `echo` skill:
```
aea add skill echo
```

- For this tutorial, we will use the `stub` connection - 
a development connection that uses the file system to 
receive and send the messages.
```
aea add connection stub
``` 

- Finally, run the agent with the `stub` connection:
```
aea -v DEBUG run --connection stub
```

The agent will be listening for new messages
posted on the file `myagent/input_file`,
and will answer on the file `myagent/output_file`.

## Send a message

First of all, let's create the message we 
want to send:

```python
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
message = DefaultMessage(type=DefaultMessage.Type.BYTES, content=b"hello")
DefaultSerializer().encode(message)
```

You should get:
```
b'{"type": "bytes", "content": "aGVsbG8="}'
```

To send this message to an agent using the `stub` connection,
we'll add a line to `myagent/input_file`, 
formatted in the following way:
```
RECIPIENT,SENDER,PROTOCOL_ID,ENCODED_MESSAGE
```

- `RECIPIENT` is the name of our agent, `myagent`
- `SENDER` is the sender of the message - us.
- `PROTOCOL_ID` is the protocol of our message - in our example, `default`
- `ENCODED_MESSAGE` is the serialized message we created above.

Assuming you are in the `myagent` folder, execute this command 
to send the message:
```bash
echo 'myagent,sender_agent,default,{"type": "bytes", "content": "aGVsbG8="}' >> ./input_file
```

## Receive a message

At this point, our Echo agent should have answered
to our request. You can check the logging messages
on the console where you executed `aea run` to realize that.  

To read the response, just look into `output_file`:

```bash
cat output_file
```

you should get:
```
sender_agent,myagent,default,{"type": "bytes", "content": "aGVsbG8="}
```
