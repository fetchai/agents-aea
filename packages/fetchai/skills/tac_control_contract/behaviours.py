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

from aea.crypto.base import LedgerApi
from aea.helpers.search.models import Attribute, DataModel, Description
from aea.protocols.signing.message import SigningMessage
from aea.skills.behaviours import SimpleBehaviour, TickerBehaviour

from packages.fetchai.contracts.erc1155.contract import ERC1155Contract
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.tac.message import TacMessage
from packages.fetchai.skills.tac_control_contract.game import (
    AgentState,
    Configuration,
    Game,
    Phase,
)
from packages.fetchai.skills.tac_control_contract.helpers import (
    generate_currency_id_to_name,
    generate_currency_ids,
    generate_good_id_to_name,
    generate_good_ids,
)
from packages.fetchai.skills.tac_control_contract.parameters import Parameters

CONTROLLER_DATAMODEL = DataModel(
    "tac",
    [Attribute("version", str, True, "Version number of the TAC Controller Agent.")],
)


class TACBehaviour(SimpleBehaviour):
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
        ledger_api = self.context.ledger_apis.get_api(parameters.ledger)
        if parameters.is_contract_deployed:
            self._set_game(parameters, ledger_api, contract)
        else:
            self._deploy_contract(ledger_api, contract)

    def _set_game(
        self, parameters: Parameters, ledger_api: LedgerApi, contract: ERC1155Contract
    ) -> None:
        """Set the contract and configuration based on provided parameters."""
        game = cast(Game, self.context.game)
        game.phase = Phase.CONTRACT_DEPLOYED
        self.context.logger.info("Setting up the game")
        configuration = Configuration(parameters.version_id, parameters.tx_fee,)
        configuration.good_id_to_name = generate_good_id_to_name(parameters.good_ids)
        configuration.currency_id_to_name = generate_currency_id_to_name(
            parameters.currency_ids
        )
        configuration.contract_address = parameters.contract_address
        game.conf = configuration

    def _deploy_contract(
        self, ledger_api: LedgerApi, contract: ERC1155Contract
    ) -> None:
        """Send deploy contract tx msg to decision maker."""
        game = cast(Game, self.context.game)
        game.phase = Phase.CONTRACT_DEPLOYMENT_PROPOSAL
        self.context.logger.info(
            "[{}]: Sending deploy transaction to decision maker.".format(
                self.context.agent_name
            )
        )
        # request deploy tx
        # contract.set_instance(ledger_api)
        # transaction_message = contract.get_deploy_transaction_msg(
        #     deployer_address=self.context.agent_address,
        #     ledger_api=ledger_api,
        #     skill_callback_id=self.context.skill_id,
        # )
        # self.context.decision_maker_message_queue.put_nowait(transaction_message)

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        game = cast(Game, self.context.game)
        parameters = cast(Parameters, self.context.parameters)
        now = datetime.datetime.now()
        contract = cast(ERC1155Contract, self.context.contracts.erc1155)
        ledger_api = self.context.ledger_apis.get_api(parameters.ledger)
        if (
            game.phase.value == Phase.CONTRACT_DEPLOYED.value
            and parameters.registration_start_time
            < now
            < parameters.registration_end_time
        ):
            game.phase = Phase.GAME_REGISTRATION
            self._register_tac(parameters)
        elif (
            game.phase.value == Phase.GAME_REGISTRATION.value
            and parameters.registration_end_time < now < parameters.start_time
        ):
            self.context.logger.info(
                "[{}] Closing registration!".format(self.context.agent_name)
            )
            if game.registration.nb_agents < parameters.min_nb_agents:
                game.phase = Phase.CANCELLED_GAME
                self.context.logger.info(
                    "[{}]: Registered agents={}, minimum agents required={}".format(
                        self.context.agent_name,
                        game.registration.nb_agents,
                        parameters.min_nb_agents,
                    )
                )
                self._end_tac(game, "cancelled")
                self._unregister_tac()
                self.context.is_active = False
            else:
                game.phase = Phase.GAME_SETUP
                game.create()
                self._unregister_tac()
        elif (
            game.phase.value == Phase.GAME_SETUP.value
            and parameters.registration_end_time < now < parameters.start_time
        ):
            game.phase = Phase.TOKENS_CREATION_PROPOSAL
            self._create_items(game, ledger_api, contract)
        elif game.phase.value == Phase.TOKENS_CREATED.value:
            game.phase = Phase.TOKENS_MINTING_PROPOSAL
            self._mint_items(game, ledger_api, contract)
        elif (
            game.phase.value == Phase.TOKENS_MINTED.value
            and parameters.start_time < now < parameters.end_time
        ):
            game.phase = Phase.GAME
            self._start_tac(game)
        elif game.phase.value == Phase.GAME.value and now > parameters.end_time:
            game.phase = Phase.POST_GAME
            self._end_tac(game, "finished")
            self._game_finished_summary(game)
            self.context.is_active = False

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        if self._registered_desc is not None:
            self._unregister_tac()

    def _register_tac(self, parameters) -> None:
        """
        Register on the OEF as a TAC controller agent.

        :return: None.
        """
        self._oef_msg_id += 1
        desc = Description(
            {"version": parameters.version_id}, data_model=CONTROLLER_DATAMODEL,
        )
        self.context.logger.info(
            "[{}]: Registering TAC data model".format(self.context.agent_name)
        )
        oef_msg = OefSearchMessage(
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            dialogue_reference=(str(self._oef_msg_id), ""),
            service_description=desc,
        )
        oef_msg.counterparty = self.context.search_service_address
        self.context.outbox.put_message(message=oef_msg)
        self._registered_desc = desc
        self.context.logger.info(
            "[{}]: TAC open for registration until: {}".format(
                self.context.agent_name, parameters.registration_end_time
            )
        )

    def _unregister_tac(self) -> None:
        """
        Unregister from the OEF as a TAC controller agent.

        :return: None.
        """
        if self._registered_desc is not None:
            self._oef_msg_id += 1
            self.context.logger.info(
                "[{}]: Unregistering TAC data model".format(self.context.agent_name)
            )
            oef_msg = OefSearchMessage(
                performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
                dialogue_reference=(str(self._oef_msg_id), ""),
                service_description=self._registered_desc,
            )
            oef_msg.counterparty = self.context.search_service_address
            self.context.outbox.put_message(message=oef_msg)
            self._registered_desc = None

    def _create_items(
        self, game: Game, ledger_api: LedgerApi, contract: ERC1155Contract
    ) -> None:
        """Send create items transaction to decision maker."""
        self.context.logger.info(
            "[{}]: Sending create_items transaction to decision maker.".format(
                self.context.agent_name
            )
        )
        tx_msg = self._get_create_items_tx_msg(  # pylint: disable=assignment-from-none
            game.conf, ledger_api, contract
        )
        self.context.decision_maker_message_queue.put_nowait(tx_msg)

    def _mint_items(
        self, game: Game, ledger_api: LedgerApi, contract: ERC1155Contract
    ) -> None:
        """Send mint items transactions to decision maker."""
        self.context.logger.info(
            "[{}]: Sending mint_items transactions to decision maker.".format(
                self.context.agent_name
            )
        )
        for agent_state in game.initial_agent_states.values():
            tx_msg = self._get_mint_goods_and_currency_tx_msg(  # pylint: disable=assignment-from-none
                agent_state, ledger_api, contract
            )
            self.context.decision_maker_message_queue.put_nowait(tx_msg)

    def _start_tac(self, game: Game) -> None:
        """Create a game and send the game configuration to every registered agent."""
        self.context.logger.info(
            "[{}]: Starting competition with configuration:\n{}".format(
                self.context.agent_name, game.holdings_summary
            )
        )
        self.context.logger.info(
            "[{}]: Computed theoretical equilibrium:\n{}".format(
                self.context.agent_name, game.equilibrium_summary
            )
        )
        for agent_address in game.conf.agent_addr_to_name.keys():
            agent_state = game.current_agent_states[agent_address]
            tac_msg = TacMessage(
                performative=TacMessage.Performative.GAME_DATA,
                amount_by_currency_id=agent_state.amount_by_currency_id,
                exchange_params_by_currency_id=agent_state.exchange_params_by_currency_id,
                quantities_by_good_id=agent_state.quantities_by_good_id,
                utility_params_by_good_id=agent_state.utility_params_by_good_id,
                tx_fee=game.conf.tx_fee,
                agent_addr_to_name=game.conf.agent_addr_to_name,
                good_id_to_name=game.conf.good_id_to_name,
                currency_id_to_name=game.conf.currency_id_to_name,
                version_id=game.conf.version_id,
                info={"contract_address": game.conf.contract_address},
            )
            self.context.logger.debug(
                "[{}]: sending game data to '{}'.".format(
                    self.context.agent_name, agent_address
                )
            )
            self.context.logger.debug(
                "[{}]: game data={}".format(self.context.agent_name, str(tac_msg))
            )
            tac_msg.counterparty = agent_address
            self.context.outbox.put_message(message=tac_msg)

    def _end_tac(self, game: Game, reason: str) -> None:
        """Notify agents that the TAC is cancelled."""
        self.context.logger.info(
            "[{}]: Notifying agents that TAC is {}.".format(
                self.context.agent_name, reason
            )
        )
        for agent_addr in game.registration.agent_addr_to_name.keys():
            tac_msg = TacMessage(performative=TacMessage.Performative.CANCELLED)
            tac_msg.counterparty = agent_addr
            self.context.outbox.put_message(message=tac_msg)

    def _game_finished_summary(self, game: Game) -> None:
        """Provide summary of game stats."""
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

    def _get_create_items_tx_msg(  # pylint: disable=no-self-use
        self,
        configuration: Configuration,
        ledger_api: LedgerApi,
        contract: ERC1155Contract,
    ) -> SigningMessage:
        # request tx
        # token_ids = [
        #     int(good_id) for good_id in configuration.good_id_to_name.keys()
        # ] + [
        #     int(currency_id) for currency_id in configuration.currency_id_to_name.keys()
        # ]
        # tx_msg = contract.get_create_batch_transaction_msg(
        #     deployer_address=self.context.agent_address,
        #     ledger_api=ledger_api,
        #     skill_callback_id=self.context.skill_id,
        #     token_ids=token_ids,
        # )
        return None  # type: ignore

    def _get_mint_goods_and_currency_tx_msg(  # pylint: disable=no-self-use,useless-return
        self, agent_state: AgentState, ledger_api: LedgerApi, contract: ERC1155Contract,
    ) -> SigningMessage:
        token_ids = []  # type: List[int]
        mint_quantities = []  # type: List[int]
        for good_id, quantity in agent_state.quantities_by_good_id.items():
            token_ids.append(int(good_id))
            mint_quantities.append(quantity)
        for currency_id, amount in agent_state.amount_by_currency_id.items():
            token_ids.append(int(currency_id))
            mint_quantities.append(amount)
        # tx_msg = contract.get_mint_batch_transaction_msg(
        #     deployer_address=self.context.agent_address,
        #     recipient_address=agent_state.agent_address,
        #     mint_quantities=mint_quantities,
        #     ledger_api=ledger_api,
        #     skill_callback_id=self.context.skill_id,
        #     token_ids=token_ids,
        # )
        return None  # type: ignore


