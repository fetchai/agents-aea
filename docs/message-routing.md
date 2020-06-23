
Message routing can be split up into the routing of incoming and outgoing messages.

# Incoming messages

- connections receive envelopes which they deposit in inbox
- agent loop's react picks envelopes off the inbox
- tries to decode the message; errors are handled by the error skill
- messages are dispatched to all relevant handlers

# Outgoing messages

- skills deposit messages in outbox
- outbox constructs an envelope from the message

- multiplexer assigns messages to relevant connection based on three rules:
1. checks if envelope context exists and uses that
2. checks if default routing applies
3. sends to default connection

- connections can encode envelopes where necessary
