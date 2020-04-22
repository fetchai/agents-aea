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

"""This module contains the tests for the orm-integration.md guide."""
import json
import logging
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import mistune
import pytest
import yaml
from click.testing import CliRunner

from aea.cli import cli
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE, DEFAULT_SKILL_CONFIG_FILE
from ...conftest import ROOT_DIR, CLI_LOG_OPTION

logger = logging.getLogger(__name__)


ledger_config_replacement = """ledger_apis:
  fetchai:
    network: testnet"""


seller_strategy_replacement = """models:                        
  strategy:                    
    class_name: Strategy      
    args:                      
      total_price: 10          
      seller_tx_fee: 0         
      currency_id: 'FET'       
      ledger_id: 'fetchai'     
      is_ledger_tx: True       
      has_data_source: True    
      data_for_sale: {}        
      search_schema:           
        attribute_one:         
          name: country        
          type: str            
          is_required: True    
        attribute_two:         
          name: city           
          type: str            
          is_required: True    
      search_data:             
        country: UK            
        city: Cambridge        
dependencies:                   
  SQLAlchemy: {}"""

buyer_strategy_replacement = """models:                          
  strategy:                      
    class_name: Strategy        
    args:                        
      max_price: 40              
      max_buyer_tx_fee: 100      
      currency_id: 'FET'         
      ledger_id: 'fetchai'       
      is_ledger_tx: True         
      search_query:              
        search_term: country     
        search_value: UK         
        constraint_type: '=='    
ledgers: ['fetchai']"""


ORM_SELLER_STRATEGY_PATH = Path(
    ROOT_DIR, "tests", "test_docs", "test_orm_integration", "orm_seller_strategy.py"
)


