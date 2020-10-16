<details><summary>What is the Open Economic Framework (OEF)?</summary>
The 'Open Economic Framework' (OEF) is a node that enables search, discovery and communicate with possible clients or services.
<br><br>
You can read more about the ledgers and the OEF <a href="../oef-ledger/"> here </a>
</details>

<details><summary>What is the AEA?</summary>
AEA is short for Autonomous Economic Agents. AEAs act independently of constant user input and autonomously execute actions to achieve their objective.
Their goal is to create economic value for you, their owner.
<br><br>
You can read more about the AEAs <a href="../app-areas/"> here </a>
</details>

<details><summary>How do agents talk to others when they don't know each other?</summary>
For the Autonomous Economic Agents (AEAs) to be able to talk to others, firstly they need to find them,
and then, implement the same protocols in order to be able to deserialize the envelops they receive.
<br><br>
You can read more about the Search and Discovery <a href="../oef-ledger/">here</a> and more about envelops and protocols <a href="../core-components-1/">here</a>

</details>

<details><summary>How does an AEA use blockchain?</summary>
The AEA framework enables the agents to interact with public blockchains to complete transactions. Currently, the framework supports
two different networks natively: the `Fetch.ai` network and the `Ethereum` network.
<br><br>
You can read more about the intergration of ledger <a href="../ledger-integration/">here</a>

</details>

<details><summary>How does one install third party libraries?</summary>
The framework supports the use of third-party libraries hosted on PyPI we can directly reference the external dependencies.
The `aea install` command will install each dependency that the specific AEA needs and is listed in the skill's YAML file.
</details>

<details><summary>How does one connect to a database?</summary>
You have two options to connect to a database:
- Creating a wrapper that communicates with the database and imports a Model. You can find an example implementation in the `weather_station` package
- Using an ORM (object-relational mapping) library, and implementing the logic inside a class that inherits from the Model abstract class.
<br><br>
For a detailed example of how to use an ORM follow the <a href='../orm-integration/'>ORM use case</a>
</details>

<details><summary>How does one connect to a live-stream of data?</summary>
You can create a wrapper class that communicates with the source and import this class in your skill,
or you can use a third-party library by listing the dependency in the skill's `.yaml` file. Then you can import this library in a strategy class that inherits
from the Model abstract class.
<br><br>
You can find example of this implementation in the <a href='../generic-skills-step-by-step/#step4-create-the-strategy_1'> thermometer step by step guide </a>
</details>

<details><summary>How does one connect a frontend?</summary>
There are two options that one could connect a frontend. The first option would be to create an HTTP connection and then create an app that will communicate with this
connections.
The other option is to create a frontend client that will communicate with the agent via the <a href="../oef-ledger/">OEF communication network</a>.
<br><br>
You can find a more detailed approach <a href="../connect-a-frontend/">here</a>.
</details>

<details><summary>Is the AEA framework ideal for agent-based modeling?</summary>
The goal of agent-based modeling is to search for explanatory insight into the collective behavior of agents obeying simple rules, typically in natural systems rather than in designing agents or solving specific practical or engineering problems.
Although it would be potentially possible, it would be inefficient to use the AEA framework for that kind of problem.
<br><br>
You can find more details <a href="../app-areas/">here</a>
</details>

<details><summary>Can you manage multiple AEA projects at once with the CLI?</summary>
Individual CLI calls are currently scoped to a single project. You can have multiple AEA projects in a given root directory but you will have to use the CLI for each project independently.
<br>
We are looking to add support for interacting with multiple AEA projects via a single CLI call in the future.
<br><br>
You can find more details about the CLI commands <a href="../cli-commands/">here</a>
</details>

<details><summary>When a new AEA is created, is the `vendor` folder populated with some default packages?</summary>
All AEA projects by default hold the `fetchai/stub:0.11.0` connection, the `fetchai/default:0.7.0` protocol and the `fetchai/error:0.7.0` skill. These (as all other packages installed from the registry) are placed in the vendor's folder.
<br><br>
You can find more details about the file structure <a href="../package-imports/">here</a>
</details>

<details><summary>Is there a standardization for private key files?</summary>
Currently, the private keys are stored in `.txt` files. This is temporary and will be improved soon.
</details>

<details><summary>How to use the same protocol in different skills?</summary>
By default, envelopes of a given protocol get routed to all skills which have a handler supporting that protocol.

The `URI` in the `EnvelopeContext` can be used to route envelopes of a given protocol to a specific skill. The `URI` path needs to be set to the skill's `public_id.to_uri_path`.
</details>

<details><summary>Why does the AEA framework use its own package registry?</summary>
AEA packages could be described as personalized plugins for the AEA runtime. They are not like a library and therefore not suitable for distribution via <a href='https://pypi.org/' target="_blank">PyPI</a>.
</details>
