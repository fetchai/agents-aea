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
"""Run an ACN libp2p node without requiring the agents framework."""

import argparse
import os
import subprocess  # nosec
import sys
from binascii import unhexlify
from typing import Dict, List, Optional

# following imports needed only if checks are enabled  # isort:skip
from base58 import b58decode
from ecdsa import SigningKey, curves
from multihash import decode as multihashdecode  # type: ignore


class AcnNodeConfig:
    """Store the configuration of an acn node as a dictionary."""

    KEY = "AEA_P2P_ID"
    URI = "AEA_P2P_URI"
    EXTERNAL_URI = "AEA_P2P_URI_PUBLIC"
    DELEGATE_URI = "AEA_P2P_DELEGATE_URI"
    MONITORING_URI = "AEA_P2P_URI_MONITORING"
    ENTRY_PEERS_MADDRS = "AEA_P2P_ENTRY_URIS"
    IPC_IN = "AEA_TO_NODE"
    IPC_OUT = "NODE_TO_AEA"
    AEA_ADDRESS = "AEA_AGENT_ADDR"
    ACN_LOG_FILE = "ACN_LOG_FILE"
    LIST_SEPARATOR = ","

    def __init__(
        self,
        key: str,
        uri: str,
        external_uri: Optional[str] = None,
        delegate_uri: Optional[str] = None,
        monitoring_uri: Optional[str] = None,
        entry_peers_maddrs: Optional[List[str]] = None,
        log_file: Optional[str] = None,
        enable_checks: bool = True,
    ):
        """
        Initialize a new ACN configuration from arguments

        :param key: node private key to use as identity
        :param uri: node local uri to bind to
        :param external_uri: node external uri, needed to be reached by others
        :param delegate_uri: node local uri for delegate service
        :param monitoring_uri: node monitoring uri
        :param entry_peers_maddrs: multiaddresses of peers to join their network
        :param log_file: path to log file, opened in append mode
        :param enable_checks: to check if provided configuration is valid
        """
        self.config: Dict[str, str] = dict()

        self.config[AcnNodeConfig.KEY] = key
        self.config[AcnNodeConfig.URI] = uri
        self.config[AcnNodeConfig.EXTERNAL_URI] = (
            external_uri if external_uri is not None else ""
        )
        self.config[AcnNodeConfig.DELEGATE_URI] = (
            delegate_uri if delegate_uri is not None else ""
        )
        self.config[AcnNodeConfig.MONITORING_URI] = (
            monitoring_uri if monitoring_uri is not None else ""
        )

        entry_peers_maddrs_list = (
            AcnNodeConfig.LIST_SEPARATOR.join(entry_peers_maddrs)
            if entry_peers_maddrs is not None
            else ""
        )
        self.config[AcnNodeConfig.ENTRY_PEERS_MADDRS] = entry_peers_maddrs_list

        self.config[AcnNodeConfig.ACN_LOG_FILE] = (
            log_file if log_file is not None else ""
        )
        self.config[AcnNodeConfig.AEA_ADDRESS] = ""
        self.config[AcnNodeConfig.IPC_IN] = ""
        self.config[AcnNodeConfig.IPC_OUT] = ""

        if enable_checks:
            AcnNodeConfig.check_config(self.config)

    def dump(self, file_path: str) -> None:
        """Write current configuration to file."""
        with open(file_path, "w") as f:
            for key, value in self.config.items():
                f.write("{}={}\n".format(key, value))

    @classmethod
    def from_file(cls, file_path: str, enable_checks: bool = True) -> "AcnNodeConfig":
        """
        Create a new AcnNodeConfig objet from file.

        :param file_path: path to the file containing the configuration
        :param enable_checks: whether or not to enable checks
        :return: newly created AcnNodeConfig object, if successful
        """

        lines: List[str] = list()
        with open(file_path, "r") as f:
            lines = f.readlines()

        config = dict()
        for nbr, line in enumerate(lines):
            parts = line.strip().split("=")
            if len(parts) != 2:
                raise ValueError(
                    "Malformed configuration line {}: {}".format(nbr + 1, line)
                )
            config[parts[0]] = parts[1]

        key = config[AcnNodeConfig.KEY]
        uri = config[AcnNodeConfig.URI]
        external_uri = config.get(AcnNodeConfig.EXTERNAL_URI, None)
        delegate_uri = config.get(AcnNodeConfig.DELEGATE_URI, None)
        monitoring_uri = config.get(AcnNodeConfig.MONITORING_URI, None)
        entry_peers = config.get(AcnNodeConfig.ENTRY_PEERS_MADDRS, "")
        log_file = config.get(AcnNodeConfig.ACN_LOG_FILE, "")

        return cls(
            key,
            uri,
            external_uri,
            delegate_uri,
            monitoring_uri,
            entry_peers.split(","),
            log_file,
            enable_checks,
        )

    @staticmethod
    def check_config(config: Dict[str, str]) -> None:
        """
        Validate an ACN node configuration.

        :param config: dictionary containing the configuration to check
        """

        SigningKey.from_string(
            unhexlify(config[AcnNodeConfig.KEY]), curve=curves.SECP256k1
        )

        AcnNodeConfig._check_uri(config[AcnNodeConfig.URI])
        if config[AcnNodeConfig.EXTERNAL_URI] != "":
            AcnNodeConfig._check_uri(config[AcnNodeConfig.EXTERNAL_URI])
        if config[AcnNodeConfig.DELEGATE_URI] != "":
            AcnNodeConfig._check_uri(config[AcnNodeConfig.DELEGATE_URI])
        if config[AcnNodeConfig.MONITORING_URI] != "":
            AcnNodeConfig._check_uri(config[AcnNodeConfig.MONITORING_URI])

        maddrs = config[AcnNodeConfig.ENTRY_PEERS_MADDRS].split(
            AcnNodeConfig.LIST_SEPARATOR
        )
        for maddr in maddrs:
            AcnNodeConfig._check_maddr(maddr)

    @staticmethod
    def _check_uri(uri: str) -> None:
        """Check uri."""
        if uri == "":
            return
        parts = uri.split(":")
        if len(parts) != 2:
            raise ValueError("Malformed uri '{}'".format(uri))
        int(parts[1])

    @staticmethod
    def _check_maddr(maddr: str) -> None:
        """Check multiaddress."""
        if maddr == "":
            return
        parts = maddr.split("/")
        if len(parts) != 7:
            raise ValueError("Malformed multiaddress '{}'".format(maddr))
        multihashdecode(b58decode(parts[-1]))


