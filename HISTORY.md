# Release History

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
