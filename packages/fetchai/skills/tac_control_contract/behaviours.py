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
from typing import List, Optional, cast

from aea.crypto.ethereum import EthereumApi
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.helpers.search.models import Attribute, DataModel, Description
from aea.skills.base import Behaviour

from packages.fetchai.contracts.erc1155.contract import ERC1155Contract
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.oef_search.serialization import OefSearchSerializer
from packages.fetchai.protocols.tac.message import TacMessage
from packages.fetchai.protocols.tac.serialization import TacSerializer
from packages.fetchai.skills.tac_control_contract.game import (
    AgentState,
    Configuration,
    Game,
    Phase,
)
from packages.fetchai.skills.tac_control_contract.helpers import (
    generate_currency_id_to_name,
    generate_good_id_to_name,
)
from packages.fetchai.skills.tac_control_contract.parameters import Parameters

CONTROLLER_DATAMODEL = DataModel(
    "tac",
    [Attribute("version", str, True, "Version number of the TAC Controller Agent.")],
)


class TACBehaviour(Behaviour):
    """This class implements the TAC control behaviour."""

    def __init__(self, **kwargs):
        """Instantiate the behaviour."""
        super().__init__(**kwargs)
        self._oef_msg_id = 0
        self._registered_desc = None  # type: Optional[Description]

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        parameters = cast(Parameters, self.context.parameters)
        contract = cast(ERC1155Contract, self.context.contracts.erc1155)
        ledger_api = cast(
            EthereumApi, self.context.ledger_apis.apis.get(parameters.ledger)
        )
        if parameters.contract_address is None:
            self.context.logger.debug("Sending deploy transaction to decision maker.")
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
            game = cast(Game, self.context.game)
            configuration = Configuration(  # type: ignore
                parameters.version_id, parameters.tx_fee,
            )
            configuration.good_id_to_name = generate_good_id_to_name(
                parameters.good_ids
            )
            configuration.currency_id_to_name = generate_currency_id_to_name(
                parameters.currency_id
            )
            game.conf = configuration

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        game = cast(Game, self.context.game)
        parameters = cast(Parameters, self.context.parameters)
        now = datetime.datetime.now()
        contract = cast(ERC1155Contract, self.context.contracts.erc1155)
        ledger_api = cast(
            EthereumApi, self.context.ledger_apis.apis.get(parameters.ledger)
        )
        if (
            game.phase.value == Phase.PRE_GAME.value
            and parameters.registration_start_time
            < now
            < parameters.registration_end_time
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
            and parameters.registration_end_time < now < parameters.start_time
        ):
            if game.registration.nb_agents < parameters.min_nb_agents:
                self._cancel_tac()
                game.phase = Phase.POST_GAME
                self._unregister_tac()
            else:
                self.context.logger.info("Setting Up the TAC game.")
                game.phase = Phase.GAME_SETUP
                game.create()
                self._unregister_tac()
        elif (
            game.phase.value == Phase.GAME_SETUP.value
            and parameters.registration_end_time < now < parameters.start_time
            and contract.is_deployed
        ):
            game.phase = Phase.GAME_TOKEN_CREATION
            self.context.logger.info(
                "Sending create_items transaction to decision maker."
            )
            tx_msg = self._create_items(game.conf, ledger_api, contract)
            self.context.decision_maker_message_queue.put_nowait(tx_msg)
        elif (
            game.phase.value == Phase.GAME_TOKENS_CREATED.value
            and parameters.registration_end_time < now < parameters.start_time
        ):
            game.phase = Phase.GAME_TOKEN_MINTING
            self.context.logger.info(
                "Sending mint_items transactions to decision maker."
            )
            for agent_state in game.initial_agent_states.values():
                transaction_message = self._mint_goods_and_currency(
                    agent_state, ledger_api, contract
                )
                self.context.decision_maker_message_queue.put_nowait(
                    transaction_message
                )
        elif (
            game.phase.value == Phase.GAME.value
            and parameters.start_time < now < parameters.end_time
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
        oef_msg = OefSearchMessage(
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            dialogue_reference=(str(self._oef_msg_id), ""),
            service_description=desc,
        )
        self.context.outbox.put_message(
            to=self.context.search_service_address,
            sender=self.context.agent_address,
            protocol_id=OefSearchMessage.protocol_id,
            message=OefSearchSerializer().encode(oef_msg),
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
        oef_msg = OefSearchMessage(
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            dialogue_reference=(str(self._oef_msg_id), ""),
            service_description=self._registered_desc,
        )
        self.context.outbox.put_message(
            to=self.context.search_service_address,
            sender=self.context.agent_address,
            protocol_id=OefSearchMessage.protocol_id,
            message=OefSearchSerializer().encode(oef_msg),
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
        for agent_address in game.conf.agent_addr_to_name.keys():
            agent_state = game.current_agent_states[agent_address]
            tac_msg = TacMessage(
                type=TacMessage.Performative.GAME_DATA,
                amount_by_currency_id=agent_state.amount_by_currency_id,
                exchange_params_by_currency_id=agent_state.exchange_params_by_currency_id,
                quantities_by_good_id=agent_state.quantities_by_good_id,
                utility_params_by_good_id=agent_state.utility_params_by_good_id,
                tx_fee=game.conf.tx_fee,
                agent_addr_to_name=game.conf.agent_addr_to_name,
                good_id_to_name=game.conf.good_id_to_name,
                currency_id_to_name=game.conf.currency_id_to_name,
                version_id=game.conf.version_id,
                contract_address=game.conf.contract_address,
            )
            self.context.logger.debug(
                "[{}]: sending game data to '{}': {}".format(
                    self.context.agent_name, agent_address, str(tac_msg)
                )
            )
            self.context.outbox.put_message(
                to=agent_address,
                sender=self.context.agent_address,
                protocol_id=TacMessage.protocol_id,
                message=TacSerializer().encode(tac_msg),
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
            tac_msg = TacMessage(type=TacMessage.Performative.CANCELLED)
            self.context.outbox.put_message(
                to=agent_addr,
                sender=self.context.agent_address,
                protocol_id=TacMessage.protocol_id,
                message=TacSerializer().encode(tac_msg),
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

    def _create_items(
        self,
        configuration: Configuration,
        ledger_api: EthereumApi,
        contract: ERC1155Contract,
    ) -> TransactionMessage:
        token_ids = [
            int(good_id) for good_id in configuration.good_id_to_name.keys()
        ] + [
            int(currency_id) for currency_id in configuration.currency_id_to_name.keys()
        ]
        tx_msg = contract.get_create_batch_transaction(
            deployer_address=self.context.agent_address,
            ledger_api=ledger_api,
            skill_callback_id=self.context.skill_id,
            token_ids=token_ids,
        )
        return tx_msg

    def _mint_goods_and_currency(
        self,
        agent_state: AgentState,
        ledger_api: EthereumApi,
        contract: ERC1155Contract,
    ) -> TransactionMessage:
        token_ids = []  # type: List[int]
        mint_quantities = []  # type: List[int]
        for good_id, quantity in agent_state.quantities_by_good_id.items():
            token_ids.append(int(good_id))
            mint_quantities.append(quantity)
        for currency_id, amount in agent_state.amount_by_currency_id.items():
            token_ids.append(int(currency_id))
            mint_quantities.append(amount)
        tx_msg = contract.get_mint_batch_transaction(
            deployer_address=self.context.agent_address,
            recipient_address=agent_state.agent_address,
            mint_quantities=mint_quantities,
            ledger_api=ledger_api,
            skill_callback_id=self.context.skill_id,
            token_ids=token_ids,
        )
        return tx_msg
