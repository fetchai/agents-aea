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

import re
from typing import Dict, List, Tuple, cast

from aea.configurations.base import ProtocolSpecification
from aea.protocols.generator.common import (
    SPECIFICATION_COMPOSITIONAL_TYPES,
    SPECIFICATION_PRIMITIVE_TYPES,
    _get_sub_types_of_compositional_types,
)

# The following names are reserved for standard message fields and cannot be
# used as user defined names for performative or contents
RESERVED_NAMES = {"body", "message_id", "dialogue_reference", "target", "performative"}

# Regular expression patterns for various fields in protocol specifications
PERFORMATIVE_REGEX_PATTERN = "^[a-zA-Z0-9]+$|^[a-zA-Z0-9]+(_?[a-zA-Z0-9]+)+$"
CONTENT_NAME_REGEX_PATTERN = "^[a-zA-Z0-9]+$|^[a-zA-Z0-9]+(_?[a-zA-Z0-9]+)+$"

CT_CONTENT_REGEX_PATTERN = "^ct:([A-Z]+[a-z]*)+$"  # or maybe "ct:(?:[A-Z][a-z]+)+" or # "^ct:[A-Z][a-zA-Z0-9]*$"

ROLE_REGEX_PATTERN = "^[a-zA-Z0-9]+$|^[a-zA-Z0-9]+(_?[a-zA-Z0-9]+)+$"
END_STATE_REGEX_PATTERN = "^[a-zA-Z0-9]+$|^[a-zA-Z0-9]+(_?[a-zA-Z0-9]+)+$"


def _is_reserved_name(content_name: str) -> bool:
    """
    Evaluate whether a content name is a reserved name or not.

    :param content_name: a content name
    :return: Boolean result
    """
    return content_name in RESERVED_NAMES


def _is_valid_regex(regex_pattern: str, text: str) -> bool:
    """
    Evaluate whether a 'text' matches a regular expression pattern.

    :param regex_pattern: the regular expression pattern
    :param text: the text on which to match regular expression

    :return: Boolean result
    """
    match = re.match(regex_pattern, text)
    if match:
        return True
    else:
        return False


def _has_brackets(content_type: str) -> bool:
    for compositional_type in SPECIFICATION_COMPOSITIONAL_TYPES:
        if content_type.startswith(compositional_type):
            content_type = content_type[len(compositional_type):]
            return content_type[0] == "[" and content_type[len(content_type)-1] == "]"
    raise SyntaxError("Content type must be a compositional type!")


def _is_valid_ct(content_type: str) -> bool:
    content_type = content_type.strip()
    return _is_valid_regex(content_type, CT_CONTENT_REGEX_PATTERN)


def _is_valid_pt(content_type: str) -> bool:
    content_type = content_type.strip()
    return content_type in SPECIFICATION_PRIMITIVE_TYPES


def _is_valid_set(content_type: str) -> bool:
    content_type = content_type.strip()

    if not content_type.startswith("pt:set"):
        return False

    if not _has_brackets(content_type):
        return False

    sub_types = _get_sub_types_of_compositional_types(content_type)
    if len(sub_types) != 1:
        return False

    sub_type = sub_types[0]
    return _is_valid_pt(sub_type)


def _is_valid_list(content_type: str) -> bool:
    content_type = content_type.strip()

    if not content_type.startswith("pt:list"):
        return False

    if not _has_brackets(content_type):
        return False

    sub_types = _get_sub_types_of_compositional_types(content_type)
    if len(sub_types) != 1:
        return False

    sub_type = sub_types[0]
    return _is_valid_pt(sub_type)


def _is_valid_dict(content_type: str) -> bool:
    content_type = content_type.strip()

    if not content_type.startswith("pt:dict"):
        return False

    if not _has_brackets(content_type):
        return False

    sub_types = _get_sub_types_of_compositional_types(content_type)
    if len(sub_types) != 2:
        return False

    sub_type_1 = sub_types[0]
    sub_type_2 = sub_types[1]
    return _is_valid_pt(sub_type_1) and _is_valid_pt(sub_type_2)


def _is_valid_union(content_type: str) -> bool:
    content_type = content_type.strip()

    if not content_type.startswith("pt:union"):
        return False

    if not _has_brackets(content_type):
        return False

    sub_types = _get_sub_types_of_compositional_types(content_type)
    for sub_type in sub_types:
        if not (
                _is_valid_ct(sub_type)
                or _is_valid_pt(sub_type)
                or _is_valid_set(sub_type)
                or _is_valid_list(sub_type)
                or _is_valid_dict(sub_type)
        ):
            return False

    return True


def _is_valid_optional(content_type: str) -> bool:
    content_type = content_type.strip()

    if not content_type.startswith("pt:optional"):
        return False

    if not _has_brackets(content_type):
        return False

    sub_types = _get_sub_types_of_compositional_types(content_type)
    if len(sub_types) != 1:
        return False

    sub_type = sub_types[0]
    return (
            _is_valid_ct(sub_type)
            or _is_valid_pt(sub_type)
            or _is_valid_set(sub_type)
            or _is_valid_list(sub_type)
            or _is_valid_dict(sub_type)
            or _is_valid_union(sub_type)
    )


