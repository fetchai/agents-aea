An agent that is generated using the AEA framework is a modular system with different connections, contracts, protocols and skills.

## File structure

The file structure of an AEA is fixed.

The top level directory has the AEA's name. Below is a `aea-config.yaml` configuration file, then directories containing the connections, contracts, protocols, and skills developed by the developer as part of the given project. The connections, contracts, protocols and skills used from the registry are located in `vendor` and sorted by author. Finally, there are files containing the private keys of the AEA.

When we create a new agent with the command `aea create my_aea` we create the file structure that looks like the following:

``` bash
aea_name/
  aea-config.yaml       YAML configuration of the AEA
  fet_private_key.txt   The private key file
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

The developer can create new directories where necessary but the core structure must remain the same.

## AEA Config Yaml

The `aea-config.yaml` is the top level configuration file of an AEA. It defines the global configurations as well as the component/package dependencies of the AEA. In some sense, the AEA can therefore be understood as an orchestrator of components.

For the AEA to use a package, the `public_id` for the package must be listed in the `aea-config.yaml` file, e.g.
``` yaml
connections:
- fetchai/stub:0.1.0
```

The above shows a part of the `aea-config.yaml`. If you see the connections, you will see that we follow a pattern of `author/name_package:version` to identify each package, also referred to as `public_id`. Here the `author` is the author of the package.

## Vendor and package directories

The `vendor` folder contains the packages from the registry which have been developed by ourselves, other authors or Fetch.ai and are namespaced by author name.

The packages we develop as part of the given AEA project are in the respective `connections/`, `contracts/`, `protocols/`, and `skills/` folders.

In the above configuration example, the package is authored by Fetch.ai and is located inside the `vendor/fetchai/connections` folder.

## Importing modules from packages

The way we import modules from packages inside the agent is in the form of `packages.{author}.{package_type}.{package_name}.{module_name}`. So for the above example, the import path is `packages.fetchai.connections.stub.{module_name}`.

The framework loads the modules from the local agent project and adds them to Python's `sys.modules` under the respective path.

## Python dependencies of packages

Python dependencies of packages are specified in their respective configuration files under `dependencies`.

## Create a package

If you want to create a package, you can use the <a href="../scaffolding/">CLI command</a> `aea scaffold connection/contract/protocol/skill [name]` and this will create the package and put it inside the respective folder based on the command for example if we `scaffold` skill with the name `my_skill`
it will be located inside the folder skills in the root directory of the agent (`my_aea/skills/my_skill`).

## Use published packages

On the other hand, if you use a package from the registry or the `packages` located in the AEA repository, you will be able to locate the package under the folder `vendor` after adding it using the CLI.

## Difference of vendor and own packages

The packages you have developed in the context of the given AEA project should be located in the root folders (`connections/`, `contracs/`, `protocols/` and `skills/`) and all the packages you have added from the registry should be located in the `vendor` folder, under the relevant author.
