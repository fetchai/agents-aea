# Release History

## 0.8.0 (2020-12-17)

- Adds support for protocol dialogue rules validation
- Fixes url forwarding in http server connection
- Revises protocols to correctly define terminal states
- Adds a build command
- Adds build command support for libp2p connection
- Adds multiple fixes to libp2p connection
- Adds prometheus connection and protocol
- Adds tests for confirmation AW1 skill
- Adds oracle demo docs
- Replaces pickle with protobuf in all protocols
- Refactors oef models to account for semantic irregularities
- Updates docs for demos relying on Ganache
- Adds generic storage support
- Adds configurable dialogue offloading
- Fixes transaction generation on confirmation bugs
- Fixes transaction processing order in all buyer skills
- Extends ledger api protocol to query ledger state
- Adds remove-key command in CLI
- Multiple tac stability fixes
- Adds support for configurable error handler
- Multiple additional tests to improve stability
- Multiple docs updates based on user feedback
- Multiple additional tests and test stability fixes

## 0.7.5 (2020-11-25)

- Adds AW3 AEAs
- Adds basic oracle skills and contracts
- Replaces usage of Ropsten testnet with Ganache in packages
- Fixes multiplexer setup when used outside AEA
- Improves help command output of CLI
- Adds integration tests for simple skills
- Adds version check on CLI push
- Adds integration tests for tac negotiation skills
- Multiple docs updates based on user feedback
- Multiple additional tests and test stability fixes

## 0.7.4 (2020-11-18)

- Replaces error skill handler usage with built in handler
- Extends MultiAgentManager to support persistence between runs
- Replaces usage of Ropsten testnet with Ganache
- Adds support for symlink creation during scaffold and add
- Makes contract interface loading extensible
- Adds support for PEP561
- Adds integration tests for launcher command
- Adds support for storage of unique page address in SOEF
- Fixes publish command bug on Windows
- Refactors constants usage throughout
- Adds support for profiling on aea run
- Multiple stability improvements to core async modules
- Multiple docs updates based on user feedback
- Multiple additional tests and test stability fixes

## 0.7.3 (2020-11-12)

- Extends AW AEAs
- Fixes overwriting of private key files on startup
- Fixes behaviour bugs
- Adds tests for tac participation skill
- Adds development setup guide
- Improves exception logging for easier debugging
- Fixes mixed mode in upgrade command
- Reduces verbosity of some CLI commands
- Multiple docs updates based on user feedback
- Multiple additional tests and test stability fixes

## 0.7.2 (2020-11-09)

- Fixes some AW2 AEAs
- Improves generic buyer AEA
- Fixes a few backwards incompatibilities on CLI (upgrade, add, fetch) introduced in 0.7.1
- Fixes geo locations in some tests
- Multiple docs updates based on user feedback
- Multiple additional tests and test stability fixes

## 0.7.1 (2020-11-05)

- Adds two AEAs for Agent World 2
- Refactors dialogue class to optimize for memory
- Refactors message class to optimize for memory
- Adds mixed registry mode to CLI and makes it default
- Extends upgrade command to automatically update references of non-vendor packages
- Adds deployment scripts for kubernetes
- Extends config set/get support for lists and dicts
- Fixes location specifiers throughout code base
- Imposes limits on length of user defined strings like author and package name
- Relaxes version specifiers for some dependencies
- Adds support for skills to reference connections as dependencies
- Makes ledger and currency ids configurable
- Adds test coverage for the tac control skills
- Improves quickstart guidance and adds docker images
- Multiple docs updates based on user feedback
- Multiple additional tests and test stability fixes

## 0.7.0 (2020-10-22)

- Adds two AEAs for Agent World 1
- Adds support to apply config overrides to CLI calls transfer and get-wealth
- Adds install scripts to install AEA and dependencies on all major OS (Windows, MacOs, Ubuntu)
- Adds developer mailing list opt-in step to CLI init
- Modifies custom configs in aea-config to use public id
- Adds all non-optional fields in aea-config by default
- Fixes upgrade command to properly handle dependencies of non-vendor packages
- Remove all distributed packages and add them to registry
- Adds public ids to all skill init files and makes it a requirement
- Adds primitive benchmarks for libp2p node
- Adds Prometheus monitoring to libp2p node
- Makes body a private attribute in message base class
- Renames bodyy to body in http protocol
- Adds support for abstract connections
- Refactors protobuf schemas for protocols to avoid code duplication
- Multiple docs updates based on user feedback
- Multiple additional tests and test stability fixes

## 0.6.3 (2020-10-16)

