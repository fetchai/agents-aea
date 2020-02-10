The AEA framework uses each own way of enabling the agents to communicate with each other. Specifically, we are creating an envelope that contains the details
we want to pass to the other agent. An envelope contains the following fields : 
`to`, `sender`, `protocol_id`, `message`, `context`.

### Explanation of envelope 

- to: the address that we want to send the envelope.
- sender: the address of the sender.
- protocol_id: the protocol we used to serialize the message. 
- message: the message that we want to send to the receiver of the message. Implements a specific protocol.
- context: an optional field to specify routing information in a URI.

The most important thing to pay attention here is the `protocol_id` and the `message`.
Each message implements a protocol, which means that the receiver of the message must know the
protocol that is used to serialize the message if we want him to be able to read it. If the receiver doesn't 'know'
how to deserialize the message he will not be able to answer us. 

A message could be of different types, for example, a `DefaultMessage` would be serialized in a different way from 
a `FIPAMessage` and the receiver must implement different handlers to 'understand' the content of the message.

In order to understand the protocols in more details please read <a href='/protocol/'>here</a>
