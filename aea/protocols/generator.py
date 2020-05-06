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
"""This module contains the protocol generator."""

import itertools
import logging
import os
import re
from datetime import date
from os import path
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from aea.configurations.base import (
    ProtocolSpecification,
    ProtocolSpecificationParseError,
)

MESSAGE_IMPORT = "from aea.protocols.base import Message"
SERIALIZER_IMPORT = "from aea.protocols.base import Serializer"

PATH_TO_PACKAGES = "packages"
INIT_FILE_NAME = "__init__.py"
PROTOCOL_YAML_FILE_NAME = "protocol.yaml"
MESSAGE_DOT_PY_FILE_NAME = "message.py"
DIALOGUE_DOT_PY_FILE_NAME = "dialogue.py"
CUSTOM_TYPES_DOT_PY_FILE_NAME = "custom_types.py"
SERIALIZATION_DOT_PY_FILE_NAME = "serialization.py"

CUSTOM_TYPE_PATTERN = "ct:[A-Z][a-zA-Z0-9]*"
SPECIFICATION_PRIMITIVE_TYPES = ["pt:bytes", "pt:int", "pt:float", "pt:bool", "pt:str"]
PYTHON_PRIMITIVE_TYPES = [
    "bytes",
    "int",
    "float",
    "bool",
    "str",
    "FrozenSet",
    "Tuple",
    "Dict",
    "Union",
    "Optional",
]
BASIC_FIELDS_AND_TYPES = {
    "name": str,
    "author": str,
    "version": str,
    "license": str,
    "description": str,
}
PYTHON_TYPE_TO_PROTO_TYPE = {
    "bytes": "bytes",
    "int": "int32",
    "float": "float",
    "bool": "bool",
    "str": "string",
}
RESERVED_NAMES = {"body", "message_id", "dialogue_reference", "target", "performative"}

logger = logging.getLogger(__name__)

indent = ""


def _change_indent(number: int, mode: str = None) -> None:
    """
    Update the value of 'indent' global variable.

    This function controls the indentation of the code produced throughout the generator.

    There are two modes:
    - Setting the indent to a desired 'number' level. In this case, 'mode' has to be set to "s".
    - Updating the incrementing/decrementing the indentation level by 'number' amounts. In this case 'mode' is None.

    :param number: the number of indentation levels to set/increment/decrement
    :param mode: the mode of indentation change
    :return: None
    """
    global indent

    if mode and mode == "s":
        if number >= 0:
            indent = number * "    "
        else:
            raise ValueError("Error: setting indent to be a negative number.")
    else:
        if number >= 0:
            for _ in itertools.repeat(None, number):
                indent += "    "
        else:
            if abs(number) <= len(indent) / 4:
                indent = indent[abs(number) * 4 :]
            else:
                raise ValueError(
                    "Not enough spaces in the 'indent' variable to remove."
                )


def _copyright_header_str(author: str) -> str:
    """
    Produce the copyright header text for a protocol.

    :param author: the author of the protocol.
    :return: The copyright header text.
    """
    copy_right_str = (
        "# -*- coding: utf-8 -*-\n"
        "# ------------------------------------------------------------------------------\n"
        "#\n"
    )
    copy_right_str += "#   Copyright {} {}\n".format(date.today().year, author)
    copy_right_str += (
        "#\n"
        '#   Licensed under the Apache License, Version 2.0 (the "License");\n'
        "#   you may not use this file except in compliance with the License.\n"
        "#   You may obtain a copy of the License at\n"
        "#\n"
        "#       http://www.apache.org/licenses/LICENSE-2.0\n"
        "#\n"
        "#   Unless required by applicable law or agreed to in writing, software\n"
        '#   distributed under the License is distributed on an "AS IS" BASIS,\n'
        "#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.\n"
        "#   See the License for the specific language governing permissions and\n"
        "#   limitations under the License.\n"
        "#\n"
        "# ------------------------------------------------------------------------------\n"
    )
    return copy_right_str


def _to_camel_case(text: str) -> str:
    """
    Convert a text in snake_case format into the CamelCase format

    :param text: the text to be converted.
    :return: The text in CamelCase format.
    """
    return "".join(word.title() for word in text.split("_"))


def _camel_case_to_snake_case(text: str) -> str:
    """
    Convert a text in CamelCase format into the snake_case format

    :param text: the text to be converted.
    :return: The text in CamelCase format.
    """
    return re.sub(r"(?<!^)(?=[A-Z])", "_", text).lower()


def _is_composition_type_with_custom_type(content_type: str) -> bool:
    """
    Evaluate whether the content_type is a composition type (FrozenSet, Tuple, Dict) and contains a custom type as a sub-type.

    :param: the content type
    :return: Boolean result
    """
    if content_type.startswith("Optional"):
        sub_type = _get_sub_types_of_compositional_types(content_type)[0]
        result = _is_composition_type_with_custom_type(sub_type)
    elif content_type.startswith("Union"):
        sub_types = _get_sub_types_of_compositional_types(content_type)
        result = False
        for sub_type in sub_types:
            if _is_composition_type_with_custom_type(sub_type):
                result = True
                break
    elif content_type.startswith("Dict"):
        sub_type_1 = _get_sub_types_of_compositional_types(content_type)[0]
        sub_type_2 = _get_sub_types_of_compositional_types(content_type)[1]

        result = (sub_type_1 not in PYTHON_TYPE_TO_PROTO_TYPE.keys()) or (
            sub_type_2 not in PYTHON_TYPE_TO_PROTO_TYPE.keys()
        )
    elif content_type.startswith("FrozenSet") or content_type.startswith("Tuple"):
        sub_type = _get_sub_types_of_compositional_types(content_type)[0]
        result = sub_type not in PYTHON_TYPE_TO_PROTO_TYPE.keys()
    else:
        result = False
    return result


def _get_sub_types_of_compositional_types(compositional_type: str) -> tuple:
    """
    Extract the sub-types of compositional types.

    This method handles both specification types (e.g. pt:set[], pt:dict[]) as well as python types (e.g. FrozenSet[], Union[]).

    :param compositional_type: the compositional type string whose sub-types are to be extracted.
    :return: tuple containing all extracted sub-types.
    """
    sub_types_list = list()
    if compositional_type.startswith("Optional") or compositional_type.startswith(
        "pt:optional"
    ):
        sub_type1 = compositional_type[
            compositional_type.index("[") + 1 : compositional_type.rindex("]")
        ].strip()
        sub_types_list.append(sub_type1)
    if (
        compositional_type.startswith("FrozenSet")
        or compositional_type.startswith("pt:set")
        or compositional_type.startswith("pt:list")
    ):
        sub_type1 = compositional_type[
            compositional_type.index("[") + 1 : compositional_type.rindex("]")
        ].strip()
        sub_types_list.append(sub_type1)
    if compositional_type.startswith("Tuple"):
        sub_type1 = compositional_type[
            compositional_type.index("[") + 1 : compositional_type.rindex("]")
        ].strip()
        sub_type1 = sub_type1[:-5]
        sub_types_list.append(sub_type1)
    if compositional_type.startswith("Dict") or compositional_type.startswith(
        "pt:dict"
    ):
        sub_type1 = compositional_type[
            compositional_type.index("[") + 1 : compositional_type.index(",")
        ].strip()
        sub_type2 = compositional_type[
            compositional_type.index(",") + 1 : compositional_type.rindex("]")
        ].strip()
        sub_types_list.extend([sub_type1, sub_type2])
    if compositional_type.startswith("Union") or compositional_type.startswith(
        "pt:union"
    ):
        inside_union = compositional_type[
            compositional_type.index("[") + 1 : compositional_type.rindex("]")
        ].strip()
        while inside_union != "":
            if inside_union.startswith("Dict") or inside_union.startswith("pt:dict"):
                sub_type = inside_union[: inside_union.index("]") + 1].strip()
                rest_of_inside_union = inside_union[
                    inside_union.index("]") + 1 :
                ].strip()
                if rest_of_inside_union.find(",") == -1:
                    # it is the last sub-type
                    inside_union = rest_of_inside_union.strip()
                else:
                    # it is not the last sub-type
                    inside_union = rest_of_inside_union[
                        rest_of_inside_union.index(",") + 1 :
                    ].strip()
            elif inside_union.startswith("Tuple"):
                sub_type = inside_union[: inside_union.index("]") + 1].strip()
                rest_of_inside_union = inside_union[
                    inside_union.index("]") + 1 :
                ].strip()
                if rest_of_inside_union.find(",") == -1:
                    # it is the last sub-type
                    inside_union = rest_of_inside_union.strip()
                else:
                    # it is not the last sub-type
                    inside_union = rest_of_inside_union[
                        rest_of_inside_union.index(",") + 1 :
                    ].strip()
            else:
                if inside_union.find(",") == -1:
                    # it is the last sub-type
                    sub_type = inside_union.strip()
                    inside_union = ""
                else:
                    # it is not the last sub-type
                    sub_type = inside_union[: inside_union.index(",")].strip()
                    inside_union = inside_union[inside_union.index(",") + 1 :].strip()
            sub_types_list.append(sub_type)
    return tuple(sub_types_list)


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


def _union_sub_type_to_protobuf_variable_name(
    content_name: str, content_type: str
) -> str:
    """
    Given a content of type union, create a variable name for its sub-type for protobuf.

    :param content_name: the name of the content
    :param content_type: the sub-type of a union type
    :return: The variable name
    """
    if content_type.startswith("FrozenSet"):
        sub_type = _get_sub_types_of_compositional_types(content_type)[0]
        expanded_type_str = "set_of_{}".format(sub_type)
    elif content_type.startswith("Tuple"):
        sub_type = _get_sub_types_of_compositional_types(content_type)[0]
        expanded_type_str = "list_of_{}".format(sub_type)
    elif content_type.startswith("Dict"):
        sub_type_1 = _get_sub_types_of_compositional_types(content_type)[0]
        sub_type_2 = _get_sub_types_of_compositional_types(content_type)[1]
        expanded_type_str = "dict_of_{}_{}".format(sub_type_1, sub_type_2)
    else:
        expanded_type_str = content_type

    protobuf_variable_name = "{}_type_{}".format(content_name, expanded_type_str)

    return protobuf_variable_name


def _python_pt_or_ct_type_to_proto_type(content_type: str) -> str:
    """
    Convert a PT or CT from python to their protobuf equivalent.

    :param content_type: the python type
    :return: The protobuf equivalent
    """
    if content_type in PYTHON_TYPE_TO_PROTO_TYPE.keys():
        proto_type = PYTHON_TYPE_TO_PROTO_TYPE[content_type]
    else:
        proto_type = content_type
    return proto_type


def _is_valid_content_name(content_name: str) -> bool:
    return content_name not in RESERVED_NAMES


def _includes_custom_type(content_type: str) -> bool:
    """
    Evaluate whether a content type is a custom type or has a custom type as a sub-type.
    :return: Boolean result
    """
    if content_type.startswith("Optional"):
        sub_type = _get_sub_types_of_compositional_types(content_type)[0]
        result = _includes_custom_type(sub_type)
    elif content_type.startswith("Union"):
        sub_types = _get_sub_types_of_compositional_types(content_type)
        result = False
        for sub_type in sub_types:
            if _includes_custom_type(sub_type):
                result = True
                break
    elif (
        content_type.startswith("FrozenSet")
        or content_type.startswith("Tuple")
        or content_type.startswith("Dict")
        or content_type in PYTHON_TYPE_TO_PROTO_TYPE.keys()
    ):
        result = False
    else:
        result = True
    return result


