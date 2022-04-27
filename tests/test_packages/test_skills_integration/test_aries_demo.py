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
"""This package contains integration test for the aries_alice skill and the aries_faber skill."""
import random
import string
import subprocess  # nosec
from random import randint  # nosec

import pytest

from aea.test_tools.test_cases import AEATestCaseMany

from packages.fetchai.connections.p2p_libp2p.connection import (
    LIBP2P_SUCCESS_MESSAGE,
    P2PLibp2pConnection,
)
from packages.fetchai.skills.aries_alice import PUBLIC_ID as ALICE_SKILL_PUBLIC_ID
from packages.fetchai.skills.aries_faber import PUBLIC_ID as FABER_SKILL_PUBLIC_ID


def _rand_seed():
    return "".join(
        random.choice(string.ascii_uppercase + string.digits)  # nosec
        for _ in range(32)
    )


README = """
To start with test:
`pip install aries-cloudagent[indy]` acaPY is required

## VON Network

In the first terminal move to the `von-network` directory and run an instance of `von-network` locally in docker.

This <a href="https://github.com/bcgov/von-network#running-the-network-locally" target="_blank">tutorial</a> has information on starting (and stopping) the network locally.

``` bash
./manage build
./manage start 172.17.0.1,172.17.0.1,172.17.0.1,172.17.0.1 --logs
```

172.17.0.1 - is ip address of the docker0 network interface, can be used  any address assigned to the host except 127.0.0.1
"""

# set to False to run it manually
SKIP_TEST = True