- Adds skill testing tools and documentation
- Adds human readable log output regarding configuration for p2p_libp2p connection
- Adds support to install PyPI dependencies from AEABuilder and MultiAgentManager
- Adds CLI upgrade command to upgrade entire agent project and components
- Extends CLI remove command to include option to remove dependencies
- Extends SOEF chain identifier support
- Adds CLI transfer command to transfer wealth
- Adds integration tests for skills generic buyer and seller using skill testing tool
- Adds validation of component configurations when setting componenet configuration overrides
- Multiple refactoring of internal configuration and helper objects and methods
- Fix a bug on CLI push local with latest rather than version specifier
- Adds readmes in all agent projects
- Adds agent name in logger paths of runnable objects
- Fixes tac skills to work with and without erc1155 contract
- Adds additional validations on message flow
- Multiple docs updates based on user feedback
- Multiple additional tests and test stability fixes

## 0.6.2 (2020-10-01)

- Adds MultiAgentManager to manage multiple agent projects programmatically
- Improves SOEF connection reliability on unregister
- Extends configuration classes to handle overriding configurations programmatically
- Improves configuration schemas and validations
- Fixes Multiplexer termination errors
- Allow finer-grained override of component configurations from aea-config
- Fixes tac controller to work with Ethereum contracts again
- Fixes multiple deploy and development scripts
- Introduces isort to development dependencies for automated import sorting
- Adds reset password command to CLI
- Adds support for abbreviated public ids (latest) to CLI and configurations
- Adds additional docstring linters for improved api documentation checks
- Multiple docs updates including additional explanations of ACN architecture
- Multiple additional tests and test stability fixes

## 0.6.1 (2020-09-17)

- Adds a standalone script to deploy an ACN node
- Adds filtering of out-dated addresses in DHT lookups
- Updates multiple developer scripts
- Increases code coverage of all protocols to 100%
- Fixes a disconnection issue of the multiplexer
- Extends soef connection to support additional registration commands and search responses
- Extends oef_search protocol to include success performative and agent info in search response
- Adds README.mds to all skills
- Adds configurable exception policy handling for multiplexer
- Fixes support for http headers in http server connection
- Adds additional consistency checks on addresses in dialogues
- Exposes decision maker address on skill context
- Adds comprehensive benchmark scripts
- Multiple docs updates including additional explanations of soef usage
- Multiple additional tests and test stability fixes

## 0.6.0 (2020-09-01)

- Makes FetchAICrypto default again
- Bumps web3 dependencies
- Introduces support for arbitrary protocol handling by DM
- Removes custom fields in signing protocol
- Refactors and updates dialogue and dialogues models
- Moves dialogue module to protocols module
- Introduces MultiplexerStatus to collect aggregate connection status
- Moves Address types from mail to common
- Updates FetchAICrypto to work with Agentland
- Fixes circular dependencies in helpers and configurations
- Unifies contract loading with loading mechanism of other packages
- Adds get-multiaddress command to CLI
- Updates helpers scripts
- Introduces MultiInbox to unify internal message handling
- Adds additional linters (eradicate, more pylint options)
- Improves error reporting in libp2p connection
- Replaces all assert statements with proper exceptions
- Adds skill id to envelope context for improved routing
- Refactors IPC pipes
- Refactors core dependencies
- Adds support for multi-page agent configurations
- Adds type field to all package configurations
- Multiple docs updates including additional explanations of contracts usage
- Multiple additional tests and test stability fixes

## 0.5.4 (2020-08-13)

- Adds support for Windows in p2p connections
- Makes all tests Windows compatible
- Adds integration tests for p2p public dht
- Modifies contract base class to make it cross-ledger compatible
- Changes dialogue reference nonce generation
- Fixes tac skills (non-contract versions)
- Fixes Aries identity skills
- Extends cosmos crypto api to support cosmwasm
- Adds full test coverage for framework and connection packages
- Multiple docs updates including automated link integrity checks
- Multiple additional tests and test stability fixes

## 0.5.3 (2020-08-05)

- Adds support for re-starting agent after stopping it
- Adds full test coverage for protocols generator
- Adds support for dynamically adding handlers
- Improves p2p connection startup reliability
- Addresses p2p connection race condition with long running processes
- Adds connection states in connections
- Applies consistent logger usage throughout
- Adds key rotation and randomised locations for integration tests
- Adds request delays in SOEF connection to avoid request limits
- Exposes runtime states on agent and removes agent liveness object
- Adds readme files in protocols and connections
- Improves edge case handling in dialogue models
- Adds support for cosmwasm message signing
- Adds test coverage for test tools
- Adds dialogues models in all connections where required
- Transitions erc1155 skills and simple search to SOEF and p2p
- Adds full test coverage for skills modules
- Multiple docs updates
- Multiple additional tests and test stability fixes

