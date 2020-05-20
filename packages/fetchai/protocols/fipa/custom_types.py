# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2020 fetchai
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

"""This module contains class representations corresponding to every custom type in the protocol specification."""


from aea.helpers.search.models import Description as BaseDescription
from aea.helpers.search.models import Query as BaseQuery
from aea.protocols.base import Message

Description = BaseDescription

Query = BaseQuery


def role_from_first_message(message: Message) -> str:
    """
    Infer the role of the agent from an incoming or outgoing first message

    :param message: an incoming/outgoing first message
    :return: the agent's role in str format
    """
    # if message.is_set("query"):
    #     query = cast(Query, message.query)  # type: ignore
    #     if query.model is not None:
    #         is_seller = (
    #             query.model.name == SUPPLY_DATAMODEL_NAME
    #         )  # the counterparty is querying for supply
    raise NotImplementedError
    # return FipaDialogue.AgentRole.BUYER


def is_valid(message: Message) -> bool:
    """
    Check whether 'message' is a valid next message in the dialogue.

    These rules capture specific constraints designed for dialogues which are instance of a concrete sub-class of this class.

    :param message: the message to be validated
    :return: True if valid, False otherwise.
    """
    return True
