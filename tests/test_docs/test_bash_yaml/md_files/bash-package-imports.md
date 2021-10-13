``` bash
aea_name/
  aea-config.yaml       YAML configuration of the AEA
  fetchai_private_key.txt   The private key file
  connections/          Directory containing all the connections developed as part of the given project.
    connection_1/       First connection
    ...                 ...
    connection_n/       nth connection
  contracts/            Directory containing all the contracts developed as part of the given project.
    connection_1/       First connection
    ...                 ...
    connection_n/       nth connection
  protocols/            Directory containing all the protocols developed as part of the given project.
    protocol_1/         First protocol
    ...                 ...
    protocol_m/         mth protocol
  skills/               Directory containing all the skills developed as part of the given project.
    skill_1/            First skill
    ...                 ...
    skill_k/            kth skill
  vendor/               Directory containing all the added resources from the registry, sorted by author.
    author_1/           Directory containing all the resources added from author_1
      connections/      Directory containing all the added connections from author_1
        ...             ...
      protocols/        Directory containing all the added protocols from author_1
        ...             ...
      skills/           Directory containing all the added skills from author_1
        ...             ...
```
``` yaml
connections:
- fetchai/stub:0.21.0
```
