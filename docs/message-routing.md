
Message routing can be split up into the routing of incoming and outgoing `Messages`.

## Incoming `Messages`

- `Connections` receive `Envelopes` which they deposit in `InBox`
- `AgentLoop`'s react picks `Envelopes` off the `InBox`
- the AEA tries to decode the message; errors are handled by the error `Skill`
- `Messages` are dispatched to all relevant `Handlers`. To limit dispatch to a specific `Handler` in a specific `Skill` the `EnvelopeContext` can be used to reference a unique `skill id`.

## Outgoing `Messages`

- `Skills` deposit `Messages` in `OutBox`
- `OutBox` constructs an `Envelope` from the `Message`
- `Multiplexer` assigns messages to relevant `Connection` based on three rules:

	1. checks if `EnvelopeContext` exists and specifies a `Connection`, if so uses that else
	2. checks if default routing is specified for the `protocol_id` referenced in the `Envelope`, if so uses that else
	3. sends to default `Connection`.

- `Connections` can encode envelopes where necessary or pass them on for transport to another agent

## Address fields in `Envelopes`/`Messages`

Addresses can reference agents or components within an agent. If the address references an agent then it must follow the address standard of agents. If the address references a component then it must be a public id.
