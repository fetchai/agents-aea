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

from typing import List, Optional

from aea.configurations.base import PublicId
from aea.helpers.async_friendly_queue import AsyncFriendlyQueue
from aea.helpers.logging import WithLogger, get_logger
from aea.protocols.base import Message
from aea.registries.resources import Resources
from aea.skills.base import Behaviour, Handler


class Filter(WithLogger):
    """This class implements the filter of an AEA."""

    def __init__(
        self, resources: Resources, decision_maker_out_queue: AsyncFriendlyQueue
    ) -> None:
        """
        Instantiate the filter.

        :param resources: the resources
        :param decision_maker_out_queue: the decision maker queue
        """
        logger = get_logger(__name__, resources.agent_name)
        WithLogger.__init__(self, logger=logger)
        self._resources = resources
        self._decision_maker_out_queue = decision_maker_out_queue

    @property
    def resources(self) -> Resources:
        """Get resources."""
        return self._resources

    @property
    def decision_maker_out_queue(self) -> AsyncFriendlyQueue:
        """Get decision maker (out) queue."""
        return self._decision_maker_out_queue

    def get_active_handlers(
        self, protocol_id: PublicId, skill_id: Optional[PublicId] = None
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

    def handle_new_handlers_and_behaviours(self) -> None:
        """Handle the messages from the decision maker."""
        self._handle_new_behaviours()
        self._handle_new_handlers()

    async def get_internal_message(self) -> Optional[Message]:
        """Get a message from decision_maker_out_queue."""
        return await self.decision_maker_out_queue.async_get()

    def handle_internal_message(self, internal_message: Optional[Message]) -> None:
        """Handle internal message."""
        if internal_message is None:
            self.logger.warning("Got 'None' while processing internal messages.")
            return
        self._handle_internal_message(internal_message)

    def _handle_new_behaviours(self) -> None:
        """Register new behaviours added to skills."""
        for skill in self.resources.get_all_skills():
            while not skill.skill_context.new_behaviours.empty():
                new_behaviour = skill.skill_context.new_behaviours.get()
                try:
                    self.resources.behaviour_registry.register(
                        (skill.skill_context.skill_id, new_behaviour.name),
                        new_behaviour,
                        is_dynamically_added=True,
                    )
                except ValueError as e:
                    self.logger.warning(
                        "Error when trying to add a new behaviour: {}".format(str(e))
                    )

    def _handle_new_handlers(self) -> None:
        """Register new handlers added to skills."""
        for skill in self.resources.get_all_skills():
            while not skill.skill_context.new_handlers.empty():
                new_handler = skill.skill_context.new_handlers.get()
                try:
                    self.resources.handler_registry.register(
                        (skill.skill_context.skill_id, new_handler.name),
                        new_handler,
                        is_dynamically_added=True,
                    )
                except ValueError as e:
                    self.logger.warning(
                        "Error when trying to add a new handler: {}".format(str(e))
                    )

    def _handle_internal_message(self, message: Message) -> None:
        """Handle message from the Decision Maker."""
        try:
            skill_id = PublicId.from_str(message.to)
        except ValueError:
            self.logger.warning(
                "Invalid public id as destination={}".format(message.to)
            )
            return
        handler = self.resources.handler_registry.fetch_by_protocol_and_skill(
            message.protocol_id, skill_id,
        )
        if handler is not None:
            self.logger.debug(
                "Calling handler {} of skill {}".format(type(handler), skill_id)
            )
            handler.handle(message)
        else:
            self.logger.warning(
                "No internal handler fetched for skill_id={}".format(skill_id)
            )
