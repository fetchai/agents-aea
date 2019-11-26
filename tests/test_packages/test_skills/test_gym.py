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

"""This test module contains the integration test for the gym skill."""
import os
import shutil
import tempfile
import time
from pathlib import Path
from threading import Thread

import yaml

from aea.aea import AEA
from aea.cli import cli
from aea.configurations.base import SkillConfig, ConnectionConfig
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import Wallet
from aea.registries.base import Resources
from packages.connections.gym.connection import GymConnection
from ...common.click_testing import CliRunner
from ...conftest import CLI_LOG_OPTION, ROOT_DIR, CUR_PATH


class TestGymSkill:
    """Test that gym skill works."""

    @classmethod
    def setup_class(cls):
        """Set up the test class."""
        cls.runner = CliRunner()
        cls.agent_name = "my_gym_agent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

    def test_gym(self, pytestconfig):
        """Run the gym skill sequence."""
        # add packages folder
        packages_src = os.path.join(ROOT_DIR, 'packages')
        packages_dst = os.path.join(os.getcwd(), 'packages')
        shutil.copytree(packages_src, packages_dst)

        # create agent
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "create", self.agent_name], standalone_mode=False)
        assert result.exit_code == 0
        agent_dir_path = os.path.join(self.t, self.agent_name)
        os.chdir(agent_dir_path)

        # add packages and install dependencies
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "add", "skill", "gym"], standalone_mode=False)
        assert result.exit_code == 0
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "add", "connection", "gym"], standalone_mode=False)
        assert result.exit_code == 0
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "install"], standalone_mode=False)
        assert result.exit_code == 0

        # add gyms folder from examples
        gyms_src = os.path.join(self.cwd, 'examples', 'gym_ex', 'gyms')
        gyms_dst = os.path.join(self.t, self.agent_name, 'gyms')
        shutil.copytree(gyms_src, gyms_dst)

        # change config file of gym connection
        file_src = os.path.join(self.cwd, 'tests', 'test_packages', 'test_skills', 'data', 'connection.yaml')
        file_dst = os.path.join(self.t, self.agent_name, 'connections', 'gym', 'connection.yaml')
        shutil.copyfile(file_src, file_dst)

        # change number of training steps
        skill_config_path = Path(self.t, self.agent_name, "skills", "gym", "skill.yaml")
        skill_config = SkillConfig.from_json(yaml.safe_load(open(skill_config_path)))
        skill_config.tasks.read("GymTask").args["nb_steps"] = 100
        yaml.safe_dump(skill_config.json, open(skill_config_path, "w"))

        # start the AEA programmatically
        private_key_pem_path = os.path.join(CUR_PATH, "data", "priv.pem")
        wallet = Wallet({'default': private_key_pem_path})
        ledger_apis = LedgerApis({})
        json_connection_configuration = yaml.safe_load(open(Path(self.t, self.agent_name, "connections", "gym", "connection.yaml")))
        connection = GymConnection.from_config(wallet.public_keys['default'],
                                                ConnectionConfig.from_json(json_connection_configuration))
        gym_agent = AEA(self.agent_name, [connection], wallet, ledger_apis, resources=Resources(str(Path(self.t, self.agent_name))))
        t = Thread(target=gym_agent.start)
        t.start()

        # check the gym run ends

        time.sleep(10.0)

        gym_agent.stop()
        t.join()

        os.chdir(self.t)
        self.result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "delete", self.agent_name], standalone_mode=False)

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass
