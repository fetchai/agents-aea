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
""" Deploy an ACN libp2p node to a kubernetes cluster """

import argparse
from pathlib import Path
from tempfile import mkdtemp
from typing import Dict, List, Optional

k8s_deployment_name = "ph-deployment-name-here"
k8s_cluster_namespace = "ph-cluster-namespace-here"
k8s_check_listening_host = "ph-latest-entry-peer-host-here"
k8s_check_listening_port = "ph-latest-entry-peer-port-here"
k8s_docker_image_url = "ph-gcr-image-with-tag-here"
k8s_docker_container_name = "ph-container-name-here"
k8s_dnsname = "ph-dnsname-here"
k8s_dnsname_target = "ph-dnsname-target-here"

node_port_number = "ph-node-port-number-here"
node_port_number_delegate = "ph-node-delegate-port-number-here"
node_private_key = "ph-node-priv-key-name-here"
node_uri_external = "ph-node-external-uri-here"
node_uri = "ph-node-local-uri-here"
node_uri_delegate = "ph-node-delegate-uri-here"
node_entry_peers = "ph-node-entry-peers-list-here"
node_key_name = "ph-node-priv-key-name-here"
node_key_encoded = "ph-base64-encoded-private-key-here"


config: Dict[str, str] = {}

k8s_deployment_templates = [
    "k8s/deployment.yaml",
    "k8s/dns.yaml",
    "k8s/secrect.yaml",
    "k8s/istion.yaml",
]


class AcnK8sConfig:
    """
    """

    def __init__(
        self,
        root_dir: str,
        key_file: str,
        port: int,
        delegate_port: int,
        entry_peers: Optional[List[str]],
        enable_checks: bool = True,
    ):
        """
        """
        self.workdir = ""
        self.root_dir = root_dir
        self.port = port
        self.port_delegate = delegate_port
        self.entry_peers = entry_peers if entry_peers is not None else []

        self.key = ""
        with open(key_file, "r") as f:
            self.key = f.read().strip()

        self.deployment_files = []
        self.template_files = []   # type: List[Path]
        self._fetch_deployment_templates()

        if enable_checks:
            self._check_config()

    def _fetch_deployment_templates(self):
        for  template in k8s_deployment_templates:
            path = Path(self.root_dir, template)
            if not path.is_file():
                raise ValueError("Couldn't find deployment template file: {}".format(path))
            self.template_files.append(path)
        
    def generate_deployment(self):
        """ """

        self.workdir = mkdtemp()
        
        for path in self.template_files:
            with open(path, "r") as f:
                content = f.read()
            
            content = self._substitute_placeholders(content)

            with open(self.workdir / path.name, "w") as f:
                f.write(content)

            

    def _check_config(self):
        


def parse_commandline():
    """ Parse script cl arguments """

    # args:
    # - scripts absolute path
    # - private key file
    # - port number / uri
    # |__-> deployment name
    # - delegate port number
    # - entry peers list

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--key-file",
        action="store",
        type=str,
        dest="key",
        help="node's private key file",
    )
    parser.add_argument(
        "--port",
        action="store",
        type=str,
        dest="port",
        help="node's port number (both local and external)",
    )
    parser.add_argument(
        "--port-delegate",
        action="store",
        type=str,
        dest="delegate_port",
        required=False,
        help="node's delegate service port number (both local and external)",
    )
    parser.add_argument(
        "--entry-peers-maddrs",
        action="store",
        nargs="*",
        dest="entry_peers_maddrs",
        help="node's entry peers in libp2p multiaddress format",
    )

    args = parser.parse_args()

    return args


if __name__ == "__main__":

    args = parse_commandline()
