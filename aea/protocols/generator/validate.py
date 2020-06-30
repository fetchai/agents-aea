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
from typing import Dict, List, Optional, Set, Tuple, cast

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
    if match is not None:
        return True
    else:
        return False


def _has_brackets(content_type: str) -> bool:
    for compositional_type in SPECIFICATION_COMPOSITIONAL_TYPES:
        if content_type.startswith(compositional_type):
            content_type = content_type[len(compositional_type) :]
            return content_type[0] == "[" and content_type[len(content_type) - 1] == "]"
    raise SyntaxError("Content type must be a compositional type!")


def _is_valid_ct(content_type: str) -> bool:
    content_type = content_type.strip()
    return _is_valid_regex(CT_CONTENT_REGEX_PATTERN, content_type)


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


def _validate_performatives(performative: str) -> Tuple[bool, str]:
    """
    Evaluate whether a performative in a protocol specification is valid.

    :param performative: a performative.
    :return: Boolean result, and associated message.
    """
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

    return True, "Performative '{}' is valid.".format(performative)


def _validate_content_name(content_name: str, performative: str) -> Tuple[bool, str]:
    """
    Evaluate whether the name of a content in a protocol specification is valid.

    :param content_name: a content name.
    :param performative: the performative the content belongs to.

    :return: Boolean result, and associated message.
    """
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

    return (
        True,
        "Content name '{}' of performative '{}' is valid.".format(
            content_name, performative
        ),
    )


def _validate_content_type(
    content_type: str, content_name: str, performative: str
) -> Tuple[bool, str]:
    """
    Evaluate whether the type of a content in a protocol specification is valid.

    :param content_type: a content type.
    :param content_name: a content name.
    :param performative: the performative the content belongs to.

    :return: Boolean result, and associated message.
    """
    if not _is_valid_content_type_format(content_type):
        return (
            False,
            "Invalid type for content '{}' of performative '{}'. See documentation for the correct format of specification types.".format(
                content_name, performative,
            ),
        )

    return (
        True,
        "Type of content '{}' of performative '{}' is valid.".format(
            content_name, performative
        ),
    )


def _validate_speech_acts_section(
    protocol_specification: ProtocolSpecification,
) -> Tuple[bool, str, Optional[Set[str]], Optional[Set[str]]]:
    """
    Evaluate whether speech-acts of a protocol specification is valid.

    :param protocol_specification: a protocol specification.
    :return: Boolean result, associated message, set of all performatives (auxiliary), set of all custom types (auxiliary).
    """
    custom_types_set = set()
    performatives_set = set()

    for (
        performative,
        speech_act_content_config,
    ) in protocol_specification.speech_acts.read_all():

        # Validate performative name
        (
            result_performative_validation,
            msg_performative_validation,
        ) = _validate_performatives(performative)
        if not result_performative_validation:
            return (
                result_performative_validation,
                msg_performative_validation,
                None,
                None,
            )

        performatives_set.add(performative)

        for content_name, content_type in speech_act_content_config.args.items():

            # Validate content name
            (
                result_content_name_validation,
                msg_content_name_validation,
            ) = _validate_content_name(content_name, performative)
            if not result_content_name_validation:
                return (
                    result_content_name_validation,
                    msg_content_name_validation,
                    None,
                    None,
                )

            # Validate content type
            (
                result_content_type_validation,
                msg_content_type_validation,
            ) = _validate_content_type(content_type, content_name, performative)
            if not result_content_type_validation:
                return (
                    result_content_type_validation,
                    msg_content_type_validation,
                    None,
                    None,
                )

            if _is_valid_ct(content_type):
                custom_types_set.add(content_type.strip())

    return True, "Speech-acts are valid.", performatives_set, custom_types_set


def _validate_protocol_buffer_schema_code_snippets(
    protocol_specification: ProtocolSpecification, custom_types_set: Set[str]
) -> Tuple[bool, str]:
    """
    Evaluate whether the protobuf code snippet section of a protocol specification is valid.

    :param protocol_specification: a protocol specification.
    :param custom_types_set: set of all custom types in the dialogue.

    :return: Boolean result, and associated message.
    """
    if (
        protocol_specification.protobuf_snippets is not None
        and protocol_specification.protobuf_snippets != ""
    ):
        for custom_type in protocol_specification.protobuf_snippets.keys():
            if custom_type not in custom_types_set:
                return (
                    False,
                    "Extra protobuf code snippet provided. Type '{}' is not used anywhere in your protocol definition.".format(
                        custom_type,
                    ),
                )
            custom_types_set.remove(custom_type)

        if len(custom_types_set) != 0:
            return (
                False,
                "No protobuf code snippet is provided for the following custom types: {}".format(
                    custom_types_set,
                ),
            )

    return True, "Protobuf code snippet section is valid."


def _validate_initiation(
    initiation: List[str], performatives_set: Set[str]
) -> Tuple[bool, str]:
    """
    Evaluate whether the initiation field in a protocol specification is valid.

    :param initiation: List of initial messages of a dialogue.
    :param performatives_set: set of all performatives in the dialogue.

    :return: Boolean result, and associated message.
    """
    for performative in initiation:
        if performative not in performatives_set:
            return (
                False,
                "Performative '{}' specified in \"initiation\" is not defined in the protocol's speech-acts.".format(
                    performative,
                ),
            )

    return True, "Initial messages are valid."


