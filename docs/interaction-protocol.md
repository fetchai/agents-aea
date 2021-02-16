
<a href="https://en.wikipedia.org/wiki/Interaction_protocol" target="_blank">Interaction protocols</a> are possible communication scenarios between agents or agent components (specifically, skills and connections).

There are multiple types of interactions an AEA can have:

- AEA to AEA interactions. You can find some examples in the <a href="../demos">demo section</a>.

- Interactions between an AEA's internal components.


<img src="../assets/interaction-protocols.jpg" alt="Interaction protocols" class="center" style="display: block; margin-left: auto; margin-right: auto;width:80%;">


Usually, an interaction involves three types of framework packages: <a href="../skill">skills</a>, <a href="../protocol">protocols</a> and <a href="../connection">connections</a>.

### Example 1: negotiation

The <a href="../generic-skills">generic buyer/seller skills</a> use the `fetchai/fipa` protocol which defines the negotiation dialogue between two AEAs. The `fetchai/generic_buyer` and `fetchai/generic_seller` skills implement specific strategies for engaging in such negotiations, by providing the logic for producing negotiation messages to be sent, handling negotiation messages received. The `fetchai/p2p_libp2p` connection is then used for connecting to the <a href="../acn">agent communication network</a> enabling two AEAs with these skills to deliver negotiation messages to each other.

### Example 2: AEA <> web client 

In the <a href="../http-connection-and-skill">http connection guide</a> we demonstrate how an AEA with an http server connection (e.g. `fetchai/http_server`) receives http payloads from web clients, translates them to messages conforming with the `fetchai/http` protocol and passes it to a skill (e.g. `fetchai/http_echo`) to process. The `fetchai/http` protocol in this case is used for communication between the connection and the skill.

### Example 3 : AEA <> 3rd party server

The `fetchai/http_client` connection can be used to make requests to third party servers. In this case, a skill containing the logic for the production of http requests would create messages conforming with the `fetchai/http` protocol and sends it to the `fetchai/http_client` connection which in turn translates it into http payload and sends it to the destination server. 

Note that in general, third party SDKs can be wrapped in a connection and shared with other developers as a package. Often this also involves creating a custom protocol to enforce the type of interactions permitted between skills and the connection wrapping the SDK.


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