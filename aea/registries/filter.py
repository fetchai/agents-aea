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

"""This module contains registries."""

import logging
import queue
from queue import Queue
from typing import List, Optional, cast

from aea.configurations.base import (
    PublicId,
    SkillId,
)
from aea.protocols.base import Message
from aea.protocols.signing.message import SigningMessage
from aea.registries.resources import Resources
from aea.skills.base import Behaviour, Handler

logger = logging.getLogger(__name__)


class Filter:
    """This class implements the filter of an AEA."""

    def __init__(self, resources: Resources, decision_maker_out_queue: Queue):
        """
        Instantiate the filter.

        :param resources: the resources
        :param decision_maker_out_queue: the decision maker queue
        """
        self._resources = resources
        self._decision_maker_out_queue = decision_maker_out_queue

    @property
    def resources(self) -> Resources:
        """Get resources."""
        return self._resources

    @property
    def decision_maker_out_queue(self) -> Queue:
        """Get decision maker (out) queue."""
        return self._decision_maker_out_queue

    def get_active_handlers(
        self, protocol_id: PublicId, skill_id: Optional[SkillId] = None
    ) -> List[Handler]:
        """
        Get active handlers based on protocol id and optional skill id.

        :param protocol_id: the protocol id
        :param skill_id: the skill id
        :return: the list of handlers currently active
        """
        if skill_id is not None:
            handler = self.resources.get_handler(protocol_id, skill_id)
            active_handlers = (
                [] if handler is None or not handler.context.is_active else [handler]
            )
        else:
            handlers = self.resources.get_handlers(protocol_id)
            active_handlers = list(
                filter(lambda handler: handler.context.is_active, handlers)
            )
        return active_handlers

    def get_active_behaviours(self) -> List[Behaviour]:
        """
        Get the active behaviours.

        :return: the list of behaviours currently active
        """
        behaviours = self.resources.get_all_behaviours()
        active_behaviour = list(
            filter(lambda b: b.context.is_active and not b.is_done(), behaviours)
        )
        return active_behaviour

    def handle_internal_messages(self) -> None:
        """
        Handle the messages from the decision maker.

        :return: None
        """
        self._handle_decision_maker_out_queue()
        # get new behaviours from the agent skills
        self._handle_new_behaviours()

    def _handle_decision_maker_out_queue(self) -> None:
        """Process descision maker's messages."""
        while not self.decision_maker_out_queue.empty():
            try:
                internal_message = (
                    self.decision_maker_out_queue.get_nowait()
                )  # type: Optional[Message]
                self._process_internal_message(internal_message)
            except queue.Empty:
                logger.warning("The decision maker out queue is unexpectedly empty.")
                continue

    def _process_internal_message(self, internal_message: Optional[Message]) -> None:
        if internal_message is None:
            logger.warning("Got 'None' while processing internal messages.")
        elif isinstance(
            internal_message, SigningMessage
        ):  # TODO: remove; all messages allowed
            internal_message = cast(SigningMessage, internal_message)
            self._handle_signing_message(internal_message)
        else:
            # TODO: is it expected unknown data type here?
            logger.warning("Cannot handle a {} message.".format(type(internal_message)))

    def _handle_new_behaviours(self) -> None:
        """Register new behaviours added to skills."""
        for skill in self.resources.get_all_skills():
            while not skill.skill_context.new_behaviours.empty():
                new_behaviour = skill.skill_context.new_behaviours.get()
                try:
                    self.resources.behaviour_registry.register(
                        (skill.skill_context.skill_id, new_behaviour.name),
                        new_behaviour,
                    )
                except ValueError as e:
                    logger.warning(
                        "Error when trying to add a new behaviour: {}".format(str(e))
                    )

    def _handle_signing_message(self, signing_message: SigningMessage):
        """Handle transaction message from the Decision Maker."""
        skill_callback_ids = [
            PublicId.from_str(skill_id)
            for skill_id in signing_message.skill_callback_ids
        ]
        for skill_id in skill_callback_ids:
            handler = self.resources.handler_registry.fetch_by_protocol_and_skill(
                signing_message.protocol_id, skill_id
            )
            if handler is not None:
                logger.debug(
                    "Calling handler {} of skill {}".format(type(handler), skill_id)
                )
                signing_message.counterparty = "decision_maker"  # TODO: temp fix
                signing_message.is_incoming = True
                handler.handle(cast(Message, signing_message))
            else:
                logger.warning(
                    "No internal handler fetched for skill_id={}".format(skill_id)
                )