def _validate_reply(
    reply: Dict[str, List[str]], performatives_set: Set[str]
) -> Tuple[bool, str]:
    """
    Evaluate whether the reply structure in a protocol specification is valid.

    :param reply: Reply structure of a dialogue.
    :param performatives_set: set of all performatives in the dialogue.

    :return: Boolean result, and associated message.
    """
    performatives_set_2 = performatives_set.copy()

    for performative in reply.keys():
        if performative not in performatives_set_2:
            return (
                False,
                "Performative '{}' specified in \"reply\" is not defined in the protocol's speech-acts.".format(
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

    return True, "Reply structure is valid."


def _validate_termination(
    termination: List[str], performatives_set: Set[str]
) -> Tuple[bool, str]:
    """
    Evaluate whether termination field in a protocol specification is valid.

    :param termination: List of terminal messages of a dialogue.
    :param performatives_set: set of all performatives in the dialogue.

    :return: Boolean result, and associated message.
    """
    for performative in termination:
        if performative not in performatives_set:
            return (
                False,
                "Performative '{}' specified in \"termination\" is not defined in the protocol's speech-acts.".format(
                    performative,
                ),
            )

    return True, "Terminal messages are valid."


def _validate_roles(roles: Set[str]) -> Tuple[bool, str]:
    """
    Evaluate whether roles field in a protocol specification is valid.

    :param roles: Set of roles of a dialogue.
    :return: Boolean result, and associated message.
    """
    for role in roles:
        if not _is_valid_regex(ROLE_REGEX_PATTERN, role):
            return (
                False,
                "Invalid name for role '{}'. Role names must match the following regular expression: {} ".format(
                    role, ROLE_REGEX_PATTERN
                ),
            )

    return True, "Dialogue roles are valid."


def _validate_end_states(end_states: List[str]) -> Tuple[bool, str]:
    """
    Evaluate whether end_states field in a protocol specification is valid.

    :param end_states: List of end states of a dialogue.
    :return: Boolean result, and associated message.
    """
    for end_state in end_states:
        if not _is_valid_regex(END_STATE_REGEX_PATTERN, end_state):
            return (
                False,
                "Invalid name for end_state '{}'. End_state names must match the following regular expression: {} ".format(
                    end_state, END_STATE_REGEX_PATTERN
                ),
            )

    return True, "Dialogue end_states are valid."


def _validate_dialogue_section(
    protocol_specification: ProtocolSpecification, performatives_set: Set[str]
) -> Tuple[bool, str]:
    """
    Evaluate whether the dialogue section of a protocol specification is valid.

    :param protocol_specification: a protocol specification.
    :param performatives_set: set of all performatives in the dialogue.

    :return: Boolean result, and associated message.
    """
    if (
        protocol_specification.dialogue_config != {}
        and protocol_specification.dialogue_config is not None
    ):
        # Validate initiation
        result_initiation_validation, msg_initiation_validation = _validate_initiation(
            cast(List[str], protocol_specification.dialogue_config["initiation"]),
            performatives_set,
        )
        if not result_initiation_validation:
            return result_initiation_validation, msg_initiation_validation

        # Validate reply
        result_reply_validation, msg_reply_validation = _validate_reply(
            cast(Dict[str, List[str]], protocol_specification.dialogue_config["reply"]),
            performatives_set,
        )
        if not result_reply_validation:
            return result_reply_validation, msg_reply_validation

        # Validate termination
        (
            result_termination_validation,
            msg_termination_validation,
        ) = _validate_termination(
            cast(List[str], protocol_specification.dialogue_config["termination"]),
            performatives_set,
        )
        if not result_termination_validation:
            return result_termination_validation, msg_termination_validation

        # Validate roles
        result_roles_validation, msg_roles_validation = _validate_roles(
            cast(Set[str], protocol_specification.dialogue_config["roles"])
        )
        if not result_roles_validation:
            return result_roles_validation, msg_roles_validation

        # Validate end_state
        result_end_states_validation, msg_end_states_validation = _validate_end_states(
            cast(List[str], protocol_specification.dialogue_config["end_states"])
        )
        if not result_end_states_validation:
            return result_end_states_validation, msg_end_states_validation

    return True, "Dialogue section of the protocol specification is valid."


def validate(protocol_specification: ProtocolSpecification) -> Tuple[bool, str]:
    """
    Evaluate whether a protocol specification is valid.

    :param protocol_specification: a protocol specification.
    :return: Boolean result, and associated message.
    """
    # Validate speech-acts section
    (
        result_speech_acts_validation,
        msg_speech_acts_validation,
        performatives_set,
        custom_types_set,
    ) = _validate_speech_acts_section(protocol_specification)
    if not result_speech_acts_validation:
        return result_speech_acts_validation, msg_speech_acts_validation

    # Validate protocol buffer schema code snippets
    result_protobuf_validation, msg_protobuf_validation = _validate_protocol_buffer_schema_code_snippets(protocol_specification, custom_types_set)  # type: ignore
    if not result_protobuf_validation:
        return result_protobuf_validation, msg_protobuf_validation

    # Validate dialogue section
    result_dialogue_validation, msg_dialogue_validation = _validate_dialogue_section(protocol_specification, performatives_set)  # type: ignore
    if not result_dialogue_validation:
        return result_dialogue_validation, msg_dialogue_validation

    return True, "Protocol specification is valid."