@pytest.mark.unstable
@pytest.mark.integration
class TestAriesSkillsDemo(AEATestCaseMany):
    """Test integrated aries skills."""

    capture_log = True
    alice_seed: str
    bob_seed: str
    faber_seed: str

    @classmethod
    def get_port(cls) -> int:
        """Get next tcp port number."""
        cls.port += 1  # type: ignore
        return cls.port  # type: ignore

    @classmethod
    def start_acapy(
        cls, name: str, base_port: int, seed: str, endpoint_host: str, genesis_url: str
    ) -> subprocess.Popen:
        """Start acapy process."""
        return subprocess.Popen(  # nosec
            [
                "python3",
                "-m",
                "aries_cloudagent",
                "start",
                "--auto-ping-connection",
                "--auto-respond-messages",
                "--auto-store-credential",
                "--auto-accept-invites",
                "--auto-accept-requests",
                "--auto-respond-credential-proposal",
                "--auto-respond-credential-offer",
                "--auto-respond-credential-request",
                "--auto-respond-presentation-proposal",
                "--auto-respond-presentation-request",
                # "--debug-credentials",
                # "--debug-presentations",
                # "--debug-connections",
                "--admin",
                "127.0.0.1",
                str(base_port + 1),
                "--admin-insecure-mode",
                "--inbound-transport",
                "http",
                "0.0.0.0",
                str(base_port),
                "--outbound-transp",
                "http",
                "--webhook-url",
                f"http://127.0.0.1:{str(base_port+2)}/webhooks",
                "-e",
                f"http://{endpoint_host}:{base_port}",
                "--genesis-url",
                genesis_url,
                "--wallet-type",
                "indy",
                "--wallet-name",
                name + str(randint(10000000, 999999999999)),  # nosec
                "--wallet-key",
                "walkey",
                "--seed",
                seed,  # type: ignore
                "--recreate-wallet",
                "--wallet-local-did",
                "--auto-provision",
                "--label",
                name,
            ]
        )

    @classmethod
    def setup_class(cls) -> None:
        """Setup test case."""
        if SKIP_TEST:
            cls._is_teardown_class_called = True  # fix for teardown check fixture
            raise pytest.skip("test skipped, check code to enable it")
        check_acapy = subprocess.run("aca-py", shell=True, capture_output=True)  # nosec
        assert b"usage: aca-py" in check_acapy.stdout, "aca-py is not installed!"

        cls.port = 10001  # type: ignore
        super(TestAriesSkillsDemo, cls).setup_class()
        acapy_host = "192.168.1.43"
        cls.alice = "alice"  # type: ignore
        cls.soef_id = "intro_aries" + str(  # type: ignore
            randint(1000000, 99999999999999)  # nosec
        )
        cls.alice_seed = _rand_seed()  # type: ignore

        cls.bob = "bob"  # type: ignore
        cls.bob_seed = _rand_seed()  # type: ignore

        cls.faber = "faber"  # type: ignore
        cls.faber_seed = _rand_seed()  # type: ignore
        cls.controller = "controller"  # type: ignore
        cls.fetch_agent("fetchai/aries_alice", cls.alice, is_local=True)  # type: ignore
        cls.fetch_agent("fetchai/aries_alice", cls.bob, is_local=True)  # type: ignore
        cls.fetch_agent("fetchai/aries_faber", cls.faber, is_local=True)  # type: ignore
        cls.create_agents(cls.controller,)  # type: ignore

        cls.set_agent_context(cls.controller)  # type: ignore
        cls.add_item("connection", "fetchai/p2p_libp2p")

        addr = f"127.0.0.1:{cls.get_port()}"
        p2p_config = {  # type: ignore
            "delegate_uri": None,  # f"127.0.0.1:{cls.get_port()}",
            "entry_peers": [],
            "local_uri": addr,
            "public_uri": addr,
        }
        cls.nested_set_config(
            "vendor.fetchai.connections.p2p_libp2p.config", p2p_config
        )
        cls.generate_private_key("fetchai", "fetchai.key")
        cls.add_private_key("fetchai", "fetchai.key")
        cls.add_private_key("fetchai", "fetchai.key", connection=True)
        cls.run_cli_command("build", cwd=cls._get_cwd())
        cls.run_cli_command("issue-certificates", cwd=cls._get_cwd())
        r = cls.run_cli_command(
            "get-multiaddress",
            "fetchai",
            "-c",
            "-i",
            str(P2PLibp2pConnection.connection_id),
            "-u",
            "public_uri",
            cwd=cls._get_cwd(),
        )
        peer_addr = r.stdout.strip()
        for agent_name in [cls.alice, cls.bob, cls.faber]:  # type: ignore
            cls.set_agent_context(agent_name)
            p2p_config = {
                "delegate_uri": None,  # f"127.0.0.1:{cls.get_port()}",
                "entry_peers": [peer_addr],
                "local_uri": f"127.0.0.1:{cls.get_port()}",
                "public_uri": None,
            }
            cls.generate_private_key("fetchai", "fetchai.key")
            cls.add_private_key("fetchai", "fetchai.key")
            cls.add_private_key(
                "fetchai", "fetchai.key", connection=True,
            )
            cls.nested_set_config(
                "vendor.fetchai.connections.p2p_libp2p.config", p2p_config
            )

            cls.run_cli_command("build", cwd=cls._get_cwd())
            cls.run_cli_command("issue-certificates", cwd=cls._get_cwd())

        cls.set_agent_context(cls.alice)  # type: ignore
        cls.set_config(
            "vendor.fetchai.skills.aries_alice.models.strategy.args.seed",
            cls.alice_seed,  # type: ignore
        )
        cls.set_config(
            "vendor.fetchai.skills.aries_alice.models.strategy.args.service_data.value",
            cls.soef_id,  # type: ignore
        )
        cls.set_config(
            "vendor.fetchai.skills.aries_alice.models.strategy.args.search_query.search_value",
            cls.soef_id,  # type: ignore
        )
        cls.set_config(
            "vendor.fetchai.skills.aries_alice.models.strategy.args.admin_host",
            "127.0.0.1",
        )
        cls.set_config(
            "vendor.fetchai.skills.aries_alice.models.strategy.args.admin_port",
            "8031",
            "int",
        )

        cls.set_config(
            "vendor.fetchai.connections.webhook.config.webhook_port", "8032", "int"
        )
        cls.set_config(
            "vendor.fetchai.connections.webhook.config.webhook_address", "127.0.0.1"
        )
        cls.set_config(
            "vendor.fetchai.connections.webhook.config.target_skill_id",
            str(ALICE_SKILL_PUBLIC_ID),
        )
        cls.set_config(
            "vendor.fetchai.connections.webhook.config.webhook_url_path",
            "/webhooks/topic/{topic}/",
        )

        cls.set_agent_context(cls.bob)  # type: ignore
        cls.set_config(
            "vendor.fetchai.skills.aries_alice.models.strategy.args.seed",
            cls.bob_seed,  # type: ignore
        )
        cls.set_config(
            "vendor.fetchai.skills.aries_alice.models.strategy.args.service_data.value",
            cls.soef_id,  # type: ignore
        )
        cls.set_config(
            "vendor.fetchai.skills.aries_alice.models.strategy.args.search_query.search_value",
            cls.soef_id,  # type: ignore
        )
        cls.set_config(
            "vendor.fetchai.skills.aries_alice.models.strategy.args.admin_host",
            "127.0.0.1",
        )
        cls.set_config(
            "vendor.fetchai.skills.aries_alice.models.strategy.args.admin_port",
            "8041",
            "int",
        )

        cls.set_config(
            "vendor.fetchai.connections.webhook.config.webhook_port", "8042", "int"
        )
        cls.set_config(
            "vendor.fetchai.connections.webhook.config.webhook_address", "127.0.0.1"
        )
        cls.set_config(
            "vendor.fetchai.connections.webhook.config.target_skill_id",
            str(ALICE_SKILL_PUBLIC_ID),
        )
        cls.set_config(
            "vendor.fetchai.connections.webhook.config.webhook_url_path",
            "/webhooks/topic/{topic}/",
        )

        cls.set_agent_context(cls.faber)  # type: ignore
        cls.set_config(
            "vendor.fetchai.skills.aries_faber.models.strategy.args.seed",
            cls.faber_seed,  # type: ignore
        )

        cls.set_config(
            "vendor.fetchai.skills.aries_faber.models.strategy.args.search_query.search_value",
            cls.soef_id,  # type: ignore
        )
        cls.set_config(
            "vendor.fetchai.skills.aries_faber.models.strategy.args.admin_host",
            "127.0.0.1",
        )
        cls.set_config(
            "vendor.fetchai.skills.aries_faber.models.strategy.args.admin_port",
            "8021",
            "int",
        )

        cls.set_config(
            "vendor.fetchai.connections.webhook.config.target_skill_id",
            str(FABER_SKILL_PUBLIC_ID),
        )
        cls.set_config(
            "vendor.fetchai.connections.webhook.config.webhook_port", "8022", "int"
        )
        cls.set_config(
            "vendor.fetchai.connections.webhook.config.webhook_address", "127.0.0.1"
        )
        cls.set_config(
            "vendor.fetchai.connections.webhook.config.webhook_url_path",
            "/webhooks/topic/{topic}/",
        )

        cls.extra_processes = [  # type: ignore
            cls.start_acapy(
                "alice",
                8030,
                cls.alice_seed,
                acapy_host,
                "http://localhost:9000/genesis",
            ),
            cls.start_acapy(
                "bob", 8040, cls.bob_seed, acapy_host, "http://localhost:9000/genesis",
            ),
            cls.start_acapy(
                "faber",
                8020,
                cls.faber_seed,
                acapy_host,
                "http://localhost:9000/genesis",
            ),
        ]

    def test_alice_faber_demo(self):
        """Run demo test."""
        self.set_agent_context(self.controller)
        controller_process = self.run_agent()
        self.extra_processes.append(controller_process)

        check_strings = (
            "Starting libp2p node...",
            "Connecting to libp2p node...",
            "Successfully connected to libp2p node!",
            LIBP2P_SUCCESS_MESSAGE,
        )

        missing_strings = self.missing_from_output(
            controller_process, check_strings, timeout=30, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in controller output.".format(missing_strings)

        self.set_agent_context(self.faber)
        faber_process = self.run_agent()
        self.extra_processes.append(faber_process)

        self.set_agent_context(self.alice)
        alice_process = self.run_agent()
        self.extra_processes.append(alice_process)

        self.set_agent_context(self.bob)
        bob_process = self.run_agent()
        self.extra_processes.append(bob_process)

        missing_strings = self.missing_from_output(
            faber_process,
            ["Connected to alice", "Connected to bob"],
            timeout=80,
            is_terminating=False,
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in faber output.".format(missing_strings)

        missing_strings = self.missing_from_output(
            alice_process,
            ["Connected to faber", "Got credentials proof from bob"],
            timeout=80,
            is_terminating=False,
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in alice output.".format(missing_strings)

        missing_strings = self.missing_from_output(
            bob_process,
            ["Connected to faber", "Got credentials proof from alice"],
            timeout=80,
            is_terminating=False,
        )
        assert missing_strings == [], "Strings {} didn't appear in bob output.".format(
            missing_strings
        )

    @classmethod
    def teardown_class(cls) -> None:
        """Tear down test case."""
        super(TestAriesSkillsDemo, cls).teardown_class()
        for proc in cls.extra_processes:  # type: ignore
            proc.kill()
            proc.wait(10)


if __name__ == "__main__":
    pytest.main([__file__])
