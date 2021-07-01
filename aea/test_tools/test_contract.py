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
"""This module contains test case classes based on pytest for AEA contract testing."""
import asyncio
import os
import time
from pathlib import Path
from queue import Queue
from types import SimpleNamespace
from typing import Any, Dict, Optional, Tuple, Type, cast

from aea_ledger_ethereum import EthereumCrypto
from aea_ledger_fetchai import FetchAICrypto

from aea.configurations.loader import ComponentType, ConfigLoaders, ContractConfig, PackageType, SkillConfig, load_component_configuration
from aea.context.base import AgentContext
from aea.contracts.base import Contract, contract_registry
from aea.crypto.ledger_apis import DEFAULT_CURRENCY_DENOMINATIONS
from aea.crypto.registries import (
    crypto_registry,
    faucet_apis_registry,
    ledger_apis_registry,
)
from aea.exceptions import AEAEnforceError
from aea.helpers.io import open_file
from aea.identity.base import Identity
from aea.mail.base import Address
from aea.multiplexer import AsyncMultiplexer, Multiplexer, OutBox
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue, DialogueMessage, Dialogues
from aea.skills.tasks import TaskManager

from tests.conftest import (
    ETHEREUM_ADDRESS_ONE,
    ETHEREUM_ADDRESS_TWO,
    ETHEREUM_PRIVATE_KEY_PATH,
    ETHEREUM_PRIVATE_KEY_TWO_PATH,
    FETCHAI_TESTNET_CONFIG,
    MAX_FLAKY_RERUNS,
    ROOT_DIR,
    get_register_erc1155,
)


COUNTERPARTY_AGENT_ADDRESS = "counterparty"
COUNTERPARTY_SKILL_ADDRESS = "some_author/some_skill:0.1.0"


class BaseSkillTestCase:
    """A class to test a skill."""

    path_to_contract: Path = Path(".")
    # is_agent_to_agent_messages: bool = True
    _contract: Contract
    # _multiplexer: AsyncMultiplexer
    # _outbox: OutBox

    @property
    def contract(self) -> Contract:
        """Get the contract."""
        try:
            value = self._contract
        except AttributeError:
            raise ValueError("Ensure the contract is set during setup_class.")
        return value

    @classmethod
    def setup(cls, **kwargs: Any) -> None:
        """Set up the contract test case."""
        cls.ledger_api = ledger_apis_registry.make(
            FetchAICrypto.identifier, **FETCHAI_TESTNET_CONFIG
        )
        cls.faucet_api = faucet_apis_registry.make(FetchAICrypto.identifier)
        cls.deployer_crypto = crypto_registry.make(FetchAICrypto.identifier)
        cls.item_owner_crypto = crypto_registry.make(FetchAICrypto.identifier)

        # # Test tokens IDs
        # cls.token_ids_a = [
        #     340282366920938463463374607431768211456,
        #     340282366920938463463374607431768211457,
        #     340282366920938463463374607431768211458,
        #     340282366920938463463374607431768211459,
        #     340282366920938463463374607431768211460,
        #     340282366920938463463374607431768211461,
        #     340282366920938463463374607431768211462,
        #     340282366920938463463374607431768211463,
        #     340282366920938463463374607431768211464,
        #     340282366920938463463374607431768211465,
        # ]
        #
        # cls.token_id_b = 680564733841876926926749214863536422912

        # Refill deployer account from faucet
        cls.refill_from_faucet(
            cls.ledger_api, cls.faucet_api, cls.deployer_crypto.address
        )

        # Refill item owner account from faucet
        cls.refill_from_faucet(
            cls.ledger_api, cls.faucet_api, cls.item_owner_crypto.address
        )

        # cls.set_contract()
        # directory = Path(ROOT_DIR, "packages", "fetchai", "contracts", "erc1155")
        configuration = load_component_configuration(ComponentType.CONTRACT, cls.path_to_contract)
        configuration._directory = cls.path_to_contract
        configuration = cast(ContractConfig, configuration)

        if str(configuration.public_id) not in contract_registry.specs:
            # load contract into sys modules
            Contract.from_config(configuration)

        cls._contract = contract_registry.make(str(configuration.public_id))

    @staticmethod
    def refill_from_faucet(ledger_api, faucet_api, address):
        """Refill from faucet."""
        start_balance = ledger_api.get_balance(address)

        faucet_api.get_wealth(address)

        tries = 15
        while tries > 0:
            tries -= 1
            time.sleep(1)

            balance = ledger_api.get_balance(address)
            if balance != start_balance:
                break


        #
        #
        # identity = Identity("test_agent_name", "test_agent_address")
        #
        # cls._multiplexer = AsyncMultiplexer()
        # cls._multiplexer._out_queue = (  # pylint: disable=protected-access
        #     asyncio.Queue()
        # )
        # cls._outbox = OutBox(cast(Multiplexer, cls._multiplexer))
        # _shared_state = cast(Optional[Dict[str, Any]], kwargs.pop("shared_state", None))
        # _skill_config_overrides = cast(
        #     Optional[Dict[str, Any]], kwargs.pop("config_overrides", None)
        # )
        # _dm_context_kwargs = cast(
        #     Dict[str, Any], kwargs.pop("dm_context_kwargs", dict())
        # )
        #
        # agent_context = AgentContext(
        #     identity=identity,
        #     connection_status=cls._multiplexer.connection_status,
        #     outbox=cls._outbox,
        #     decision_maker_message_queue=Queue(),
        #     decision_maker_handler_context=SimpleNamespace(**_dm_context_kwargs),
        #     task_manager=TaskManager(),
        #     default_ledger_id=identity.default_address_key,
        #     currency_denominations=DEFAULT_CURRENCY_DENOMINATIONS,
        #     default_connection=None,
        #     default_routing={},
        #     search_service_address="dummy_author/dummy_search_skill:0.1.0",
        #     decision_maker_address="dummy_decision_maker_address",
        #     data_dir=os.getcwd(),
        # )
        #
        # # Pre-populate the 'shared_state' prior to loading the skill
        # if _shared_state is not None:
        #     for key, value in _shared_state.items():
        #         agent_context.shared_state[key] = value
        #
        # skill_configuration_file_path: Path = Path(cls.path_to_skill, "skill.yaml")
        # loader = ConfigLoaders.from_package_type(PackageType.SKILL)
        #
        # with open_file(skill_configuration_file_path) as fp:
        #     skill_config: SkillConfig = loader.load(fp)
        #
        # # Override skill's config prior to loading
        # if _skill_config_overrides is not None:
        #     skill_config.update(_skill_config_overrides)
        #
        # skill_config.directory = cls.path_to_skill
        #
        # cls._skill = Skill.from_config(skill_config, agent_context)
