The file structure of an agent is fixed.

The top level directory has the agent's name. Below is a `yaml` configuration file, then directories containing the connections, protocols, and skills, and a file containing the private key of the agent.

The developer can create new directories where necessary but the core structure must remain the same.

The CLI tool provides a way to scaffold out the required directory structure for new agents. See the instructions for that <a href="../scaffolding/">here</a>.

``` bash
agent_name/
  aea-config.yaml       YAML configuration of the agent
  private_key.pem       The private key file
  connections/          Directory containing all the supported connections
    connection_1/       First connection
    ...                 ...
    connection_n/       nth connection
  protocols/            Directory containing all supported protocols
    protocol_1/         First protocol
    ...                 ...
    protocol_m/         mth protocol 
  skills/               Directory containing all the skill components
    skill_1/            First skill
    ...                 ...
    skill_k/            kth skill
```

<br />
