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
from typing import Any, Dict, List, Optional, Set, Tuple, cast

from aea.configurations.base import ProtocolSpecification
from aea.protocols.generator.common import (
    SPECIFICATION_COMPOSITIONAL_TYPES,
    SPECIFICATION_PRIMITIVE_TYPES,
    _get_sub_types_of_compositional_types,
    _has_matched_brackets,
)


# The following names are reserved for standard message fields and cannot be
# used as user defined names for performative or contents
RESERVED_NAMES = {"_body", "message_id", "dialogue_reference", "target", "performative"}

# Regular expression patterns for various fields in protocol specifications
PERFORMATIVE_REGEX_PATTERN = "^[a-zA-Z0-9]+$|^[a-zA-Z0-9]+(_?[a-zA-Z0-9]+)+$"
CONTENT_NAME_REGEX_PATTERN = "^[a-zA-Z0-9]+$|^[a-zA-Z0-9]+(_?[a-zA-Z0-9]+)+$"

CT_CONTENT_TYPE_REGEX_PATTERN = "^ct:([A-Z]+[a-z]*)+$"  # or maybe "ct:(?:[A-Z][a-z]+)+" or # "^ct:[A-Z][a-zA-Z0-9]*$"

ROLE_REGEX_PATTERN = "^[a-zA-Z0-9]+$|^[a-zA-Z0-9]+(_?[a-zA-Z0-9]+)+$"
END_STATE_REGEX_PATTERN = "^[a-zA-Z0-9]+$|^[a-zA-Z0-9]+(_?[a-zA-Z0-9]+)+$"

DIALOGUE_SECTION_REQUIRED_FIELDS = [
    "initiation",
    "reply",
    "termination",
    "roles",
    "end_states",
    "keep_terminal_state_dialogues",
]


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
    return match is not None


def _has_brackets(content_type: str) -> bool:
    """
    Evaluate whether a compositional content type in a protocol specification is valid has corresponding brackets.

    :param content_type: an 'set' content type.
    :return: Boolean result
    """
    for compositional_type in SPECIFICATION_COMPOSITIONAL_TYPES:
        if content_type.startswith(compositional_type):
            content_type = content_type[len(compositional_type) :]
            if len(content_type) < 2:
                return False
            return content_type[0] == "[" and content_type[len(content_type) - 1] == "]"
    raise SyntaxError("Content type must be a compositional type!")


def _is_valid_ct(content_type: str) -> bool:
    """
    Evaluate whether the format of a 'ct' content type in a protocol specification is valid.

    :param content_type: a 'ct' content type.
    :return: Boolean result
    """
    content_type = content_type.strip()
    return _is_valid_regex(CT_CONTENT_TYPE_REGEX_PATTERN, content_type)


def _is_valid_pt(content_type: str) -> bool:
    """
    Evaluate whether the format of a 'pt' content type in a protocol specification is valid.

    :param content_type: a 'pt' content type.
    :return: Boolean result
    """
    content_type = content_type.strip()
    return content_type in SPECIFICATION_PRIMITIVE_TYPES


def _is_valid_set(content_type: str) -> bool:
    """
    Evaluate whether the format of a 'set' content type in a protocol specification is valid.

    :param content_type: a 'set' content type.
    :return: Boolean result
    """
    content_type = content_type.strip()

    if not content_type.startswith("pt:set"):
        return False

    if not _has_matched_brackets(content_type):
        return False

    if not _has_brackets(content_type):
        return False

    sub_types = _get_sub_types_of_compositional_types(content_type)
    if len(sub_types) != 1:
        return False

    sub_type = sub_types[0]
    return _is_valid_pt(sub_type)


def _is_valid_list(content_type: str) -> bool:
    """
    Evaluate whether the format of a 'list' content type in a protocol specification is valid.

    :param content_type: a 'list' content type.
    :return: Boolean result
    """
    content_type = content_type.strip()

    if not content_type.startswith("pt:list"):
        return False

    if not _has_matched_brackets(content_type):
        return False

    if not _has_brackets(content_type):
        return False

    sub_types = _get_sub_types_of_compositional_types(content_type)
    if len(sub_types) != 1:
        return False

    sub_type = sub_types[0]
    return _is_valid_pt(sub_type)


