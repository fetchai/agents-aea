
Message routing can be split up into the routing of incoming and outgoing `Messages`.

## Incoming `Messages`

- `Connections` receive or create `Envelopes` which they deposit in the `InBox`
- the `AgentLoop` picks `Envelopes` off the `InBox`
- the `AEA` tries to decode the message; errors are handled by the `ErrorHandler`
- `Messages` are dispatched based on two rules:

	1. checks if `to` field can be interpreted as `skill_id`, if so uses that together with the `protocol_id` to dispatch to the protocol's `Handler` in the specified `Skill`, else
	2. checks if `EnvelopeContext` esits and specifies a `Skill`, if so uses that together with the `protocol_id` to dispatch to the protocol's `Handler` in the specified `Skill`, else
	3. uses the `protocol_id` to dispatch to the protocol's `Handler` in all skills supporting the protocol.

## Outgoing `Messages`

- `Skills` deposit `Messages` in `OutBox`
- `OutBox` constructs an `Envelope` from the `Message`
- `Multiplexer` assigns messages to relevant `Connection` based on four rules:

	1. checks if `to` field can be interpreted as `connection_id`, if so uses that else
	2. checks if `EnvelopeContext` exists and specifies a `Connection`, if so uses that else
	3. checks if default routing is specified for the `protocol_id` referenced in the `Envelope`, if so uses that else
	4. sends to default `Connection`.

- `Connections` can process `Envelopes` directly or encode them for transport to another agent.

## Address fields in `Envelopes`/`Messages`

Addresses can reference agents or components (`Skill` and `Connections` only) within an agent. If the address references an agent then it must follow the address standard of agents. If the address references a component then it must be a public id.
