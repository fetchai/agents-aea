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
"""This module contains models for soef connection tests."""

from aea.helpers.search.models import Attribute, DataModel, Location

from packages.fetchai.connections.soef.connection import ModelNames


AGENT_LOCATION_MODEL = DataModel(
    ModelNames.location_agent,
    [Attribute("location", Location, True, "The location where the agent is.")],
    "A data model to describe location of an agent.",
)


AGENT_PERSONALITY_MODEL = DataModel(
    ModelNames.personality_agent,
    [
        Attribute("piece", str, True, "The personality piece key."),
        Attribute("value", str, True, "The personality piece value."),
    ],
    "A data model to describe the personality of an agent.",
)


SET_SERVICE_KEY_MODEL = DataModel(
    ModelNames.set_service_key,
    [
        Attribute("key", str, True, "Service key name."),
        Attribute("value", str, True, "Service key value."),
    ],
    "A data model to set service key.",
)


REMOVE_SERVICE_KEY_MODEL = DataModel(
    ModelNames.remove_service_key,
    [Attribute("key", str, True, "Service key name.")],
    "A data model to remove service key.",
)

PING_MODEL = DataModel(ModelNames.ping, [], "A data model for ping command.",)


SEARCH_MODEL = DataModel(
    ModelNames.search_model,
    [Attribute("location", Location, True, "The location where the agent is.")],
    "A data model to perform search.",
)
