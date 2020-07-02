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
from pathlib import Path

import mistune

import pytest

import yaml

from aea.test_tools.test_cases import AEATestCaseMany, UseOef

from ...conftest import FUNDED_FET_PRIVATE_KEY_1, MAX_FLAKY_RERUNS, ROOT_DIR

seller_strategy_replacement = """models:
  dialogues:
    args: {}
    class_name: Dialogues
  strategy:
    args:
      currency_id: FET
      data_for_sale:
        temperature: 26
      data_model:
        attribute_one:
          is_required: true
          name: country
          type: str
        attribute_two:
          is_required: true
          name: city
          type: str
      data_model_name: location
      has_data_source: false
      is_ledger_tx: true
      ledger_id: fetchai
      service_data:
        city: Cambridge
        country: UK
      service_id: generic_service
      unit_price: 10
    class_name: Strategy
dependencies:
  SQLAlchemy: {}"""

buyer_strategy_replacement = """models:
  dialogues:
    args: {}
    class_name: Dialogues
  strategy:
    args:
      currency_id: FET
      data_model:
        attribute_one:
          is_required: true
          name: country
          type: str
        attribute_two:
          is_required: true
          name: city
          type: str
      data_model_name: location
      is_ledger_tx: true
      ledger_id: fetchai
      max_negotiations: 1
      max_tx_fee: 1
      max_unit_price: 20
      search_query:
        constraint_one:
          constraint_type: ==
          search_term: country
          search_value: UK
        constraint_two:
          constraint_type: ==
          search_term: city
          search_value: Cambridge
      service_id: generic_service
    class_name: Strategy"""


ORM_SELLER_STRATEGY_PATH = Path(
    ROOT_DIR, "tests", "test_docs", "test_orm_integration", "orm_seller_strategy.py"
)


class TestOrmIntegrationDocs(AEATestCaseMany, UseOef):
    """This class contains the tests for the orm-integration.md guide."""

    @pytest.mark.unstable
    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
    def test_orm_integration_docs_example(self):
        """Run the weather skills sequence."""
        seller_aea_name = "my_thermometer_aea"
        buyer_aea_name = "my_thermometer_client"
        self.create_agents(seller_aea_name, buyer_aea_name)

        ledger_apis = {"fetchai": {"network": "testnet"}}
        default_routing = {"fetchai/ledger_api:0.1.0": "fetchai/ledger:0.1.0"}

        # Setup seller
        self.set_agent_context(seller_aea_name)
        self.add_item("connection", "fetchai/oef:0.5.0")
        self.add_item("connection", "fetchai/ledger:0.1.0")
        self.add_item("skill", "fetchai/thermometer:0.5.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.5.0")
        self.force_set_config("agent.ledger_apis", ledger_apis)
        setting_path = "agent.default_routing"
        self.force_set_config(setting_path, default_routing)
        self.eject_item("skill", "fetchai/thermometer:0.5.0")
        seller_skill_config_replacement = yaml.safe_load(seller_strategy_replacement)
        self.force_set_config(
            "skills.thermometer.models", seller_skill_config_replacement["models"],
        )
        self.force_set_config(
            "skills.thermometer.dependencies",
            seller_skill_config_replacement["dependencies"],
        )
        # Replace the seller strategy
        seller_stategy_path = Path(
            seller_aea_name, "skills", "thermometer", "strategy.py",
        )
        self.replace_file_content(seller_stategy_path, ORM_SELLER_STRATEGY_PATH)
        self.fingerprint_item(
            "skill", "{}/thermometer:0.1.0".format(self.author),
        )
        self.run_install()

        # Setup Buyer
        self.set_agent_context(buyer_aea_name)
        self.add_item("connection", "fetchai/oef:0.5.0")
        self.add_item("connection", "fetchai/ledger:0.1.0")
        self.add_item("skill", "fetchai/thermometer_client:0.4.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.5.0")
        self.force_set_config("agent.ledger_apis", ledger_apis)
        setting_path = "agent.default_routing"
        self.force_set_config(setting_path, default_routing)
        buyer_skill_config_replacement = yaml.safe_load(buyer_strategy_replacement)
        self.force_set_config(
            "vendor.fetchai.skills.generic_buyer.models",
            buyer_skill_config_replacement["models"],
        )
        self.run_install()

        # add funded key
        self.generate_private_key("fetchai")
        self.add_private_key("fetchai", "fet_private_key.txt")
        self.replace_private_key_in_file(
            FUNDED_FET_PRIVATE_KEY_1, "fet_private_key.txt"
        )

        # Fire the sub-processes and the threads.
        self.set_agent_context(seller_aea_name)
        seller_aea_process = self.run_agent()

        self.set_agent_context(buyer_aea_name)
        buyer_aea_process = self.run_agent()

        check_strings = (
            "updating services on OEF service directory.",
            "unregistering services from OEF service directory.",
            "received CFP from sender=",
            "sending a PROPOSE with proposal=",
            "received ACCEPT from sender=",
            "sending MATCH_ACCEPT_W_INFORM to sender=",
            "received INFORM from sender=",
            "checking whether transaction=",
            "transaction confirmed, sending data=",
        )
        missing_strings = self.missing_from_output(
            seller_aea_process, check_strings, timeout=180, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in seller_aea output.".format(missing_strings)

        check_strings = (
            "found agents=",
            "sending CFP to agent=",
            "received proposal=",
            "accepting the proposal from sender=",
            "received MATCH_ACCEPT_W_INFORM from sender=",
            "requesting transfer transaction from ledger api...",
            "received raw transaction=",
            "proposing the transaction to the decision maker. Waiting for confirmation ...",
            "transaction signing was successful.",
            "sending transaction to ledger.",
            "transaction was successfully submitted. Transaction digest=",
            "informing counterparty=",
            "received INFORM from sender=",
            "received the following data=",
        )
        missing_strings = self.missing_from_output(
            buyer_aea_process, check_strings, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in buyer_aea output.".format(missing_strings)

        self.terminate_agents(seller_aea_process, buyer_aea_process)
        assert (
            self.is_successfully_terminated()
        ), "Agents weren't successfully terminated."


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
