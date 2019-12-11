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

"""This module contains the default message definition."""
from enum import Enum
from typing import Optional, List, cast

from aea.protocols.base import Message
from aea.protocols.oef.models import Description, Query


class OEFMessage(Message):
    """The OEF message class."""

    protocol_id = "oef"

    class Type(Enum):
        """OEF Message types."""

        REGISTER_SERVICE = "register_service"
        REGISTER_AGENT = "register_agent"
        UNREGISTER_SERVICE = "unregister_service"
        UNREGISTER_AGENT = "unregister_agent"
        SEARCH_SERVICES = "search_services"
        SEARCH_AGENTS = "search_agents"
        OEF_ERROR = "oef_error"
        DIALOGUE_ERROR = "dialogue_error"
        SEARCH_RESULT = "search_result"

        def __str__(self):
            """Get string representation."""
            return self.value

    class OEFErrorOperation(Enum):
        """Operation code for the OEF. It is returned in the OEF Error messages."""

        REGISTER_SERVICE = 0
        UNREGISTER_SERVICE = 1
        SEARCH_SERVICES = 2
        SEARCH_SERVICES_WIDE = 3
        SEARCH_AGENTS = 4
        SEND_MESSAGE = 5
        REGISTER_AGENT = 6
        UNREGISTER_AGENT = 7

        OTHER = 10000

        def __str__(self):
            """Get string representation."""
            return str(self.value)

    def __init__(self, oef_type: Optional[Type] = None,
                 **kwargs):
        """
        Initialize.

        :param oef_type: the type of OEF message.
        """
        super().__init__(type=oef_type, **kwargs)
        assert self.check_consistency(), "OEFMessage initialization inconsistent."

    @property
    def type(self) -> Type:  # noqa: F821
        """Get the type of the oef_message."""
        assert self.is_set("type"), "type is not set."
        return OEFMessage.Type(self.get("type"))

    @property
    def id(self) -> int:
        """Get the id of the oef_message."""
        assert self.is_set("id"), "id is not set."
        return cast(int, self.get('id'))

    @property
    def service_description(self) -> Description:
        """Get the service_description from the message."""
        assert self.is_set("service_description"), "service_description is not set"
        return cast(Description, self.get('service_description'))

    @property
    def service_id(self) -> str:
        """Get the service_id from the message."""
        assert self.is_set("service_id"), "service_id is not set."
        return cast(str, self.get("service_id"))

    @property
    def agent_description(self) -> Description:
        """Get the agent_description from the message."""
        assert self.is_set("agent_description"), "agent_description is not set."
        return cast(Description, self.get("agent_description"))

    @property
    def agent_id(self) -> str:
        """Get the agent_id from the message."""
        assert self.is_set("agent_id"), "agent_id is not set."
        return cast(str, self.get("agent_id"))

    @property
    def query(self) -> Query:
        """Get the query from the message."""
        assert self.is_set("query"), "query is not set."
        return cast(Query, self.get("query"))

    @property
    def agents(self) -> List[str]:
        """Get the agents from the message."""
        assert self.is_set("agents"), "list of agents is not set."
        return cast(List[str], self.get("agents"))

    @property
    def operation(self) -> OEFErrorOperation:  # noqa: F821
        """Get the error_operation code from the message."""
        assert self.is_set("operation"), "operation is not set."
        return OEFMessage.OEFErrorOperation(self.get("operation"))

    @property
    def dialogue_id(self) -> int:
        """Get the dialogue_id from the message."""
        assert self.is_set("dialogue_id"), "dialogue_id is not set."
        return cast(int, self.get("dialogue_id"))

    @property
    def origin(self) -> str:
        """Get the origin from the message."""
        assert self.is_set("origin"), "origin is not set."
        return cast(str, self.get("origin"))

    def check_consistency(self) -> bool:
        """Check that the data is consistent."""
        try:
            assert self.type is not None, "type must not be None."
            assert isinstance(self.id, int), "id must be int."

            if self.type == OEFMessage.Type.REGISTER_SERVICE:
                assert isinstance(self.service_description, Description), \
                    "service_description must be of type Description."
                assert isinstance(self.service_id, str), "service_id must be of type str."
            elif self.type == OEFMessage.Type.REGISTER_AGENT:
                assert isinstance(self.agent_description, Description), "agent_description must be of type Description."
                assert isinstance(self.agent_id, str), "agent_id must be of type str."
            elif self.type == OEFMessage.Type.UNREGISTER_SERVICE:
                assert isinstance(self.service_description, Description), \
                    "service_description must be of type Description."
                assert isinstance(self.service_id, str), "service_id must be of type str."
            elif self.type == OEFMessage.Type.UNREGISTER_AGENT:
                assert isinstance(self.agent_description, Description), "agent_description must be of type Description."
                assert isinstance(self.agent_id, str), "agent_id must be of type str."
            elif self.type == OEFMessage.Type.SEARCH_SERVICES:
                assert isinstance(self.query, Query), "query must be of type Query."
            elif self.type == OEFMessage.Type.SEARCH_AGENTS:
                assert isinstance(self.query, Query), "query must be of type Query."
            elif self.type == OEFMessage.Type.SEARCH_RESULT:
                assert type(self.agents) == list and all(type(a) == str for a in self.agents)
            elif self.type == OEFMessage.Type.OEF_ERROR:
                assert isinstance(self.operation, OEFMessage.OEFErrorOperation), \
                    "operation must be type of OEFErrorOperation"
            elif self.type == OEFMessage.Type.DIALOGUE_ERROR:
                assert isinstance(self.dialogue_id, int), "dialogue_id must be of type int."
                assert isinstance(self.origin, str), "origin must be of type str."
            else:
                raise ValueError("Type not recognized.")
        except (AssertionError, ValueError):
            return False

        return True
