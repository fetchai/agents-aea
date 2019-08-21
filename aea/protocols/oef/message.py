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
from typing import Optional

from oef.messages import OEFErrorOperation
from oef.query import Query
from oef.schema import Description

from aea.protocols.base.message import Message


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

    def __init__(self, oef_type: Optional[Type] = None,
                 **kwargs):
        """
        Initialize.

        :param oef_type: the type of OEF message.
        """
        super().__init__(type=str(oef_type), **kwargs)

    def check_consistency(self) -> bool:
        """Check that the data is consistent."""
        try:
            assert self.is_set("type")
            oef_type = OEFMessage.Type(self.get("type"))
            if oef_type == OEFMessage.Type.REGISTER_SERVICE:
                service_description = self.get("service_description")
                assert self.is_set("id")
                assert self.is_set("service_id")
                service_id = self.get("service_id")
                assert isinstance(service_description, Description)
                assert isinstance(service_id, str)
            elif oef_type == OEFMessage.Type.REGISTER_AGENT:
                assert self.is_set("id")
                assert self.is_set("agent_description")
                agent_description = self.get("agent_description")
                assert isinstance(agent_description, Description)
            elif oef_type == OEFMessage.Type.UNREGISTER_SERVICE:
                assert self.is_set("id")
                assert self.is_set("service_id")
                service_id = self.get("service_id")
                assert isinstance(service_id, str)
            elif oef_type == OEFMessage.Type.UNREGISTER_AGENT:
                assert self.is_set("id")
            elif oef_type == OEFMessage.Type.SEARCH_SERVICES:
                assert self.is_set("id")
                assert self.is_set("query")
                query = self.get("query")
                assert isinstance(query, Query)
            elif oef_type == OEFMessage.Type.SEARCH_AGENTS:
                assert self.is_set("id")
                assert self.is_set("query")
                query = self.get("query")
                assert isinstance(query, Query)
            elif oef_type == OEFMessage.Type.SEARCH_RESULT:
                assert self.is_set("id")
                assert self.is_set("agents")
                agents = self.get("agents")
                assert type(agents) == list and all(type(a) == str for a in agents)
            elif oef_type == OEFMessage.Type.OEF_ERROR:
                assert self.is_set("id")
                assert self.is_set("operation")
                operation = self.get("operation")
                assert operation in set(OEFErrorOperation)
            elif oef_type == OEFMessage.Type.DIALOGUE_ERROR:
                assert self.is_set("id")
                assert self.is_set("dialogue_id")
                assert self.is_set("origin")
            else:
                raise ValueError("Type not recognized.")
        except (AssertionError, ValueError):
            return False

        return True
