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
from typing import List, cast

from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.protocols.contract_api.message import ContractApiMessage
from packages.fetchai.skills.tac_control.behaviours import TacBehaviour
from packages.fetchai.skills.tac_control_contract.dialogues import (
    ContractApiDialogue,
    ContractApiDialogues,
)
from packages.fetchai.skills.tac_control_contract.game import (
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

LEDGER_API_ADDRESS = "///"


class TacBehaviour(TacBehaviour):
    """This class implements the TAC control behaviour."""

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        super().setup()
        parameters = cast(Parameters, self.context.parameters)
        if not parameters.is_contract_deployed:
            self._request_contract_deploy_transaction()

    def _request_contract_deploy_transaction(self) -> None:
        """
        Request contract deploy transaction

        :return: None
        """
        parameters = cast(Parameters, self.context.parameters)
        contract_api_dialogues = cast(
            ContractApiDialogues, self.context.contract_api_dialogues
        )
        contract_api_msg, contract_api_dialogue = contract_api_dialogues.create(
            counterparty=LEDGER_API_ADDRESS,
            performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
            ledger_id=parameters.ledger_id,
            contract_id="fetchai/erc1155:0.10.0",
            callable="get_deploy_transaction",
            kwargs=ContractApiMessage.Kwargs(
                {"deployer_address": self.context.agent_address}
            ),
        )
        contract_api_dialogue = cast(ContractApiDialogue, contract_api_dialogue,)
        contract_api_dialogue.terms = strategy.get_deploy_terms()
        self.context.outbox.put_message(message=contract_api_msg)
        self.context.logger.info("requesting contract deployment transaction...")

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        game = cast(Game, self.context.game)
        parameters = cast(Parameters, self.context.parameters)
        now = datetime.datetime.now()
        if (
            game.phase.value == Phase.CONTRACT_DEPLOYED.value
            and parameters.registration_start_time
            < now
            < parameters.registration_end_time
        ):
            game.phase = Phase.GAME_REGISTRATION
            self._register_tac(parameters)
            self.context.logger.info(
                "TAC open for registration until: {}".format(parameters.start_time)
            )
        elif (
            game.phase.value == Phase.GAME_REGISTRATION.value
            and parameters.registration_end_time < now < parameters.start_time
        ):
            self.context.logger.info("closing registration!")
            if game.registration.nb_agents < parameters.min_nb_agents:
                self.context.logger.info(
                    "registered agents={}, minimum agents required={}".format(
                        game.registration.nb_agents, parameters.min_nb_agents,
                    )
                )
                self._cancel_tac(game)
                game.phase = Phase.POST_GAME
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
            self._request_create_items_transaction(game)
        elif game.phase.value == Phase.TOKENS_CREATED.value:
            game.phase = Phase.TOKENS_MINTING_PROPOSAL
            self._request_mint_items_transaction(game)
        elif (
            game.phase.value == Phase.TOKENS_MINTED.value
            and parameters.start_time < now < parameters.end_time
        ):
            game.phase = Phase.GAME
            self._start_tac(game)
        elif game.phase.value == Phase.GAME.value and now > parameters.end_time:
            game.phase = Phase.POST_GAME
            self._cancel_tac(game)
            self.context.is_active = False

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        super().teardown()

    def _request_create_items_transaction(self, game: Game) -> None:
        """
        Request token create transaction

        :return: None
        """
        parameters = cast(Parameters, self.context.parameters)
        contract_api_dialogues = cast(
            ContractApiDialogues, self.context.contract_api_dialogues
        )
        token_ids = [int(good_id) for good_id in game.conf.good_id_to_name.keys()] + [
            int(currency_id) for currency_id in game.conf.currency_id_to_name.keys()
        ]
        contract_api_msg, contract_api_dialogue = contract_api_dialogues.create(
            counterparty=LEDGER_API_ADDRESS,
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            ledger_id=parameters.ledger_id,
            contract_id="fetchai/erc1155:0.10.0",
            callable="get_create_batch_transaction",
            kwargs=ContractApiMessage.Kwargs(
                {"deployer_address": self.context.agent_address, "token_ids": token_ids}
            ),
        )
        contract_api_dialogue = cast(ContractApiDialogue, contract_api_dialogue)
        contract_api_dialogue.terms = strategy.get_create_items_terms()
        self.context.outbox.put_message(message=contract_api_msg)
        self.context.logger.info("requesting create items transaction...")

    def _request_mint_items_transaction(self, game: Game) -> None:
        """
        Request token mint transaction

        :return: None
        """
        self.context.logger.info("requesting mint_items transactions.")
        for agent_state in game.initial_agent_states.values():
            parameters = cast(Parameters, self.context.parameters)
            token_ids = []  # type: List[int]
            mint_quantities = []  # type: List[int]
            for good_id, quantity in agent_state.quantities_by_good_id.items():
                token_ids.append(int(good_id))
                mint_quantities.append(quantity)
            for currency_id, amount in agent_state.amount_by_currency_id.items():
                token_ids.append(int(currency_id))
                mint_quantities.append(amount)
            contract_api_dialogues = cast(
                ContractApiDialogues, self.context.contract_api_dialogues
            )
            contract_api_msg, contract_api_dialogue = contract_api_dialogues.create(
                counterparty=LEDGER_API_ADDRESS,
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
                ledger_id=parameters.ledger_id,
                contract_id="fetchai/erc1155:0.10.0",
                contract_address=parameters.contract_address,
                callable="get_mint_batch_transaction",
                kwargs=ContractApiMessage.Kwargs(
                    {
                        "deployer_address": self.context.agent_address,
                        "recipient_address": self.context.agent_address,
                        "token_ids": token_ids,
                        "mint_quantities": mint_quantities,
                    }
                ),
            )
            contract_api_dialogue = cast(ContractApiDialogue, contract_api_dialogue)
            contract_api_dialogue.terms = strategy.get_mint_token_terms()
            self.context.outbox.put_message(message=contract_api_msg)


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
                    "cannot verify whether contract deployment was successful. Retrying..."
                )
            elif tx_receipt.status != 1:
                self.context.is_active = False
                self.context.warning(
                    "the contract did not deployed successfully. Transaction hash: {}. Aborting!".format(
                        tx_receipt.transactionHash.hex()
                    )
                )
            else:
                self.context.logger.info(
                    "the contract was successfully deployed. Contract address: {}. Transaction hash: {}".format(
                        tx_receipt.contractAddress, tx_receipt.transactionHash.hex(),
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
                    "cannot verify whether token creation was successful. Retrying..."
                )
            elif tx_receipt.status != 1:
                self.context.is_active = False
                self.context.warning(
                    "the token creation wasn't successful. Transaction hash: {}. Aborting!".format(
                        tx_receipt.transactionHash.hex()
                    )
                )
            else:
                self.context.logger.info(
                    "successfully created the tokens. Transaction hash: {}".format(
                        tx_receipt.transactionHash.hex()
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
                        "cannot verify whether token minting for agent_addr={} was successful. Retrying...".format(
                            agent_addr
                        )
                    )
                elif tx_receipt.status != 1:
                    self.context.is_active = False
                    self.context.logger.warning(
                        "the token minting for agent_addr={} wasn't successful. Transaction hash: {}. Aborting!".format(
                            agent_addr, tx_receipt.transactionHash.hex(),
                        )
                    )
                else:
                    self.context.logger.info(
                        "successfully minted the tokens for agent_addr={}. Transaction hash: {}".format(
                            agent_addr, tx_receipt.transactionHash.hex(),
                        )
                    )
                    game.contract_manager.add_confirmed_mint_tokens_agents(agent_addr)
                    if len(game.contract_manager.confirmed_mint_tokens_agents) == len(
                        game.initial_agent_states
                    ):
                        self.context.logger.info("All tokens minted!")
                        game.phase = Phase.TOKENS_MINTED
