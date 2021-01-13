
<a href="https://en.wikipedia.org/wiki/Interaction_protocol" target="_blank">Interaction protocols</a> are possible communication scenarios between agents or agent components (specifically, skills and connections).

There are multiple types of interactions an AEA can have:

- AEA to AEA interactions, as for instance demonstrated in the <a href="../demos">demo sections</a>.

- AEA internal interactions, between components of the framework.


Usually, an interaction involves three types of framework packages: <a href="../skill">skills</a>, <a href="../protocol">protocols</a> and <a href="../connection">connections</a>.

### Example 1: negotiation

In the <a href="../generic-skills">generic buyer/seller skills</a> the protocol `fetchai/fipa` is used for maintaining the negotiation dialogue between two AEAs. The skills `fetchai/generic_buyer` and `fetchai/generic_seller` are used to implement the handling and generating of individual messages and associated logic. The connection `fetchai/p2p_libp2p` is used for connecting to the <a href="../acn">agent communication network</a>.

### Example 2: AEA <> web client 

In the <a href="../http-connection-and-skill">http connection and skill guide</a> we demo how a skill (`fetchai/http_echo`) can be used to process http requests received by a http server connection (`fetchai/http_server`). The `fetchai/http` protocol is used for communication between the connection and skill.

### Example 3 : AEA <> 3rd party server

The `fetchai/http_client` connection can be used to make requests to third party servers. Alternatively, a third party SDK can be wrapped in a connection and shared with other developers as a package. Often, the developer will also create a custom protocol to enforce the type of interactions permitted with the SDK wrapped in such a connection.


## Next steps

### Recommended

We recommend you continue with the next step in the 'Getting Started' series:

- <a href="../generic-skills-step-by-step/">Trade between two AEAs</a>

### Relevant deep-dives

Most AEA development focuses on developing the `Skills` and `Protocols` necessary for an AEA to deliver against its economic objectives and implement interaction protocols.

Understanding `Protocols` is core to developing your own agent. You can learn more about the `Protocols` agents use to communicate with each other and how they are created in the following section:

- <a href="../protocol">Protocols</a>

Most of an AEA developer's time is spent on `Skill` development. `Skills` are the core business logic components of an AEA. Check out the following guide to learn more:

- <a href="../skill">Skills</a>

In most cases, one of the available `Connection` packages can be used. Occasionally, you might develop your own `Connection`:

- <a href="../connection">Connections</a>

<br />