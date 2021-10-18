An agent that is generated using the AEA framework is a modular system with different connections, contracts, protocols and skills.

## File structure

The file structure of an AEA is fixed.

The top level directory has the AEA's name. Below is a `aea-config.yaml` configuration file, then directories containing the connections, contracts, protocols, and skills developed by the developer as part of the given project. The connections, contracts, protocols and skills used from the registry (local or remote - added via `aea fetch` or `aea add`) are located in `vendor` and sorted by author. Build artefacts are placed in the `.build/` directory and certificates are placed in the `.certs/` directory. Finally, there are files containing the private keys of the AEA.

When we create a new agent with the command `aea create my_aea` we create the file structure that looks like the following:

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

The developer can create new directories where necessary but the core structure must remain the same.

## AEA Configuration YAML

The `aea-config.yaml` is the top level configuration file of an AEA. It defines the global configurations as well as the component/package dependencies of the AEA. In some sense, the AEA can therefore be understood as an orchestrator of components.

For the AEA to use a package, the `public_id` for the package must be listed in the `aea-config.yaml` file, e.g.
``` yaml
connections:
- fetchai/stub:0.21.0
```

The above shows a part of the `aea-config.yaml`. If you see the connections, you will see that we follow a pattern of `author/name_package:version` to identify each package, also referred to as `public_id`. Here the `author` is the author of the package.

## Vendor and package directories

The `vendor` folder contains the packages from the registry (local or remote) which have been developed by ourselves, other authors or Fetch.ai and are namespaced by author name.

The packages we develop as part of the given AEA project are in the respective `connections/`, `contracts/`, `protocols/`, and `skills/` folders.

In the above configuration example, the package is authored by Fetch.ai and is located inside the `vendor/fetchai/connections` folder.

## Importing modules from packages

The way we import modules from packages inside the agent is in the form of `packages.{author}.{package_type}.{package_name}.{module_name}`. So for the above example, the import path is `packages.fetchai.connections.stub.{module_name}`.

The framework loads the modules from the local agent project and adds them to Python's `sys.modules` under the respective path.

We use a custom package management approach for the AEAs rather than the default Python one as it provides us with more flexibility, especially when it comes to extension beyond the Python ecosystem.

## Python dependencies of packages

Python dependencies of packages are specified in their respective configuration files under `dependencies`. They will be installed when `aea install` is run on an agent project.

## Create a package

If you want to create a package, you can use the <a href="../scaffolding/">CLI command</a> `aea scaffold connection/contract/protocol/skill [name]` and this will create the package and put it inside the respective folder based on the command for example if we `scaffold` skill with the name `my_skill`
it will be located inside the folder skills in the root directory of the agent (`my_aea/skills/my_skill`).

## Use published packages from the registry

If you want to use a finished package, you can use a package from the registry.

There or two registries. The remote registry operated by Fetch.ai and a local registry stub. The local registry stub is a directory called `packages` which contains packages in a nested structure with authors on the top level, followed by the package type, then package name. An example of such a directory is the `packages` directory located in the AEA repository. The local registry is useful for development.

You can use the CLI to interact with the registry. By default the CLI points to the remote registry. You can point it to the local registry via the flag `--local`.

## Package versioning

By default, the AEA can only handle one version per package. That is, a project should never use both `some_author/some_package_name:0.1.0` and `some_author/some_package_name:0.2.0`.

If two AEA packages with the same author and name but different versions are used in the same Python process, then only the code from one of the packages (generally not deterministic) will be available in `sys.modules`. This can lead to inconsistencies and exceptions at runtime.
