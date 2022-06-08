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
"""This module extracts a valid protocol specification into pythonic objects."""

import re
from typing import Dict, List, cast

from aea.configurations.base import (
    ProtocolSpecification,
    ProtocolSpecificationParseError,
)
from aea.protocols.generator.common import (
    SPECIFICATION_PRIMITIVE_TYPES,
    _get_sub_types_of_compositional_types,
)


def _ct_specification_type_to_python_type(specification_type: str) -> str:
    """
    Convert a custom specification type into its python equivalent.

    :param specification_type: a protocol specification data type
    :return: The equivalent data type in Python
    """
    python_type = specification_type[3:]
    return python_type


def _pt_specification_type_to_python_type(specification_type: str) -> str:
    """
    Convert a primitive specification type into its python equivalent.

    :param specification_type: a protocol specification data type
    :return: The equivalent data type in Python
    """
    python_type = specification_type[3:]
    return python_type


def _pct_specification_type_to_python_type(specification_type: str) -> str:
    """
    Convert a primitive collection specification type into its python equivalent.

    :param specification_type: a protocol specification data type
    :return: The equivalent data type in Python
    """
    element_type = _get_sub_types_of_compositional_types(specification_type)[0]
    element_type_in_python = _specification_type_to_python_type(element_type)
    if specification_type.startswith("pt:set"):
        python_type = "FrozenSet[{}]".format(element_type_in_python)
    else:
        python_type = "Tuple[{}, ...]".format(element_type_in_python)
    return python_type


def _pmt_specification_type_to_python_type(specification_type: str) -> str:
    """
    Convert a primitive mapping specification type into its python equivalent.

    :param specification_type: a protocol specification data type
    :return: The equivalent data type in Python
    """
    element_types = _get_sub_types_of_compositional_types(specification_type)
    element1_type_in_python = _specification_type_to_python_type(element_types[0])
    element2_type_in_python = _specification_type_to_python_type(element_types[1])
    python_type = "Dict[{}, {}]".format(
        element1_type_in_python, element2_type_in_python
    )
    return python_type


def _mt_specification_type_to_python_type(specification_type: str) -> str:
    """
    Convert a 'pt:union' specification type into its python equivalent.

    :param specification_type: a protocol specification data type
    :return: The equivalent data type in Python
    """
    sub_types = _get_sub_types_of_compositional_types(specification_type)
    python_type = "Union["
    for sub_type in sub_types:
        python_type += "{}, ".format(_specification_type_to_python_type(sub_type))
    python_type = python_type[:-2]
    python_type += "]"
    return python_type


def _optional_specification_type_to_python_type(specification_type: str) -> str:
    """
    Convert a 'pt:optional' specification type into its python equivalent.

    :param specification_type: a protocol specification data type
    :return: The equivalent data type in Python
    """
    element_type = _get_sub_types_of_compositional_types(specification_type)[0]
    element_type_in_python = _specification_type_to_python_type(element_type)
    python_type = "Optional[{}]".format(element_type_in_python)
    return python_type


def _specification_type_to_python_type(specification_type: str) -> str:
    """
    Convert a data type in protocol specification into its Python equivalent.

    :param specification_type: a protocol specification data type
    :return: The equivalent data type in Python
    """
    if specification_type.startswith("pt:optional"):
        python_type = _optional_specification_type_to_python_type(specification_type)
    elif specification_type.startswith("pt:union"):
        python_type = _mt_specification_type_to_python_type(specification_type)
    elif specification_type.startswith("ct:"):
        python_type = _ct_specification_type_to_python_type(specification_type)
    elif specification_type in SPECIFICATION_PRIMITIVE_TYPES:
        python_type = _pt_specification_type_to_python_type(specification_type)
    elif specification_type.startswith("pt:set"):
        python_type = _pct_specification_type_to_python_type(specification_type)
    elif specification_type.startswith("pt:list"):
        python_type = _pct_specification_type_to_python_type(specification_type)
    elif specification_type.startswith("pt:dict"):
        python_type = _pmt_specification_type_to_python_type(specification_type)
    else:
        raise ProtocolSpecificationParseError(
            "Unsupported type: '{}'".format(specification_type)
        )
    return python_type


