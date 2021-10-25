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

from packages.fetchai.connections.ledger.base import (
    CONNECTION_ID as LEDGER_CONNECTION_PUBLIC_ID,
)
from packages.fetchai.protocols.contract_api.message import ContractApiMessage
from packages.fetchai.skills.tac_control.behaviours import (
    TacBehaviour as BaseTacBehaviour,
)
from packages.fetchai.skills.tac_control_contract.dialogues import (
    ContractApiDialogue,
    ContractApiDialogues,
)
from packages.fetchai.skills.tac_control_contract.game import Game, Phase
from packages.fetchai.skills.tac_control_contract.parameters import Parameters


LEDGER_API_ADDRESS = str(LEDGER_CONNECTION_PUBLIC_ID)


class TacBehaviour(BaseTacBehaviour):
    """This class implements the TAC control behaviour."""

    def setup(self) -> None:
        """Implement the setup."""
        super().setup()
        parameters = cast(Parameters, self.context.parameters)
        if not parameters.is_contract_deployed:
            game = cast(Game, self.context.game)
            game.phase = Phase.CONTRACT_DEPLOYMENT_PROPOSAL
            self._request_contract_deploy_transaction()

    def _request_contract_deploy_transaction(self) -> None:
        """Request contract deploy transaction"""
        parameters = cast(Parameters, self.context.parameters)
        contract_api_dialogues = cast(
            ContractApiDialogues, self.context.contract_api_dialogues
        )
        contract_api_msg, contract_api_dialogue = contract_api_dialogues.create(
            counterparty=LEDGER_API_ADDRESS,
            performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
            ledger_id=parameters.ledger_id,
            contract_id=parameters.contract_id,
            callable=ContractApiDialogue.Callable.GET_DEPLOY_TRANSACTION.value,
            kwargs=ContractApiMessage.Kwargs(
                {"deployer_address": self.context.agent_address, "gas": parameters.gas}
            ),
        )
        contract_api_dialogue = cast(ContractApiDialogue, contract_api_dialogue,)
        contract_api_dialogue.terms = parameters.get_deploy_terms()
        contract_api_dialogue.callable = (
            ContractApiDialogue.Callable.GET_DEPLOY_TRANSACTION
        )
        self.context.outbox.put_message(message=contract_api_msg)
        self.context.logger.info("requesting contract deployment transaction...")

    def act(self) -> None:
        """Implement the act."""
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
            self._register_tac()
            self.context.logger.info(
                "TAC open for registration until: {}".format(
                    parameters.registration_end_time
                )
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
                game.conf.contract_address = parameters.contract_address
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
        elif game.phase.value == Phase.TOKENS_MINTING_PROPOSAL.value:
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

    def _request_create_items_transaction(self, game: Game) -> None:
        """
        Request token create transaction

        :param game: the game
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
            contract_id=parameters.contract_id,
            contract_address=parameters.contract_address,
            callable=ContractApiDialogue.Callable.GET_CREATE_BATCH_TRANSACTION.value,
            kwargs=ContractApiMessage.Kwargs(
                {
                    "deployer_address": self.context.agent_address,
                    "token_ids": token_ids,
                    "gas": parameters.gas,
                }
            ),
        )
        contract_api_dialogue = cast(ContractApiDialogue, contract_api_dialogue)
        contract_api_dialogue.terms = parameters.get_create_token_terms()
        contract_api_dialogue.callable = (
            ContractApiDialogue.Callable.GET_CREATE_BATCH_TRANSACTION
        )
        self.context.outbox.put_message(message=contract_api_msg)
        self.context.logger.info("requesting create items transaction...")

    def _request_mint_items_transaction(self, game: Game) -> None:
        """
        Request token mint transaction

        :param game: the game
        """
        if not game.is_allowed_to_mint:
            return
        game.is_allowed_to_mint = False
        agent_state = game.get_next_agent_state_for_minting()
        if agent_state is None:
            return
        name = game.registration.agent_addr_to_name[agent_state.agent_address]
        self.context.logger.info(
            f"requesting mint_items transactions for agent={name}."
        )
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
            contract_id=parameters.contract_id,
            contract_address=parameters.contract_address,
            callable=ContractApiDialogue.Callable.GET_MINT_BATCH_TRANSACTION.value,
            kwargs=ContractApiMessage.Kwargs(
                {
                    "deployer_address": self.context.agent_address,
                    "recipient_address": agent_state.agent_address,
                    "token_ids": token_ids,
                    "mint_quantities": mint_quantities,
                    "gas": parameters.gas,
                }
            ),
        )
        contract_api_dialogue = cast(ContractApiDialogue, contract_api_dialogue)
        contract_api_dialogue.terms = parameters.get_mint_token_terms()
        contract_api_dialogue.callable = (
            ContractApiDialogue.Callable.GET_MINT_BATCH_TRANSACTION
        )
        self.context.outbox.put_message(message=contract_api_msg)
