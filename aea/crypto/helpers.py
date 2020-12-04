# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
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

"""Module wrapping the helpers of public and private key cryptography."""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

from aea.configurations.base import AgentConfig, PackageType
from aea.configurations.constants import (
    DEFAULT_AEA_CONFIG_FILE,
    PRIVATE_KEY_PATH_SCHEMA,
)
from aea.configurations.loader import ConfigLoaders
from aea.crypto.registries import crypto_registry, make_crypto, make_faucet_api


_default_logger = logging.getLogger(__name__)


def verify_or_create_private_keys(
    aea_project_path: Path, exit_on_error: bool = True,
) -> AgentConfig:
    """
    Verify or create private keys.

    :param aea_project_path: path to an AEA project.
    :param exit_on_error: whether we should exit the program on error.
    :return: the agent configuration.
    """
    path_to_aea_config = aea_project_path / DEFAULT_AEA_CONFIG_FILE
    agent_loader = ConfigLoaders.from_package_type(PackageType.AGENT)
    fp = path_to_aea_config.open(mode="r", encoding="utf-8")
    aea_conf = agent_loader.load(fp)

    for identifier, _ in aea_conf.private_key_paths.read_all():
        if identifier not in crypto_registry.supported_ids:  # pragma: nocover
            raise ValueError(
                "Unsupported identifier `{}` in private key paths. Supported identifiers: {}.".format(
                    identifier, sorted(crypto_registry.supported_ids)
                )
            )

    for identifier in crypto_registry.supported_ids:
        config_private_key_path = aea_conf.private_key_paths.read(identifier)
        if config_private_key_path is None:
            private_key_path = PRIVATE_KEY_PATH_SCHEMA.format(identifier)
            if identifier == aea_conf.default_ledger:  # pragma: nocover
                if os.path.exists(private_key_path):
                    raise ValueError(
                        "File {} for private key {} already exists. Add to aea-config.yaml.".format(
                            repr(config_private_key_path), identifier
                        )
                    )
                create_private_key(
                    identifier,
                    private_key_file=str(aea_project_path / private_key_path),
                )
                aea_conf.private_key_paths.update(identifier, private_key_path)
        else:
            try:
                try_validate_private_key_path(
                    identifier,
                    str(aea_project_path / config_private_key_path),
                    exit_on_error=exit_on_error,
                )
            except FileNotFoundError:  # pragma: no cover
                raise ValueError(
                    "File {} for private key {} not found.".format(
                        repr(config_private_key_path), identifier,
                    )
                )

    # update aea config
    fp = path_to_aea_config.open(mode="w", encoding="utf-8")
    agent_loader.dump(aea_conf, fp)
    return aea_conf


def try_validate_private_key_path(
    ledger_id: str, private_key_path: str, exit_on_error: bool = True
) -> None:
    """
    Try validate a private key path.

    :param ledger_id: one of 'fetchai', 'ethereum'
    :param private_key_path: the path to the private key.
    :return: None
    :raises: ValueError if the identifier is invalid.
    """
    try:
        # to validate the file, we just try to create a crypto object
        # with private_key_path as parameter
        make_crypto(ledger_id, private_key_path=private_key_path)
    except Exception as e:  # pylint: disable=broad-except  # thats ok, will exit or reraise
        error_msg = "This is not a valid private key file: '{}'\n Exception: '{}'".format(
            private_key_path, e
        )
        if exit_on_error:
            _default_logger.exception(error_msg)  # show exception traceback on exit
            sys.exit(1)
        else:  # pragma: no cover
            _default_logger.error(error_msg)
            raise


def create_private_key(ledger_id: str, private_key_file: str) -> None:
    """
    Create a private key for the specified ledger identifier.

    :param ledger_id: the ledger identifier.
    :param private_key_file: the private key file.
    :return: None
    :raises: ValueError if the identifier is invalid.
    """
    crypto = make_crypto(ledger_id)
    crypto.dump(open(private_key_file, "wb"))


def try_generate_testnet_wealth(
    identifier: str, address: str, url: Optional[str] = None, _sync: bool = True
) -> None:
    """
    Try generate wealth on a testnet.

    :param identifier: the identifier of the ledger
    :param address: the address to check for
    :param url: the url
    :param _sync: whether to wait to sync or not; currently unused
    :return: None
    """
    faucet_api = make_faucet_api(identifier)
    if faucet_api is not None:
        faucet_api.get_wealth(address, url)