class ContractBehaviour(TickerBehaviour):
    """This class implements the TAC control behaviour."""

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        game = cast(Game, self.context.game)
        parameters = cast(Parameters, self.context.parameters)
        ledger_api = self.context.ledger_apis.get_api(parameters.ledger)
        if game.phase.value == Phase.CONTRACT_DEPLOYING.value:
            tx_receipt = ledger_api.get_transaction_receipt(
                tx_digest=game.contract_manager.deploy_tx_digest
            )
            if tx_receipt is None:
                self.context.logger.info(
                    "[{}]: Cannot verify whether contract deployment was successful. Retrying...".format(
                        self.context.agent_name
                    )
                )
            elif tx_receipt.status != 1:
                self.context.is_active = False
                self.context.warning(
                    "[{}]: The contract did not deployed successfully. Transaction hash: {}. Aborting!".format(
                        self.context.agent_name, tx_receipt.transactionHash.hex()
                    )
                )
            else:
                self.context.logger.info(
                    "[{}]: The contract was successfully deployed. Contract address: {}. Transaction hash: {}".format(
                        self.context.agent_name,
                        tx_receipt.contractAddress,
                        tx_receipt.transactionHash.hex(),
                    )
                )
                configuration = Configuration(parameters.version_id, parameters.tx_fee,)
                currency_ids = generate_currency_ids(parameters.nb_currencies)
                configuration.currency_id_to_name = generate_currency_id_to_name(
                    currency_ids
                )
                good_ids = generate_good_ids(parameters.nb_goods)
                configuration.good_id_to_name = generate_good_id_to_name(good_ids)
                configuration.contract_address = tx_receipt.contractAddress
                game.conf = configuration
                game.phase = Phase.CONTRACT_DEPLOYED
        elif game.phase.value == Phase.TOKENS_CREATING.value:
            tx_receipt = ledger_api.get_transaction_receipt(
                tx_digest=game.contract_manager.create_tokens_tx_digest
            )
            if tx_receipt is None:
                self.context.logger.info(
                    "[{}]: Cannot verify whether token creation was successful. Retrying...".format(
                        self.context.agent_name
                    )
                )
            elif tx_receipt.status != 1:
                self.context.is_active = False
                self.context.warning(
                    "[{}]: The token creation wasn't successful. Transaction hash: {}. Aborting!".format(
                        self.context.agent_name, tx_receipt.transactionHash.hex()
                    )
                )
            else:
                self.context.logger.info(
                    "[{}]: Successfully created the tokens. Transaction hash: {}".format(
                        self.context.agent_name, tx_receipt.transactionHash.hex()
                    )
                )
                game.phase = Phase.TOKENS_CREATED
        elif game.phase.value == Phase.TOKENS_MINTING.value:
            for (
                agent_addr,
                tx_digest,
            ) in game.contract_manager.mint_tokens_tx_digests.items():
                if agent_addr in game.contract_manager.confirmed_mint_tokens_agents:
                    continue
                tx_receipt = ledger_api.get_transaction_receipt(tx_digest=tx_digest)
                if tx_receipt is None:
                    self.context.logger.info(
                        "[{}]: Cannot verify whether token minting for agent_addr={} was successful. Retrying...".format(
                            self.context.agent_name, agent_addr
                        )
                    )
                elif tx_receipt.status != 1:
                    self.context.is_active = False
                    self.context.logger.warning(
                        "[{}]: The token minting for agent_addr={} wasn't successful. Transaction hash: {}. Aborting!".format(
                            self.context.agent_name,
                            agent_addr,
                            tx_receipt.transactionHash.hex(),
                        )
                    )
                else:
                    self.context.logger.info(
                        "[{}]: Successfully minted the tokens for agent_addr={}. Transaction hash: {}".format(
                            self.context.agent_name,
                            agent_addr,
                            tx_receipt.transactionHash.hex(),
                        )
                    )
                    game.contract_manager.add_confirmed_mint_tokens_agents(agent_addr)
                    if len(game.contract_manager.confirmed_mint_tokens_agents) == len(
                        game.initial_agent_states
                    ):
                        self.context.logger.info("All tokens minted!")
                        game.phase = Phase.TOKENS_MINTED