class ProtocolGenerator:
    """This class generates a protocol_verification package from a ProtocolTemplate object."""

    def __init__(
        self,
        protocol_specification: ProtocolSpecification,
        output_path: str = ".",
        path_to_protocol_package: Optional[str] = None,
    ) -> None:
        """
        Instantiate a protocol generator.

        :param protocol_specification: the protocol specification object
        :param output_path: the path to the location in which the protocol module is to be generated.
        :return: None
        """
        self.protocol_specification = protocol_specification
        self.protocol_specification_in_camel_case = _to_camel_case(
            self.protocol_specification.name
        )
        self.output_folder_path = os.path.join(output_path, protocol_specification.name)
        self.path_to_protocol_package = (
            path_to_protocol_package + self.protocol_specification.name
            if path_to_protocol_package is not None
            else "{}.{}.protocols.{}".format(
                PATH_TO_PACKAGES,
                self.protocol_specification.author,
                self.protocol_specification.name,
            )
        )

        self._imports = {
            "Set": True,
            "Tuple": True,
            "cast": True,
            "FrozenSet": False,
            "Dict": False,
            "Union": False,
            "Optional": False,
        }

        self._speech_acts = dict()  # type: Dict[str, Dict[str, str]]
        self._all_performatives = list()  # type: List[str]
        self._all_unique_contents = dict()  # type: Dict[str, str]
        self._all_custom_types = list()  # type: List[str]
        self._custom_custom_types = dict()  # type: Dict[str, str]

        # dialogue config
        self._reply = dict()  # type: Dict[str, List[str]]

        try:
            self._setup()
        except Exception:
            raise

    def _setup(self) -> None:
        """
        Extract all relevant data structures from the specification.

        :return: None
        """
        all_performatives_set = set()
        all_custom_types_set = set()

        for (
            performative,
            speech_act_content_config,
        ) in self.protocol_specification.speech_acts.read_all():
            all_performatives_set.add(performative)
            self._speech_acts[performative] = {}
            for content_name, content_type in speech_act_content_config.args.items():
                # check content's name is valid
                if not _is_valid_content_name(content_name):
                    raise ProtocolSpecificationParseError(
                        "Invalid name for content '{}' of performative '{}'. This name is reserved.".format(
                            content_name, performative,
                        )
                    )

                # determine necessary imports from typing
                if len(re.findall("pt:set\\[", content_type)) >= 1:
                    self._imports["FrozenSet"] = True
                if len(re.findall("pt:dict\\[", content_type)) >= 1:
                    self._imports["Dict"] = True
                if len(re.findall("pt:union\\[", content_type)) >= 1:
                    self._imports["Union"] = True
                if len(re.findall("pt:optional\\[", content_type)) >= 1:
                    self._imports["Optional"] = True

                # specification type --> python type
                pythonic_content_type = _specification_type_to_python_type(content_type)

                # check composition type does not include custom type
                if _is_composition_type_with_custom_type(pythonic_content_type):
                    raise ProtocolSpecificationParseError(
                        "Invalid type for content '{}' of performative '{}'. A custom type cannot be used in the following composition types: [pt:set, pt:list, pt:dict].".format(
                            content_name, performative,
                        )
                    )

                self._all_unique_contents[content_name] = pythonic_content_type
                self._speech_acts[performative][content_name] = pythonic_content_type
                if content_type.startswith("ct:"):
                    all_custom_types_set.add(pythonic_content_type)

        # sort the sets
        self._all_performatives = sorted(all_performatives_set)
        self._all_custom_types = sorted(all_custom_types_set)

        # "XXX" custom type --> "CustomXXX"
        self._custom_custom_types = {
            pure_custom_type: "Custom" + pure_custom_type
            for pure_custom_type in self._all_custom_types
        }
        if self.protocol_specification.dialogue_config:
            self._reply = self.protocol_specification.dialogue_config["reply"]

    def _import_from_typing_module(self) -> str:
        """
        Manage import statement for the typing package.

        :return: import statement for the typing package
        """
        ordered_packages = [
            "Dict",
            "FrozenSet",
            "Optional",
            "Set",
            "Tuple",
            "Union",
            "cast",
        ]
        import_str = "from typing import "
        for package in ordered_packages:
            if self._imports[package]:
                import_str += "{}, ".format(package)
        import_str = import_str[:-2]
        return import_str

    def _import_from_custom_types_module(self) -> str:
        """
        Manage import statement from custom_types module

        :return: import statement for the custom_types module
        """
        import_str = ""
        if self._all_custom_types:
            for custom_class in self._all_custom_types:
                import_str += "from {}.custom_types import {} as Custom{}\n".format(
                    self.path_to_protocol_package, custom_class, custom_class,
                )
            import_str = import_str[:-1]
        return import_str

    def _performatives_str(self) -> str:
        """
        Generate the performatives instance property string, a set containing all valid performatives of this protocol.

        :return: the performatives set string
        """
        performatives_str = "{"
        for performative in self._all_performatives:
            performatives_str += '"{}", '.format(performative)
        performatives_str = performatives_str[:-2]
        performatives_str += "}"
        return performatives_str

    def _performatives_enum_str(self) -> str:
        """
        Generate the performatives Enum class.

        :return: the performatives Enum string
        """
        enum_str = indent + "class Performative(Enum):\n"
        _change_indent(1)
        enum_str += indent + '"""Performatives for the {} protocol."""\n\n'.format(
            self.protocol_specification.name
        )
        for performative in self._all_performatives:
            enum_str += indent + '{} = "{}"\n'.format(
                performative.upper(), performative
            )
        enum_str += "\n"
        enum_str += indent + "def __str__(self):\n"
        _change_indent(1)
        enum_str += indent + '"""Get the string representation."""\n'
        enum_str += indent + "return self.value\n"
        _change_indent(-1)
        enum_str += "\n"
        _change_indent(-1)

        return enum_str

    def _check_content_type_str(self, content_name: str, content_type: str) -> str:
        """
        Produce the checks of elements of compositional types.

        :param content_name: the name of the content to be checked
        :param content_type: the type of the content to be checked
        :return: the string containing the checks.
        """
        check_str = ""
        if content_type.startswith("Optional["):
            optional = True
            check_str += indent + 'if self.is_set("{}"):\n'.format(content_name)
            _change_indent(1)
            check_str += indent + "expected_nb_of_contents += 1\n"
            content_type = _get_sub_types_of_compositional_types(content_type)[0]
            check_str += indent + "{} = cast({}, self.{})\n".format(
                content_name, self._to_custom_custom(content_type), content_name
            )
            content_variable = content_name
        else:
            optional = False
            content_variable = "self." + content_name
        if content_type.startswith("Union["):
            element_types = _get_sub_types_of_compositional_types(content_type)
            unique_standard_types_set = set()
            for typing_content_type in element_types:
                if typing_content_type.startswith("FrozenSet"):
                    unique_standard_types_set.add("frozenset")
                elif typing_content_type.startswith("Tuple"):
                    unique_standard_types_set.add("tuple")
                elif typing_content_type.startswith("Dict"):
                    unique_standard_types_set.add("dict")
                else:
                    unique_standard_types_set.add(typing_content_type)
            unique_standard_types_list = sorted(unique_standard_types_set)
            check_str += indent
            check_str += "assert "
            for unique_type in unique_standard_types_list:
                check_str += "type({}) == {} or ".format(
                    content_variable, self._to_custom_custom(unique_type)
                )
            check_str = check_str[:-4]
            check_str += ", \"Invalid type for content '{}'. Expected either of '{}'. Found '{{}}'.\".format(type({}))\n".format(
                content_name,
                [
                    unique_standard_type
                    for unique_standard_type in unique_standard_types_list
                ],
                content_variable,
            )
            if "frozenset" in unique_standard_types_list:
                check_str += indent + "if type({}) == frozenset:\n".format(
                    content_variable
                )
                _change_indent(1)
                check_str += indent + "assert (\n"
                _change_indent(1)
                frozen_set_element_types_set = set()
                for element_type in element_types:
                    if element_type.startswith("FrozenSet"):
                        frozen_set_element_types_set.add(
                            _get_sub_types_of_compositional_types(element_type)[0]
                        )
                frozen_set_element_types = sorted(frozen_set_element_types_set)
                for frozen_set_element_type in frozen_set_element_types:
                    check_str += (
                        indent
                        + "all(type(element) == {} for element in {}) or\n".format(
                            self._to_custom_custom(frozen_set_element_type),
                            content_variable,
                        )
                    )
                check_str = check_str[:-4]
                check_str += "\n"
                _change_indent(-1)
                if len(frozen_set_element_types) == 1:
                    check_str += (
                        indent
                        + "), \"Invalid type for elements of content '{}'. Expected ".format(
                            content_name
                        )
                    )
                    for frozen_set_element_type in frozen_set_element_types:
                        check_str += "'{}'".format(
                            self._to_custom_custom(frozen_set_element_type)
                        )
                    check_str += '."\n'
                else:
                    check_str += (
                        indent
                        + "), \"Invalid type for frozenset elements in content '{}'. Expected either ".format(
                            content_name
                        )
                    )
                    for frozen_set_element_type in frozen_set_element_types:
                        check_str += "'{}' or ".format(
                            self._to_custom_custom(frozen_set_element_type)
                        )
                    check_str = check_str[:-4]
                    check_str += '."\n'
                _change_indent(-1)
            if "tuple" in unique_standard_types_list:
                check_str += indent + "if type({}) == tuple:\n".format(content_variable)
                _change_indent(1)
                check_str += indent + "assert (\n"
                _change_indent(1)
                tuple_element_types_set = set()
                for element_type in element_types:
                    if element_type.startswith("Tuple"):
                        tuple_element_types_set.add(
                            _get_sub_types_of_compositional_types(element_type)[0]
                        )
                tuple_element_types = sorted(tuple_element_types_set)
                for tuple_element_type in tuple_element_types:
                    check_str += (
                        indent
                        + "all(type(element) == {} for element in {}) or \n".format(
                            self._to_custom_custom(tuple_element_type), content_variable
                        )
                    )
                check_str = check_str[:-4]
                check_str += "\n"
                _change_indent(-1)
                if len(tuple_element_types) == 1:
                    check_str += (
                        indent
                        + "), \"Invalid type for tuple elements in content '{}'. Expected ".format(
                            content_name
                        )
                    )
                    for tuple_element_type in tuple_element_types:
                        check_str += "'{}'".format(
                            self._to_custom_custom(tuple_element_type)
                        )
                    check_str += '."\n'
                else:
                    check_str += (
                        indent
                        + "), \"Invalid type for tuple elements in content '{}'. Expected either ".format(
                            content_name
                        )
                    )
                    for tuple_element_type in tuple_element_types:
                        check_str += "'{}' or ".format(
                            self._to_custom_custom(tuple_element_type)
                        )
                    check_str = check_str[:-4]
                    check_str += '."\n'
                _change_indent(-1)
            if "dict" in unique_standard_types_list:
                check_str += indent + "if type({}) == dict:\n".format(content_variable)
                _change_indent(1)
                check_str += (
                    indent
                    + "for key_of_{}, value_of_{} in {}.items():\n".format(
                        content_name, content_name, content_variable
                    )
                )
                _change_indent(1)
                check_str += indent + "assert (\n"
                _change_indent(1)
                dict_key_value_types = dict()
                for element_type in element_types:
                    if element_type.startswith("Dict"):
                        dict_key_value_types[
                            _get_sub_types_of_compositional_types(element_type)[0]
                        ] = _get_sub_types_of_compositional_types(element_type)[1]
                for element1_type in sorted(dict_key_value_types.keys()):
                    check_str += (
                        indent
                        + "(type(key_of_{}) == {} and type(value_of_{}) == {}) or\n".format(
                            content_name,
                            self._to_custom_custom(element1_type),
                            content_name,
                            self._to_custom_custom(dict_key_value_types[element1_type]),
                        )
                    )
                check_str = check_str[:-4]
                check_str += "\n"
                _change_indent(-1)

                if len(dict_key_value_types) == 1:
                    check_str += (
                        indent
                        + "), \"Invalid type for dictionary key, value in content '{}'. Expected ".format(
                            content_name
                        )
                    )
                    for key in sorted(dict_key_value_types.keys()):
                        check_str += "'{}', '{}'".format(key, dict_key_value_types[key])
                    check_str += '."\n'
                else:
                    check_str += (
                        indent
                        + "), \"Invalid type for dictionary key, value in content '{}'. Expected ".format(
                            content_name
                        )
                    )
                    for key in sorted(dict_key_value_types.keys()):
                        check_str += "'{}','{}' or ".format(
                            key, dict_key_value_types[key]
                        )
                    check_str = check_str[:-4]
                    check_str += '."\n'
                _change_indent(-2)
        elif content_type.startswith("FrozenSet["):
            # check the type
            check_str += (
                indent
                + "assert type({}) == frozenset, \"Invalid type for content '{}'. Expected 'frozenset'. Found '{{}}'.\".format(type({}))\n".format(
                    content_variable, content_name, content_variable
                )
            )
            element_type = _get_sub_types_of_compositional_types(content_type)[0]
            check_str += indent + "assert all(\n"
            _change_indent(1)
            check_str += indent + "type(element) == {} for element in {}\n".format(
                self._to_custom_custom(element_type), content_variable
            )
            _change_indent(-1)
            check_str += (
                indent
                + "), \"Invalid type for frozenset elements in content '{}'. Expected '{}'.\"\n".format(
                    content_name, element_type
                )
            )
        elif content_type.startswith("Tuple["):
            # check the type
            check_str += (
                indent
                + "assert type({}) == tuple, \"Invalid type for content '{}'. Expected 'tuple'. Found '{{}}'.\".format(type({}))\n".format(
                    content_variable, content_name, content_variable
                )
            )
            element_type = _get_sub_types_of_compositional_types(content_type)[0]
            check_str += indent + "assert all(\n"
            _change_indent(1)
            check_str += indent + "type(element) == {} for element in {}\n".format(
                self._to_custom_custom(element_type), content_variable
            )
            _change_indent(-1)
            check_str += (
                indent
                + "), \"Invalid type for tuple elements in content '{}'. Expected '{}'.\"\n".format(
                    content_name, element_type
                )
            )
        elif content_type.startswith("Dict["):
            # check the type
            check_str += (
                indent
                + "assert type({}) == dict, \"Invalid type for content '{}'. Expected 'dict'. Found '{{}}'.\".format(type({}))\n".format(
                    content_variable, content_name, content_variable
                )
            )
            element_type_1 = _get_sub_types_of_compositional_types(content_type)[0]
            element_type_2 = _get_sub_types_of_compositional_types(content_type)[1]
            # check the keys type then check the values type
            check_str += indent + "for key_of_{}, value_of_{} in {}.items():\n".format(
                content_name, content_name, content_variable
            )
            _change_indent(1)
            check_str += indent + "assert (\n"
            _change_indent(1)
            check_str += indent + "type(key_of_{}) == {}\n".format(
                content_name, self._to_custom_custom(element_type_1)
            )
            _change_indent(-1)
            check_str += (
                indent
                + "), \"Invalid type for dictionary keys in content '{}'. Expected '{}'. Found '{{}}'.\".format(type(key_of_{}))\n".format(
                    content_name, element_type_1, content_name
                )
            )

            check_str += indent + "assert (\n"
            _change_indent(1)
            check_str += indent + "type(value_of_{}) == {}\n".format(
                content_name, self._to_custom_custom(element_type_2)
            )
            _change_indent(-1)
            check_str += (
                indent
                + "), \"Invalid type for dictionary values in content '{}'. Expected '{}'. Found '{{}}'.\".format(type(value_of_{}))\n".format(
                    content_name, element_type_2, content_name
                )
            )
            _change_indent(-1)
        else:
            check_str += (
                indent
                + "assert type({}) == {}, \"Invalid type for content '{}'. Expected '{}'. Found '{{}}'.\".format(type({}))\n".format(
                    content_variable,
                    self._to_custom_custom(content_type),
                    content_name,
                    content_type,
                    content_variable,
                )
            )
        if optional:
            _change_indent(-1)
        return check_str

    def _message_class_str(self) -> str:
        """
        Produce the content of the Message class.

        :return: the message.py file content
        """
        _change_indent(0, "s")

        # Header
        cls_str = _copyright_header_str(self.protocol_specification.author) + "\n"

        # Module docstring
        cls_str += (
            indent
            + '"""This module contains {}\'s message definition."""\n\n'.format(
                self.protocol_specification.name
            )
        )

        # Imports
        cls_str += indent + "import logging\n"
        cls_str += indent + "from enum import Enum\n"
        cls_str += self._import_from_typing_module() + "\n\n"
        cls_str += indent + "from aea.configurations.base import ProtocolId\n"
        cls_str += MESSAGE_IMPORT + "\n"
        if self._import_from_custom_types_module():
            cls_str += "\n" + self._import_from_custom_types_module() + "\n"
        else:
            cls_str += self._import_from_custom_types_module()
        cls_str += (
            indent
            + '\nlogger = logging.getLogger("aea.packages.{}.protocols.{}.message")\n'.format(
                self.protocol_specification.author, self.protocol_specification.name
            )
        )
        cls_str += indent + "\nDEFAULT_BODY_SIZE = 4\n"

        # Class Header
        cls_str += indent + "\n\nclass {}Message(Message):\n".format(
            self.protocol_specification_in_camel_case
        )
        _change_indent(1)
        cls_str += indent + '"""{}"""\n\n'.format(
            self.protocol_specification.description
        )

        # Class attributes
        cls_str += indent + 'protocol_id = ProtocolId("{}", "{}", "{}")\n'.format(
            self.protocol_specification.author,
            self.protocol_specification.name,
            self.protocol_specification.version,
        )
        for custom_type in self._all_custom_types:
            cls_str += "\n"
            cls_str += indent + "{} = Custom{}\n".format(custom_type, custom_type)

        # Performatives Enum
        cls_str += "\n" + self._performatives_enum_str()

        # __init__
        cls_str += indent + "def __init__(\n"
        _change_indent(1)
        cls_str += indent + "self,\n"
        cls_str += indent + "performative: Performative,\n"
        cls_str += indent + 'dialogue_reference: Tuple[str, str] = ("", ""),\n'
        cls_str += indent + "message_id: int = 1,\n"
        cls_str += indent + "target: int = 0,\n"
        cls_str += indent + "**kwargs,\n"
        cls_str += indent + "):\n"
        cls_str += indent + '"""\n'
        cls_str += indent + "Initialise an instance of {}Message.\n\n".format(
            self.protocol_specification_in_camel_case
        )
        cls_str += indent + ":param message_id: the message id.\n"
        cls_str += indent + ":param dialogue_reference: the dialogue reference.\n"
        cls_str += indent + ":param target: the message target.\n"
        cls_str += indent + ":param performative: the message performative.\n"
        cls_str += indent + '"""\n'
        cls_str += indent + "super().__init__(\n"
        _change_indent(1)
        cls_str += indent + "dialogue_reference=dialogue_reference,\n"
        cls_str += indent + "message_id=message_id,\n"
        cls_str += indent + "target=target,\n"
        cls_str += (
            indent
            + "performative={}Message.Performative(performative),\n".format(
                self.protocol_specification_in_camel_case
            )
        )
        cls_str += indent + "**kwargs,\n"
        _change_indent(-1)
        cls_str += indent + ")\n"
        cls_str += indent + "self._performatives = {}\n".format(
            self._performatives_str()
        )
        _change_indent(-1)

        # Instance properties
        cls_str += indent + "@property\n"
        cls_str += indent + "def valid_performatives(self) -> Set[str]:\n"
        _change_indent(1)
        cls_str += indent + '"""Get valid performatives."""\n'
        cls_str += indent + "return self._performatives\n\n"
        _change_indent(-1)
        cls_str += indent + "@property\n"
        cls_str += indent + "def dialogue_reference(self) -> Tuple[str, str]:\n"
        _change_indent(1)
        cls_str += indent + '"""Get the dialogue_reference of the message."""\n'
        cls_str += (
            indent
            + 'assert self.is_set("dialogue_reference"), "dialogue_reference is not set."\n'
        )
        cls_str += (
            indent + 'return cast(Tuple[str, str], self.get("dialogue_reference"))\n\n'
        )
        _change_indent(-1)
        cls_str += indent + "@property\n"
        cls_str += indent + "def message_id(self) -> int:\n"
        _change_indent(1)
        cls_str += indent + '"""Get the message_id of the message."""\n'
        cls_str += (
            indent + 'assert self.is_set("message_id"), "message_id is not set."\n'
        )
        cls_str += indent + 'return cast(int, self.get("message_id"))\n\n'
        _change_indent(-1)
        cls_str += indent + "@property\n"
        cls_str += indent + "def performative(self) -> Performative:  # noqa: F821\n"
        _change_indent(1)
        cls_str += indent + '"""Get the performative of the message."""\n'
        cls_str += (
            indent + 'assert self.is_set("performative"), "performative is not set."\n'
        )
        cls_str += (
            indent
            + 'return cast({}Message.Performative, self.get("performative"))\n\n'.format(
                self.protocol_specification_in_camel_case
            )
        )
        _change_indent(-1)
        cls_str += indent + "@property\n"
        cls_str += indent + "def target(self) -> int:\n"
        _change_indent(1)
        cls_str += indent + '"""Get the target of the message."""\n'
        cls_str += indent + 'assert self.is_set("target"), "target is not set."\n'
        cls_str += indent + 'return cast(int, self.get("target"))\n\n'
        _change_indent(-1)

        for content_name in sorted(self._all_unique_contents.keys()):
            content_type = self._all_unique_contents[content_name]
            cls_str += indent + "@property\n"
            cls_str += indent + "def {}(self) -> {}:\n".format(
                content_name, self._to_custom_custom(content_type)
            )
            _change_indent(1)
            cls_str += (
                indent
                + '"""Get the \'{}\' content from the message."""\n'.format(
                    content_name
                )
            )
            if not content_type.startswith("Optional"):
                cls_str += (
                    indent
                    + 'assert self.is_set("{}"), "\'{}\' content is not set."\n'.format(
                        content_name, content_name
                    )
                )
            cls_str += indent + 'return cast({}, self.get("{}"))\n\n'.format(
                self._to_custom_custom(content_type), content_name
            )
            _change_indent(-1)

        # check_consistency method
        cls_str += indent + "def _is_consistent(self) -> bool:\n"
        _change_indent(1)
        cls_str += (
            indent
            + '"""Check that the message follows the {} protocol."""\n'.format(
                self.protocol_specification.name
            )
        )
        cls_str += indent + "try:\n"
        _change_indent(1)
        cls_str += (
            indent
            + "assert type(self.dialogue_reference) == tuple, \"Invalid type for 'dialogue_reference'. Expected 'tuple'. Found '{}'.\""
            ".format(type(self.dialogue_reference))\n"
        )
        cls_str += (
            indent
            + "assert type(self.dialogue_reference[0]) == str, \"Invalid type for 'dialogue_reference[0]'. Expected 'str'. Found '{}'.\""
            ".format(type(self.dialogue_reference[0]))\n"
        )
        cls_str += (
            indent
            + "assert type(self.dialogue_reference[1]) == str, \"Invalid type for 'dialogue_reference[1]'. Expected 'str'. Found '{}'.\""
            ".format(type(self.dialogue_reference[1]))\n"
        )
        cls_str += (
            indent
            + "assert type(self.message_id) == int, \"Invalid type for 'message_id'. Expected 'int'. Found '{}'.\""
            ".format(type(self.message_id))\n"
        )
        cls_str += (
            indent
            + "assert type(self.target) == int, \"Invalid type for 'target'. Expected 'int'. Found '{}'.\""
            ".format(type(self.target))\n\n"
        )

        cls_str += indent + "# Light Protocol Rule 2\n"
        cls_str += indent + "# Check correct performative\n"
        cls_str += (
            indent
            + "assert type(self.performative) == {}Message.Performative".format(
                self.protocol_specification_in_camel_case
            )
        )
        cls_str += (
            ", \"Invalid 'performative'. Expected either of '{}'. Found '{}'.\".format("
        )
        cls_str += "self.valid_performatives, self.performative"
        cls_str += ")\n\n"

        cls_str += indent + "# Check correct contents\n"
        cls_str += (
            indent + "actual_nb_of_contents = len(self.body) - DEFAULT_BODY_SIZE\n"
        )
        cls_str += indent + "expected_nb_of_contents = 0\n"
        counter = 1
        for performative, contents in self._speech_acts.items():
            if counter == 1:
                cls_str += indent + "if "
            else:
                cls_str += indent + "elif "
            cls_str += "self.performative == {}Message.Performative.{}:\n".format(
                self.protocol_specification_in_camel_case, performative.upper(),
            )
            _change_indent(1)
            nb_of_non_optional_contents = 0
            for content_type in contents.values():
                if not content_type.startswith("Optional"):
                    nb_of_non_optional_contents += 1

            cls_str += indent + "expected_nb_of_contents = {}\n".format(
                nb_of_non_optional_contents
            )
            for content_name, content_type in contents.items():
                cls_str += self._check_content_type_str(content_name, content_type)
            counter += 1
            _change_indent(-1)

        cls_str += "\n"
        cls_str += indent + "# Check correct content count\n"
        cls_str += (
            indent + "assert expected_nb_of_contents == actual_nb_of_contents, "
            '"Incorrect number of contents. Expected {}. Found {}"'
            ".format(expected_nb_of_contents, actual_nb_of_contents)\n\n"
        )

        cls_str += indent + "# Light Protocol Rule 3\n"
        cls_str += indent + "if self.message_id == 1:\n"
        _change_indent(1)
        cls_str += (
            indent
            + "assert self.target == 0, \"Invalid 'target'. Expected 0 (because 'message_id' is 1). Found {}.\".format(self.target)\n"
        )
        _change_indent(-1)
        cls_str += indent + "else:\n"
        _change_indent(1)
        cls_str += (
            indent + "assert 0 < self.target < self.message_id, "
            "\"Invalid 'target'. Expected an integer between 1 and {} inclusive. Found {}.\""
            ".format(self.message_id - 1, self.target,)\n"
        )
        _change_indent(-2)
        cls_str += indent + "except (AssertionError, ValueError, KeyError) as e:\n"
        _change_indent(1)
        cls_str += indent + "logger.error(str(e))\n"
        cls_str += indent + "return False\n\n"
        _change_indent(-1)
        cls_str += indent + "return True\n"

        return cls_str

    def _end_state_enum_str(self) -> str:
        """
        Generate the end state Enum class.

        :return: the end state Enum string
        """
        enum_str = indent + "class EndState(Enum):\n"
        _change_indent(1)
        enum_str += (
            indent + '"""This class defines the end states of a dialogue."""\n\n'
        )
        enum_str += indent + "SUCCESSFUL = 0\n"
        enum_str += indent + "DECLINED_CFP = 1\n"
        enum_str += indent + "DECLINED_PROPOSE = 2\n"
        enum_str += indent + "DECLINED_ACCEPT = 3\n"
        _change_indent(-1)
        return enum_str

    def _agent_role_enum_str(self) -> str:
        """
        Generate the agent role Enum class.

        :return: the agent role Enum string
        """
        enum_str = indent + "class AgentRole(Enum):\n"
        _change_indent(1)
        enum_str += (
            indent + '"""This class defines the agent\'s role in the dialogue."""\n\n'
        )
        enum_str += indent + 'SELLER = "seller"\n'
        enum_str += indent + 'BUYER = "buyer"\n'
        _change_indent(-1)
        return enum_str

    def _dialogue_class_str(self) -> str:
        """
        Produce the content of the Message class.

        :return: the message.py file content
        """
        _change_indent(0, "s")

        # Header
        cls_str = _copyright_header_str(self.protocol_specification.author) + "\n"

        # Module docstring
        cls_str += indent + '"""\n'
        cls_str += (
            indent
            + "This module contains the classes required for {} dialogue management.\n\n".format(
                self.protocol_specification.name
            )
        )
        cls_str += (
            indent
            + "- DialogueLabel: The dialogue label class acts as an identifier for dialogues.\n"
        )
        cls_str += (
            indent
            + "- Dialogue: The dialogue class maintains state of a dialogue and manages it.\n"
        )
        cls_str += (
            indent + "- Dialogues: The dialogues class keeps track of all dialogues.\n"
        )
        cls_str += indent + '"""\n\n'

        # Imports
        cls_str += indent + "from enum import Enum\n"
        cls_str += indent + "from typing import Dict, List, Tuple, Union, cast\n\n"
        cls_str += (
            indent
            + "from aea.helpers.dialogue.base import Dialogue, DialogueLabel, Dialogues\n"
        )
        cls_str += indent + "from aea.mail.base import Address\n"
        cls_str += indent + "from aea.protocols.base import Message\n\n"
        cls_str += indent + "from {}.message import {}Message\n".format(
            self.path_to_protocol_package, self.protocol_specification_in_camel_case,
        )

        # Constants
        cls_str += indent + "\n"
        cls_str += indent + "REPLY = " + str(self._reply) + "\n"

        # Class Header
        cls_str += "\n\nclass {}Dialogue(Dialogue):\n".format(
            self.protocol_specification_in_camel_case
        )
        _change_indent(1)
        cls_str += (
            indent
            + '"""The {} dialogue class maintains state of a dialogue and manages it."""\n'.format(
                self.protocol_specification.name
            )
        )

        # Class Constants
        cls_str += indent + "\n"
        cls_str += indent + "STARTING_MESSAGE_ID = 1\n"
        cls_str += indent + "STARTING_TARGET = 0\n"
        cls_str += indent + "\n"

        # Performatives Enum
        cls_str += "\n" + self._end_state_enum_str()
        cls_str += "\n" + self._agent_role_enum_str()
        cls_str += "\n"

        # __init__
        cls_str += indent + "def __init__(\n"
        _change_indent(1)
        cls_str += (
            indent + "self, dialogue_label: DialogueLabel, is_seller: bool, **kwargs\n"
        )
        _change_indent(-1)
        cls_str += indent + ") -> None:\n"
        _change_indent(1)
        cls_str += indent + '"""\n'
        cls_str += indent + "Initialize a dialogue label.\n\n"
        cls_str += indent + ":param dialogue_label: the identifier of the dialogue.\n"
        cls_str += (
            indent
            + ":param is_seller: indicates whether the agent associated with the dialogue is a seller or buyer\n\n"
        )
        cls_str += indent + ":return: None\n"
        cls_str += indent + '"""\n'
        cls_str += indent + "super().__init__(self, dialogue_label=dialogue_label)\n"
        cls_str += indent + "self._is_seller = is_seller\n"
        cls_str += indent + "self._role = (\n"
        _change_indent(1)
        cls_str += (
            indent
            + "{}Dialogue.AgentRole.SELLER if is_seller else {}Dialogue.AgentRole.BUYER\n".format(
                self.protocol_specification_in_camel_case,
                self.protocol_specification_in_camel_case,
            )
        )
        _change_indent(-1)
        cls_str += indent + ")\n\n"
        _change_indent(-1)

        # Instance properties
        cls_str += indent + "@property\n"
        cls_str += indent + "def is_seller(self) -> bool:\n"
        _change_indent(1)
        cls_str += (
            indent
            + '"""Check whether the agent acts as the seller in this dialogue."""\n'
        )
        cls_str += indent + "return self._is_seller\n\n"
        _change_indent(-1)
        cls_str += indent + "@property\n"
        cls_str += indent + 'def role(self) -> "{}Dialogue.AgentRole":\n'.format(
            self.protocol_specification_in_camel_case
        )
        _change_indent(1)
        cls_str += indent + '"""Get role of agent in dialogue."""\n'
        cls_str += indent + "return self._role\n\n"
        _change_indent(-1)

        # is_consistent method
        cls_str += (
            indent
            + "def is_valid_next_message(self, {}_msg: Message) -> bool:\n".format(
                self.protocol_specification.name
            )
        )
        _change_indent(1)
        cls_str += (
            indent
            + '"""Check that the message is consistent with respect to the {} dialogue according to the protocol."""\n'.format(
                self.protocol_specification.name
            )
        )
        cls_str += indent + "{}_msg = cast({}Message, {}_msg)\n".format(
            self.protocol_specification.name,
            self.protocol_specification_in_camel_case,
            self.protocol_specification.name,
        )
        cls_str += indent + "this_message_id = {}_msg.message_id\n".format(
            self.protocol_specification.name
        )
        cls_str += indent + "this_target = {}_msg.target\n".format(
            self.protocol_specification.name
        )
        cls_str += indent + "this_performative = {}_msg.performative\n".format(
            self.protocol_specification.name
        )
        cls_str += (
            indent
            + "last_outgoing_message = cast({}Message, self.last_outgoing_message)\n".format(
                self.protocol_specification_in_camel_case
            )
        )
        cls_str += indent + "if last_outgoing_message is None:\n"
        _change_indent(1)
        cls_str += indent + "result = (\n"
        _change_indent(1)
        cls_str += (
            indent
            + "this_message_id == {}Dialogue.STARTING_MESSAGE_ID\n".format(
                self.protocol_specification_in_camel_case
            )
        )
        cls_str += indent + "and this_target == {}Dialogue.STARTING_TARGET\n".format(
            self.protocol_specification_in_camel_case
        )
        cls_str += (
            indent
            + "and this_performative == {}Message.Performative.CFP\n".format(
                self.protocol_specification_in_camel_case
            )
        )
        _change_indent(-1)
        cls_str += indent + ")\n"
        _change_indent(-1)
        cls_str += indent + "else:\n"
        _change_indent(1)
        cls_str += indent + "last_message_id = last_outgoing_message.message_id\n"
        cls_str += indent + "last_target = last_outgoing_message.target\n"
        cls_str += indent + "last_performative = last_outgoing_message.performative\n"
        cls_str += indent + "result = (\n"
        _change_indent(1)
        cls_str += indent + "this_message_id == last_message_id + 1\n"
        cls_str += indent + "and this_target == last_target + 1\n"
        cls_str += indent + "and last_performative in REPLY[this_performative]\n"
        _change_indent(-1)
        cls_str += indent + ")\n"
        _change_indent(-1)
        cls_str += indent + "return result\n\n"
        _change_indent(-1)

        # assign final label
        cls_str += (
            indent
            + "def assign_final_dialogue_label(self, final_dialogue_label: DialogueLabel) -> None:\n"
        )
        _change_indent(1)
        cls_str += indent + '"""\n'
        cls_str += indent + "Assign the final dialogue label.\n\n"
        cls_str += indent + ":param final_dialogue_label: the final dialogue label\n"
        cls_str += indent + ":return: None\n"
        cls_str += indent + '"""\n'
        cls_str += indent + "assert (\n"
        _change_indent(1)
        cls_str += indent + "self.dialogue_label.dialogue_starter_reference\n"
        cls_str += indent + "== final_dialogue_label.dialogue_starter_reference\n"
        _change_indent(-1)
        cls_str += indent + ")\n"
        cls_str += (
            indent + 'assert self.dialogue_label.dialogue_responder_reference == ""\n'
        )
        cls_str += (
            indent + 'assert final_dialogue_label.dialogue_responder_reference != ""\n'
        )
        cls_str += indent + "assert (\n"
        _change_indent(1)
        cls_str += indent + "self.dialogue_label.dialogue_opponent_addr\n"
        cls_str += indent + "== final_dialogue_label.dialogue_opponent_addr\n"
        _change_indent(-1)
        cls_str += indent + ")\n"
        cls_str += indent + "assert (\n"
        _change_indent(1)
        cls_str += indent + "self.dialogue_label.dialogue_starter_addr\n"
        cls_str += indent + "== final_dialogue_label.dialogue_starter_addr\n"
        _change_indent(-1)
        cls_str += indent + ")\n"
        cls_str += indent + "self._dialogue_label = final_dialogue_label\n\n"
        _change_indent(-2)

        # stats class
        cls_str += indent + "class {}DialogueStats(object):\n".format(
            self.protocol_specification_in_camel_case
        )
        _change_indent(1)
        cls_str += (
            indent
            + '"""Class to handle statistics for {} dialogues."""\n\n'.format(
                self.protocol_specification.name
            )
        )
        cls_str += indent + "def __init__(self) -> None:\n"
        _change_indent(1)
        cls_str += indent + '"""Initialize a StatsManager."""\n'
        cls_str += indent + "self._self_initiated = {\n"
        _change_indent(1)
        cls_str += indent + "{}Dialogue.EndState.SUCCESSFUL: 0,\n".format(
            self.protocol_specification_in_camel_case
        )
        cls_str += indent + "{}Dialogue.EndState.DECLINED_CFP: 0,\n".format(
            self.protocol_specification_in_camel_case
        )
        cls_str += indent + "{}Dialogue.EndState.DECLINED_PROPOSE: 0,\n".format(
            self.protocol_specification_in_camel_case
        )
        cls_str += indent + "{}Dialogue.EndState.DECLINED_ACCEPT: 0,\n".format(
            self.protocol_specification_in_camel_case
        )
        _change_indent(-1)
        cls_str += indent + "}}  # type: Dict[{}Dialogue.EndState, int]\n".format(
            self.protocol_specification_in_camel_case
        )
        cls_str += indent + "self._other_initiated = {\n"
        _change_indent(1)
        cls_str += indent + "{}Dialogue.EndState.SUCCESSFUL: 0,\n".format(
            self.protocol_specification_in_camel_case
        )
        cls_str += indent + "{}Dialogue.EndState.DECLINED_CFP: 0,\n".format(
            self.protocol_specification_in_camel_case
        )
        cls_str += indent + "{}Dialogue.EndState.DECLINED_PROPOSE: 0,\n".format(
            self.protocol_specification_in_camel_case
        )
        cls_str += indent + "{}Dialogue.EndState.DECLINED_ACCEPT: 0,\n".format(
            self.protocol_specification_in_camel_case
        )
        _change_indent(-1)
        cls_str += indent + "}}  # type: Dict[{}Dialogue.EndState, int]\n\n".format(
            self.protocol_specification_in_camel_case
        )
        _change_indent(-1)
        cls_str += indent + "@property\n"
        cls_str += (
            indent
            + "def self_initiated(self) -> Dict[{}Dialogue.EndState, int]:\n".format(
                self.protocol_specification_in_camel_case
            )
        )
        _change_indent(1)
        cls_str += (
            indent + '"""Get the stats dictionary on self initiated dialogues."""\n'
        )
        cls_str += indent + "return self._self_initiated\n\n"
        _change_indent(-1)
        cls_str += indent + "@property\n"
        cls_str += (
            indent
            + "def other_initiated(self) -> Dict[{}Dialogue.EndState, int]:\n".format(
                self.protocol_specification_in_camel_case
            )
        )
        _change_indent(1)
        cls_str += (
            indent + '"""Get the stats dictionary on other initiated dialogues."""\n'
        )
        cls_str += indent + "return self._other_initiated\n\n"
        _change_indent(-1)
        cls_str += indent + "def add_dialogue_endstate(\n"
        _change_indent(1)
        cls_str += (
            indent
            + "self, end_state: {}Dialogue.EndState, is_self_initiated: bool\n".format(
                self.protocol_specification_in_camel_case
            )
        )
        _change_indent(-1)
        cls_str += indent + ") -> None:\n"
        _change_indent(1)
        cls_str += indent + '"""\n'
        cls_str += indent + "Add dialogue endstate stats.\n\n"
        cls_str += indent + ":param end_state: the end state of the dialogue\n"
        cls_str += (
            indent
            + ":param is_self_initiated: whether the dialogue is initiated by the agent or the opponent\n\n"
        )
        cls_str += indent + ":return: None\n"
        cls_str += indent + '"""\n'
        cls_str += indent + "if is_self_initiated:\n"
        _change_indent(1)
        cls_str += indent + "self._self_initiated[end_state] += 1\n"
        _change_indent(-1)
        cls_str += indent + "else:\n"
        _change_indent(1)
        cls_str += indent + "self._other_initiated[end_state] += 1\n"
        _change_indent(-3)

        # dialogues class
        cls_str += indent + "class {}Dialogues(Dialogues):\n".format(
            self.protocol_specification_in_camel_case
        )
        _change_indent(1)
        cls_str += (
            indent
            + '"""This class keeps track of all {} dialogues."""\n\n'.format(
                self.protocol_specification.name
            )
        )
        cls_str += indent + "def __init__(self) -> None:\n"
        _change_indent(1)
        cls_str += indent + '"""\n'
        cls_str += indent + "Initialize dialogues.\n\n"
        cls_str += indent + ":return: None\n"
        cls_str += indent + '"""\n'
        cls_str += indent + "super().__init__(self)\n"
        cls_str += (
            indent
            + "self._initiated_dialogues = {{}}  # type: Dict[DialogueLabel, {}Dialogue]\n".format(
                self.protocol_specification_in_camel_case
            )
        )
        cls_str += (
            indent
            + "self._dialogues_as_seller = {{}}  # type: Dict[DialogueLabel, {}Dialogue]\n".format(
                self.protocol_specification_in_camel_case
            )
        )
        cls_str += (
            indent
            + "self._dialogues_as_buyer = {{}}  # type: Dict[DialogueLabel, {}Dialogue]\n".format(
                self.protocol_specification_in_camel_case
            )
        )
        cls_str += indent + "self._dialogue_stats = {}DialogueStats()\n".format(
            self.protocol_specification_in_camel_case
        )
        _change_indent(-1)
        cls_str += indent + "@property\n"
        cls_str += (
            indent
            + "def dialogues_as_seller(self) -> Dict[DialogueLabel, {}Dialogue]:\n".format(
                self.protocol_specification_in_camel_case
            )
        )
        _change_indent(1)
        cls_str += (
            indent
            + '"""Get dictionary of dialogues in which the agent acts as a seller."""\n'
        )
        cls_str += indent + "return self._dialogues_as_seller\n\n"
        _change_indent(-1)
        cls_str += indent + "@property\n"
        cls_str += (
            indent
            + "def dialogues_as_buyer(self) -> Dict[DialogueLabel, {}Dialogue]:\n".format(
                self.protocol_specification_in_camel_case
            )
        )
        _change_indent(1)
        cls_str += (
            indent
            + '"""Get dictionary of dialogues in which the agent acts as a buyer."""\n'
        )
        cls_str += indent + "return self._dialogues_as_buyer\n\n"
        _change_indent(-1)
        cls_str += indent + "@property\n"
        cls_str += indent + "def dialogue_stats(self) -> {}DialogueStats:\n".format(
            self.protocol_specification_in_camel_case
        )
        _change_indent(1)
        cls_str += indent + '"""Get the dialogue statistics."""\n'
        cls_str += indent + "return self._dialogue_stats\n"
        _change_indent(-1)

        # get dialogue
        cls_str += (
            indent
            + "def get_dialogue(self, {}_msg: Message, agent_addr: Address) -> Dialogue:\n".format(
                self.protocol_specification.name
            )
        )
        _change_indent(1)
        cls_str += indent + '"""\n'
        cls_str += (
            indent
            + "Given a message addressed to a specific dialogue, retrieve this dialogue if the message is a valid next move.\n\n"
        )
        cls_str += indent + ":param {}_msg: the message\n".format(
            self.protocol_specification.name
        )
        cls_str += indent + ":param agent_addr: the address of the agent\n\n"
        cls_str += indent + ":return: the dialogue\n"
        cls_str += indent + '"""\n'
        cls_str += indent + "result = None\n"
        cls_str += indent + "{}_msg = cast({}Message, {}_msg)\n".format(
            self.protocol_specification.name,
            self.protocol_specification_in_camel_case,
            self.protocol_specification.name,
        )
        cls_str += indent + "dialogue_reference = {}_msg.dialogue_reference\n".format(
            self.protocol_specification.name
        )
        cls_str += indent + "self_initiated_dialogue_label = DialogueLabel(\n"
        _change_indent(1)
        cls_str += (
            indent
            + "dialogue_reference, {}_msg.counterparty, agent_addr\n".format(
                self.protocol_specification.name
            )
        )
        _change_indent(-1)
        cls_str += indent + ")\n"
        cls_str += indent + "other_initiated_dialogue_label = DialogueLabel(\n"
        _change_indent(1)
        cls_str += (
            indent
            + "dialogue_reference, {}_msg.counterparty, {}_msg.counterparty\n".format(
                self.protocol_specification.name, self.protocol_specification.name
            )
        )
        _change_indent(-1)
        cls_str += indent + ")\n"
        cls_str += indent + "if other_initiated_dialogue_label in self.dialogues:\n"
        _change_indent(1)
        cls_str += indent + "other_initiated_dialogue = cast(\n"
        _change_indent(1)
        cls_str += (
            indent
            + "{}Dialogue, self.dialogues[other_initiated_dialogue_label]\n".format(
                self.protocol_specification_in_camel_case
            )
        )
        _change_indent(-1)
        cls_str += indent + ")\n"
        cls_str += (
            indent
            + "if other_initiated_dialogue.is_valid_next_message({}_msg):\n".format(
                self.protocol_specification.name
            )
        )
        _change_indent(1)
        cls_str += indent + "result = other_initiated_dialogue\n"
        _change_indent(-2)
        cls_str += indent + "if self_initiated_dialogue_label in self.dialogues:\n"
        _change_indent(1)
        cls_str += indent + "self_initiated_dialogue = cast(\n"
        _change_indent(1)
        cls_str += (
            indent
            + "{}Dialogue, self.dialogues[self_initiated_dialogue_label]\n".format(
                self.protocol_specification_in_camel_case
            )
        )
        _change_indent(-1)
        cls_str += indent + ")\n"
        cls_str += (
            indent
            + "if self_initiated_dialogue.is_valid_next_message({}_msg):\n".format(
                self.protocol_specification.name
            )
        )
        _change_indent(1)
        cls_str += indent + "result = self_initiated_dialogue\n"
        _change_indent(-2)
        cls_str += indent + "if result is None:\n"
        _change_indent(1)
        cls_str += indent + 'raise ValueError("Should have found dialogue.")\n'
        _change_indent(-1)
        cls_str += indent + "return result\n"
        _change_indent(-1)

        # create methods
        cls_str += indent + "def create_self_initiated(\n"
        _change_indent(1)
        cls_str += indent + "self,\n"
        cls_str += indent + "dialogue_opponent_addr: Address,\n"
        cls_str += indent + "dialogue_starter_addr: Address,\n"
        cls_str += indent + "is_seller: bool,\n"
        _change_indent(-1)
        cls_str += indent + ") -> Dialogue:\n"
        _change_indent(1)
        cls_str += indent + '"""\n'
        cls_str += indent + "Create a self initiated dialogue.\n\n"
        cls_str += (
            indent
            + ":param dialogue_opponent_addr: the pbk of the agent with which the dialogue is kept.\n"
        )
        cls_str += (
            indent
            + ":param dialogue_starter_addr: the pbk of the agent which started the dialogue\n"
        )
        cls_str += indent + ":param is_seller: boolean indicating the agent role\n\n"
        cls_str += indent + ":return: the created dialogue.\n"
        cls_str += indent + '"""\n'
        cls_str += (
            indent + 'dialogue_reference = (str(self._next_dialogue_nonce()), "")\n'
        )
        cls_str += indent + "dialogue_label = DialogueLabel(\n"
        _change_indent(1)
        cls_str += (
            indent
            + "dialogue_reference, dialogue_opponent_addr, dialogue_starter_addr\n"
        )
        _change_indent(-1)
        cls_str += indent + ")\n"
        cls_str += indent + "dialogue = {}Dialogue(dialogue_label, is_seller)\n".format(
            self.protocol_specification_in_camel_case
        )
        cls_str += (
            indent + "self._initiated_dialogues.update({dialogue_label: dialogue})\n"
        )
        cls_str += indent + "return dialogue\n\n"
        _change_indent(-1)
        cls_str += indent + "def create_opponent_initiated(\n"
        _change_indent(1)
        cls_str += indent + "self,\n"
        cls_str += indent + "dialogue_opponent_addr: Address,\n"
        cls_str += indent + "dialogue_reference: Tuple[str, str],\n"
        cls_str += indent + "is_seller: bool,\n"
        _change_indent(-1)
        cls_str += indent + ") -> Dialogue:\n"
        _change_indent(1)
        cls_str += indent + '"""\n'
        cls_str += indent + "Save an opponent initiated dialogue.\n\n"
        cls_str += (
            indent
            + ":param dialogue_opponent_addr: the address of the agent with which the dialogue is kept.\n"
        )
        cls_str += (
            indent + ":param dialogue_reference: the reference of the dialogue.\n"
        )
        cls_str += (
            indent + ":param is_seller: keeps track if the counterparty is a seller.\n"
        )
        cls_str += indent + ":return: the created dialogue\n"
        cls_str += indent + '"""\n'
        cls_str += indent + "assert (\n"
        _change_indent(1)
        cls_str += (
            indent + 'dialogue_reference[0] != "" and dialogue_reference[1] == ""\n'
        )
        _change_indent(-1)
        cls_str += (
            indent
            + '), "Cannot initiate dialogue with preassigned dialogue_responder_reference!"\n'
        )
        cls_str += indent + "new_dialogue_reference = (\n"
        _change_indent(1)
        cls_str += indent + "dialogue_reference[0],\n"
        cls_str += indent + "str(self._next_dialogue_nonce()),\n"
        _change_indent(-1)
        cls_str += indent + ")\n"
        cls_str += indent + "dialogue_label = DialogueLabel(\n"
        _change_indent(1)
        cls_str += (
            indent
            + "new_dialogue_reference, dialogue_opponent_addr, dialogue_opponent_addr\n"
        )
        _change_indent(-1)
        cls_str += indent + ")\n"
        cls_str += indent + "result = self._create(dialogue_label, is_seller)\n"
        cls_str += indent + "return result\n\n"
        _change_indent(-1)
        cls_str += (
            indent
            + "def _create(self, dialogue_label: DialogueLabel, is_seller: bool) -> {}Dialogue:\n".format(
                self.protocol_specification_in_camel_case
            )
        )
        _change_indent(1)
        cls_str += indent + '"""\n'
        cls_str += indent + "Create a dialogue.\n\n"
        cls_str += indent + ":param dialogue_label: the dialogue label\n"
        cls_str += indent + ":param is_seller: boolean indicating the agent role\n\n"
        cls_str += indent + ":return: the created dialogue\n"
        cls_str += indent + '"""\n'
        cls_str += indent + "assert dialogue_label not in self.dialogues\n"
        cls_str += indent + "dialogue = {}Dialogue(dialogue_label, is_seller)\n".format(
            self.protocol_specification_in_camel_case
        )
        cls_str += indent + "if is_seller:\n"
        _change_indent(1)
        cls_str += indent + "assert dialogue_label not in self.dialogues_as_seller\n"
        cls_str += (
            indent + "self._dialogues_as_seller.update({dialogue_label: dialogue})\n"
        )
        _change_indent(-1)
        cls_str += indent + "else:\n"
        _change_indent(1)
        cls_str += indent + "assert dialogue_label not in self.dialogues_as_buyer\n"
        cls_str += (
            indent + "self._dialogues_as_buyer.update({dialogue_label: dialogue})\n"
        )
        _change_indent(-1)
        cls_str += indent + "self.dialogues.update({dialogue_label: dialogue})\n"
        cls_str += indent + "return dialogue\n"
        _change_indent(-1)

        return cls_str

    def _custom_types_module_str(self) -> str:
        """
        Produces the contents of the custom_types module, containing classes corresponding to every custom type in the protocol specification.

        :return: the custom_types.py file content
        """
        _change_indent(0, "s")

        # Header
        cls_str = _copyright_header_str(self.protocol_specification.author) + "\n"

        # Module docstring
        cls_str += '"""This module contains class representations corresponding to every custom type in the protocol specification."""\n'

        if not self._all_custom_types:
            return cls_str

        # class code per custom type
        for custom_type in self._all_custom_types:
            cls_str += indent + "\n\nclass {}:\n".format(custom_type)
            _change_indent(1)
            cls_str += (
                indent
                + '"""This class represents an instance of {}."""\n\n'.format(
                    custom_type
                )
            )
            cls_str += indent + "def __init__(self):\n"
            _change_indent(1)
            cls_str += indent + '"""Initialise an instance of {}."""\n'.format(
                custom_type
            )
            cls_str += indent + "raise NotImplementedError\n\n"
            _change_indent(-1)
            cls_str += indent + "@staticmethod\n"
            cls_str += (
                indent
                + 'def encode({}_protobuf_object, {}_object: "{}") -> None:\n'.format(
                    _camel_case_to_snake_case(custom_type),
                    _camel_case_to_snake_case(custom_type),
                    custom_type,
                )
            )
            _change_indent(1)
            cls_str += indent + '"""\n'
            cls_str += (
                indent
                + "Encode an instance of this class into the protocol buffer object.\n\n"
            )
            cls_str += (
                indent
                + "The protocol buffer object in the {}_protobuf_object argument must be matched with the instance of this class in the '{}_object' argument.\n\n".format(
                    _camel_case_to_snake_case(custom_type),
                    _camel_case_to_snake_case(custom_type),
                )
            )
            cls_str += (
                indent
                + ":param {}_protobuf_object: the protocol buffer object whose type corresponds with this class.\n".format(
                    _camel_case_to_snake_case(custom_type)
                )
            )
            cls_str += (
                indent
                + ":param {}_object: an instance of this class to be encoded in the protocol buffer object.\n".format(
                    _camel_case_to_snake_case(custom_type)
                )
            )
            cls_str += indent + ":return: None\n"
            cls_str += indent + '"""\n'
            cls_str += indent + "raise NotImplementedError\n\n"
            _change_indent(-1)

            cls_str += indent + "@classmethod\n"
            cls_str += indent + 'def decode(cls, {}_protobuf_object) -> "{}":\n'.format(
                _camel_case_to_snake_case(custom_type), custom_type,
            )
            _change_indent(1)
            cls_str += indent + '"""\n'
            cls_str += (
                indent
                + "Decode a protocol buffer object that corresponds with this class into an instance of this class.\n\n"
            )
            cls_str += (
                indent
                + "A new instance of this class must be created that matches the protocol buffer object in the '{}_protobuf_object' argument.\n\n".format(
                    _camel_case_to_snake_case(custom_type)
                )
            )
            cls_str += (
                indent
                + ":param {}_protobuf_object: the protocol buffer object whose type corresponds with this class.\n".format(
                    _camel_case_to_snake_case(custom_type)
                )
            )
            cls_str += (
                indent
                + ":return: A new instance of this class that matches the protocol buffer object in the '{}_protobuf_object' argument.\n".format(
                    _camel_case_to_snake_case(custom_type)
                )
            )
            cls_str += indent + '"""\n'
            cls_str += indent + "raise NotImplementedError\n\n"
            _change_indent(-1)

            cls_str += indent + "def __eq__(self, other):\n"
            _change_indent(1)
            cls_str += indent + "raise NotImplementedError\n"
            _change_indent(-2)
        return cls_str

    def _encoding_message_content_from_python_to_protobuf(
        self, content_name: str, content_type: str,
    ) -> str:
        """
        Produce the encoding of message contents for the serialisation class.

        :param content_name: the name of the content to be encoded
        :param content_type: the type of the content to be encoded
        :return: the encoding string
        """
        encoding_str = ""
        if content_type in PYTHON_TYPE_TO_PROTO_TYPE.keys():
            encoding_str += indent + "{} = msg.{}\n".format(content_name, content_name)
            encoding_str += indent + "performative.{} = {}\n".format(
                content_name, content_name
            )
        elif content_type.startswith("FrozenSet") or content_type.startswith("Tuple"):
            encoding_str += indent + "{} = msg.{}\n".format(content_name, content_name)
            encoding_str += indent + "performative.{}.extend({})\n".format(
                content_name, content_name
            )
        elif content_type.startswith("Dict"):
            encoding_str += indent + "{} = msg.{}\n".format(content_name, content_name)
            encoding_str += indent + "performative.{}.update({})\n".format(
                content_name, content_name
            )
        elif content_type.startswith("Union"):
            sub_types = _get_sub_types_of_compositional_types(content_type)
            for sub_type in sub_types:
                sub_type_name_in_protobuf = _union_sub_type_to_protobuf_variable_name(
                    content_name, sub_type
                )
                encoding_str += indent + 'if msg.is_set("{}"):\n'.format(
                    sub_type_name_in_protobuf
                )
                _change_indent(1)
                encoding_str += indent + "performative.{}_is_set = True\n".format(
                    sub_type_name_in_protobuf
                )
                encoding_str += self._encoding_message_content_from_python_to_protobuf(
                    sub_type_name_in_protobuf, sub_type
                )
                _change_indent(-1)
        elif content_type.startswith("Optional"):
            sub_type = _get_sub_types_of_compositional_types(content_type)[0]
            if not sub_type.startswith("Union"):
                encoding_str += indent + 'if msg.is_set("{}"):\n'.format(content_name)
                _change_indent(1)
                encoding_str += indent + "performative.{}_is_set = True\n".format(
                    content_name
                )
            encoding_str += self._encoding_message_content_from_python_to_protobuf(
                content_name, sub_type
            )
            if not sub_type.startswith("Union"):
                _change_indent(-1)
        else:
            encoding_str += indent + "{} = msg.{}\n".format(content_name, content_name)
            encoding_str += indent + "{}.encode(performative.{}, {})\n".format(
                content_type, content_name, content_name
            )
        return encoding_str

    def _decoding_message_content_from_protobuf_to_python(
        self,
        performative: str,
        content_name: str,
        content_type: str,
        variable_name_in_protobuf: Optional[str] = "",
    ) -> str:
        """
        Produce the decoding of message contents for the serialisation class.

        :param performative: the performative to which the content belongs
        :param content_name: the name of the content to be decoded
        :param content_type: the type of the content to be decoded
        :param no_indents: the number of indents based on the previous sections of the code
        :return: the decoding string
        """
        decoding_str = ""
        variable_name = (
            content_name if not variable_name_in_protobuf else variable_name_in_protobuf
        )
        if content_type in PYTHON_TYPE_TO_PROTO_TYPE.keys():
            decoding_str += indent + "{} = {}_pb.{}.{}\n".format(
                content_name,
                self.protocol_specification.name,
                performative,
                variable_name,
            )
            decoding_str += indent + 'performative_content["{}"] = {}\n'.format(
                content_name, content_name
            )
        elif content_type.startswith("FrozenSet"):
            decoding_str += indent + "{} = {}_pb.{}.{}\n".format(
                content_name,
                self.protocol_specification.name,
                performative,
                content_name,
            )
            decoding_str += indent + "{}_frozenset = frozenset({})\n".format(
                content_name, content_name
            )
            decoding_str += (
                indent
                + 'performative_content["{}"] = {}_frozenset\n'.format(
                    content_name, content_name
                )
            )
        elif content_type.startswith("Tuple"):
            decoding_str += indent + "{} = {}_pb.{}.{}\n".format(
                content_name,
                self.protocol_specification.name,
                performative,
                content_name,
            )
            decoding_str += indent + "{}_tuple = tuple({})\n".format(
                content_name, content_name
            )
            decoding_str += indent + 'performative_content["{}"] = {}_tuple\n'.format(
                content_name, content_name
            )
        elif content_type.startswith("Dict"):
            decoding_str += indent + "{} = {}_pb.{}.{}\n".format(
                content_name,
                self.protocol_specification.name,
                performative,
                content_name,
            )
            decoding_str += indent + "{}_dict = dict({})\n".format(
                content_name, content_name
            )
            decoding_str += indent + 'performative_content["{}"] = {}_dict\n'.format(
                content_name, content_name
            )
        elif content_type.startswith("Union"):
            sub_types = _get_sub_types_of_compositional_types(content_type)
            for sub_type in sub_types:
                sub_type_name_in_protobuf = _union_sub_type_to_protobuf_variable_name(
                    content_name, sub_type
                )
                decoding_str += indent + "if {}_pb.{}.{}_is_set:\n".format(
                    self.protocol_specification.name,
                    performative,
                    sub_type_name_in_protobuf,
                )
                _change_indent(1)
                decoding_str += self._decoding_message_content_from_protobuf_to_python(
                    performative=performative,
                    content_name=content_name,
                    content_type=sub_type,
                    variable_name_in_protobuf=sub_type_name_in_protobuf,
                )
                _change_indent(-1)
        elif content_type.startswith("Optional"):
            sub_type = _get_sub_types_of_compositional_types(content_type)[0]
            if not sub_type.startswith("Union"):
                decoding_str += indent + "if {}_pb.{}.{}_is_set:\n".format(
                    self.protocol_specification.name, performative, content_name
                )
                _change_indent(1)
                # no_indents += 1
            decoding_str += self._decoding_message_content_from_protobuf_to_python(
                performative, content_name, sub_type
            )
            if not sub_type.startswith("Union"):
                _change_indent(-1)
        else:
            decoding_str += indent + "pb2_{} = {}_pb.{}.{}\n".format(
                variable_name,
                self.protocol_specification.name,
                performative,
                variable_name,
            )
            decoding_str += indent + "{} = {}.decode(pb2_{})\n".format(
                content_name, content_type, variable_name,
            )
            decoding_str += indent + 'performative_content["{}"] = {}\n'.format(
                content_name, content_name
            )
        return decoding_str

    def _to_custom_custom(self, content_type: str) -> str:
        """
        Evaluate whether a content type is a custom type or has a custom type as a sub-type.
        :return: Boolean result
        """
        new_content_type = content_type
        if _includes_custom_type(content_type):
            for custom_type in self._all_custom_types:
                new_content_type = new_content_type.replace(
                    custom_type, self._custom_custom_types[custom_type]
                )
        return new_content_type

    def _serialization_class_str(self) -> str:
        """
        Produce the content of the Serialization class.

        :return: the serialization.py file content
        """
        _change_indent(0, "s")

        # Header
        cls_str = _copyright_header_str(self.protocol_specification.author) + "\n"

        # Module docstring
        cls_str += indent + '"""Serialization module for {} protocol."""\n\n'.format(
            self.protocol_specification.name
        )

        # Imports
        cls_str += indent + "from typing import Any, Dict, cast\n\n"
        cls_str += MESSAGE_IMPORT + "\n"
        cls_str += SERIALIZER_IMPORT + "\n\n"
        cls_str += indent + "from {} import (\n    {}_pb2,\n)\n".format(
            self.path_to_protocol_package, self.protocol_specification.name,
        )
        for custom_type in self._all_custom_types:
            cls_str += indent + "from {}.custom_types import (\n    {},\n)\n".format(
                self.path_to_protocol_package, custom_type,
            )
        cls_str += indent + "from {}.message import (\n    {}Message,\n)\n".format(
            self.path_to_protocol_package, self.protocol_specification_in_camel_case,
        )

        # Class Header
        cls_str += indent + "\n\nclass {}Serializer(Serializer):\n".format(
            self.protocol_specification_in_camel_case,
        )
        _change_indent(1)
        cls_str += indent + '"""Serialization for the \'{}\' protocol."""\n\n'.format(
            self.protocol_specification.name,
        )

        # encoder
        cls_str += indent + "def encode(self, msg: Message) -> bytes:\n"
        _change_indent(1)
        cls_str += indent + '"""\n'
        cls_str += indent + "Encode a '{}' message into bytes.\n\n".format(
            self.protocol_specification_in_camel_case,
        )
        cls_str += indent + ":param msg: the message object.\n"
        cls_str += indent + ":return: the bytes.\n"
        cls_str += indent + '"""\n'
        cls_str += indent + "msg = cast({}Message, msg)\n".format(
            self.protocol_specification_in_camel_case
        )
        cls_str += indent + "{}_msg = {}_pb2.{}Message()\n".format(
            self.protocol_specification.name,
            self.protocol_specification.name,
            self.protocol_specification_in_camel_case,
        )
        cls_str += indent + "{}_msg.message_id = msg.message_id\n".format(
            self.protocol_specification.name
        )
        cls_str += indent + "dialogue_reference = msg.dialogue_reference\n"
        cls_str += (
            indent
            + "{}_msg.dialogue_starter_reference = dialogue_reference[0]\n".format(
                self.protocol_specification.name
            )
        )
        cls_str += (
            indent
            + "{}_msg.dialogue_responder_reference = dialogue_reference[1]\n".format(
                self.protocol_specification.name
            )
        )
        cls_str += indent + "{}_msg.target = msg.target\n\n".format(
            self.protocol_specification.name
        )
        cls_str += indent + "performative_id = msg.performative\n"
        counter = 1
        for performative, contents in self._speech_acts.items():
            if counter == 1:
                cls_str += indent + "if "
            else:
                cls_str += indent + "elif "
            cls_str += "performative_id == {}Message.Performative.{}:\n".format(
                self.protocol_specification_in_camel_case, performative.upper()
            )
            _change_indent(1)
            cls_str += (
                indent
                + "performative = {}_pb2.{}Message.{}_Performative()  # type: ignore\n".format(
                    self.protocol_specification.name,
                    self.protocol_specification_in_camel_case,
                    performative.title(),
                )
            )
            for content_name, content_type in contents.items():
                cls_str += self._encoding_message_content_from_python_to_protobuf(
                    content_name, content_type
                )
            cls_str += indent + "{}_msg.{}.CopyFrom(performative)\n".format(
                self.protocol_specification.name, performative
            )

            counter += 1
            _change_indent(-1)
        cls_str += indent + "else:\n"
        _change_indent(1)
        cls_str += (
            indent
            + 'raise ValueError("Performative not valid: {}".format(performative_id))\n\n'
        )
        _change_indent(-1)

        cls_str += indent + "{}_bytes = {}_msg.SerializeToString()\n".format(
            self.protocol_specification.name, self.protocol_specification.name
        )
        cls_str += indent + "return {}_bytes\n\n".format(
            self.protocol_specification.name
        )
        _change_indent(-1)

        # decoder
        cls_str += indent + "def decode(self, obj: bytes) -> Message:\n"
        _change_indent(1)
        cls_str += indent + '"""\n'
        cls_str += indent + "Decode bytes into a '{}' message.\n\n".format(
            self.protocol_specification_in_camel_case,
        )
        cls_str += indent + ":param obj: the bytes object.\n"
        cls_str += indent + ":return: the '{}' message.\n".format(
            self.protocol_specification_in_camel_case
        )
        cls_str += indent + '"""\n'
        cls_str += indent + "{}_pb = {}_pb2.{}Message()\n".format(
            self.protocol_specification.name,
            self.protocol_specification.name,
            self.protocol_specification_in_camel_case,
        )
        cls_str += indent + "{}_pb.ParseFromString(obj)\n".format(
            self.protocol_specification.name
        )
        cls_str += indent + "message_id = {}_pb.message_id\n".format(
            self.protocol_specification.name
        )
        cls_str += (
            indent
            + "dialogue_reference = ({}_pb.dialogue_starter_reference, {}_pb.dialogue_responder_reference)\n".format(
                self.protocol_specification.name, self.protocol_specification.name
            )
        )
        cls_str += indent + "target = {}_pb.target\n\n".format(
            self.protocol_specification.name
        )
        cls_str += indent + 'performative = {}_pb.WhichOneof("performative")\n'.format(
            self.protocol_specification.name
        )
        cls_str += (
            indent
            + "performative_id = {}Message.Performative(str(performative))\n".format(
                self.protocol_specification_in_camel_case
            )
        )
        cls_str += indent + "performative_content = dict()  # type: Dict[str, Any]\n"
        counter = 1
        for performative, contents in self._speech_acts.items():
            if counter == 1:
                cls_str += indent + "if "
            else:
                cls_str += indent + "elif "
            cls_str += "performative_id == {}Message.Performative.{}:\n".format(
                self.protocol_specification_in_camel_case, performative.upper()
            )
            _change_indent(1)
            if not contents:
                cls_str += indent + "pass\n"
            else:
                for content_name, content_type in contents.items():
                    cls_str += self._decoding_message_content_from_protobuf_to_python(
                        performative, content_name, content_type
                    )
            counter += 1
            _change_indent(-1)
        cls_str += indent + "else:\n"
        _change_indent(1)
        cls_str += (
            indent
            + 'raise ValueError("Performative not valid: {}.".format(performative_id))\n\n'
        )
        _change_indent(-1)

        cls_str += indent + "return {}Message(\n".format(
            self.protocol_specification_in_camel_case,
        )
        _change_indent(1)
        cls_str += indent + "message_id=message_id,\n"
        cls_str += indent + "dialogue_reference=dialogue_reference,\n"
        cls_str += indent + "target=target,\n"
        cls_str += indent + "performative=performative,\n"
        cls_str += indent + "**performative_content\n"
        _change_indent(-1)
        cls_str += indent + ")\n"
        _change_indent(-2)

        return cls_str

    def _content_to_proto_field_str(
        self, content_name: str, content_type: str, tag_no: int,
    ) -> Tuple[str, int]:
        """
        Convert a message content to its representation in a protocol buffer schema.

        :param content_name: the name of the content
        :param content_type: the type of the content
        :param content_type: the tag number
        :return: the content in protocol buffer schema
        """
        entry = ""

        if content_type.startswith("FrozenSet") or content_type.startswith(
            "Tuple"
        ):  # it is a <PCT>
            element_type = _get_sub_types_of_compositional_types(content_type)[0]
            proto_type = _python_pt_or_ct_type_to_proto_type(element_type)
            entry = indent + "repeated {} {} = {};\n".format(
                proto_type, content_name, tag_no
            )
            tag_no += 1
        elif content_type.startswith("Dict"):  # it is a <PMT>
            key_type = _get_sub_types_of_compositional_types(content_type)[0]
            value_type = _get_sub_types_of_compositional_types(content_type)[1]
            proto_key_type = _python_pt_or_ct_type_to_proto_type(key_type)
            proto_value_type = _python_pt_or_ct_type_to_proto_type(value_type)
            entry = indent + "map<{}, {}> {} = {};\n".format(
                proto_key_type, proto_value_type, content_name, tag_no
            )
            tag_no += 1
        elif content_type.startswith("Union"):  # it is an <MT>
            sub_types = _get_sub_types_of_compositional_types(content_type)
            for sub_type in sub_types:
                sub_type_name = _union_sub_type_to_protobuf_variable_name(
                    content_name, sub_type
                )
                content_to_proto_field_str, tag_no = self._content_to_proto_field_str(
                    sub_type_name, sub_type, tag_no
                )
                entry += content_to_proto_field_str
        elif content_type.startswith("Optional"):  # it is an <O>
            sub_type = _get_sub_types_of_compositional_types(content_type)[0]
            content_to_proto_field_str, tag_no = self._content_to_proto_field_str(
                content_name, sub_type, tag_no
            )
            entry = content_to_proto_field_str
            entry += indent + "bool {}_is_set = {};\n".format(content_name, tag_no)
            tag_no += 1
        else:  # it is a <CT> or <PT>
            proto_type = _python_pt_or_ct_type_to_proto_type(content_type)
            entry = indent + "{} {} = {};\n".format(proto_type, content_name, tag_no)
            tag_no += 1
        return entry, tag_no

    def _protocol_buffer_schema_str(self) -> str:
        """
        Produce the content of the Protocol Buffers schema.

        :return: the protocol buffers schema content
        """
        _change_indent(0, "s")

        # heading
        proto_buff_schema_str = indent + 'syntax = "proto3";\n\n'
        proto_buff_schema_str += indent + "package fetch.aea.{};\n\n".format(
            self.protocol_specification_in_camel_case
        )
        proto_buff_schema_str += indent + "message {}Message{{\n\n".format(
            self.protocol_specification_in_camel_case
        )
        _change_indent(1)

        # custom types
        if self._all_custom_types and (self.protocol_specification.protobuf_snippets):
            proto_buff_schema_str += indent + "// Custom Types\n"
            for custom_type in self._all_custom_types:
                proto_buff_schema_str += indent + "message {}{{\n".format(custom_type)
                _change_indent(1)

                # formatting and adding the custom type protobuf entry
                specification_custom_type = "ct:" + custom_type
                proto_part = self.protocol_specification.protobuf_snippets[
                    specification_custom_type
                ]
                number_of_new_lines = proto_part.count("\n")
                if number_of_new_lines:
                    formatted_proto_part = proto_part.replace(
                        "\n", "\n" + indent, number_of_new_lines - 1
                    )
                else:
                    formatted_proto_part = proto_part
                proto_buff_schema_str += indent + formatted_proto_part
                _change_indent(-1)

                proto_buff_schema_str += indent + "}\n\n"
            proto_buff_schema_str += "\n"

        # performatives
        proto_buff_schema_str += indent + "// Performatives and contents\n"
        for performative, contents in self._speech_acts.items():
            proto_buff_schema_str += indent + "message {}_Performative{{".format(
                performative.title()
            )
            _change_indent(1)
            tag_no = 1
            if not contents:
                proto_buff_schema_str += "}\n\n"
            else:
                proto_buff_schema_str += "\n"
                for content_name, content_type in contents.items():
                    (
                        content_to_proto_field_str,
                        tag_no,
                    ) = self._content_to_proto_field_str(
                        content_name, content_type, tag_no
                    )
                    proto_buff_schema_str += content_to_proto_field_str
                _change_indent(-1)
                proto_buff_schema_str += indent + "}\n\n"
        proto_buff_schema_str += "\n"
        _change_indent(-1)

        # meta-data
        proto_buff_schema_str += indent + "// Standard {}Message fields\n".format(
            self.protocol_specification_in_camel_case
        )
        proto_buff_schema_str += indent + "int32 message_id = 1;\n"
        proto_buff_schema_str += indent + "string dialogue_starter_reference = 2;\n"
        proto_buff_schema_str += indent + "string dialogue_responder_reference = 3;\n"
        proto_buff_schema_str += indent + "int32 target = 4;\n"
        proto_buff_schema_str += indent + "oneof performative{\n"
        _change_indent(1)
        tag_no = 5
        for performative in self._all_performatives:
            proto_buff_schema_str += indent + "{}_Performative {} = {};\n".format(
                performative.title(), performative, tag_no
            )
            tag_no += 1
        _change_indent(-1)
        proto_buff_schema_str += indent + "}\n"
        _change_indent(-1)

        proto_buff_schema_str += indent + "}\n"
        return proto_buff_schema_str

    def _protocol_yaml_str(self) -> str:
        """
        Produce the content of the protocol.yaml file.

        :return: the protocol.yaml content
        """
        protocol_yaml_str = "name: {}\n".format(self.protocol_specification.name)
        protocol_yaml_str += "author: {}\n".format(self.protocol_specification.author)
        protocol_yaml_str += "version: {}\n".format(self.protocol_specification.version)
        protocol_yaml_str += "description: {}\n".format(
            self.protocol_specification.description
        )
        protocol_yaml_str += "license: {}\n".format(self.protocol_specification.license)
        protocol_yaml_str += "aea_version: '{}'\n".format(
            self.protocol_specification.aea_version
        )
        protocol_yaml_str += "fingerprint: {}\n"
        protocol_yaml_str += "fingerprint_ignore_patterns: []\n"
        protocol_yaml_str += "dependencies:\n"
        protocol_yaml_str += "    protobuf: {}\n"

        return protocol_yaml_str

    def _init_str(self) -> str:
        """
        Produce the content of the __init__.py file.

        :return: the __init__.py content
        """
        init_str = _copyright_header_str(self.protocol_specification.author)
        init_str += "\n"
        init_str += '"""This module contains the support resources for the {} protocol."""\n'.format(
            self.protocol_specification.name
        )

        return init_str

    def _generate_file(self, file_name: str, file_content: str) -> None:
        """
        Create a protocol file.

        :return: None
        """
        pathname = path.join(self.output_folder_path, file_name)

        with open(pathname, "w") as file:
            file.write(file_content)

    def generate(self) -> None:
        """
        Create the protocol package with Message, Serialization, __init__, protocol.yaml files.

        :return: None
        """
        # Create the output folder
        output_folder = Path(self.output_folder_path)
        if not output_folder.exists():
            os.mkdir(output_folder)

        # Generate the protocol files
        self._generate_file(INIT_FILE_NAME, self._init_str())
        self._generate_file(PROTOCOL_YAML_FILE_NAME, self._protocol_yaml_str())
        self._generate_file(MESSAGE_DOT_PY_FILE_NAME, self._message_class_str())
        self._generate_file(DIALOGUE_DOT_PY_FILE_NAME, self._dialogue_class_str())
        if self._all_custom_types:
            self._generate_file(
                CUSTOM_TYPES_DOT_PY_FILE_NAME, self._custom_types_module_str()
            )
        self._generate_file(
            SERIALIZATION_DOT_PY_FILE_NAME, self._serialization_class_str()
        )
        self._generate_file(
            "{}.proto".format(self.protocol_specification.name),
            self._protocol_buffer_schema_str(),
        )

        # Warn if specification has custom types
        if self._all_custom_types:
            incomplete_generation_warning_msg = "The generated protocol is incomplete, because the protocol specification contains the following custom types: {}. Update the generated '{}' file with the appropriate implementations of these custom types.".format(
                self._all_custom_types, CUSTOM_TYPES_DOT_PY_FILE_NAME
            )
            logger.warning(incomplete_generation_warning_msg)

        # Compile protobuf schema
        cmd = "protoc -I={} --python_out={} {}/{}.proto".format(
            self.output_folder_path,
            self.output_folder_path,
            self.output_folder_path,
            self.protocol_specification.name,
        )
        os.system(cmd)  # nosec
