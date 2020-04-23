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
import logging
import os
import signal
import time
from pathlib import Path

import mistune

import pytest

import yaml

from aea.crypto.fetchai import FETCHAI
from aea.test_tools.decorators import skip_test_ci
from aea.test_tools.generic import force_set_config
from aea.test_tools.test_cases import AEAWithOefTestCase

from ...conftest import ROOT_DIR

logger = logging.getLogger(__name__)


seller_strategy_replacement = """models:
  dialogues:
    args: {}
    class_name: Dialogues
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
  dialogues:
    args: {}
    class_name: Dialogues
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


class TestOrmIntegrationDocs(AEAWithOefTestCase):
    """This class contains the tests for the orm-integration.md guide."""

    @skip_test_ci
    def test_orm_integration_docs_example(self, pytestconfig):
        """Run the weather skills sequence."""
        self.initialize_aea()

        seller_aea_name = "my_seller_aea"
        buyer_aea_name = "my_buyer_aea"
        self.create_agents(seller_aea_name, buyer_aea_name)

        ledger_apis = {FETCHAI: {"network": "testnet"}}

        # Setup seller
        seller_aea_dir_path = Path(self.t, seller_aea_name)
        os.chdir(seller_aea_dir_path)
        self.add_item("connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/generic_seller:0.1.0")
        self.run_install()
        force_set_config("agent.ledger_apis", ledger_apis)
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")

        # Setup Buyer
        buyer_aea_dir_path = Path(self.t, buyer_aea_name)
        os.chdir(buyer_aea_dir_path)

        self.add_item("connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/generic_buyer:0.1.0")
        self.run_install()
        force_set_config("agent.ledger_apis", ledger_apis)
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")

        # Generate and add private keys
        self.generate_private_key()
        self.add_private_key()

        # Add some funds to the buyer
        self.generate_wealth()

        # Update the seller AEA skill configs.
        os.chdir(seller_aea_dir_path)
        seller_skill_config_replacement = yaml.safe_load(seller_strategy_replacement)
        force_set_config(
            "vendor.fetchai.skills.generic_seller.models",
            seller_skill_config_replacement["models"],
        )

        # Update the buyer AEA skill configs.
        os.chdir(buyer_aea_dir_path)
        buyer_skill_config_replacement = yaml.safe_load(buyer_strategy_replacement)
        force_set_config(
            "vendor.fetchai.skills.generic_buyer.models",
            buyer_skill_config_replacement["models"],
        )

        # Replace the seller strategy
        seller_stategy_path = Path(
            seller_aea_dir_path,
            "vendor",
            "fetchai",
            "skills",
            "generic_seller",
            "strategy.py",
        )
        self.replace_file_content(seller_stategy_path, ORM_SELLER_STRATEGY_PATH)
        os.chdir(seller_aea_dir_path / "vendor" / "fetchai")
        self.run_cli_command("fingerprint", "skill", "fetchai/generic_seller:0.1.0")

        # Fire the sub-processes and the threads.
        os.chdir(seller_aea_dir_path)
        self.run_install()
        process_one = self.run_agent("--connections", "fetchai/oef:0.2.0")

        os.chdir(buyer_aea_dir_path)
        process_two = self.run_agent("--connections", "fetchai/oef:0.2.0")

        self.start_tty_read_thread(process_one)
        self.start_error_read_thread(process_one)
        self.start_tty_read_thread(process_two)
        self.start_error_read_thread(process_two)

        time.sleep(20)
        process_one.send_signal(signal.SIGINT)
        process_two.send_signal(signal.SIGINT)

        process_one.wait(timeout=10)
        process_two.wait(timeout=10)

        assert process_one.returncode == 0
        assert process_two.returncode == 0


def test_strategy_consistency():
    """
    Test that the seller strategy specified in the documentation
    is the same we use in the tests.
    """
    markdown_parser = mistune.create_markdown(renderer=mistune.AstRenderer())

    skill_doc_file = Path(ROOT_DIR, "docs", "orm-integration.md")
    doc = markdown_parser(skill_doc_file.read_text())
    # get only code blocks
    code_blocks = list(filter(lambda x: x["type"] == "block_code", doc))
    python_code_blocks = list(
        filter(
            lambda x: x["info"] is not None and x["info"].strip() == "python",
            code_blocks,
        )
    )

    strategy_file_content = ORM_SELLER_STRATEGY_PATH.read_text()
    for python_code_block in python_code_blocks:
        if not python_code_block["text"] in strategy_file_content:
            pytest.fail(
                "Code block not present in strategy file:\n{}".format(
                    python_code_block["text"]
                )
            )
