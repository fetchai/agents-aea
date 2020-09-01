This document describes the configuration files of the different packages.

## AEA config yaml

The following provides a list of the relevant regex used:
``` yaml
PACKAGE_REGEX: "[a-zA-Z_][a-zA-Z0-9_]*"
AUTHOR_REGEX: "[a-zA-Z_][a-zA-Z0-9_]*"
PUBLIC_ID_REGEX: "^[a-zA-Z0-9_]*/[a-zA-Z_][a-zA-Z0-9_]*:(0|[1-9]\\d*)\\.(0|[1-9]\\d*)\\.(0|[1-9]\\d*)(?:-((?:0|[1-9]\\d*|\\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\\.(?:0|[1-9]\\d*|\\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\\+([0-9a-zA-Z-]+(?:\\.[0-9a-zA-Z-]+)*))?$"
LEDGER_ID_REGEX: "^[^\\d\\W]\\w*\\Z"
```

The `aea-config.yaml` defines the AEA project. The compulsary components are listed below:
``` yaml
agent_name: my_agent                            # Name of the AEA project (must satisfy PACKAGE_REGEX)
author: fetchai                                 # Author handle of the project's author (must satisfy AUTHOR_REGEX)
version: 0.1.0                                  # Version of the AEA project (a semantic version number, see https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string")
description: A demo project                     # Description of the AEA project
license: Apache-2.0                             # License of the AEA project
aea_version: '>=0.6.0, <0.7.0'                  # AEA framework version(s) compatible with the AEA project (a version number that matches PEP 440 version schemes, or a comma-separated list of PEP 440 version specifiers, see https://www.python.org/dev/peps/pep-0440/#version-specifiers)
fingerprint: {}                                 # Fingerprint of AEA project components.
fingerprint_ignore_patterns: []                 # Ignore pattern for the fingerprinting tool.
connections:                                    # The list of connection public ids the AEA project depends on (each public id must satisfy PUBLIC_ID_REGEX)
- fetchai/stub:0.9.0
contracts: []                                   # The list of contract public ids the AEA project depends on (each public id must satisfy PUBLIC_ID_REGEX).
protocols:                                      # The list of protocol public ids the AEA project depends on (each public id must satisfy PUBLIC_ID_REGEX).
- fetchai/default:0.5.0
skills:                                         # The list of skill public ids the AEA project depends on (each public id must satisfy PUBLIC_ID_REGEX).
- fetchai/error:0.5.0
default_connection: fetchai/p2p_libp2p:0.8.0    # The default connection used for envelopes sent by the AEA (must satisfy PUBLIC_ID_REGEX).
default_ledger: fetchai                         # The default ledger identifier the AEA project uses (must satisfy LEDGER_ID_REGEX)
logging_config:                                 # The logging configurations the AEA project uses
  disable_existing_loggers: false
  version: 1
private_key_paths:                              # The private key paths the AEA project uses (keys must satisfy LEDGER_ID_REGEX, values must be file paths)
  fetchai: fetchai_private_key.txt
connection_private_key_paths:                   # The private key paths the AEA project uses for its connections (keys must satisfy LEDGER_ID_REGEX, values must be file paths)
  fetchai: fetchai_private_key.txt
registry_path: ../packages                      # The path to the local package registry (must be a directory path and point to a directory called `packages`)
```

The `aea-config.yaml` can be extended with a number of optional fields:
``` yaml
execution_timeout: 0                            # The execution time limit on each call to `react` and `act` (0 disables the feature)
timeout: 0.05                                   # The sleep time on each AEA loop spin (only relevant for the `sync` mode)
max_reactions: 20                               # The maximum number of envelopes processed per call to `react` (only relevant for the `sync` mode)
skill_exception_policy: propagate               # The exception policy applied to skills (must be one of "propagate", "just_log", or "stop_and_exit")
default_routing: {}                             # The default routing scheme applied to envelopes sent by the AEA, it maps from protocol public ids to connection public ids (both keys and values must satisfy PUBLIC_ID_REGEX)
loop_mode: async                                # The agent loop mode (must be one of "sync" or "async")
runtime_mode: threaded                          # The runtime mode (must be one of "threaded" or "async") and determines how agent loop and multiplexer are run
```