def _is_valid_content_type_format(content_type: str) -> bool:
    return (
            _is_valid_ct(content_type)
            or _is_valid_pt(content_type)
            or _is_valid_set(content_type)
            or _is_valid_list(content_type)
            or _is_valid_dict(content_type)
            or _is_valid_union(content_type)
            or _is_valid_optional(content_type)
    )


def validate(protocol_specification: ProtocolSpecification) -> Tuple[bool, str]:
    """
    Evaluate whether a protocol specification is valid or not.

    :param protocol_specification: a protocol specification
    :return: Boolean result
    """
    custom_types_set = set()
    performatives_set = set()

    # Validate speech-acts section
    for (
        performative,
        speech_act_content_config,
    ) in protocol_specification.speech_acts.read_all():

        # Validate performative name
        if not _is_valid_regex(PERFORMATIVE_REGEX_PATTERN, performative):
            return (
                False,
                "Invalid name for performative '{}'. Performative names must match the following regular expression: {} ".format(
                    performative, PERFORMATIVE_REGEX_PATTERN
                ),
            )

        if _is_reserved_name(performative):
            return (
                False,
                "Invalid name for performative '{}'. This name is reserved.".format(
                    performative,
                ),
            )

        performatives_set.add(performative)

        for content_name, content_type in speech_act_content_config.args.items():

            # Validate content name
            if not _is_valid_regex(PERFORMATIVE_REGEX_PATTERN, content_name):
                return (
                    False,
                    "Invalid name for content '{}' of performative '{}'. Content names must match the following regular expression: {} ".format(
                        content_name, performative, CONTENT_NAME_REGEX_PATTERN
                    ),
                )

            if _is_reserved_name(content_name):
                return (
                    False,
                    "Invalid name for content '{}' of performative '{}'. This name is reserved.".format(
                        content_name, performative,
                    ),
                )

            # Validate content type
            if not _is_valid_content_type_format(content_type):
                return (
                    False,
                    "Invalid type for content '{}' of performative '{}'. See documentation for the correct format of specification types.".format(
                        content_name, performative,
                    ),
                )

            if _is_valid_ct(content_type):
                custom_types_set.add(content_type.strip())

    # Validate protocol buffer schema code snippets
    if (
            protocol_specification.protobuf_snippets is not None
            and protocol_specification.protobuf_snippets != ""
    ):
        custom_types_set_2 = custom_types_set.copy()
        for custom_type in protocol_specification.protobuf_snippets.keys():
            if custom_type not in custom_types_set_2:
                return (
                    False,
                    "Extra protobuf code snippet provided. Type {} is not used anywhere in your protocol definition.".format(
                        custom_type,
                    ),
                )
            custom_types_set_2.remove(custom_type)

        if len(custom_types_set_2) != 0:
            return (
                False,
                "No protobuf code snippet is provided for the following custom types: {}".format(
                    custom_types_set_2,
                ),
            )

    # Validate dialogue section
    if (
            protocol_specification.dialogue_config != {}
            and protocol_specification.dialogue_config is not None
    ):
        # Validate initiation
        for performative in cast(List[str], protocol_specification.dialogue_config["initiation"]):
            if performative not in performatives_set:
                return (
                    False,
                    "Performative '{}' specified in \"initiation\" is not defined in the protocol's speech-acts.".format(
                        performative,
                    ),
                )

        # Validate reply
        performatives_set_2 = performatives_set.copy()
        for performative in protocol_specification.dialogue_config["reply"].keys():
            if performative not in performatives_set_2:
                return (
                    False,
                    "Performative {} specified in \"reply\" is not defined in the protocol's speech-acts.".format(
                        performative,
                    ),
                )
            performatives_set_2.remove(performative)

        if len(performatives_set_2) != 0:
            return (
                False,
                "No reply is provided for the following performatives: {}".format(
                    performatives_set_2,
                ),
            )

        # Validate termination
        for performative in cast(List[str], protocol_specification.dialogue_config["termination"]):
            if performative not in performatives_set:
                return (
                    False,
                    "Performative '{}' specified in \"termination\" is not defined in the protocol's speech-acts.".format(
                        performative,
                    ),
                )

        # Validate roles
        for role in cast(Dict[str, None], protocol_specification.dialogue_config["roles"]):
            if not _is_valid_regex(ROLE_REGEX_PATTERN, role):
                return (
                    False,
                    "Invalid name for role '{}'. Role names must match the following regular expression: {} ".format(
                        role, ROLE_REGEX_PATTERN
                    ),
                )

        # Validate end_state
        for end_state in cast(List[str], protocol_specification.dialogue_config["end_states"]):
            if not _is_valid_regex(END_STATE_REGEX_PATTERN, end_state):
                return (
                    False,
                    "Invalid name for end_state '{}'. End_state names must match the following regular expression: {} ".format(
                        end_state, END_STATE_REGEX_PATTERN
                    ),
                )

    return True, "Protocol specification is valid."