def _is_valid_dict(content_type: str) -> bool:
    """
    Evaluate whether the format of a 'dict' content type in a protocol specification is valid.

    :param content_type: a 'dict' content type.
    :return: Boolean result
    """
    content_type = content_type.strip()

    if not content_type.startswith("pt:dict"):
        return False

    if not _has_matched_brackets(content_type):
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
    """
    Evaluate whether the format of a 'union' content type in a protocol specification is valid.

    :param content_type: an 'union' content type.
    :return: Boolean result
    """
    content_type = content_type.strip()

    if not content_type.startswith("pt:union"):
        return False

    if not _has_matched_brackets(content_type):
        return False

    if not _has_brackets(content_type):
        return False

    sub_types = _get_sub_types_of_compositional_types(content_type)
    # check there are at least two subtypes in the union
    if len(sub_types) < 2:
        return False

    # check there are no duplicate subtypes in the union
    sub_types_set = set(sub_types)
    if len(sub_types) != len(sub_types_set):
        return False

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
    """
    Evaluate whether the format of an 'optional' content type in a protocol specification is valid.

    :param content_type: an 'optional' content type.
    :return: Boolean result
    """
    content_type = content_type.strip()

    if not content_type.startswith("pt:optional"):
        return False

    if not _has_matched_brackets(content_type):
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
    """
    Evaluate whether the format of a content type in a protocol specification is valid.

    :param content_type: a content type.
    :return: Boolean result
    """
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
    # check performative is not a reserved name
    if _is_reserved_name(performative):
        return (
            False,
            "Invalid name for performative '{}'. This name is reserved.".format(
                performative,
            ),
        )

    # check performative's format
    if not _is_valid_regex(PERFORMATIVE_REGEX_PATTERN, performative):
        return (
            False,
            "Invalid name for performative '{}'. Performative names must match the following regular expression: {} ".format(
                performative, PERFORMATIVE_REGEX_PATTERN
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
    # check content name's format
    if not _is_valid_regex(CONTENT_NAME_REGEX_PATTERN, content_name):
        return (
            False,
            "Invalid name for content '{}' of performative '{}'. Content names must match the following regular expression: {} ".format(
                content_name, performative, CONTENT_NAME_REGEX_PATTERN
            ),
        )

    # check content name is not a reserved name
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

    content_names_types: Dict[str, Tuple[str, str]] = dict()

    # check that speech-acts definition is not empty
    if len(protocol_specification.speech_acts.read_all()) == 0:
        return (
            False,
            "Speech-acts cannot be empty!",
            None,
            None,
        )

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

            # check type of content_type
            if not isinstance(content_type, str):
                return (
                    False,
                    "Invalid type for '{}'. Expected str. Found {}.".format(
                        content_name, type(content_type)
                    ),
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

            # check content name isn't repeated with a different type
            if content_name in content_names_types:
                last_performative = content_names_types[content_name][0]
                last_content_type = content_names_types[content_name][1]
                if last_content_type != content_type:
                    return (
                        False,
                        "Content '{}' with type '{}' under performative '{}' is already defined under performative '{}' with a different type ('{}').".format(
                            content_name,
                            content_type,
                            performative,
                            last_performative,
                            last_content_type,
                        ),
                        None,
                        None,
                    )

            content_names_types[content_name] = (performative, content_type)

            if _is_valid_ct(content_type):
                custom_types_set.add(content_type.strip())

    return True, "Speech-acts are valid.", performatives_set, custom_types_set


def _validate_protocol_buffer_schema_code_snippets(
    protocol_specification: ProtocolSpecification, custom_types_set: Set[str]
) -> Tuple[bool, str]:
    """
    Evaluate whether the protobuf code snippet section of a protocol specification is valid.

    :param protocol_specification: a protocol specification.
    :param custom_types_set: set of all custom types in the protocol.

    :return: Boolean result, and associated message.
    """
    if (
        protocol_specification.protobuf_snippets is not None
        and protocol_specification.protobuf_snippets != ""
    ):
        # check all custom types are actually used in speech-acts definition
        for custom_type in protocol_specification.protobuf_snippets.keys():
            if custom_type not in custom_types_set:
                return (
                    False,
                    "Extra protobuf code snippet provided. Type '{}' is not used anywhere in your protocol definition.".format(
                        custom_type,
                    ),
                )
            custom_types_set.remove(custom_type)

        # check that no custom type already used in speech-acts definition is missing
        if len(custom_types_set) != 0:
            return (
                False,
                "No protobuf code snippet is provided for the following custom types: {}".format(
                    custom_types_set,
                ),
            )

    return True, "Protobuf code snippet section is valid."


def _validate_field_existence(dialogue_config: List[str]) -> Tuple[bool, str]:
    """
    Evaluate whether the dialogue section of a protocol specification contains the required fields.

    :param dialogue_config: the dialogue section of a protocol specification.

    :return: Boolean result, and associated message.
    """
    # check required fields exist
    for required_field in DIALOGUE_SECTION_REQUIRED_FIELDS:
        if required_field not in dialogue_config:
            return (
                False,
                "Missing required field '{}' in the dialogue section of the protocol specification.".format(
                    required_field
                ),
            )

    return True, "Dialogue section has all the required fields."


def _validate_initiation(
    initiation: List[str], performatives_set: Set[str]
) -> Tuple[bool, str]:
    """
    Evaluate whether the initiation field in a protocol specification is valid.

    :param initiation: List of initial messages of a dialogue.
    :param performatives_set: set of all performatives in the dialogue.

    :return: Boolean result, and associated message.
    """
    # check type
    if not isinstance(initiation, list):
        return (
            False,
            "Invalid type for initiation. Expected list. Found '{}'.".format(
                type(initiation)
            ),
        )

    # check initiation is not empty/None
    if len(initiation) == 0 or initiation is None:
        return (
            False,
            "At least one initial performative for this dialogue must be specified.",
        )

    # check performatives are previously defined
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
    reply_definition: Dict[str, List[str]], performatives_set: Set[str]
) -> Tuple[bool, str, Optional[Set[str]]]:
    """
    Evaluate whether the reply definition in a protocol specification is valid.

    :param reply_definition: Reply structure of a dialogue.
    :param performatives_set: set of all performatives in the dialogue.

    :return: Boolean result, and associated message.
    """
    # check type
    if not isinstance(reply_definition, dict):
        return (
            False,
            "Invalid type for the reply definition. Expected dict. Found '{}'.".format(
                type(reply_definition)
            ),
            None,
        )

    performatives_set_2 = performatives_set.copy()
    terminal_performatives_from_reply = set()

    for performative, replies in reply_definition.items():
        # check only previously defined performatives are included in the reply definition
        if performative not in performatives_set_2:
            return (
                False,
                "Performative '{}' specified in \"reply\" is not defined in the protocol's speech-acts.".format(
                    performative,
                ),
                None,
            )

        # check the type of replies
        if not isinstance(replies, list):
            return (
                False,
                "Invalid type for replies of performative {}. Expected list. Found '{}'.".format(
                    performative, type(replies)
                ),
                None,
            )

        # check all replies are performatives which are previously defined in the speech-acts definition
        for reply in replies:
            if reply not in performatives_set:
                return (
                    False,
                    "Performative '{}' in the list of replies for '{}' is not defined in speech-acts.".format(
                        reply, performative
                    ),
                    None,
                )

        performatives_set_2.remove(performative)

        if len(replies) == 0:
            terminal_performatives_from_reply.add(performative)

    # check all previously defined performatives are included in the reply definition
    if len(performatives_set_2) != 0:
        return (
            False,
            "No reply is provided for the following performatives: {}".format(
                performatives_set_2,
            ),
            None,
        )

    return True, "Reply structure is valid.", terminal_performatives_from_reply


def _validate_termination(
    termination: List[str],
    performatives_set: Set[str],
    terminal_performatives_from_reply: Set[str],
) -> Tuple[bool, str]:
    """
    Evaluate whether termination field in a protocol specification is valid.

    :param termination: List of terminal messages of a dialogue.
    :param performatives_set: set of all performatives in the dialogue.
    :param terminal_performatives_from_reply: terminal performatives extracted from reply structure.

    :return: Boolean result, and associated message.
    """
    # check type
    if not isinstance(termination, list):
        return (
            False,
            "Invalid type for termination. Expected list. Found '{}'.".format(
                type(termination)
            ),
        )

    # check termination is not empty/None
    if len(termination) == 0 or termination is None:
        return (
            False,
            "At least one terminal performative for this dialogue must be specified.",
        )

    # check terminal performatives are previously defined
    for performative in termination:
        if performative not in performatives_set:
            return (
                False,
                "Performative '{}' specified in \"termination\" is not defined in the protocol's speech-acts.".format(
                    performative,
                ),
            )

    # check that there are no repetitive performatives in termination
    number_of_duplicates = len(termination) - len(set(termination))
    if number_of_duplicates > 0:
        return (
            False,
            'There are {} duplicate performatives in "termination".'.format(
                number_of_duplicates,
            ),
        )

    # check terminal performatives have no replies
    for performative in termination:
        if performative not in terminal_performatives_from_reply:
            return (
                False,
                'The terminal performative \'{}\' specified in "termination" is assigned replies in "reply".'.format(
                    performative,
                ),
            )

    # check performatives with no replies are specified as terminal performatives
    for performative in terminal_performatives_from_reply:
        if performative not in termination:
            return (
                False,
                "The performative '{}' has no replies but is not listed as a terminal performative in \"termination\".".format(
                    performative,
                ),
            )

    return True, "Terminal messages are valid."


def _validate_roles(roles: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Evaluate whether roles field in a protocol specification is valid.

    :param roles: Set of roles of a dialogue.
    :return: Boolean result, and associated message.
    """
    # check type
    if not isinstance(roles, dict):
        return (
            False,
            "Invalid type for roles. Expected dict. Found '{}'.".format(type(roles)),
        )

    # check number of roles
    if not 1 <= len(roles) <= 2:
        return (
            False,
            "There must be either 1 or 2 roles defined in this dialogue. Found {}".format(
                len(roles)
            ),
        )

    # check each role's format
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
    # check type
    if not isinstance(end_states, list):
        return (
            False,
            "Invalid type for roles. Expected list. Found '{}'.".format(
                type(end_states)
            ),
        )

    # check each end_state's format
    for end_state in end_states:
        if not _is_valid_regex(END_STATE_REGEX_PATTERN, end_state):
            return (
                False,
                "Invalid name for end_state '{}'. End_state names must match the following regular expression: {} ".format(
                    end_state, END_STATE_REGEX_PATTERN
                ),
            )

    return True, "Dialogue end_states are valid."


def _validate_keep_terminal(keep_terminal_state_dialogues: bool) -> Tuple[bool, str]:
    """
    Evaluate whether keep_terminal_state_dialogues field in a protocol specification is valid.

    :param keep_terminal_state_dialogues: the value of keep_terminal_state_dialogues.
    :return: Boolean result, and associated message.
    """
    # check the type of keep_terminal_state_dialogues's value
    if (
        type(keep_terminal_state_dialogues)  # pylint: disable=unidiomatic-typecheck
        != bool
    ):
        return (
            False,
            "Invalid type for keep_terminal_state_dialogues. Expected bool. Found {}.".format(
                type(keep_terminal_state_dialogues)
            ),
        )

    return True, "Dialogue keep_terminal_state_dialogues is valid."


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
        # validate required fields exist
        (
            result_field_existence_validation,
            msg_field_existence_validation,
        ) = _validate_field_existence(
            cast(List[str], protocol_specification.dialogue_config),
        )
        if not result_field_existence_validation:
            return result_field_existence_validation, msg_field_existence_validation

        # Validate initiation
        result_initiation_validation, msg_initiation_validation = _validate_initiation(
            cast(List[str], protocol_specification.dialogue_config["initiation"]),
            performatives_set,
        )
        if not result_initiation_validation:
            return result_initiation_validation, msg_initiation_validation

        # Validate reply
        (
            result_reply_validation,
            msg_reply_validation,
            terminal_performatives_from_reply,
        ) = _validate_reply(
            cast(Dict[str, List[str]], protocol_specification.dialogue_config["reply"]),
            performatives_set,
        )
        if not result_reply_validation:
            return result_reply_validation, msg_reply_validation

        # Validate termination
        terminal_performatives_from_reply = cast(
            Set[str], terminal_performatives_from_reply
        )
        (
            result_termination_validation,
            msg_termination_validation,
        ) = _validate_termination(
            cast(List[str], protocol_specification.dialogue_config["termination"]),
            performatives_set,
            terminal_performatives_from_reply,
        )
        if not result_termination_validation:
            return result_termination_validation, msg_termination_validation

        # Validate roles
        result_roles_validation, msg_roles_validation = _validate_roles(
            cast(Dict[str, Any], protocol_specification.dialogue_config["roles"])
        )
        if not result_roles_validation:
            return result_roles_validation, msg_roles_validation

        # Validate end_state
        result_end_states_validation, msg_end_states_validation = _validate_end_states(
            cast(List[str], protocol_specification.dialogue_config["end_states"])
        )
        if not result_end_states_validation:
            return result_end_states_validation, msg_end_states_validation

        # Validate keep_terminal_state_dialogues
        (
            result_keep_terminal_validation,
            msg_keep_terminal_validation,
        ) = _validate_keep_terminal(
            cast(
                bool,
                protocol_specification.dialogue_config["keep_terminal_state_dialogues"],
            )
        )
        if not result_keep_terminal_validation:
            return result_keep_terminal_validation, msg_keep_terminal_validation

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
