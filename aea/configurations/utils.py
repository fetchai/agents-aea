# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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

"""AEA configuration utils."""
from functools import singledispatch
from typing import Dict, Optional, Set

from aea.configurations.base import (
    AgentConfig,
    ComponentId,
    ComponentType,
    ConnectionConfig,
    ContractConfig,
    PackageConfiguration,
    ProtocolConfig,
    PublicId,
    SkillConfig,
)
from aea.configurations.data_types import PackageIdPrefix


@singledispatch
def replace_component_ids(
    _arg: PackageConfiguration,
    _replacements: Dict[ComponentType, Dict[PublicId, PublicId]],
) -> None:
    """
    Update public id references in a package configuration.

    This depends on the actual configuration being considered.
    """


@replace_component_ids.register(AgentConfig)  # type: ignore
def _(
    arg: AgentConfig,
    replacements: Dict[ComponentType, Dict[PublicId, PublicId]],
) -> None:
    """
    Replace references in agent configuration.

    It breaks down in:
    1) replace public ids in 'protocols', 'connections', 'contracts' and 'skills';
    2) replace public ids in default routing;
    3) replace public id of default connection;
    4) replace custom component configurations.

    :param arg: the agent configuration.
    :param replacements: the replacement mapping.
    """
    _replace_component_id(
        arg,
        {
            ComponentType.PROTOCOL,
            ComponentType.CONNECTION,
            ComponentType.CONTRACT,
            ComponentType.SKILL,
        },
        replacements,
    )

    # update default routing
    protocol_replacements = replacements.get(ComponentType.PROTOCOL, {})
    connection_replacements = replacements.get(ComponentType.CONNECTION, {})
    for protocol_id, connection_id in list(arg.default_routing.items()):

        # update protocol (if replacements provides it)
        new_protocol_id = protocol_replacements.get(protocol_id, protocol_id)
        old_value = arg.default_routing.pop(protocol_id)
        arg.default_routing[new_protocol_id] = old_value
        # in case needs to be used below
        protocol_id = new_protocol_id

        # update connection (if replacements provides it)
        new_connection_id = connection_replacements.get(connection_id, connection_id)
        arg.default_routing[protocol_id] = new_connection_id

    # update default connection
    if arg.default_connection is not None:
        default_connection_public_id = arg.default_connection
        new_default_connection_public_id = replacements.get(
            ComponentType.CONNECTION, {}
        ).get(default_connection_public_id, default_connection_public_id)
        arg.default_connection = new_default_connection_public_id

    for component_id in set(arg.component_configurations.keys()):
        replacements_by_type = replacements.get(component_id.component_type, {})
        if component_id.public_id in replacements_by_type:
            new_component_id = ComponentId(
                component_id.component_type,
                replacements_by_type[component_id.public_id],
            )
            old_value = arg.component_configurations.pop(component_id)
            arg.component_configurations[new_component_id] = old_value


@replace_component_ids.register(ProtocolConfig)  # type: ignore
def _(
    _arg: ProtocolConfig,
    _replacements: Dict[ComponentType, Dict[PublicId, PublicId]],
) -> None:
    """Do nothing - protocols have no references."""


@replace_component_ids.register(ConnectionConfig)  # type: ignore
def _(
    arg: ConnectionConfig,
    replacements: Dict[ComponentType, Dict[PublicId, PublicId]],
) -> None:
    """Replace references in a connection configuration."""
    _replace_component_id(
        arg, {ComponentType.PROTOCOL, ComponentType.CONNECTION}, replacements
    )

    protocol_replacements = replacements.get(ComponentType.PROTOCOL, {})
    for old_protocol_id in set(arg.restricted_to_protocols):
        new_protocol_id = protocol_replacements.get(old_protocol_id, old_protocol_id)
        arg.restricted_to_protocols.remove(old_protocol_id)
        arg.restricted_to_protocols.add(new_protocol_id)

    for old_protocol_id in set(arg.excluded_protocols):
        new_protocol_id = protocol_replacements.get(old_protocol_id, old_protocol_id)
        arg.excluded_protocols.remove(old_protocol_id)
        arg.excluded_protocols.add(new_protocol_id)


@replace_component_ids.register(ContractConfig)  # type: ignore
def _(  # type: ignore
    _arg: ContractConfig,
    _replacements: Dict[ComponentType, Dict[PublicId, PublicId]],
) -> None:
    """Do nothing - contracts have no references."""


@replace_component_ids.register(SkillConfig)  # type: ignore
def _(
    arg: SkillConfig,
    replacements: Dict[ComponentType, Dict[PublicId, PublicId]],
) -> None:
    """Replace references in a skill configuration."""
    _replace_component_id(
        arg,
        {
            ComponentType.PROTOCOL,
            ComponentType.CONNECTION,
            ComponentType.CONTRACT,
            ComponentType.SKILL,
        },
        replacements,
    )


def _replace_component_id(
    config: PackageConfiguration,
    types_to_update: Set[ComponentType],
    replacements: Dict[ComponentType, Dict[PublicId, PublicId]],
) -> None:
    """
    Replace a component id.

    :param config: the component configuration to update.
    :param types_to_update: the types to update.
    :param replacements: the replacements.
    """
    for component_type in types_to_update:
        public_id_set = getattr(config, component_type.to_plural(), set())
        replacements_given_type = replacements.get(component_type, {})
        for old_public_id in list(public_id_set):
            new_public_id = replacements_given_type.get(old_public_id, old_public_id)
            public_id_set.remove(old_public_id)
            public_id_set.add(new_public_id)


def get_latest_component_id_from_prefix(
    agent_config: AgentConfig, component_prefix: PackageIdPrefix
) -> Optional[ComponentId]:
    """
    Get component id with the greatest version in an agent configuration given its prefix.

    :param agent_config: the agent configuration.
    :param component_prefix: the package prefix.
    :return: the package id with the greatest version, or None if not found.
    """
    all_dependencies = agent_config.package_dependencies
    chosen_component_ids = [
        c for c in all_dependencies if c.component_prefix == component_prefix
    ]
    nb_results = len(chosen_component_ids)
    return chosen_component_ids[0] if nb_results == 1 else None
