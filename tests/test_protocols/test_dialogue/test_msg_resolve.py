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
"""
This module contains the tests for the dialogue messages resolution.

issue: https://github.com/fetchai/agents-aea/issues/2128
"""

from aea.common import Address
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue

from packages.fetchai.protocols.tac.dialogues import TacDialogue, TacDialogues
from packages.fetchai.protocols.tac.message import TacMessage


def role_participant(  # pylint: disable=unused-argument
    message: Message, receiver_address: Address
) -> BaseDialogue.Role:
    """Infer the role of the agent from an incoming/outgoing first message

    :param message: an incoming/outgoing first message
    :param receiver_address: the address of the receiving agent
    :return: The role of the agent
    """
    return TacDialogue.Role.PARTICIPANT


def role_controller(  # pylint: disable=unused-argument
    message: Message, receiver_address: Address
) -> BaseDialogue.Role:
    """Infer the role of the agent from an incoming/outgoing first message

    :param message: an incoming/outgoing first message
    :param receiver_address: the address of the receiving agent
    :return: The role of the agent
    """
    return TacDialogue.Role.PARTICIPANT


def test_dialogues_message_resolved_properly():
    """
    Test for the issue in parallel messages sends in the dialogues system.

    issue: https://github.com/fetchai/agents-aea/issues/2128
    """
    addr1 = "addr1"
    addr2 = "addr2"
    part1 = TacDialogues(addr1, role_from_first_message=role_participant)
    part2 = TacDialogues(addr2, role_from_first_message=role_participant)

    msg, _ = part1.create(
        addr2, performative=TacMessage.Performative.REGISTER, agent_name=addr1
    )

    dialogue = part2.update(msg)
    assert dialogue
    game_data_msg = dialogue.reply(performative=TacMessage.Performative.GAME_DATA)

    dialogue = part1.update(game_data_msg)
    assert dialogue
    transaction1_msg = dialogue.reply(performative=TacMessage.Performative.TRANSACTION)
    transaction2_msg = dialogue.reply(performative=TacMessage.Performative.TRANSACTION)

    dialogue = part2.update(transaction1_msg)
    assert dialogue
    comfirmation1_msg = dialogue.reply(
        performative=TacMessage.Performative.TRANSACTION_CONFIRMATION
    )

    dialogue = part1.update(comfirmation1_msg)
    assert dialogue
    transaction3_msg = dialogue.reply(performative=TacMessage.Performative.TRANSACTION)

    dialogue = part2.update(transaction2_msg)
    assert dialogue
    comfirmation2_msg = dialogue.reply(
        performative=TacMessage.Performative.TRANSACTION_CONFIRMATION
    )
    assert comfirmation2_msg.target == transaction2_msg.message_id

    dialogue = part1.update(comfirmation2_msg)
    assert dialogue

    dialogue = part2.update(transaction3_msg)
    assert dialogue
    msg1 = dialogue.reply(performative=TacMessage.Performative.TRANSACTION_CONFIRMATION)

    # self reply
    msg2 = dialogue.reply(performative=TacMessage.Performative.TRANSACTION_CONFIRMATION)
    assert abs(msg2.message_id) - abs(msg1.message_id) == 1
    assert msg2.target == msg1.message_id