## 0.5.2 (2020-07-21)

- Transitions demos to agent-land test network, P2P and SOEF connections
- Adds full test coverage for helpers modules
- Adds full test coverage for core modules
- Adds CLI functionality to upload README.md files with packages
- Adds full test coverage for registries module
- Multiple docs updates
- Multiple additional tests and test stability fixes

## 0.5.1 (2020-07-14)

- Adds support for agent name being appended to all log statements
- Adds redesigned GUI
- Extends dialogue api for easier dialogue maintenance
- Resolves blocking logic in oef and gym connections
- Adds full test coverage on aea modules configurations, components and mail
- Adds ping background task for soef connection
- Adds full test coverage for all connection packages
- Multiple docs updates
- Multiple additional tests and test stability fixes

## 0.5.0 (2020-07-06)

- Refactors all connections to be fully async friendly
- Adds almost complete test coverage on connections
- Adds complete test coverage for cli and cli gui
- Fixes cli gui functionality and removes oef node dependency
- Refactors p2p go code and increases test coverage
- Refactors protocol generator for higher code reusability
- Adds option for skills to depend on other skills
- Adds abstract skills option
- Adds ledger connections to execute ledger related queries and transactions, removes ledger apis from skill context
- Adds contracts registry and removes them from skill context
- Rewrites all skills to be fully message based
- Replaces internal messages with protocols (signing and state update)
- Multiple refactoring to improve pylint adherence
- Multiple docs updates
- Multiple test stability fixes

## 0.4.1 (2020-06-15)

- Updates component package module loading for skill and connection
- Unifies component package loading across package types
- Adds connections registry to resources
- Upgrades CLI commands for easier programmatic usage
- Adds AEARunner and AEALauncher for programmatic launch of multiple agents
- Refactors AEABuilder to support re-entrancy and resetting
- Fixes tac packages to work with erc1155 contract
- Multiple refactoring to improve public and private access patterns
- Multiple docs updates
- Multiple test stability fixes

## 0.4.0 (2020-06-08)

- Updates message handling in skills
- Replaces serializer implementation; all serialization is now performed framework side
- Updates all skills for compatibility with new message handling
- Updates all protocols and protocol generator
- Updates package loading mechnanism
- Adds p2p_libp2p_client connection
- Fixes CLI bugs and refactors CLI
- Adds eject command to CLI
- Exposes identity and connection cryptos to all connections
- Updates connection loading mechanism
- Updates all connections for compatibility with new loading mechanism
- Extracts multiplexer into its own module
- Implements list all CLI command 
- Updates wallet to split into several crypto stores
- Refactors component registry and resources
- Extends soef connection functionality
- Implements AEABuilder reentrancy
- Updates p2p_libp2p connection
- Adds support for configurable runtime
- Refactors documentation
- Multiple docs updates
- Multiple test stability fixes

## 0.3.3 (2020-05-24)

- Adds option to pass ledger apis to aea builder
- Refactors decision maker: separates interface and implementation; adds loading mechanisms so framework users can provide their own implementation
- Adds async and sync agent loop implementations; agent can be run in both sync and async mode
- Completes transition to atomic cli commands (fetch, generate, scaffold)
- Refactors dialogue api: adds much simplified api; updates generator accordingly; updates skills
- Adds support for crypto module extensions: framework users can register their own crypto module
- Adds crypto module and ledger support for cosmos
- Adds simple-oef (soef) connection
- Adds p2p_libp2p connection for true p2p connectivity
- Adds pypi dependency consistency checks for aea projects
- Refactors cli for improved programmatic usage of components
- Adds skill exception handling policies and configuration options
- Adds comprehensive documentation of configuration files
- Multiple docs updates
- Multiple test stability fixes

## 0.3.2 (2020-05-07)

- Adds dialogue generation functionality to protocol generator
- Fixes add CLI commands to be atomic
- Adds Windows platform support
- Stability improvements to test pipeline
- Improves test coverage of CLI
- Implements missing doc tests
- Implements end-to-end tests for all skills
- Adds missing agent projects to registry
- Improves AEABuilder class for programmatic usage
- Exposes missing AEA configs on agent config file
- Extends Aries demo
- Adds method to check sdtout for test cases
- Adds code of conduct and security guidelines to repo
- Multiple docs updates
- Multiple additional unit tests
- Multiple additional minor fixes and changes

## 0.3.1 (2020-04-27)

