# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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

"""This package contains the behaviours."""

import datetime
import logging
import time
from typing import Dict, List, Optional, Union, cast

from aea.contracts.ethereum import Contract
from aea.crypto.base import LedgerApi
from aea.crypto.ethereum import EthereumApi
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.helpers.search.models import Attribute, DataModel, Description
from aea.mail.base import Address
from aea.skills.base import Behaviour

from packages.fetchai.protocols.oef.message import OEFMessage
from packages.fetchai.protocols.oef.serialization import DEFAULT_OEF, OEFSerializer
from packages.fetchai.protocols.tac.message import TACMessage
from packages.fetchai.protocols.tac.serialization import TACSerializer
from packages.fetchai.skills.tac_control_contract.game import Configuration, Game, Phase
from packages.fetchai.skills.tac_control_contract.parameters import Parameters

CONTROLLER_DATAMODEL = DataModel(
    "tac",
    [Attribute("version", str, True, "Version number of the TAC Controller Agent.")],
)

logger = logging.getLogger("aea.tac_control_skill")


class TACBehaviour(Behaviour):
    """This class implements the TAC control behaviour."""

    def __init__(self, **kwargs):
        """Instantiate the behaviour."""
        super().__init__(**kwargs)
        self._oef_msg_id = 0
        self._registered_desc = None  # type: Optional[Description]
        self.is_items_created = False
        self.can_start = False
        self.agent_counter = 0
        self.token_ids = []

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        parameters = cast(Parameters, self.context.parameters)
        contract = cast(Contract, self.context.contracts.erc1155)
        ledger_api = cast(EthereumApi, self.context.ledger_apis.apis.get("ethereum"))
        #  Deploy the contract if there is no address in the parameters
        if parameters.contract_address is None:
            contract.set_instance(ledger_api)
            transaction_message = contract.get_deploy_transaction(  # type: ignore
                deployer_address=self.context.agent_address,
                ledger_api=ledger_api,
                skill_callback_id=self.context.skill_id,
            )

            self.context.decision_maker_message_queue.put_nowait(transaction_message)
        else:
            self.context.logger.info("Setting the address of the deployed contract")
            contract.set_deployed_instance(
                ledger_api=ledger_api,
                contract_address=str(parameters.contract_address),
            )
            contract.token_ids = parameters.good_ids  # type: ignore

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        game = cast(Game, self.context.game)
        parameters = cast(Parameters, self.context.parameters)
        now = datetime.datetime.now()
        contract = cast(Contract, self.context.contracts.erc1155)

        if (
            contract.is_deployed
            and not self.is_items_created
            and game.phase.value == Phase.PRE_GAME.value
        ):
            self.context.configuration = Configuration(  # type: ignore
                parameters.version_id, parameters.tx_fee,
            )
            self.context.configuration.set_good_id_to_name(
                parameters.nb_goods, contract
            )
            token_ids_dictionary = cast(
                Dict[str, str], self.context.configuration.good_id_to_name
            )
            self.token_ids = [int(token_id) for token_id in token_ids_dictionary.keys()]
            self.context.logger.info("Creating the items.")
            transaction_message = self._create_items(self.token_ids)
            self.context.decision_maker_message_queue.put_nowait(transaction_message)
            time.sleep(10)
        if (
            game.phase.value == Phase.PRE_GAME.value
            and parameters.registration_start_time < now < parameters.start_time
        ):

            game.phase = Phase.GAME_REGISTRATION
            self._register_tac()
            self.context.logger.info(
                "[{}]: TAC open for registration until: {}".format(
                    self.context.agent_name, parameters.start_time
                )
            )
        elif (
            game.phase.value == Phase.GAME_REGISTRATION.value
            and parameters.start_time < now < parameters.end_time
        ):
            if game.registration.nb_agents < parameters.min_nb_agents:
                self._cancel_tac()
                game.phase = Phase.POST_GAME
                self._unregister_tac()
            else:
                self.context.logger.info("Setting Up the TAC game.")
                game.phase = Phase.GAME_SETUP
                # self._start_tac()
                game.create()
                self._unregister_tac()
                self.context.logger.info("Mint objects after registration.")
                for agent in self.context.configuration.agent_addr_to_name.keys():
                    self._mint_objects(
                        is_batch=True, address=agent,
                    )
                    self.agent_counter += 1
                game.phase = Phase.GAME
        elif (
            game.phase.value == Phase.GAME.value
            and parameters.start_time < now < parameters.end_time
            and self.can_start
        ):
            self.context.logger.info("Starting the TAC game.")
            self._start_tac()
        elif game.phase.value == Phase.GAME.value and now > parameters.end_time:
            self._cancel_tac()
            game.phase = Phase.POST_GAME

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        if self._registered_desc is not None:
            self._unregister_tac()

    def _register_tac(self) -> None:
        """
        Register on the OEF as a TAC controller agent.

        :return: None.
        """
        self._oef_msg_id += 1
        desc = Description(
            {"version": self.context.parameters.version_id},
            data_model=CONTROLLER_DATAMODEL,
        )
        self.context.logger.info(
            "[{}]: Registering TAC data model".format(self.context.agent_name)
        )
        oef_msg = OEFMessage(
            type=OEFMessage.Type.REGISTER_SERVICE,
            id=self._oef_msg_id,
            service_description=desc,
            service_id="",
        )
        self.context.outbox.put_message(
            to=DEFAULT_OEF,
            sender=self.context.agent_address,
            protocol_id=OEFMessage.protocol_id,
            message=OEFSerializer().encode(oef_msg),
        )
        self._registered_desc = desc

    def _unregister_tac(self) -> None:
        """
        Unregister from the OEF as a TAC controller agent.

        :return: None.
        """
        self._oef_msg_id += 1
        self.context.logger.info(
            "[{}]: Unregistering TAC data model".format(self.context.agent_name)
        )
        oef_msg = OEFMessage(
            type=OEFMessage.Type.UNREGISTER_SERVICE,
            id=self._oef_msg_id,
            service_description=self._registered_desc,
            service_id="",
        )
        self.context.outbox.put_message(
            to=DEFAULT_OEF,
            sender=self.context.agent_address,
            protocol_id=OEFMessage.protocol_id,
            message=OEFSerializer().encode(oef_msg),
        )
        self._registered_desc = None

    def _start_tac(self):
        """Create a game and send the game configuration to every registered agent."""
        game = cast(Game, self.context.game)
        # game.create()

        self.context.logger.info(
            "[{}]: Started competition:\n{}".format(
                self.context.agent_name, game.holdings_summary
            )
        )
        self.context.logger.info(
            "[{}]: Computed equilibrium:\n{}".format(
                self.context.agent_name, game.equilibrium_summary
            )
        )
        for agent_address in game.configuration.agent_addr_to_name.keys():
            agent_state = game.current_agent_states[agent_address]
            tac_msg = TACMessage(
                type=TACMessage.Type.GAME_DATA,
                amount_by_currency_id=agent_state.amount_by_currency_id,
                exchange_params_by_currency_id=agent_state.exchange_params_by_currency_id,
                quantities_by_good_id=agent_state.quantities_by_good_id,
                utility_params_by_good_id=agent_state.utility_params_by_good_id,
                tx_fee=game.configuration.tx_fee,
                agent_addr_to_name=game.configuration.agent_addr_to_name,
                good_id_to_name=game.configuration.good_id_to_name,
                version_id=game.configuration.version_id,
            )
            self.context.logger.debug(
                "[{}]: sending game data to '{}': {}".format(
                    self.context.agent_name, agent_address, str(tac_msg)
                )
            )
            self.context.outbox.put_message(
                to=agent_address,
                sender=self.context.agent_address,
                protocol_id=TACMessage.protocol_id,
                message=TACSerializer().encode(tac_msg),
            )

    def _cancel_tac(self):
        """Notify agents that the TAC is cancelled."""
        game = cast(Game, self.context.game)
        self.context.logger.info(
            "[{}]: Notifying agents that TAC is cancelled.".format(
                self.context.agent_name
            )
        )
        for agent_addr in game.registration.agent_addr_to_name.keys():
            tac_msg = TACMessage(type=TACMessage.Type.CANCELLED)
            self.context.outbox.put_message(
                to=agent_addr,
                sender=self.context.agent_address,
                protocol_id=TACMessage.protocol_id,
                message=TACSerializer().encode(tac_msg),
            )
        if game.phase == Phase.GAME:
            self.context.logger.info(
                "[{}]: Finished competition:\n{}".format(
                    self.context.agent_name, game.holdings_summary
                )
            )
            self.context.logger.info(
                "[{}]: Computed equilibrium:\n{}".format(
                    self.context.agent_name, game.equilibrium_summary
                )
            )

            self.context.is_active = False

    def _create_items(self, token_ids: Union[List[int], int]) -> TransactionMessage:
        contract = cast(Contract, self.context.contracts.erc1155)
        ledger_api = cast(LedgerApi, self.context.ledger_apis.apis.get("ethereum"))
        if type(token_ids) == list:
            return contract.get_create_batch_transaction(  # type: ignore
                deployer_address=self.context.agent_address,
                ledger_api=ledger_api,
                skill_callback_id=self.context.skill_id,
                token_ids=token_ids,
            )
        else:
            return contract.get_create_single_transaction(  # type: ignore
                deployer_address=self.context.agent_address,
                ledger_api=ledger_api,
                skill_callback_id=self.context.skill_id,
                token_id=token_ids,
            )

    def _mint_objects(
        self, is_batch: bool, address: Address, token_id: int = None
    ):
        self.context.logger.info("Minting the items")
        contract = self.context.contracts.erc1155
        parameters = cast(Parameters, self.context.parameters)
        if is_batch:
            minting = [parameters.base_good_endowment] * parameters.nb_goods
            transaction_message = contract.get_mint_batch_transaction(
                deployer_address=self.context.agent_address,
                recipient_address=address,
                mint_quantities=minting,
                ledger_api=self.context.ledger_apis.apis.get("ethereum"),
                skill_callback_id=self.context.skill_id,
                token_ids=self.token_ids,
            )
            self.context.decision_maker_message_queue.put_nowait(transaction_message)
        else:
            self.context.logger.info("Minting the game currency")
            contract = self.context.contracts.erc1155
            parameters = cast(Parameters, self.context.parameters)
            transaction_message = contract.get_mint_single_tx(
                deployer_address=self.context.agent_address,
                recipient_address=self.context.agent_address,
                mint_quantity=parameters.money_endowment,
                ledger_api=self.context.ledger_apis.apis.get("ethereum"),
                skill_callback_id=self.context.skill_id,
                token_id=token_id,
            )
            self.context.decision_maker_message_queue.put_nowait(transaction_message)