class AcnNodeStandalone:
    """Deploy an acn node in standalone mode."""

    def __init__(self, config: AcnNodeConfig, libp2p_node_binary: str):
        """
        Initialize a new AcnNodeStandalone object.

        :param config: node's configuration
        :param libp2p_node_binary: path to libp2p node binary
        """

        self.config = config
        self.binary = libp2p_node_binary
        self._proc = None  # type: Optional[subprocess.Popen]

    def run(self):
        """Run the node."""
        config_file = ".acn_config"
        self.config.dump(config_file)

        cmd = [self.binary, config_file]

        if self.config.config[AcnNodeConfig.ACN_LOG_FILE] != "":
            self._proc = subprocess.Popen(  # nosec
                cmd,
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
            )
            with open(
                self.config.config[AcnNodeConfig.ACN_LOG_FILE], "ab", 1
            ) as log_file:
                for line in self._proc.stdout:
                    sys.stdout.buffer.write(line)
                    log_file.write(line)
                    log_file.flush()
        else:
            self._proc = subprocess.Popen(  # nosec
                cmd,
                shell=False,
            )

        try:
            self._proc.wait()
        except KeyboardInterrupt:
            pass

    def stop(self):
        """Stop the node."""
        if self._proc is not None:
            self._proc.terminate()
            self._proc.wait()


def parse_command_line():
    """Parse script cl arguments."""

    parser = argparse.ArgumentParser()
    parser.add_argument("libp2p_node")
    config = parser.add_mutually_exclusive_group(required=False)
    config.add_argument(
        "--config-from-env",
        action="store_true",
        dest="config_from_env",
        help="get node configuration from environment variables",
    )
    config.add_argument(
        "--config-from-file",
        action="store",
        type=str,
        dest="config_from_file",
        help="node configuration file",
    )

    parser.add_argument(
        "--key-file",
        action="store",
        type=str,
        dest="key",
        help="node's private key file",
    )
    parser.add_argument(
        "--uri",
        action="store",
        type=str,
        dest="uri",
        help="node's local uri in format {ip_address:port}",
    )
    parser.add_argument(
        "--uri-external",
        action="store",
        type=str,
        dest="external_uri",
        required=False,
        help="node's external uri in format {ip_address:port}",
    )
    parser.add_argument(
        "--uri-delegate",
        action="store",
        type=str,
        dest="delegate_uri",
        required=False,
        help="node's delegate service uri in format {ip_address:port}",
    )
    parser.add_argument(
        "--uri-monitoring",
        action="store",
        type=str,
        dest="monitoring_uri",
        required=False,
        help="node's monitoring service uri in format {ip_address:port}",
    )
    parser.add_argument(
        "--entry-peers-maddrs",
        action="store",
        nargs="*",
        dest="entry_peers_maddrs",
        help="node's entry peer uri in libp2p multiaddress fromat",
    )
    parser.add_argument(
        "--log-file",
        action="store",
        type=str,
        dest="log_file",
        required=False,
        help="path to node logging file",
    )

    args = parser.parse_args()

    if (
        args.config_from_env is False
        and args.config_from_file is None
        and (args.key is None or args.uri is None or args.external_uri is None)
    ):
        parser.error(
            "--key-file, --uri, and --uri-external are required when configuration is not passed through env or file"
        )

    return args


if __name__ == "__main__":

    run_args = parse_command_line()

    node_config: Optional[AcnNodeConfig] = None

    if run_args.config_from_env:
        run_key = os.environ[AcnNodeConfig.KEY]
        run_uri = os.environ[AcnNodeConfig.URI]
        run_external_uri = os.environ.get(AcnNodeConfig.EXTERNAL_URI)
        run_delegate_uri = os.environ.get(AcnNodeConfig.DELEGATE_URI)
        run_monitoring_uri = os.environ.get(AcnNodeConfig.MONITORING_URI)
        run_entry_peers = os.environ.get(AcnNodeConfig.ENTRY_PEERS_MADDRS)
        run_entry_peers_list = (
            run_entry_peers.split(",") if run_entry_peers is not None else []
        )
        run_log_file = os.environ.get(AcnNodeConfig.ACN_LOG_FILE, "")
        node_config = AcnNodeConfig(
            run_key,
            run_uri,
            run_external_uri,
            run_delegate_uri,
            run_monitoring_uri,
            run_entry_peers_list,
            run_log_file,
        )

    elif run_args.config_from_file is not None:
        node_config = AcnNodeConfig.from_file(run_args.config_from_file)

    else:
        with open(run_args.key, "r") as file:
            run_key = file.read().strip()
        node_config = AcnNodeConfig(
            run_key,
            run_args.uri,
            run_args.external_uri,
            run_args.delegate_uri,
            run_args.monitoring_uri,
            run_args.entry_peers_maddrs,
            run_args.log_file,
        )

    node = AcnNodeStandalone(node_config, run_args.libp2p_node)
    try:
        node.run()
    except Exception:
        node.stop()
        raise