- Adds p2p_stub connection
- Adds p2p_noise connection
- Adds webhook connection
- Upgrades error handling for error skill
- Fixes default timeout on main agent loop and provides setter in AEABuilder
- Adds multithreading support for launch command
- Provides support for kwargs to AEA constructor to be set on skill context
- Renames ConfigurationType with PackageType for consistency
- Provides a new AEATestCase class for improved testing
- Adds execution time limits for act/react calls
- TAC skills refactoring and contract integration
- Supports contract dependencies being added automatically
- Adds HTTP example skill
- Allows for skill inactivation during initialisation
- Improves error messages on skill loading errors
- Improves Readme, particularly for PyPI
- Adds support for Location based queries and descriptions
- Refactors skills tests to use AEATestCase
- Adds fingerprint and scaffold cli command for contract
- Adds multiple additional docs tests
- Makes task manager initialize pool lazily
- Multiple docs updates
- Multiple additional unit tests
- Multiple additional minor fixes and changes

## 0.3.0 (2020-04-02)

- Introduces IPFS based hashing of files to detect changes, ensure consistency and allow for content addressing
- Introduces aea fingerprint command to CLI
- Adds support for contract type packages which wrap smart contracts and their APIs
- Introduces AEABuilder class for much improved programmatic usage of the framework
- Moves protocol generator into alpha stage for light protocols
- Switches CLI to use remote registry by default
- Comprehensive documentation updates on new and existing features
- Additional demos to introduce the contracts functionality
- Protocol, Contract, Skill and Connection inherits from the same class, Component
- Improved APIs for Configuration classes
- All protocols now generated with protocol generator
- Multiple additional unit tests
- Multiple additional minor fixes and changes

## 0.2.4 (2020-03-25)

- Breaking change to all protocols as we transition to auto-generated protocols
- Fixes to protocol generator to move it to alpha status
- Updates to documentation on protocols and OEF search and communication nodes
- Improvements and fixes to AEA launch command
- Multiple docs updates and restructuring
- Multiple additional minor fixes and changes

## 0.2.3 (2020-03-19)

- Fixes stub connection file I/O
- Fixes OEF connection teardown
- Fixes CLI GUI subprocesses issues
- Adds support for URI based routing of envelopes
- Improves skill guide by adding a service provider agent
- Protocol generator bug fixes
- Add aea_version field to package yaml files for version management
- Multiple docs updates and restructuring
- Multiple additional minor fixes and changes

## 0.2.2 (2020-03-09)

- Fixes registry to only load registered packages
- Migrates default protocol to generator produced version
- Adds http connection and http protocol
- Adds cli init command for easier setting of author
- Refactoring and behind the scenes improvements to CLI
- Multiple docs updates
- Protocol generator improvements and fixes
- Adds cli launch command to launch multiple agents
- Increases test coverage for aea package and tests package
- Make project comply with PEP 518
- Multiple additional minor fixes and changes

## 0.2.1 (2020-02-21)

- Add minimal aea install
- Updates finite state machine behaviour to use any simple behaviour in states
- Adds example of programmatic and CLI based AEAs interacting
- Exposes the logger on the skill context
- Adds serialization (encoding/decoding) support to protocol generator
- Adds additional docs and videos
- Introduces test coverage to all code in docs
- Increases test coverage for aea package
- Multiple additional minor fixes and changes

## 0.2.0 (2020-02-07)

- Skills can now programmatically register behaviours
- Tasks are no longer a core component of the skill, the functor pattern is used
- Refactors the task manager
- Adds nonces to transaction data so transactions can be verified
- Adds documentation for the protocol generator
- Fixes several compatibility issues between CLI and registry
- Adds skills to connect a thermometer to an AEA
- Adds generic buyer and seller skills
- Adds much more documentation on AEA vs MVC frameworks, core components, new guides and more
- Removes the wallet from the agent constructor and moves it to the AEA constructor
- Allows behaviours to be initialized from a skill
- Adds multiple improvements to the protocol generator, including custom types and serialization
- Removes the default crypto object
- Replaces `SharedClass` with `Model` taxonomy for easier transition for web developers
- Adds bandit to CLI for security checks
- Makes private key paths in configs a dictionary so values can be set from CLI
- Introduces Identity object
- Increases test coverage
- Multiple additional minor fixes and changes

## 0.1.17 (2020-01-27)

- Add programmatic mode flag to AEA
- Introduces vendorized project structure
- Adds further tests for decision maker
- Upgrades sign transaction function for ethereum api proxy
- Adds black and bugbear to linters
- Applies public id usage throughout AEA business logic
- Adds guide on how to deploy an AEA on a raspberry pi
- Addresses multiple issues in the protocol generator
- Fixes aea config
- Adds CLI commands to create wealth and get wealth and address
- Change default author and license
- Adds guide on agent vs AEAs
- Updates docs and improves guides
- Adds support for inactivating skills programmatically
- Makes decision maker run in separate thread
- Multiple additional minor fixes and changes