class TestOrmIntegrationDocs:
    """This class contains the tests for the orm-integration.md guide."""

    @pytest.fixture(autouse=True)
    def _start_oef_node(self, network_node):
        """Start an oef node."""

    @classmethod
    def setup_class(cls):
        """Set the tests up."""
        cls.tmpdir = tempfile.mkdtemp()
        cls.oldcwd = os.getcwd()
        os.chdir(cls.tmpdir)
        cls.runner = CliRunner()

        cls.aea_seller_name = "my_seller_aea"
        cls.aea_buyer_name = "my_buyer_aea"
        cls.aea_seller_dir = Path(cls.tmpdir, cls.aea_seller_name)
        cls.aea_buyer_dir = Path(cls.tmpdir, cls.aea_buyer_name)

        # copy 'packages/' into temporary test directory
        shutil.copytree(Path(ROOT_DIR, "packages"), Path(cls.tmpdir, "packages"))

        markdown_parser = mistune.create_markdown(renderer=mistune.AstRenderer())

        skill_doc_file = Path(ROOT_DIR, "docs", "orm-integration.md")
        doc = markdown_parser(skill_doc_file.read_text())
        # get only code blocks
        code_blocks = list(filter(lambda x: x["type"] == "block_code" == "python", doc))
        cls.python_code_blocks = list(
            filter(lambda x: x["info"].strip() == "python" == "python", code_blocks)
        )

    def test_strategy_consistency(self):
        """
        Test that the seller strategy specified in the documentation
        is the same we use in the tests.
        """
        strategy_file_content = ORM_SELLER_STRATEGY_PATH.read_text()
        for python_code_block in self.python_code_blocks:
            if not python_code_block["text"] in strategy_file_content:
                pytest.fail(
                    "Code block not present in strategy file:\n{}".format(
                        python_code_block["text"]
                    )
                )

    def test_example(self):
        """Test the example."""
        # # init the CLI tool locally
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "init", "--local", "--author", "fakeauthor"],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        # Create the seller AEA (ledger version)
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", self.aea_seller_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        os.chdir(self.aea_seller_dir)
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "connection", "fetchai/oef:0.2.0"],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        result = self.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "add",
                "--local",
                "skill",
                "fetchai/generic_seller:0.1.0",
            ],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        os.chdir(self.tmpdir)

        # Create the buyer client
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", self.aea_buyer_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        os.chdir(self.aea_buyer_dir)
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "connection", "fetchai/oef:0.2.0"],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "skill", "fetchai/generic_buyer:0.1.0"],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "generate-key", "fetchai"], standalone_mode=False,
        )
        assert result.exit_code == 0
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add-key", "fetchai", "fet_private_key.txt"],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "generate-wealth", "fetchai"], standalone_mode=False,
        )
        assert result.exit_code == 0

        # Update the AEA configs
        aea_config_seller = self.aea_seller_dir / DEFAULT_AEA_CONFIG_FILE
        aea_config_buyer = self.aea_buyer_dir / DEFAULT_AEA_CONFIG_FILE
        new_content_seller = re.sub(
            "ledger_apis:.*", ledger_config_replacement, aea_config_seller.read_text()
        )
        new_content_buyer = re.sub(
            "ledger_apis:.*", ledger_config_replacement, aea_config_buyer.read_text()
        )
        aea_config_seller.write_text(new_content_seller)
        aea_config_buyer.write_text(new_content_buyer)

        # Update the seller AEA skill configs.
        seller_skill_config_path = Path(
            self.aea_seller_dir,
            "vendor",
            "fetchai",
            "skills",
            "generic_seller",
            DEFAULT_SKILL_CONFIG_FILE,
        )
        seller_skill_config = yaml.safe_load(seller_skill_config_path.open())
        seller_skill_config.update(yaml.safe_load(seller_strategy_replacement))
        yaml.safe_dump(seller_skill_config, seller_skill_config_path.open("w"))

        # Update the buyer AEA skill configs.
        buyer_skill_config_path = Path(
            self.aea_buyer_dir,
            "vendor",
            "fetchai",
            "skills",
            "generic_buyer",
            DEFAULT_SKILL_CONFIG_FILE,
        )
        updated_skill_config = yaml.safe_load(buyer_skill_config_path.open())
        updated_skill_config.update(yaml.safe_load(buyer_strategy_replacement))
        yaml.safe_dump(updated_skill_config, buyer_skill_config_path.open("w"))

        # Run aea install in both agents
        os.chdir(self.aea_seller_dir)
        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "install"], standalone_mode=False,
        )
        assert result.exit_code == 0
        os.chdir(self.aea_buyer_dir)
        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "install"], standalone_mode=False,
        )
        assert result.exit_code == 0

        # Set default connection in both agents
        os.chdir(self.aea_seller_dir)
        result = self.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "config",
                "set",
                "agent.default_connection",
                "fetchai/oef:0.2.0",
            ],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        os.chdir(self.aea_buyer_dir)
        result = self.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "config",
                "set",
                "agent.default_connection",
                "fetchai/oef:0.2.0",
            ],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        # Replace the seller strategy
        seller_stategy_path = Path(
            self.aea_seller_dir,
            "vendor",
            "fetchai",
            "skills",
            "generic_seller",
            "strategy.py",
        )
        seller_stategy_path.write_text(ORM_SELLER_STRATEGY_PATH.read_text())

        try:
            os.chdir(self.aea_seller_dir)
            process_one = subprocess.Popen(  # nosec
                [
                    sys.executable,
                    "-m",
                    "aea.cli",
                    "run",
                    "--connections",
                    "fetchai/oef:0.2.0",
                ],
                stdout=subprocess.PIPE,
                env=os.environ.copy(),
            )

            os.chdir(self.aea_buyer_dir)
            process_two = subprocess.Popen(  # nosec
                [
                    sys.executable,
                    "-m",
                    "aea.cli",
                    "run",
                    "--connections",
                    "fetchai/oef:0.2.0",
                ],
                stdout=subprocess.PIPE,
                env=os.environ.copy(),
            )

            time.sleep(10.0)
        finally:
            process_one.send_signal(signal.SIGINT)
            process_one.wait(timeout=10)
            process_two.send_signal(signal.SIGINT)
            process_two.wait(timeout=10)

            if not process_one.returncode == 0:
                poll_one = process_one.poll()
                if poll_one is None:
                    process_one.terminate()
                    process_one.wait(2)

            if not process_two.returncode == 0:
                poll_two = process_two.poll()
                if poll_two is None:
                    process_two.terminate()
                    process_two.wait(2)

            os.chdir(self.tmpdir)
            result = self.runner.invoke(
                cli,
                [*CLI_LOG_OPTION, "delete", self.aea_seller_name],
                standalone_mode=False,
            )
            assert result.exit_code == 0
            result = self.runner.invoke(
                cli,
                [*CLI_LOG_OPTION, "delete", self.aea_buyer_name],
                standalone_mode=False,
            )
            assert result.exit_code == 0

    @classmethod
    def teardown_class(cls):
        """Tear the class down."""
        os.chdir(cls.oldcwd)
        try:
            shutil.rmtree(cls.tmpdir)
        except (OSError, IOError):
            pass