## Connection config yaml

The `connection.yaml`, which is present in each connection package, has the following required fields:
``` yaml
name: scaffold                                  # Name of the package (must satisfy PACKAGE_REGEX)
author: fetchai                                 # Author handle of the package's author (must satisfy AUTHOR_REGEX)
version: 0.1.0                                  # Version of the package (a semantic version number, see https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string")
type: connection                                # The type of the package; for connections, it must be "connection"
description: A scaffold connection              # Description of the package
license: Apache-2.0                             # License of the package
aea_version: '>=0.6.0, <0.7.0'                  # AEA framework version(s) compatible with the AEA project (a version number that matches PEP 440 version schemes, or a comma-separated list of PEP 440 version specifiers, see https://www.python.org/dev/peps/pep-0440/#version-specifiers)
fingerprint:                                    # Fingerprint of package components.
  __init__.py: QmZvYZ5ECcWwqiNGh8qNTg735wu51HqaLxTSifUxkQ4KGj
  connection.py: QmagwVgaPgfeXqVTgcpFESA4DYsteSbojz94SLtmnHNAze
fingerprint_ignore_patterns: []                 # Ignore pattern for the fingerprinting tool.
protocols: []                                   # The list of protocol public ids the package depends on (each public id must satisfy PUBLIC_ID_REGEX).
class_name: MyScaffoldConnection                # The class name of the class implementing the connection interface.
config:                                         # A dictionary containing the kwargs for the connection instantiation.
  foo: bar
excluded_protocols: []                          # The list of protocol public ids the package does not permit (each public id must satisfy PUBLIC_ID_REGEX).
restricted_to_protocols: []                     # The list of protocol public ids the package is limited to (each public id must satisfy PUBLIC_ID_REGEX).
dependencies: {}                                # The python dependencies the package relies on.
```

## Contract config yaml

The `contract.yaml`, which is present in each contract package, has the following required fields:
``` yaml
name: scaffold                                  # Name of the package (must satisfy PACKAGE_REGEX)
author: fetchai                                 # Author handle of the package's author (must satisfy AUTHOR_REGEX)
version: 0.1.0                                  # Version of the package (a semantic version number, see https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string")
type: contract                                  # The type of the package; for contracts, it must be "contract"
description: A scaffold contract                # Description of the package
license: Apache-2.0                             # License of the package
aea_version: '>=0.6.0, <0.7.0'                  # AEA framework version(s) compatible with the AEA project (a version number that matches PEP 440 version schemes, or a comma-separated list of PEP 440 version specifiers, see https://www.python.org/dev/peps/pep-0440/#version-specifiers)
fingerprint:                                    # Fingerprint of package components.
  __init__.py: QmPBwWhEg3wcH1q9612srZYAYdANVdWLDFWKs7TviZmVj6
  contract.py: QmXvjkD7ZVEJDJspEz5YApe5bRUxvZHNi8vfyeVHPyQD5G
fingerprint_ignore_patterns: []                 # Ignore pattern for the fingerprinting tool.
class_name: MyScaffoldContract                  # The class name of the class implementing the contract interface.
contract_interface_paths: {}                    # The paths to the contract interfaces (one for each ledger identifier).
config:                                         # A dictionary containing the kwargs for the contract instantiation.
  foo: bar
dependencies: {}                                # The python dependencies the package relies on.
```

## Protocol config yaml

