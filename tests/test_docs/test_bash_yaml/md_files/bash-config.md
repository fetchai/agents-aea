``` yaml
PACKAGE_REGEX: "[a-zA-Z_][a-zA-Z0-9_]*"
AUTHOR_REGEX: "[a-zA-Z_][a-zA-Z0-9_]*"
PUBLIC_ID_REGEX: "^[a-zA-Z0-9_]*/[a-zA-Z_][a-zA-Z0-9_]*:(0|[1-9]\\d*)\\.(0|[1-9]\\d*)\\.(0|[1-9]\\d*)(?:-((?:0|[1-9]\\d*|\\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\\.(?:0|[1-9]\\d*|\\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\\+([0-9a-zA-Z-]+(?:\\.[0-9a-zA-Z-]+)*))?$"
LEDGER_ID_REGEX: "^[^\\d\\W]\\w*\\Z"
```
``` yaml
agent_name: my_agent                            # Name of the AEA project (must satisfy PACKAGE_REGEX)
author: fetchai                                 # Author handle of the project's author (must satisfy AUTHOR_REGEX)
version: 0.1.0                                  # Version of the AEA project (a semantic version number, see https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string")
description: A demo project                     # Description of the AEA project
license: Apache-2.0                             # License of the AEA project
aea_version: '>=1.0.0, <2.0.0'               # AEA framework version(s) compatible with the AEA project (a version number that matches PEP 440 version schemes, or a comma-separated list of PEP 440 version specifiers, see https://www.python.org/dev/peps/pep-0440/#version-specifiers)
fingerprint: {}                                 # Fingerprint of AEA project components.
fingerprint_ignore_patterns: []                 # Ignore pattern for the fingerprinting tool.
connections:                                    # The list of connection public ids the AEA project depends on (each public id must satisfy PUBLIC_ID_REGEX)
- fetchai/stub:0.21.0
contracts: []                                   # The list of contract public ids the AEA project depends on (each public id must satisfy PUBLIC_ID_REGEX).
protocols:                                      # The list of protocol public ids the AEA project depends on (each public id must satisfy PUBLIC_ID_REGEX).
- fetchai/default:1.0.0
skills:                                         # The list of skill public ids the AEA project depends on (each public id must satisfy PUBLIC_ID_REGEX).
- fetchai/error:0.17.0
default_connection: fetchai/p2p_libp2p:0.25.0   # The default connection used for envelopes sent by the AEA (must satisfy PUBLIC_ID_REGEX).
default_ledger: fetchai                         # The default ledger identifier the AEA project uses (must satisfy LEDGER_ID_REGEX)
required_ledgers: [fetchai]                            # the list of identifiers of ledgers that the AEA project requires key pairs for (each item must satisfy LEDGER_ID_REGEX)
default_routing: {}                             # The default routing scheme applied to envelopes sent by the AEA, it maps from protocol public ids to connection public ids (both keys and values must satisfy PUBLIC_ID_REGEX)
connection_private_key_paths:                   # The private key paths the AEA project uses for its connections (keys must satisfy LEDGER_ID_REGEX, values must be file paths)
  fetchai: fetchai_private_key.txt
private_key_paths:                              # The private key paths the AEA project uses (keys must satisfy LEDGER_ID_REGEX, values must be file paths)
  fetchai: fetchai_private_key.txt
logging_config:                                 # The logging configurations the AEA project uses
  disable_existing_loggers: false
  version: 1
dependencies: {}                                # The python dependencies the AEA relies on (e.g. plugins). They will be installed when `aea install` is run.
```
``` yaml
period: 0.05                                    # The period to call agent's act
execution_timeout: 0                            # The execution time limit on each call to `react` and `act` (0 disables the feature)
timeout: 0.05                                   # The sleep time on each AEA loop spin (only relevant for the `sync` mode)
max_reactions: 20                               # The maximum number of envelopes processed per call to `react` (only relevant for the `sync` mode)
skill_exception_policy: propagate               # The exception policy applied to skills (must be one of "propagate", "just_log", or "stop_and_exit")
connection_exception_policy: propagate          # The exception policy applied to connections (must be one of "propagate", "just_log", or "stop_and_exit")
loop_mode: async                                # The agent loop mode (must be one of "sync" or "async")
runtime_mode: threaded                          # The runtime mode (must be one of "threaded" or "async") and determines how agent loop and multiplexer are run
error_handler: None                             # The error handler to be used.
decision_maker_handler: None                    # The decision maker handler to be used.
storage_uri: None                               # The URI to the storage.
data_dir: None                                  # The path to the directory for local files. Defaults to current working directory.
```
``` yaml
public_id: some_author/some_package:0.1.0       # The public id of the connection (must satisfy PUBLIC_ID_REGEX).
type: connection                                # for connections, this must be "connection".
config: ...                                     # a dictionary to overwrite the `config` field (see below)
```
``` yaml
public_id: some_author/some_package:0.1.0       # The public id of the connection (must satisfy PUBLIC_ID_REGEX).
type: skill                                     # for skills, this must be "skill".
behaviours:                                     # override configurations for behaviours
  behaviour_1:                                  # override configurations for "behaviour_1"
    args:                                       # arguments for a specific behaviour (see below)
      foo: bar
handlers:                                       # override configurations for handlers
  handler_1:                                    # override configurations for "handler_1"
    args:                                       # arguments for a specific handler (see below)
      foo: bar
models:                                         # override configurations for models
  model_1:                                      # override configurations for "model_1"
    args:                                       # arguments for a specific model (see below)
      foo: bar
```
``` yaml
name: scaffold                                  # Name of the package (must satisfy PACKAGE_REGEX)
author: fetchai                                 # Author handle of the package's author (must satisfy AUTHOR_REGEX)
version: 0.1.0                                  # Version of the package (a semantic version number, see https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string")
type: connection                                # The type of the package; for connections, it must be "connection"
description: A scaffold connection              # Description of the package
license: Apache-2.0                             # License of the package
aea_version: '>=1.0.0, <2.0.0'               # AEA framework version(s) compatible with the AEA project (a version number that matches PEP 440 version schemes, or a comma-separated list of PEP 440 version specifiers, see https://www.python.org/dev/peps/pep-0440/#version-specifiers)
fingerprint:                                    # Fingerprint of package components.
  __init__.py: QmZvYZ5ECcWwqiNGh8qNTg735wu51HqaLxTSifUxkQ4KGj
  connection.py: QmagwVgaPgfeXqVTgcpFESA4DYsteSbojz94SLtmnHNAze
fingerprint_ignore_patterns: []                 # Ignore pattern for the fingerprinting tool.
connections: []                                 # The list of connection public ids the package depends on (each public id must satisfy PUBLIC_ID_REGEX).
protocols: []                                   # The list of protocol public ids the package depends on (each public id must satisfy PUBLIC_ID_REGEX).
class_name: MyScaffoldConnection                # The class name of the class implementing the connection interface.
config:                                         # A dictionary containing the kwargs for the connection instantiation.
  foo: bar
excluded_protocols: []                          # The list of protocol public ids the package does not permit (each public id must satisfy PUBLIC_ID_REGEX).
restricted_to_protocols: []                     # The list of protocol public ids the package is limited to (each public id must satisfy PUBLIC_ID_REGEX).
dependencies: {}                                # The python dependencies the package relies on. They will be installed when `aea install` is run.
is_abstract: false                              # An optional boolean that if `true` makes the connection
```
``` yaml
name: scaffold                                  # Name of the package (must satisfy PACKAGE_REGEX)
author: fetchai                                 # Author handle of the package's author (must satisfy AUTHOR_REGEX)
version: 0.1.0                                  # Version of the package (a semantic version number, see https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string")
type: contract                                  # The type of the package; for contracts, it must be "contract"
description: A scaffold contract                # Description of the package
license: Apache-2.0                             # License of the package
aea_version: '>=1.0.0, <2.0.0'               # AEA framework version(s) compatible with the AEA project (a version number that matches PEP 440 version schemes, or a comma-separated list of PEP 440 version specifiers, see https://www.python.org/dev/peps/pep-0440/#version-specifiers)
fingerprint:                                    # Fingerprint of package components.
  __init__.py: QmPBwWhEg3wcH1q9612srZYAYdANVdWLDFWKs7TviZmVj6
  contract.py: QmXvjkD7ZVEJDJspEz5YApe5bRUxvZHNi8vfyeVHPyQD5G
fingerprint_ignore_patterns: []                 # Ignore pattern for the fingerprinting tool.
class_name: MyScaffoldContract                  # The class name of the class implementing the contract interface.
contract_interface_paths: {}                    # The paths to the contract interfaces (one for each ledger identifier).
config:                                         # A dictionary containing the kwargs for the contract instantiation.
  foo: bar
dependencies: {}                                # The python dependencies the package relies on. They will be installed when `aea install` is run.
```
``` yaml
name: scaffold                                  # Name of the package (must satisfy PACKAGE_REGEX)
author: fetchai                                 # Author handle of the package's author (must satisfy AUTHOR_REGEX)
version: 0.1.0                                  # Version of the package (a semantic version number, see https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string")
type: protocol                                  # The type of the package; for protocols, it must be "protocol" 
description: A scaffold protocol                # Description of the package
license: Apache-2.0                             # License of the package
aea_version: '>=1.0.0, <2.0.0'               # AEA framework version(s) compatible with the AEA project (a version number that matches PEP 440 version schemes, or a comma-separated list of PEP 440 version specifiers, see https://www.python.org/dev/peps/pep-0440/#version-specifiers)
fingerprint:                                    # Fingerprint of package components.
  __init__.py: Qmay9PmfeHqqVa3rdgiJYJnzZzTStboQEfpwXDpcgJMHTJ
  message.py: QmdvAdYSHNdZyUMrK3ue7quHAuSNwgZZSHqxYXyvh8Nie4
  serialization.py: QmVUzwaSMErJgNFYQZkzsDhuuT2Ht4EdbGJ443usHmPxVv
fingerprint_ignore_patterns: []                 # Ignore pattern for the fingerprinting tool.
dependencies: {}                                # The python dependencies the package relies on. They will be installed when `aea install` is run.
```
``` yaml
name: scaffold                                  # Name of the package (must satisfy PACKAGE_REGEX)
author: fetchai                                 # Author handle of the package's author (must satisfy AUTHOR_REGEX)
version: 0.1.0                                  # Version of the package (a semantic version number, see https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string")
type: skill                                     # The type of the package; for skills, it must be "skill"
description: A scaffold skill                   # Description of the package
license: Apache-2.0                             # License of the package
aea_version: '>=1.0.0, <2.0.0'               # AEA framework version(s) compatible with the AEA project (a version number that matches PEP 440 version schemes, or a comma-separated list of PEP 440 version specifiers, see https://www.python.org/dev/peps/pep-0440/#version-specifiers)
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
dependencies: {}                                # The python dependencies the package relies on. They will be installed when `aea install` is run.
```
