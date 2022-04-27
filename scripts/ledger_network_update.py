#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2022 Fetch.AI Limited
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
"""Setup script to update ledger network."""
import re
from pathlib import Path
from typing import Optional

import click  # type: ignore


ROOT_DIR = Path(__file__).parent / "../"

AEA_LEDGER_MODULE_FILE = ROOT_DIR / "aea/crypto/ledger_apis.py"
FETCHAI_LEDGER_FILE = (
    ROOT_DIR / "plugins/aea-ledger-fetchai/aea_ledger_fetchai/fetchai.py"
)
LEDGER_INTEGRATION_MD = ROOT_DIR / "docs/ledger-integration.md"


class NetworkConfig:
    """Ledger network configuration data class."""

    net_name: str
    chain_id: str
    denom: str
    rest_api_address: str
    rpc_api_address: str
    faucet_url: Optional[str]
    explorer_url: Optional[str]

    def __init__(
        self,
        net_name: str,
        chain_id: str,
        denom: str,
        rest_api_address: str,
        rpc_api_address: str,
        faucet_url: Optional[str] = None,
        explorer_url: Optional[str] = None,
    ):
        """
        Set network config.

        :param net_name: str
        :param chain_id: str
        :param denom: str
        :param rest_api_address: str
        :param rpc_api_address: str
        :param faucet_url: optional str
        :param explorer_url: optional str
        """
        self.net_name = net_name
        self.chain_id = chain_id
        self.denom = denom
        self.rest_api_address = rest_api_address
        self.rpc_api_address = rpc_api_address
        self.faucet_url = faucet_url or self.make_faucet_url(net_name)
        self.explorer_url = explorer_url or self.make_explorer_url(net_name)

    @staticmethod
    def make_faucet_url(net_name) -> str:
        """Make default faucet url based on net name."""
        return f"https://faucet-{net_name}.t-v2-london-c.fetch-ai.com"

    @staticmethod
    def make_explorer_url(net_name) -> str:
        """Make default explorer url based on net name."""
        return f"https://explore-{net_name}.fetch.ai"

    def __str__(self) -> str:
        """Return lines of network configration to be printed."""
        return (
            f"Net name: {self.net_name}\n"
            f"Chain id: {self.chain_id}\n"
            f"Denom: {self.denom}\n"
            f"REST API address: {self.rest_api_address}\n"
            f"RPC address: {self.rpc_api_address}\n"
            f"Testnet faucet address: {self.faucet_url}\n"
            f"Block explorer address: {self.explorer_url}\n"
        )


def _get_value(variable_name: str, text: str) -> str:
    m = re.search(fr'{variable_name} = "(.*)"', text, re.MULTILINE)
    if m:
        return m.groups()[0]
    raise ValueError("Value not found")


