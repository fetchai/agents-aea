The file structure of an agent is fixed.

The top level directory has the agent's name. Below is a `yaml` configuration file, then directories containing the connections, protocols, and skills, and a file containing the private key of the agent.

The developer can create new directories where necessary but the core structure must remain the same.

The CLI tool provides a way to scaffold out the required directory structure for new agents. See the instructions for that <a href="../scaffolding/" target=_blank>here</a>.

``` bash
agentName/
  agent.yml       YAML configuration of the agent
  connections/    Directory containing all the supported connections
    connection1/  First connection
    ...           ...
    connectionN/  nth connection
  protocols/      Directory containing all supported protocols
    protocol1/    First protocol
    ...           ...
    protocolK/    kth protocol 
  skills/         Directory containing all the skill components
    skill1/       First skill
    ...           ...
    skillN/       nth skill
```

<br />