## 0.1.16 (2020-01-12)

- Completes tac skills implementation
- Adds default ledger field to agent config
- Converts ledger apis to dictionary fields in agent config
- Introduces public ids to CLI and deprecate usage of package names only
- Adds local push and public commands to CLI
- Introduces ledger api abstract class
- Unifies import paths for static and dynamic imports
- Disambiguates import paths by introducing pattern of `packages.author.package_type_pluralized.package_name`
- Adds agent directory to packages with some samples
- Adds protocol generator and exposes on CLI
- Removes unused config fields
- Updates docs to align with recent changes
- Adds additional tests on CLI
- Multiple additional minor fixes and changes

## 0.1.15 (2019-12-19)

- Moves non-default packages from aea to packages directory
- Supports get & set on package configs
- Changes skill configuration resource types from lists to dictionaries
- Adds additional features to decision maker
- Refactors most protocols and improves their API
- Removes multiple unintended side-effects of the CLI
- Improves dependency referencing in config files
- Adds push and publish functionality to CLI
- Introduces simple and composite behaviours and applies them in skills
- Adds URI to envelopes
- Adds guide for programmatic assembly of an AEA
- Adds guide on agent-oriented development
- Multiple minor doc updates
- Adds additional tests
- Multiple additional minor fixes and changes

## 0.1.14 (2019-11-29)

- Removes dependency on OEF SDK's FIPA API
- Replaces dialogue id with dialogue references
- Improves CLI logging and list/search command output
- Introduces multiplexer and removes mailbox
- Adds much improved tac skills
- Adds support for CLI integration with registry
- Increases test coverage to 99%
- Introduces integration tests for skills and examples
- Adds support to run multiple connections from CLI
- Updates the docs and adds uml diagrams
- Multiple additional minor fixes and changes

## 0.1.13 (2019-11-08)

- Adds envelope serializer
- Adds support for programmatically initializing an AEA
- Adds some tests for the gui and other components
- Exposes connection status to skills
- Updates oef connection to re-establish dropped connections
- Updates the car park agent
- Multiple additional minor fixes and changes

## 0.1.12 (2019-11-01)

- Adds TCP connection (server and client)
- Fixes some examples and docs
- Refactors crypto modules and adds additional tests
- Multiple additional minor fixes and changes

## 0.1.11 (2019-10-30)

- Adds python3.8 test coverage
- Adds almost complete test coverage on aea package
- Adds filter concept for message routing
- Adds ledger integrations for fetch.ai and ethereum
- Adds carpark examples and ledger examples
- Multiple additional minor fixes and changes

## 0.1.10 (2019-10-19)

- Compatibility fixes for Ubuntu and Windows platforms
- Multiple additional minor fixes and changes

## 0.1.9 (2019-10-18)

- Stability improvements
- Higher test coverage, including on Python 3.6
- Multiple additional minor fixes and changes

## 0.1.8 (2019-10-18)

- Multiple bug fixes and improvements to gui of cli
- Adds full test coverage on cli
- Improves docs
- Multiple additional minor fixes and changes

## 0.1.7 (2019-10-14)

- Adds gui to interact with cli
- Adds new connection stub to read from/write to file
- Adds ledger entities (fetchai and ethereum); creates wallet for ledger entities
- Adds more documentation and fixes old one
- Multiple additional minor fixes and changes

## 0.1.6 (2019-10-04)

- Adds several new skills
- Extended docs on framework and skills
- Introduces core framework components like decision maker and shared classes
- Multiple additional minor fixes and changes

## 0.1.5 (2019-09-26)

- Adds scaffolding command to the CLI tool
- Extended docs
- Increased test coverage
- Multiple additional minor fixes and changes


## 0.1.4 (2019-09-20)

- Adds cli functionality to add connections
- Multiple additional minor fixes and changes

## 0.1.3 (2019-09-19)

- Adds Jenkins for CI
- Adds docker develop image
- Parses dependencies of connections/protocols/skills on the fly
- Adds validations of config files
- Adds first two working skills and fixes gym examples
- Adds docs
- Multiple additional minor fixes and changes

## 0.1.2 (2019-09-16)

- Adds aea cli tool.
- Adds aea skills framework.
- Introduces static typing checks across aea, using Mypy.
- Extends gym example

## 0.1.1 (2019-09-04)

- Provides examples and fixes.

## 0.1.0 (2019-08-21)

- Initial release of the package.