The `protocol.yaml`, which is present in each protocol package, has the following required fields:
``` yaml
name: scaffold                                  # Name of the package (must satisfy PACKAGE_REGEX)
author: fetchai                                 # Author handle of the package's author (must satisfy AUTHOR_REGEX)
version: 0.1.0                                  # Version of the package (a semantic version number, see https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string")
type: protocol                                  # The type of the package; for protocols, it must be "protocol" 
description: A scaffold protocol                # Description of the package
license: Apache-2.0                             # License of the package
aea_version: '>=0.6.0, <0.7.0'                  # AEA framework version(s) compatible with the AEA project (a version number that matches PEP 440 version schemes, or a comma-separated list of PEP 440 version specifiers, see https://www.python.org/dev/peps/pep-0440/#version-specifiers)
fingerprint:                                    # Fingerprint of package components.
  __init__.py: Qmay9PmfeHqqVa3rdgiJYJnzZzTStboQEfpwXDpcgJMHTJ
  message.py: QmdvAdYSHNdZyUMrK3ue7quHAuSNwgZZSHqxYXyvh8Nie4
  serialization.py: QmVUzwaSMErJgNFYQZkzsDhuuT2Ht4EdbGJ443usHmPxVv
fingerprint_ignore_patterns: []                 # Ignore pattern for the fingerprinting tool.
dependencies: {}                                # The python dependencies the package relies on.
```

## Skill config yaml

The `skill.yaml`, which is present in each protocol package, has the following required fields:
``` yaml
name: scaffold                                  # Name of the package (must satisfy PACKAGE_REGEX)
author: fetchai                                 # Author handle of the package's author (must satisfy AUTHOR_REGEX)
version: 0.1.0                                  # Version of the package (a semantic version number, see https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string")
type: skill                                     # The type of the package; for skills, it must be "skill"
description: A scaffold skill                   # Description of the package
license: Apache-2.0                             # License of the package
aea_version: '>=0.6.0, <0.7.0'                  # AEA framework version(s) compatible with the AEA project (a version number that matches PEP 440 version schemes, or a comma-separated list of PEP 440 version specifiers, see https://www.python.org/dev/peps/pep-0440/#version-specifiers)
fingerprint:                                    # Fingerprint of package components.
  __init__.py: QmNkZAetyctaZCUf6ACxP5onGWsSxu2hjSNoFmJ3ta6Lta
  behaviours.py: QmYa1rczhGTtMJBgCd1QR9uZhhkf45orm7TnGTE5Eizjpy
  handlers.py: QmZYyTENRr6ecnxx1FeBdgjLiBhFLVn9mqarzUtFQmNUFn
  my_model.py: QmPaZ6G37Juk63mJj88nParaEp71XyURts8AmmX1axs24V
fingerprint_ignore_patterns: []                 # Ignore pattern for the fingerprinting tool.
contracts: []                                   # The list of contract public ids the package depends on (each public id must satisfy PUBLIC_ID_REGEX).
protocols: []                                   # The list of protocol public ids the package depends on (each public id must satisfy PUBLIC_ID_REGEX).
skills: []                                      # The list of skill public ids the package depends on (each public id must satisfy PUBLIC_ID_REGEX).
is_abstract: false                              # An optional boolean that if `true` makes the skill abstract, i.e. not instantiated by the framework but importable from other skills. Defaults to `false`. 
behaviours:                                     # The dictionary describing the behaviours immplemented in the package (including their configuration)
  scaffold:                                     # Name of the behaviour under which it is made available on the skill context.
    args:                                       # Keyword arguments provided to the skill component on instantiation.
      foo: bar
    class_name: MyScaffoldBehaviour             # The class name of the class implementing the behaviour interface.
handlers:                                       # The dictionary describing the handlers immplemented in the package (including their configuration)
  scaffold:                                     # Name of the handler under which it is made available on the skill
    args:                                       # Keyword arguments provided to the skill component on instantiation.
      foo: bar
    class_name: MyScaffoldHandler               # The class name of the class implementing the handler interface.
models:                                         # The dictionary describing the models immplemented in the package (including their configuration)
  scaffold:                                     # Name of the model under which it is made available on the skill
    args:                                       # Keyword arguments provided to the skill component on instantiation.
      foo: bar
    class_name: MyModel                         # The class name of the class implementing the model interface.
dependencies: {}                                # The python dependencies the package relies on.
```
