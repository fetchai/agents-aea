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
"""This module validates a protocol specification."""

from typing import Tuple

from aea.configurations.base import ProtocolSpecification
from aea.protocols.generator.common import (
    SPECIFICATION_PRIMITIVE_TYPES,
    _get_sub_types_of_compositional_types,
)

RESERVED_NAMES = {"body", "message_id", "dialogue_reference", "target", "performative"}


def _is_composition_type_with_custom_type(content_type: str) -> bool:
    """
    Evaluate whether the content_type is a composition type (FrozenSet, Tuple, Dict) and contains a custom type as a sub-type.

    :param content_type: the content type
    :return: Boolean result
    """
    if content_type.startswith("pt:optional"):
        sub_type = _get_sub_types_of_compositional_types(content_type)[0]
        result = _is_composition_type_with_custom_type(sub_type)
    elif content_type.startswith("pt:union"):
        sub_types = _get_sub_types_of_compositional_types(content_type)
        result = False
        for sub_type in sub_types:
            if _is_composition_type_with_custom_type(sub_type):
                result = True
                break
    elif content_type.startswith("pt:dict"):
        sub_type_1 = _get_sub_types_of_compositional_types(content_type)[0]
        sub_type_2 = _get_sub_types_of_compositional_types(content_type)[1]

        result = (sub_type_1 not in SPECIFICATION_PRIMITIVE_TYPES) or (
            sub_type_2 not in SPECIFICATION_PRIMITIVE_TYPES
        )
    elif content_type.startswith("pt:set") or content_type.startswith("pt:list"):
        sub_type = _get_sub_types_of_compositional_types(content_type)[0]
        result = sub_type not in SPECIFICATION_PRIMITIVE_TYPES
    else:
        result = False
    return result


def _is_valid_content_name(content_name: str) -> bool:
    """
    Evaluate whether a content name is a reserved name or not.

    :param content_name: a content name
    :return: Boolean result
    """
    return content_name not in RESERVED_NAMES


# ToDo other validation functions


def validate(protocol_specification: ProtocolSpecification) -> Tuple[bool, str]:
    """
    Evaluate whether a protocol specification is valid or not.

    :param protocol_specification: a protocol specification
    :return: Boolean result
    """
    for (
        performative,
        speech_act_content_config,
    ) in protocol_specification.speech_acts.read_all():

        # ToDo validate performative name

        for content_name, _ in speech_act_content_config.args.items():
            if not _is_valid_content_name(content_name):
                return (
                    False,
                    "Invalid name for content '{}' of performative '{}'. This name is reserved.".format(
                        content_name, performative,
                    ),
                )

            # ToDo further validate content name

            if _is_composition_type_with_custom_type(performative):
                return (
                    False,
                    "Invalid type for content '{}' of performative '{}'. A custom type cannot be used in the following composition types: [pt:set, pt:list, pt:dict].".format(
                        content_name, performative,
                    ),
                )

            # ToDo further validate content type

    return True, "Protocol specification is valid."
