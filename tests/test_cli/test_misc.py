# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""This test module contains the tests for the `aea` sub-commands."""

import aea
from aea.cli import cli

from tests.conftest import CliRunner


def test_no_argument():
    """Test that if we run the cli tool without arguments, it exits gracefully."""
    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert result.exit_code == 0


def test_flag_version():
    """Test that the flag '--version' works correctly."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.stdout == "aea, version {}\n".format(aea.__version__)


def test_flag_help():
    """Test that the flag '--help' works correctly."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert (
        result.stdout
        == """Usage: aea [OPTIONS] COMMAND [ARGS]...

  Command-line tool for setting up an Autonomous Economic Agent (AEA).

Options:
  --version                     Show the version and exit.
  -v, --verbosity LVL           One of NOTSET, DEBUG, INFO, WARNING, ERROR,
                                CRITICAL, OFF
  -s, --skip-consistency-check  Skip consistency checks of agent during command
                                execution.
  --registry-path DIRECTORY     Provide a local registry directory full path.
  --help                        Show this message and exit.

Commands:
  add                     Add a package to the agent.
  add-key                 Add a private key to the wallet of the agent.
  build                   Build the agent and its components.
  check-packages          Run different checks on AEA packages.
  config                  Read or modify a configuration of the agent.
  create                  Create a new agent.
  delete                  Delete an agent.
  eject                   Eject a vendor package of the agent.
  fetch                   Fetch an agent from the registry.
  fingerprint             Fingerprint a non-vendor package of the agent.
  freeze                  Get the dependencies of the agent.
  generate                Generate a package for the agent.
  generate-all-protocols  Generate all protocols.
  generate-key            Generate a private key and place it in a file.
  generate-wealth         Generate wealth for the agent on a test network.
  get-address             Get the address associated with a private key of...
  get-multiaddress        Get the multiaddress associated with a private...
  get-public-key          Get the public key associated with a private key...
  get-wealth              Get the wealth associated with the private key of...
  hash                    Hashing utils.
  init                    Initialize your AEA configurations.
  install                 Install the dependencies of the agent.
  ipfs                    IPFS Commands
  issue-certificates      Issue certificates for connections that require...
  launch                  Launch many agents at the same time.
  list                    List the installed packages of the agent.
  local-registry-sync     Upgrade the local package registry.
  login                   Login to the registry account.
  logout                  Logout from the registry account.
  packages                Local package manager.
  publish                 Publish the agent to the registry.
  push                    Push a non-vendor package of the agent to the...
  push-all                Push all available packages to a registry.
  register                Create a new registry account.
  remove                  Remove a package from the agent.
  remove-key              Remove a private key from the wallet of the agent.
  reset_password          Reset the password of the registry account.
  run                     Run the agent.
  scaffold                Scaffold a package for the agent.
  search                  Search for packages in the registry.
  test                    Run tests of an AEA project.
  transfer                Transfer wealth associated with a private key of...
  upgrade                 Upgrade the packages of the agent.
"""
    )