class NetworkUpdate:
    """Ledger network update tool."""

    cur_config: NetworkConfig
    new_config: NetworkConfig
    cosmpy_version: str

    @staticmethod
    def get_current_config() -> NetworkConfig:
        """
        Get current ledger network configuration.

        :return: NetworkConfig instance
        """
        code_text = FETCHAI_LEDGER_FILE.read_text()

        rest_api_addr = _get_value("DEFAULT_ADDRESS", code_text)
        chain_id = _get_value("DEFAULT_CHAIN_ID", code_text)
        denom = _get_value("DEFAULT_CURRENCY_DENOM", code_text)
        faucet_url = _get_value("FETCHAI_TESTNET_FAUCET_URL", code_text)

        m = re.match(r"https://rest-(\w+).fetch.ai:443", rest_api_addr)
        if not m:
            raise ValueError(
                f"can not determine network name from address: {rest_api_addr}"
            )
        net_name = m.groups()[0]

        rpc_api_addr = f"https://rpc-{net_name}.fetch.ai:443"

        m = re.search(
            r'\| Block Explorer \| <a href="(.*)" target=',
            LEDGER_INTEGRATION_MD.read_text(),
            re.MULTILINE,
        )
        if not m:
            raise ValueError(f"REGEX search failed for {LEDGER_INTEGRATION_MD}")
        explorer_url = m.groups()[0]

        return NetworkConfig(
            net_name=net_name,
            chain_id=chain_id,
            denom=denom,
            rest_api_address=rest_api_addr,
            rpc_api_address=rpc_api_addr,
            faucet_url=faucet_url,
            explorer_url=explorer_url,
        )

    def get_new_config(self) -> NetworkConfig:
        """
        Get new ledger network configuration.

        :return: NetworkConfig instance
        """
        net_name = click.prompt(
            "Enter the new network name", default=self.cur_config.net_name
        )
        chain_id = f"{net_name}-1"
        chain_id = click.prompt("Enter the new chain id", default=chain_id)
        denom = "atestfet"
        denom = click.prompt("Enter the new denomination", default=denom)
        rpc_api_addr = f"https://rpc-{net_name}.fetch.ai:443"
        rpc_api_addr = click.prompt("Enter the new rpc address", default=rpc_api_addr)
        rest_api_addr = f"https://rest-{net_name}.fetch.ai:443"
        rest_api_addr = click.prompt(
            "Enter the new rest api address", default=rest_api_addr
        )
        explorer_url = NetworkConfig.make_explorer_url(net_name)
        explorer_url = click.prompt(
            "Enter the new explorer address", default=explorer_url
        )
        faucet_url = NetworkConfig.make_faucet_url(net_name)
        faucet_url = click.prompt(
            "Enter the new testnet faucet address", default=faucet_url
        )

        return NetworkConfig(
            net_name=net_name,
            chain_id=chain_id,
            denom=denom,
            rest_api_address=rest_api_addr,
            rpc_api_address=rpc_api_addr,
            faucet_url=faucet_url,
            explorer_url=explorer_url,
        )

    @staticmethod
    def get_current_cosmpy_version() -> str:
        """
        Get currect cosmpy version from fetch ledger plugin.

        :return: str
        """
        plugin_setup_py = ROOT_DIR / "plugins/aea-ledger-fetchai/setup.py"

        for i in plugin_setup_py.read_text().splitlines():
            m = re.search('"cosmpy(.*)"', i)
            if m:
                return m.groups()[0]
        raise ValueError("Can not determine current cosmpy version")

    def get_cosmpy_version(self):
        """
        Get new cosmpy version to apply.

        :return: str
        """

        cur_version = self.get_current_cosmpy_version()
        return click.prompt(
            "Enter cosmpy version (pip style, >=0.2.0)", default=cur_version
        )

    def run(self):
        """Do update."""
        self.cur_config = self.get_current_config()
        click.echo("Current network config:")
        click.echo(self.cur_config)

        self.cosmpy_version = self.get_cosmpy_version()
        click.echo("")
        self.new_config = self.get_new_config()

        click.echo("\n\n------------")
        click.echo("New network config:")
        click.echo(self.new_config)
        click.echo(f"cosmpy version is cosmpy{self.cosmpy_version}")
        click.echo()
        if not click.confirm("Do you want to continue?"):
            click.echo("Exit")
            return
        click.echo("Do the update")
        self.update_protobuf()
        self.update_spelling()
        self.update_cosmpy_version()

        self.update_docs()
        self.update_conftest()
        self.update_packages()
        self.update_plugins()
        self.update_aea_ledger_crypto()

        self.print_footer()

    @staticmethod
    def update_protobuf():
        """Update protobuf dependency."""
        click.echo("protobuf is not updating at the moment")

    def update_spelling(self):
        """Add network name to spelling file."""
        click.echo("Add network name to spelling")
        spelling = ROOT_DIR / ".spelling"
        spelling.write_text(
            spelling.read_text()
            + f"\n{self.new_config.net_name}\n{self.new_config.chain_id}"
        )

    def update_cosmpy_version(self):
        """Set new cosmpy version."""
        click.echo("Update cosmpy version")
        # pipenv
        pipenv = ROOT_DIR / "Pipfile"
        pipenv.write_text(
            re.sub(
                'cosmpy = ".*"', f'cosmpy = "{self.cosmpy_version}"', pipenv.read_text()
            )
        )
        # aea ledger fetchai plugin
        plugin_setup_py = ROOT_DIR / "plugins/aea-ledger-fetchai/setup.py"
        plugin_setup_py.write_text(
            re.sub(
                '"cosmpy.*"',
                f'"cosmpy{self.cosmpy_version}"',
                plugin_setup_py.read_text(),
            )
        )

        # aea ledger cosmos plugin
        plugin_setup_py = ROOT_DIR / "plugins/aea-ledger-cosmos/setup.py"
        plugin_setup_py.write_text(
            re.sub(
                '"cosmpy.*"',
                f'"cosmpy{self.cosmpy_version}"',
                plugin_setup_py.read_text(),
            )
        )

        # tox
        tox_file = ROOT_DIR / "tox.ini"
        tox_file.write_text(
            re.sub("cosmpy.*", f"cosmpy{self.cosmpy_version}", tox_file.read_text())
        )

    def update_aea_ledger_crypto(self):
        """Update aea/ledger/crypto.py with new defaults."""
        click.echo("Update aea/ledger/crypto.py")
        content = AEA_LEDGER_MODULE_FILE.read_text()

        content = content.replace(
            f'FETCHAI_DEFAULT_ADDRESS = "{self.cur_config.rest_api_address}"',
            f'FETCHAI_DEFAULT_ADDRESS = "{self.new_config.rest_api_address}"',
        )
        content = content.replace(
            f'FETCHAI_DEFAULT_CURRENCY_DENOM = "{self.cur_config.denom}"',
            f'FETCHAI_DEFAULT_CURRENCY_DENOM = "{self.new_config.denom}"',
        )
        content = content.replace(
            f'FETCHAI_DEFAULT_CHAIN_ID = "{self.cur_config.chain_id}"',
            f'FETCHAI_DEFAULT_CHAIN_ID = "{self.new_config.chain_id}"',
        )

        AEA_LEDGER_MODULE_FILE.write_text(content)

    def update_docs(self):
        """Update documentation."""
        click.echo("Update docs")
        docs_files = (ROOT_DIR / "docs").glob("**/*.md")
        for f in docs_files:
            content = f.read_text()
            content = content.replace(
                self.cur_config.explorer_url, self.new_config.explorer_url,
            )
            content = content.replace(
                f"Fetch.ai `{self.cur_config.net_name.capitalize()}`",
                f"Fetch.ai `{self.new_config.net_name.capitalize()}`",
            )
            content = content.replace(
                f"Fetchai {self.cur_config.net_name.capitalize()} or a local Ganache ",
                f"Fetchai {self.new_config.net_name.capitalize()} or a local Ganache ",
            )

            content = content.replace(
                f"{self.cur_config.net_name.capitalize()} block explorer",
                f"{self.new_config.net_name.capitalize()} block explorer",
            )

            content = content.replace(
                f"{self.cur_config.net_name.capitalize()} block explorer",
                f"{self.new_config.net_name.capitalize()} block explorer",
            )

            content = content.replace(
                f"{self.cur_config.net_name.capitalize()} testnet",
                f"{self.new_config.net_name.capitalize()} testnet",
            )

            content = content.replace(
                f"| Chain ID       | {self.cur_config.chain_id}",
                f"| Chain ID       | {self.new_config.chain_id}",
            )
            content = content.replace(
                f"| RPC Endpoint   | {self.cur_config.rpc_api_address}",
                f"| RPC Endpoint   | {self.new_config.rpc_api_address}",
            )

            content = content.replace(
                f"| REST Endpoint  | {self.cur_config.rest_api_address}",
                f"| REST Endpoint  | {self.new_config.rest_api_address}",
            )
            f.write_text(content)

    def update_conftest(self):
        """Update tests/conftest.py."""
        click.echo("Update tests/conftest.py")
        f = ROOT_DIR / "tests/conftest.py"
        content = f.read_text()
        content = content.replace(
            f'DEFAULT_FETCH_ADDR_REMOTE = "{self.cur_config.rest_api_address}"',
            f'DEFAULT_FETCH_ADDR_REMOTE = "{self.new_config.rest_api_address}"',
        )
        content = content.replace(
            f'DEFAULT_FETCH_CHAIN_ID = "{self.cur_config.chain_id}"',
            f'DEFAULT_FETCH_CHAIN_ID = "{self.new_config.chain_id}"',
        )
        f.write_text(content)

    def update_packages(self):
        """Update packages."""
        click.echo("Update packages")
        configs_files = (ROOT_DIR / "packages").glob("**/*.yaml")
        for f in configs_files:
            content = f.read_text()
            content = content.replace(
                f"address: {self.cur_config.rest_api_address}",
                f"address: {self.new_config.rest_api_address}",
            )
            content = content.replace(
                f"chain_id: {self.cur_config.chain_id}",
                f"chain_id: {self.new_config.chain_id}",
            )
            f.write_text(content)

    def update_plugins(self):
        """Update plugins."""
        click.echo("Update plugins")
        files = (ROOT_DIR / "plugins").glob("**/*.py")
        for f in files:
            content = f.read_text()
            content = content.replace(
                f'DEFAULT_CHAIN_ID = "{self.cur_config.chain_id}"',
                f'DEFAULT_CHAIN_ID = "{self.new_config.chain_id}"',
            )

            content = content.replace(
                f'DEFAULT_ADDRESS = "{self.cur_config.rest_api_address}"',
                f'DEFAULT_ADDRESS = "{self.new_config.rest_api_address}"',
            )
            content = content.replace(
                f'FETCHAI_DEFAULT_CHAIN_ID = "{self.cur_config.chain_id}"',
                f'FETCHAI_DEFAULT_CHAIN_ID = "{self.new_config.chain_id}"',
            )

            content = content.replace(
                f'FETCHAI_DEFAULT_ADDRESS = "{self.cur_config.rest_api_address}"',
                f'FETCHAI_DEFAULT_ADDRESS = "{self.new_config.rest_api_address}"',
            )

            content = content.replace(
                f'FETCHAI_TESTNET_FAUCET_URL = "{self.cur_config.faucet_url}"',
                f'FETCHAI_TESTNET_FAUCET_URL = "{self.new_config.faucet_url}"',
            )

            content = content.replace(
                f'"chain_id": "{self.cur_config.chain_id}"',
                f'"chain_id": "{self.new_config.chain_id}"',
            )

            f.write_text(content)

    @staticmethod
    def print_footer():
        """Print footer after everything was done."""
        click.echo("Update completed!")
        click.echo("Please check wasm files are correct")


if __name__ == "__main__":
    NetworkUpdate().run()
