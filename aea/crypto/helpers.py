# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Module wrapping the helpers of public and private key cryptography."""
from typing import cast

from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
import logging
from pathlib import Path

from fetchai.ledger.crypto import Entity  # type: ignore
from eth_account import Account  # type: ignore

from aea.crypto.default import DefaultCrypto, DEFAULT
from aea.crypto.ethereum import ETHEREUM
from aea.crypto.fetchai import FETCHAI
from aea.crypto.wallet import SUPPORTED_CRYPTOS, SUPPORTED_LEDGER_APIS
from aea.configurations.loader import ConfigLoader
from aea.configurations.base import AgentConfig, DEFAULT_AEA_CONFIG_FILE, PrivateKeyPathConfig, LedgerAPIConfig
from aea.cli.common import Context

DEFAULT_PRIVATE_KEY_FILE = 'default_private_key.pem'
FETCHAI_PRIVATE_KEY_FILE = 'fet_private_key.txt'
ETHEREUM_PRIVATE_KEY_FILE = 'eth_private_key.txt'

logger = logging.getLogger(__name__)


def _verify_or_create_private_keys(ctx: Context) -> None:
    """
    Verify or create private keys.

    :param ctx: Context
    """
    path = Path(DEFAULT_AEA_CONFIG_FILE)
    agent_loader = ConfigLoader("aea-config_schema.json", AgentConfig)
    fp = open(str(path), mode="r", encoding="utf-8")
    aea_conf = agent_loader.load(fp)

    for identifier, value in aea_conf.private_key_paths.read_all():
        if identifier not in SUPPORTED_CRYPTOS:
            ValueError("Unsupported identifier in private key paths.")

    default_private_key_config = aea_conf.private_key_paths.read(DEFAULT)
    if default_private_key_config is None:
        default_private_key_path = _create_temporary_private_key_pem_path()
        default_private_key_config = PrivateKeyPathConfig(DEFAULT, default_private_key_path)
        aea_conf.private_key_paths.create(default_private_key_config.ledger, default_private_key_config)
    else:
        default_private_key_config = cast(PrivateKeyPathConfig, default_private_key_config)
        try:
            _try_validate_private_key_pem_path(default_private_key_config.path)
        except FileNotFoundError:
            logger.error("File {} for private key {} not found.".format(repr(default_private_key_config.path), default_private_key_config.ledger))
            exit(-1)

    fetchai_private_key_config = aea_conf.private_key_paths.read(FETCHAI)
    if fetchai_private_key_config is None:
        path = Path(FETCHAI_PRIVATE_KEY_FILE)
        entity = Entity()
        with open(path, "w+") as file:
            file.write(entity.private_key_hex)
        fetchai_private_key_path = FETCHAI_PRIVATE_KEY_FILE
        fetchai_private_key_config = PrivateKeyPathConfig(FETCHAI, fetchai_private_key_path)
        aea_conf.private_key_paths.create(fetchai_private_key_config.ledger, fetchai_private_key_config)
    else:
        fetchai_private_key_config = cast(PrivateKeyPathConfig, fetchai_private_key_config)
        try:
            _try_validate_fet_private_key_path(fetchai_private_key_config.path)
        except FileNotFoundError:
            logger.error("File {} for private key {} not found.".format(repr(fetchai_private_key_config.path), fetchai_private_key_config.ledger))
            exit(-1)

    ethereum_private_key_config = aea_conf.private_key_paths.read(ETHEREUM)
    if ethereum_private_key_config is None:
        path = Path(ETHEREUM_PRIVATE_KEY_FILE)
        account = Account.create()
        with open(path, "w+") as file:
            file.write(account.privateKey.hex())
        ethereum_private_key_path = ETHEREUM_PRIVATE_KEY_FILE
        ethereum_private_key_config = PrivateKeyPathConfig(ETHEREUM, ethereum_private_key_path)
        aea_conf.private_key_paths.create(ethereum_private_key_config.ledger, ethereum_private_key_config)
    else:
        ethereum_private_key_config = cast(PrivateKeyPathConfig, ethereum_private_key_config)
        try:
            _try_validate_ethereum_private_key_path(ethereum_private_key_config.path)
        except FileNotFoundError:
            logger.error("File {} for private key {} not found.".format(repr(ethereum_private_key_config.path), ethereum_private_key_config.ledger))
            exit(-1)

    # update aea config
    path = Path(DEFAULT_AEA_CONFIG_FILE)
    fp = open(str(path), mode="w", encoding="utf-8")
    agent_loader.dump(aea_conf, fp)
    ctx.agent_config = aea_conf


