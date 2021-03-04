
Message routing can be split up into the routing of incoming and outgoing `Messages`.

It is important to keep in mind that <a href="../interaction-protocol">interaction protocols</a> can be maintained between agents (agent to agent) and between components of the AEA (component to component). In the former case, the `to`/`sender` fields of the `Envelope` are agent addresses which must follow the address standard of agents, in the latter case they are component public ids. Crucially, both addresses must reference the same type: agent or component.

## Incoming `Messages`

- `Connections` receive or create `Envelopes` which they deposit in the `InBox`
- for agent-to-agent communication only, the `Multiplexer` keeps track of the `connection_id` via which the `Envelope` was received.
- the `AgentLoop` picks `Envelopes` off the `InBox`
- the `AEA` tries to decode the message; errors are handled by the `ErrorHandler`
- `Messages` are dispatched based on two rules:

	1. checks if `to` field can be interpreted as `skill_id`, if so uses that together with the `protocol_id` to dispatch to the protocol's `Handler` in the specified `Skill`, else
	2. uses the `protocol_id` to dispatch to the protocol's `Handler` in all skills supporting the protocol.

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>For agent-to-agent communication it is advisable to have a single skill implement a given protocol. Skills can then forward the messages via skill-to-skill communication to other skills where required. Otherwise, received agent-to-agent messages will be forwarded to all skills implementing a handler for the specified protocol and the developer needs to take care to handle them appropriately (e.g. avoid multiple replies to a single message).
</p>
</div>

## Outgoing `Messages`

- `Skills` deposit `Messages` in `OutBox`
- `OutBox` constructs an `Envelope` from the `Message`
- `Multiplexer` assigns messages to relevant `Connection` based on the following rules:

	1. Component to component messages are routed by their `component_id`
	2. Agent to agent messages are routed following four rules:
		1. checks if `EnvelopeContext` exists and specifies a `Connection`, if so uses that else
		2. checks which connection handled the last message from `sender`, if present uses that else
		3. checks if default routing is specified for the `protocol_id` referenced in the `Envelope`, if so uses that else
		4. sends to default `Connection`.

- `Connections` can process `Envelopes` directly or encode them for transport to another agent.

## Usage of the `EnvelopeContext`

The `EnvelopeContext` is used to maintain agent-to-agent communication only and is managed almost entirely by the framework. The developer can set the `EnvelopeContext` explicitly for the first message in a dialogue to achieve targeted routing to connections (see 2. for outgoing messages). This is relevant when the same agent can be reached via multiple connections.

The `EnvelopeContext` is not sent to another agent.
