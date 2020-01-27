The file structure of an agent is fixed.

The top level directory has the agent's name. Below is a `yaml` configuration file, then directories containing the connections, protocols, and skills developed by the developer. The connections, protocols and skills from other authors are located in `vendor` and sorted by author. Finally, there are files containing the private keys of the agent.

The developer can create new directories where necessary but the core structure must remain the same.

The CLI tool provides a way to scaffold new connections, protocols and skills in the required directory structure for agents. See the instructions for that <a href="../scaffolding/">here</a>.

``` bash
agent_name/
  aea-config.yaml       YAML configuration of the agent
  private_key.pem       The private key file
  connections/          Directory containing all the own connections
    connection_1/       First connection
    ...                 ...
    connection_n/       nth connection
  protocols/            Directory containing all own protocols
    protocol_1/         First protocol
    ...                 ...
    protocol_m/         mth protocol 
  skills/               Directory containing all the own skills
    skill_1/            First skill
    ...                 ...
    skill_k/            kth skill
  vendor/               Directory containing all the added resources authored by other developers
    author_1/           Directory containing all the resources added from author_1
      connections/      Directory containing all the added connections from author_1
        ...             ...
      protocols/        Directory containing all the added protocols from author_1
        ...             ...
      skills/           Directory containing all the added skills from author_1
        ...             ...
```

<br />