def _verify_ledger_apis_access(ctx: Context) -> None:
    """
    Verify access to ledger apis.

    :param ctx: Context
    """
    path = Path(DEFAULT_AEA_CONFIG_FILE)
    agent_loader = ConfigLoader("aea-config_schema.json", AgentConfig)
    fp = open(str(path), mode="r", encoding="utf-8")
    aea_conf = agent_loader.load(fp)

    for identifier, value in aea_conf.ledger_apis.read_all():
        if identifier not in SUPPORTED_LEDGER_APIS:
            ValueError("Unsupported identifier in ledger apis.")

    fetchai_ledger_api_config = aea_conf.ledger_apis.read(FETCHAI)
    if fetchai_ledger_api_config is None:
        logger.debug("No fetchai ledger api config specified.")
    else:
        fetchai_ledger_api_config = cast(LedgerAPIConfig, fetchai_ledger_api_config)
        try:
            from fetchai.ledger.api import LedgerApi
            LedgerApi(fetchai_ledger_api_config.addr, fetchai_ledger_api_config.port)
        except Exception:
            logger.error("Cannot connect to fetchai ledger with provided config.")
            exit(-1)

    ethereum_ledger_config = aea_conf.ledger_apis.read(ETHEREUM)
    if ethereum_ledger_config is None:
        logger.debug("No ethereum ledger api config specified.")
    else:
        ethereum_ledger_config = cast(LedgerAPIConfig, ethereum_ledger_config)
        try:
            from web3 import Web3, HTTPProvider     # type: ignore
            Web3(HTTPProvider(ethereum_ledger_config.addr))
        except Exception:
            logger.error("Cannot connect to ethereum ledger with provided config.")
            exit(-1)


def _create_temporary_private_key() -> bytes:
    """
    Create a temporary private key.

    :return: the private key in pem format.
    """
    crypto = DefaultCrypto()
    pem = crypto._private_key.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption())  # type: ignore
    return pem


def _try_validate_private_key_pem_path(private_key_pem_path: str) -> None:
    """
    Try to validate a private key.

    :param private_key_pem_path: the path to the private key.
    :return: None
    :raises: an exception if the private key is invalid.
    """
    try:
        DefaultCrypto(private_key_pem_path=private_key_pem_path)
    except ValueError:
        logger.error("This is not a valid private key file: '{}'".format(private_key_pem_path))
        exit(-1)


def _try_validate_fet_private_key_path(private_key_path: str) -> None:
    """
    Try to validate a private key.

    :param private_key_path: the path to the private key.
    :return: None
    :raises: an exception if the private key is invalid.
    """
    try:
        with open(private_key_path, "r") as key:
            data = key.read()
            Entity.from_hex(data)
    except ValueError:
        logger.error("This is not a valid private key file: '{}'".format(private_key_path))
        exit(-1)


def _try_validate_ethereum_private_key_path(private_key_path: str) -> None:
    """
    Try to validate a private key.

    :param private_key_path: the path to the private key.
    :return: None
    :raises: an exception if the private key is invalid.
    """
    try:
        with open(private_key_path, "r") as key:
            data = key.read()
            Account.from_key(data)
    except ValueError:
        logger.error("This is not a valid private key file: '{}'".format(private_key_path))
        exit(-1)


def _create_temporary_private_key_pem_path() -> str:
    """
    Create a temporary private key and path to the file.

    :return: private_key_pem_path
    """
    pem = _create_temporary_private_key()
    file = open(DEFAULT_PRIVATE_KEY_FILE, "wb")
    file.write(pem)
    file.close()
    return DEFAULT_PRIVATE_KEY_FILE