class PythonicProtocolSpecification:  # pylint: disable=too-few-public-methods
    """This class represents a protocol specification in python."""

    def __init__(self) -> None:
        """Instantiate a Pythonic protocol specification."""
        self.speech_acts = dict()  # type: Dict[str, Dict[str, str]]
        self.all_performatives = list()  # type: List[str]
        self.all_unique_contents = dict()  # type: Dict[str, str]
        self.all_custom_types = list()  # type: List[str]
        self.custom_custom_types = dict()  # type: Dict[str, str]

        # dialogue config
        self.initial_performatives = list()  # type: List[str]
        self.reply = dict()  # type: Dict[str, List[str]]
        self.terminal_performatives = list()  # type: List[str]
        self.roles = list()  # type: List[str]
        self.end_states = list()  # type: List[str]
        self.keep_terminal_state_dialogues = False  # type: bool

        self.typing_imports = {
            "Set": True,
            "Tuple": True,
            "cast": True,
            "FrozenSet": False,
            "Dict": False,
            "Union": False,
            "Optional": False,
        }


def extract(
    protocol_specification: ProtocolSpecification,
) -> PythonicProtocolSpecification:
    """
    Converts a protocol specification into a Pythonic protocol specification.

    :param protocol_specification: a protocol specification
    :return: a Pythonic protocol specification
    """
    spec = PythonicProtocolSpecification()

    all_performatives_set = set()
    all_custom_types_set = set()

    for (
        performative,
        speech_act_content_config,
    ) in protocol_specification.speech_acts.read_all():
        all_performatives_set.add(performative)
        spec.speech_acts[performative] = {}
        for content_name, content_type in speech_act_content_config.args.items():

            # determine necessary imports from typing
            if len(re.findall("pt:set\\[", content_type)) >= 1:
                spec.typing_imports["FrozenSet"] = True
            if len(re.findall("pt:dict\\[", content_type)) >= 1:
                spec.typing_imports["Dict"] = True
            if len(re.findall("pt:union\\[", content_type)) >= 1:
                spec.typing_imports["Union"] = True
            if len(re.findall("pt:optional\\[", content_type)) >= 1:
                spec.typing_imports["Optional"] = True

            # specification type --> python type
            pythonic_content_type = _specification_type_to_python_type(content_type)

            spec.all_unique_contents[content_name] = pythonic_content_type
            spec.speech_acts[performative][content_name] = pythonic_content_type
            if content_type.startswith("ct:"):
                all_custom_types_set.add(pythonic_content_type)

    # sort the sets
    spec.all_performatives = sorted(all_performatives_set)
    spec.all_custom_types = sorted(all_custom_types_set)

    # "XXX" custom type --> "CustomXXX"
    spec.custom_custom_types = {
        pure_custom_type: "Custom" + pure_custom_type
        for pure_custom_type in spec.all_custom_types
    }

    # Dialogue attributes
    if (
        protocol_specification.dialogue_config != {}
        and protocol_specification.dialogue_config is not None
    ):
        spec.initial_performatives = [
            initial_performative.upper()
            for initial_performative in cast(
                List[str], protocol_specification.dialogue_config["initiation"]
            )
        ]
        spec.reply = cast(
            Dict[str, List[str]],
            protocol_specification.dialogue_config["reply"],
        )
        spec.terminal_performatives = [
            terminal_performative.upper()
            for terminal_performative in cast(
                List[str],
                protocol_specification.dialogue_config["termination"],
            )
        ]
        roles_set = cast(
            Dict[str, None], protocol_specification.dialogue_config["roles"]
        )
        spec.roles = sorted(roles_set)
        spec.end_states = cast(
            List[str], protocol_specification.dialogue_config["end_states"]
        )
        spec.keep_terminal_state_dialogues = cast(
            bool,
            protocol_specification.dialogue_config.get(
                "keep_terminal_state_dialogues", False
            ),
        )
    return spec
