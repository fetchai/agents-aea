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

from aea.configurations.base import ProtocolSpecification

MESSAGE_IMPORT = "from aea.protocols.base import Message"
SERIALIZER_IMPORT = "from aea.protocols.base import Serializer"

PATH_TO_PACKAGES = "packages"
INIT_FILE_NAME = "__init__.py"
PROTOCOL_YAML_FILE_NAME = "protocol.yaml"
MESSAGE_DOT_PY_FILE_NAME = "message.py"
CUSTOM_TYPES_DOT_PY_FILE_NAME = "custom_types.py"
SERIALIZATION_DOT_PY_FILE_NAME = "serialization.py"

CUSTOM_TYPE_PATTERN = "ct:[A-Z][a-zA-Z0-9]*"
PRIMITIVE_TYPES = ["pt:bytes", "pt:int", "pt:float", "pt:bool", "pt:str"]
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

logger = logging.getLogger(__name__)


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


def _get_indent_str(no_of_indents: int) -> str:
    """
    Produce a string containing a number of white spaces equal to 4 times the no_of_indents.

    :param no_of_indents: The number of indents.
    :return: The string containing spaces.
    """
    indents_str = ""
    for _ in itertools.repeat(None, no_of_indents):
        indents_str += "    "
    return indents_str


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
    elif specification_type in PRIMITIVE_TYPES:
        python_type = _pt_specification_type_to_python_type(specification_type)
    elif specification_type.startswith("pt:set"):
        python_type = _pct_specification_type_to_python_type(specification_type)
    elif specification_type.startswith("pt:list"):
        python_type = _pct_specification_type_to_python_type(specification_type)
    elif specification_type.startswith("pt:dict"):
        python_type = _pmt_specification_type_to_python_type(specification_type)
    else:
        raise TypeError("Unsupported type: '{}'".format(specification_type))
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


class ProtocolGenerator:
    """This class generates a protocol_verification package from a ProtocolTemplate object."""

    def __init__(
        self, protocol_specification: ProtocolSpecification, output_path: str = ".",
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

        self._setup()

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
                custom_types = set(re.findall(CUSTOM_TYPE_PATTERN, content_type))
                if len(re.findall("pt:set\\[", content_type)) >= 1:
                    self._imports["FrozenSet"] = True
                if len(re.findall("pt:dict\\[", content_type)) >= 1:
                    self._imports["Dict"] = True
                if len(re.findall("pt:union\\[", content_type)) >= 1:
                    self._imports["Union"] = True
                if len(re.findall("pt:optional\\[", content_type)) >= 1:
                    self._imports["Optional"] = True
                for custom_type in custom_types:
                    all_custom_types_set.add(
                        _specification_type_to_python_type(custom_type)
                    )
                pythonic_content_type = _specification_type_to_python_type(content_type)
                self._all_unique_contents[content_name] = pythonic_content_type
                self._speech_acts[performative][content_name] = pythonic_content_type
        self._all_performatives = sorted(all_performatives_set)
        self._all_custom_types = sorted(all_custom_types_set)
        self._custom_custom_types = {
            pure_custom_type: "Custom" + pure_custom_type
            for pure_custom_type in self._all_custom_types
        }

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
        if len(self._all_custom_types) == 0:
            pass
        else:
            for custom_class in self._all_custom_types:
                import_str += "from {}.{}.protocols.{}.custom_types import {} as Custom{}\n".format(
                    PATH_TO_PACKAGES,
                    self.protocol_specification.author,
                    self.protocol_specification.name,
                    custom_class,
                    custom_class,
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
        enum_str = ""
        enum_str += "    class Performative(Enum):\n"
        enum_str += str.format(
            '        """Performatives for the {} protocol."""\n\n',
            self.protocol_specification.name,
        )
        for performative in self._all_performatives:
            enum_str += '        {} = "{}"\n'.format(performative.upper(), performative)
        enum_str += "\n"
        enum_str += "        def __str__(self):\n"
        enum_str += '            """Get the string representation."""\n'
        enum_str += "            return self.value\n"
        enum_str += "\n"

        return enum_str

    def _check_content_type_str(
        self, no_of_indents: int, content_name: str, content_type: str
    ) -> str:
        """
        Produce the checks of elements of compositional types.

        :param no_of_indents: the number of indents based on the previous sections of the code
        :param content_name: the name of the content to be checked
        :param content_type: the type of the content to be checked
        :return: the string containing the checks.
        """
        check_str = ""
        indents = _get_indent_str(no_of_indents)
        if content_type.startswith("Optional["):
            # check if the content exists then...
            check_str += indents + 'if self.is_set("{}"):\n'.format(content_name)
            indents += "    "
            check_str += indents + "expected_nb_of_contents += 1\n"
            content_type = _get_sub_types_of_compositional_types(content_type)[0]
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
            check_str += indents
            check_str += "assert "
            for unique_type in unique_standard_types_list:
                check_str += "type(self.{}) == {} or ".format(
                    content_name, self._to_custom_custom(unique_type)
                )
            check_str = check_str[:-4]
            check_str += ", \"Invalid type for content '{}'. Expected either of '{}'. Found '{{}}'.\".format(type(self.{}))\n".format(
                content_name,
                [
                    unique_standard_type
                    for unique_standard_type in unique_standard_types_list
                ],
                content_name,
            )
            if "frozenset" in unique_standard_types_list:
                check_str += indents + "if type(self.{}) == frozenset:\n".format(
                    content_name
                )
                check_str += indents + "    assert (\n"
                frozen_set_element_types = set()
                for element_type in element_types:
                    if element_type.startswith("FrozenSet"):
                        frozen_set_element_types.add(
                            _get_sub_types_of_compositional_types(element_type)[0]
                        )
                for frozen_set_element_type in frozen_set_element_types:
                    check_str += (
                        indents
                        + "        all(type(element) == {} for element in self.{}) or\n".format(
                            self._to_custom_custom(frozen_set_element_type),
                            content_name,
                        )
                    )
                check_str = check_str[:-4]
                check_str += "\n"
                if len(frozen_set_element_types) == 1:
                    check_str += (
                        indents
                        + "    ), \"Invalid type for elements of content '{}'. Expected ".format(
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
                        indents
                        + "    ), \"Invalid type for frozenset elements in content '{}'. Expected either ".format(
                            content_name
                        )
                    )
                    for frozen_set_element_type in frozen_set_element_types:
                        check_str += "'{}' or ".format(
                            self._to_custom_custom(frozen_set_element_type)
                        )
                    check_str = check_str[:-4]
                    check_str += '."\n'
            if "tuple" in unique_standard_types_list:
                check_str += indents + "if type(self.{}) == tuple:\n".format(
                    content_name
                )
                check_str += indents + "    assert (\n"
                tuple_element_types = set()
                for element_type in element_types:
                    if element_type.startswith("Tuple"):
                        tuple_element_types.add(
                            _get_sub_types_of_compositional_types(element_type)[0]
                        )
                for tuple_element_type in tuple_element_types:
                    check_str += (
                        indents
                        + "        all(type(element) == {} for element in self.{}) or \n".format(
                            self._to_custom_custom(tuple_element_type), content_name
                        )
                    )
                check_str = check_str[:-4]
                check_str += "\n"
                if len(tuple_element_types) == 1:
                    check_str += (
                        indents
                        + "    ), \"Invalid type for tuple elements in content '{}'. Expected ".format(
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
                        indents
                        + "    ), \"Invalid type for tuple elements in content '{}'. Expected either ".format(
                            content_name
                        )
                    )
                    for tuple_element_type in tuple_element_types:
                        check_str += "'{}' or ".format(
                            self._to_custom_custom(tuple_element_type)
                        )
                    check_str = check_str[:-4]
                    check_str += '."\n'
            if "dict" in unique_standard_types_list:
                check_str += indents + "if type(self.{}) == dict:\n".format(
                    content_name
                )
                check_str += (
                    indents
                    + "    for key_of_{}, value_of_{} in self.{}.items():\n".format(
                        content_name, content_name, content_name
                    )
                )
                check_str += indents + "        assert (\n"
                dict_key_value_types = dict()
                for element_type in element_types:
                    if element_type.startswith("Dict"):
                        dict_key_value_types[
                            _get_sub_types_of_compositional_types(element_type)[0]
                        ] = _get_sub_types_of_compositional_types(element_type)[1]
                for element1_type, element2_type in dict_key_value_types.items():
                    check_str += (
                        indents
                        + "                (type(key_of_{}) == {} and type(value_of_{}) == {}) or\n".format(
                            content_name,
                            self._to_custom_custom(element1_type),
                            content_name,
                            self._to_custom_custom(element2_type),
                        )
                    )
                check_str = check_str[:-4]
                check_str += "\n"

                if len(dict_key_value_types) == 1:
                    check_str += (
                        indents
                        + "    ), \"Invalid type for dictionary key, value in content '{}'. Expected ".format(
                            content_name
                        )
                    )
                    for key, value in dict_key_value_types.items():
                        check_str += "'{}', '{}'".format(key, value)
                    check_str += '."\n'
                else:
                    check_str += (
                        indents
                        + "    ), \"Invalid type for dictionary key, value in content '{}'. Expected ".format(
                            content_name
                        )
                    )
                    for key, value in dict_key_value_types.items():
                        check_str += "'{}','{}' or ".format(key, value)
                    check_str = check_str[:-4]
                    check_str += '."\n'
        elif content_type.startswith("FrozenSet["):
            # check the type
            check_str += (
                indents
                + "assert type(self.{}) == frozenset, \"Invalid type for content '{}'. Expected 'frozenset'. Found '{{}}'.\".format(type(self.{}))\n".format(
                    content_name, content_name, content_name
                )
            )
            element_type = _get_sub_types_of_compositional_types(content_type)[0]
            check_str += indents + "assert all(\n"
            check_str += (
                indents
                + "    type(element) == {} for element in self.{}\n".format(
                    self._to_custom_custom(element_type), content_name
                )
            )
            check_str += (
                indents
                + "), \"Invalid type for frozenset elements in content '{}'. Expected '{}'.\"\n".format(
                    content_name, element_type
                )
            )
        elif content_type.startswith("Tuple["):
            # check the type
            check_str += (
                indents
                + "assert type(self.{}) == tuple, \"Invalid type for content '{}'. Expected 'tuple'. Found '{{}}'.\".format(type(self.{}))\n".format(
                    content_name, content_name, content_name
                )
            )
            element_type = _get_sub_types_of_compositional_types(content_type)[0]
            check_str += indents + "assert all(\n"
            check_str += (
                indents
                + "    type(element) == {} for element in self.{}\n".format(
                    self._to_custom_custom(element_type), content_name
                )
            )
            check_str += (
                indents
                + "), \"Invalid type for tuple elements in content '{}'. Expected '{}'.\"\n".format(
                    content_name, element_type
                )
            )
        elif content_type.startswith("Dict["):
            # check the type
            check_str += (
                indents
                + "assert type(self.{}) == dict, \"Invalid type for content '{}'. Expected 'dict'. Found '{{}}'.\".format(type(self.{}))\n".format(
                    content_name, content_name, content_name
                )
            )
            element_type_1 = _get_sub_types_of_compositional_types(content_type)[0]
            element_type_2 = _get_sub_types_of_compositional_types(content_type)[1]
            # check the keys type then check the values type
            check_str += (
                indents
                + "for key_of_{}, value_of_{} in self.{}.items():\n".format(
                    content_name, content_name, content_name
                )
            )
            check_str += indents + "    assert (\n"
            check_str += indents + "        type(key_of_{}) == {}\n".format(
                content_name, self._to_custom_custom(element_type_1)
            )
            check_str += (
                indents
                + "    ), \"Invalid type for dictionary keys in content '{}'. Expected '{}'. Found '{{}}'.\".format(type(key_of_{}))\n".format(
                    content_name, element_type_1, content_name
                )
            )

            check_str += indents + "    assert (\n"
            check_str += indents + "        type(value_of_{}) == {}\n".format(
                content_name, self._to_custom_custom(element_type_2)
            )
            check_str += (
                indents
                + "    ), \"Invalid type for dictionary values in content '{}'. Expected '{}'. Found '{{}}'.\".format(type(value_of_{}))\n".format(
                    content_name, element_type_2, content_name
                )
            )
        else:
            check_str += (
                indents
                + "assert type(self.{}) == {}, \"Invalid type for content '{}'. Expected '{}'. Found '{{}}'.\".format(type(self.{}))\n".format(
                    content_name,
                    self._to_custom_custom(content_type),
                    content_name,
                    content_type,
                    content_name,
                )
            )
        return check_str

    def _message_class_str(self) -> str:
        """
        Produce the content of the Message class.

        :return: the message.py file content
        """
        # Header
        cls_str = _copyright_header_str(self.protocol_specification.author) + "\n"

        # Module docstring
        cls_str += str.format(
            '"""This module contains {}\'s message definition."""\n\n'.format(
                self.protocol_specification.name
            )
        )

        # Imports
        cls_str += "from enum import Enum\n"
        cls_str += self._import_from_typing_module() + "\n\n"
        cls_str += "from aea.configurations.base import ProtocolId\n"
        cls_str += MESSAGE_IMPORT + "\n"
        if self._import_from_custom_types_module() == "":
            cls_str += self._import_from_custom_types_module()
        else:
            cls_str += "\n{}\n".format(self._import_from_custom_types_module())
        cls_str += "\nDEFAULT_BODY_SIZE = 4\n"

        # Class Header
        cls_str += str.format(
            "\n\nclass {}Message(Message):\n",
            self.protocol_specification_in_camel_case,
        )
        cls_str += str.format(
            '    """{}"""\n\n', self.protocol_specification.description
        )

        # Class attribute
        cls_str += '    protocol_id = ProtocolId("{}", "{}", "{}")\n'.format(
            self.protocol_specification.author,
            self.protocol_specification.name,
            self.protocol_specification.version,
        )
        for custom_type in self._all_custom_types:
            cls_str += "\n"
            cls_str += "    {} = Custom{}\n".format(custom_type, custom_type)

        # Performatives Enum
        cls_str += "\n{}".format(self._performatives_enum_str())

        # __init__
        cls_str += "    def __init__(\n"
        cls_str += "        self,\n"
        cls_str += "        dialogue_reference: Tuple[str, str],\n"
        cls_str += "        message_id: int,\n"
        cls_str += "        target: int,\n"
        cls_str += "        performative: Performative,\n"
        cls_str += "        **kwargs,\n"
        cls_str += "    ):\n"
        cls_str += '        """\n'
        cls_str += "        Initialise an instance of {}Message.\n\n".format(
            self.protocol_specification_in_camel_case
        )
        cls_str += "        :param message_id: the message id.\n"
        cls_str += "        :param dialogue_reference: the dialogue reference.\n"
        cls_str += "        :param target: the message target.\n"
        cls_str += "        :param performative: the message performative.\n"
        cls_str += '        """\n'
        cls_str += "        super().__init__(\n"
        cls_str += "            dialogue_reference=dialogue_reference,\n"
        cls_str += "            message_id=message_id,\n"
        cls_str += "            target=target,\n"
        cls_str += "            performative={}Message.Performative(performative),\n".format(
            self.protocol_specification_in_camel_case
        )
        cls_str += "            **kwargs,\n"
        cls_str += "        )\n"
        cls_str += "        self._performatives = {}\n".format(
            self._performatives_str()
        )
        cls_str += "        assert (\n"
        cls_str += "            self._is_consistent()\n"
        cls_str += "        ), \"This message is invalid according to the '{}' protocol.\"\n\n".format(
            self.protocol_specification.name
        )

        # Instance properties
        cls_str += "    @property\n"
        cls_str += "    def valid_performatives(self) -> Set[str]:\n"
        cls_str += '        """Get valid performatives."""\n'
        cls_str += "        return self._performatives\n\n"
        cls_str += "    @property\n"
        cls_str += "    def dialogue_reference(self) -> Tuple[str, str]:\n"
        cls_str += '        """Get the dialogue_reference of the message."""\n'
        cls_str += '        assert self.is_set("dialogue_reference"), "dialogue_reference is not set."\n'
        cls_str += (
            '        return cast(Tuple[str, str], self.get("dialogue_reference"))\n\n'
        )
        cls_str += "    @property\n"
        cls_str += "    def message_id(self) -> int:\n"
        cls_str += '        """Get the message_id of the message."""\n'
        cls_str += (
            '        assert self.is_set("message_id"), "message_id is not set."\n'
        )
        cls_str += '        return cast(int, self.get("message_id"))\n\n'
        cls_str += "    @property\n"
        cls_str += "    def performative(self) -> Performative:  # noqa: F821\n"
        cls_str += '        """Get the performative of the message."""\n'
        cls_str += (
            '        assert self.is_set("performative"), "performative is not set."\n'
        )
        cls_str += '        return cast({}Message.Performative, self.get("performative"))\n\n'.format(
            self.protocol_specification_in_camel_case
        )
        cls_str += "    @property\n"
        cls_str += "    def target(self) -> int:\n"
        cls_str += '        """Get the target of the message."""\n'
        cls_str += '        assert self.is_set("target"), "target is not set."\n'
        cls_str += '        return cast(int, self.get("target"))\n\n'
        for content_name in sorted(self._all_unique_contents.keys()):
            content_type = self._all_unique_contents[content_name]
            content_type = self._to_custom_custom(content_type)
            cls_str += "    @property\n"
            cls_str += "    def {}(self) -> {}:\n".format(content_name, content_type)
            cls_str += '        """Get the \'{}\' content from the message."""\n'.format(
                content_name
            )
            cls_str += '        assert self.is_set("{}"), "\'{}\' content is not set."\n'.format(
                content_name, content_name
            )
            cls_str += '        return cast({}, self.get("{}"))\n\n'.format(
                content_type, content_name
            )

        # check_consistency method
        cls_str += "    def _is_consistent(self) -> bool:\n"
        cls_str += str.format(
            '        """Check that the message follows the {} protocol."""\n',
            self.protocol_specification.name,
        )
        cls_str += "        try:\n"

        cls_str += "            assert (\n"
        cls_str += "                type(self.dialogue_reference) == tuple\n"
        cls_str += "            ), \"Invalid type for 'dialogue_reference'. Expected 'tuple'. Found '{}'.\".format(type(self.dialogue_reference))\n"
        cls_str += "            assert (\n"
        cls_str += "                type(self.dialogue_reference[0]) == str\n"
        cls_str += "            ), \"Invalid type for 'dialogue_reference[0]'. Expected 'str'. Found '{}'.\".format(type(self.dialogue_reference[0]))\n"
        cls_str += "            assert (\n"
        cls_str += "                type(self.dialogue_reference[1]) == str\n"
        cls_str += "            ), \"Invalid type for 'dialogue_reference[1]'. Expected 'str'. Found '{}'.\".format(type(self.dialogue_reference[1]))\n"
        cls_str += "            assert type(self.message_id) == int, \"Invalid type for 'message_id'. Expected 'int'. Found '{}'.\".format(type(self.message_id))\n"
        cls_str += "            assert type(self.target) == int, \"Invalid type for 'target'. Expected 'int'. Found '{}'.\".format(type(self.target))\n\n"

        cls_str += "            # Light Protocol Rule 2\n"
        cls_str += "            # Check correct performative\n"
        cls_str += "            assert (\n"
        cls_str += "                type(self.performative) == {}Message.Performative\n".format(
            self.protocol_specification_in_camel_case
        )
        cls_str += "            ), \"Invalid 'performative'. Expected either of '{}'. Found '{}'.\".format(\n"
        cls_str += "                self.valid_performatives, self.performative\n"
        cls_str += "            )\n\n"
        cls_str += "            # Check correct contents\n"
        cls_str += (
            "            actual_nb_of_contents = len(self.body) - DEFAULT_BODY_SIZE\n"
        )
        cls_str += "            expected_nb_of_contents = 0\n"
        counter = 1
        for performative, contents in self._speech_acts.items():
            if counter == 1:
                cls_str += "            if self.performative == {}Message.Performative.{}:\n".format(
                    self.protocol_specification_in_camel_case, performative.upper(),
                )
            else:
                cls_str += "            elif self.performative == {}Message.Performative.{}:\n".format(
                    self.protocol_specification_in_camel_case, performative.upper(),
                )
            nb_of_non_optional_contents = 0
            for content_type in contents.values():
                if not content_type.startswith("Optional"):
                    nb_of_non_optional_contents += 1

            cls_str += "                expected_nb_of_contents = {}\n".format(
                nb_of_non_optional_contents
            )
            if len(contents) == 0:
                continue
            for content_name, content_type in contents.items():
                cls_str += self._check_content_type_str(4, content_name, content_type)
            counter += 1
        cls_str += "\n            # Check correct content count\n"
        cls_str += "            assert (\n"
        cls_str += "                expected_nb_of_contents == actual_nb_of_contents\n"
        cls_str += '            ), "Incorrect number of contents. Expected {}. Found {}".format(\n'
        cls_str += "                expected_nb_of_contents, actual_nb_of_contents\n"
        cls_str += "            )\n\n"

        cls_str += "            # Light Protocol Rule 3\n"
        cls_str += "            if self.message_id == 1:\n"
        cls_str += "                assert (\n"
        cls_str += "                    self.target == 0\n"
        cls_str += "                ), \"Invalid 'target'. Expected 0 (because 'message_id' is 1). Found {}.\".format(\n"
        cls_str += "                    self.target\n"
        cls_str += "                )\n"
        cls_str += "            else:\n"
        cls_str += "                assert (\n"
        cls_str += "                    0 < self.target < self.message_id\n"
        cls_str += "                ), \"Invalid 'target'. Expected an integer between 1 and {} inclusive. Found {}.\".format(\n"
        cls_str += "                    self.message_id-1,\n"
        cls_str += "                    self.target,\n"
        cls_str += "                )\n"
        cls_str += "        except (AssertionError, ValueError, KeyError) as e:\n"
        cls_str += "            print(str(e))\n"
        cls_str += "            return False\n\n"
        cls_str += "        return True\n"

        return cls_str

    def _custom_types_module_str(self) -> str:
        """
        Produces the contents of the custom_types module, containing classes corresponding to every custom type in the protocol specification.

        :return: the custom_types.py file content
        """
        # Header
        cls_str = _copyright_header_str(self.protocol_specification.author) + "\n"

        # Module docstring
        cls_str += str.format(
            '"""This module contains class representations corresponding to every custom type in the protocol specification."""\n'
        )

        if len(self._all_custom_types) == 0:
            return cls_str

        # class code per custom type
        for custom_type in self._all_custom_types:
            cls_str += "\n\nclass {}:\n".format(custom_type)
            cls_str += '    """This class represents an instance of {}."""\n\n'.format(
                custom_type
            )
            cls_str += "    def __init__(self):\n"
            cls_str += '        """Initialise an instance of {}."""\n'.format(
                custom_type
            )
            cls_str += "        raise NotImplementedError\n\n"
            cls_str += "    @classmethod\n"
            cls_str += '    def encode(cls, performative, {}_from_message: "{}"):\n'.format(
                _camel_case_to_snake_case(custom_type), custom_type
            )
            cls_str += '        """\n'
            cls_str += "        Encode an instance of this class into the protocol buffer object.\n\n"
            cls_str += "        The content in the 'performative' argument must be matched with the message content in the '{}_from_message' argument.\n\n".format(
                _camel_case_to_snake_case(custom_type)
            )
            cls_str += "        :param performative: the performative protocol buffer object containing a content whose type is this class.\n"
            cls_str += "        :param {}_from_message: the message content to be encoded in the protocol buffer object.\n".format(
                _camel_case_to_snake_case(custom_type)
            )
            cls_str += "        :return: the 'performative' protocol buffer object encoded with the message content in the '{}_from_message' argument.\n".format(
                _camel_case_to_snake_case(custom_type)
            )
            cls_str += '        """\n'
            cls_str += "        raise NotImplementedError\n\n"

            cls_str += "    @classmethod\n"
            cls_str += '    def decode(cls, {}_from_pb2) -> "{}":\n'.format(
                _camel_case_to_snake_case(custom_type), custom_type,
            )
            cls_str += '        """\n'
            cls_str += "        Decode a protocol buffer object that corresponds with this class into an instance of this class.\n\n"
            cls_str += "        A new instance of this class must be created that matches the content in the '{}_from_pb2' argument.\n\n".format(
                _camel_case_to_snake_case(custom_type)
            )
            cls_str += "        :param {}_from_pb2: the protocol buffer content object whose type corresponds with this class.\n".format(
                _camel_case_to_snake_case(custom_type)
            )
            cls_str += "        :return: A new instance of this class that matches the protocol buffer object in the '{}_from_pb2' argument.\n".format(
                _camel_case_to_snake_case(custom_type)
            )
            cls_str += '        """\n'
            cls_str += "        raise NotImplementedError\n\n"

            cls_str += "    def __eq__(self, other):\n"
            cls_str += "        raise NotImplementedError\n"
        return cls_str

    def _encoding_message_content_from_python_to_protobuf(
        self, content_name: str, content_type: str, no_indents: int
    ) -> str:
        """
        Produce the encoding of message contents for the serialisation class.

        :param content_name: the name of the content to be encoded
        :param content_type: the type of the content to be encoded
        :param no_indents: the number of indents based on the previous sections of the code
        :return: the encoding string
        """
        encoding_str = ""
        indents = _get_indent_str(no_indents)
        if content_type in PYTHON_TYPE_TO_PROTO_TYPE.keys():
            encoding_str += indents + "{} = msg.{}\n".format(content_name, content_name)
            encoding_str += indents + "performative.{} = {}\n".format(
                content_name, content_name
            )
        elif content_type.startswith("FrozenSet") or content_type.startswith("Tuple"):
            encoding_str += indents + "{} = msg.{}\n".format(content_name, content_name)
            encoding_str += indents + "performative.{}.extend({})\n".format(
                content_name, content_name
            )
        elif content_type.startswith("Dict"):
            encoding_str += indents + "{} = msg.{}\n".format(content_name, content_name)
            encoding_str += indents + "performative.{}.update({})\n".format(
                content_name, content_name
            )
        elif content_type.startswith("Union"):
            sub_types = _get_sub_types_of_compositional_types(content_type)
            for sub_type in sub_types:
                sub_type_name_in_protobuf = _union_sub_type_to_protobuf_variable_name(
                    content_name, sub_type
                )
                encoding_str += indents + 'if msg.is_set("{}"):\n'.format(
                    sub_type_name_in_protobuf
                )
                encoding_str += (
                    indents
                    + "    "
                    + "performative.{}_is_set = True\n".format(
                        sub_type_name_in_protobuf
                    )
                )
                encoding_str += self._encoding_message_content_from_python_to_protobuf(
                    sub_type_name_in_protobuf, sub_type, no_indents + 1
                )
        elif content_type.startswith("Optional"):
            sub_type = _get_sub_types_of_compositional_types(content_type)[0]
            if not sub_type.startswith("Union"):
                encoding_str += indents + 'if msg.is_set("{}"):\n'.format(content_name)
                indents = _get_indent_str(no_indents + 1)
                encoding_str += indents + "performative.{}_is_set = True\n".format(
                    content_name
                )
                no_indents += 1
            encoding_str += self._encoding_message_content_from_python_to_protobuf(
                content_name, sub_type, no_indents
            )
        else:
            encoding_str += indents + "{} = msg.{}\n".format(content_name, content_name)
            encoding_str += (
                indents
                + "performative = {}.encode(performative, {})\n".format(
                    content_type, content_name
                )
            )
        return encoding_str

    def _decoding_message_content_from_protobuf_to_python(
        self,
        performative: str,
        content_name: str,
        content_type: str,
        no_indents: int,
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
        indents = _get_indent_str(no_indents)
        variable_name = (
            content_name
            if variable_name_in_protobuf == ""
            else variable_name_in_protobuf
        )
        if content_type in PYTHON_TYPE_TO_PROTO_TYPE.keys():
            decoding_str += indents + "{} = {}_pb.{}.{}\n".format(
                content_name,
                self.protocol_specification.name,
                performative,
                variable_name,
            )
            decoding_str += indents + 'performative_content["{}"] = {}\n'.format(
                content_name, content_name
            )
        elif content_type.startswith("FrozenSet"):
            # if not self._includes_custom_type(content_type):
            decoding_str += indents + "{} = {}_pb.{}.{}\n".format(
                content_name,
                self.protocol_specification.name,
                performative,
                content_name,
            )
            decoding_str += indents + "{}_frozenset = frozenset({})\n".format(
                content_name, content_name
            )
            decoding_str += (
                indents
                + 'performative_content["{}"] = {}_frozenset\n'.format(
                    content_name, content_name
                )
            )
        elif content_type.startswith("Tuple"):
            # if not self._includes_custom_type(content_type):
            decoding_str += indents + "{} = {}_pb.{}.{}\n".format(
                content_name,
                self.protocol_specification.name,
                performative,
                content_name,
            )
            decoding_str += indents + "{}_tuple = tuple({})\n".format(
                content_name, content_name
            )
            decoding_str += indents + 'performative_content["{}"] = {}_tuple\n'.format(
                content_name, content_name
            )
        elif content_type.startswith("Dict"):
            decoding_str += indents + "{} = {}_pb.{}.{}\n".format(
                content_name,
                self.protocol_specification.name,
                performative,
                content_name,
            )
            decoding_str += indents + "{}_dict = dict({})\n".format(
                content_name, content_name
            )
            decoding_str += indents + 'performative_content["{}"] = {}_dict\n'.format(
                content_name, content_name
            )
        elif content_type.startswith("Union"):
            sub_types = _get_sub_types_of_compositional_types(content_type)
            for sub_type in sub_types:
                sub_type_name_in_protobuf = _union_sub_type_to_protobuf_variable_name(
                    content_name, sub_type
                )
                decoding_str += indents + "if {}_pb.{}.{}_is_set:\n".format(
                    self.protocol_specification.name,
                    performative,
                    sub_type_name_in_protobuf,
                )
                decoding_str += self._decoding_message_content_from_protobuf_to_python(
                    performative=performative,
                    content_name=content_name,
                    content_type=sub_type,
                    no_indents=no_indents + 1,
                    variable_name_in_protobuf=sub_type_name_in_protobuf,
                )
        elif content_type.startswith("Optional"):
            sub_type = _get_sub_types_of_compositional_types(content_type)[0]
            if not sub_type.startswith("Union"):
                decoding_str += indents + "if {}_pb.{}.{}_is_set:\n".format(
                    self.protocol_specification.name, performative, content_name
                )
                no_indents += 1
            decoding_str += self._decoding_message_content_from_protobuf_to_python(
                performative, content_name, sub_type, no_indents
            )
        else:
            decoding_str += indents + "pb2_{} = {}_pb.{}.{}\n".format(
                variable_name,
                self.protocol_specification.name,
                performative,
                variable_name,
            )
            decoding_str += indents + "{} = {}.decode(pb2_{})\n".format(
                content_name, content_type, variable_name,
            )
            decoding_str += indents + 'performative_content["{}"] = {}\n'.format(
                content_name, content_name
            )
        return decoding_str

    def _includes_custom_type(self, content_type: str) -> bool:
        """
        Evaluate whether a content type is a custom type or has a custom type as a sub-type.

        :return: Boolean result
        """
        if content_type.startswith("Optional"):
            sub_type = _get_sub_types_of_compositional_types(content_type)[0]
            result = self._includes_custom_type(sub_type)
        elif content_type.startswith("Union"):
            sub_types = _get_sub_types_of_compositional_types(content_type)
            result = False
            for sub_type in sub_types:
                if self._includes_custom_type(sub_type):
                    result = True
                    break
        elif content_type.startswith("Dict"):
            sub_type_1 = _get_sub_types_of_compositional_types(content_type)[0]
            sub_type_2 = _get_sub_types_of_compositional_types(content_type)[1]
            result = self._includes_custom_type(
                sub_type_1
            ) or self._includes_custom_type(sub_type_2)
        elif content_type.startswith("FrozenSet") or content_type.startswith("Tuple"):
            sub_type = _get_sub_types_of_compositional_types(content_type)[0]
            result = self._includes_custom_type(sub_type)
        elif content_type in PYTHON_TYPE_TO_PROTO_TYPE.keys():
            result = False
        else:
            result = True
        return result

    def _to_custom_custom(self, content_type: str) -> str:
        """
        Evaluate whether a content type is a custom type or has a custom type as a sub-type.

        :return: Boolean result
        """
        new_content_type = content_type
        if self._includes_custom_type(content_type):
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
        # Header
        cls_str = _copyright_header_str(self.protocol_specification.author) + "\n"

        # Module docstring
        cls_str += '"""Serialization module for {} protocol."""\n\n'.format(
            self.protocol_specification.name
        )

        # Imports
        cls_str += "from typing import cast\n\n"
        cls_str += MESSAGE_IMPORT + "\n"
        cls_str += SERIALIZER_IMPORT + "\n\n"
        cls_str += str.format(
            "from {}.{}.{}.{} import (\n    {}_pb2,\n)\n",
            PATH_TO_PACKAGES,
            self.protocol_specification.author,
            "protocols",
            self.protocol_specification.name,
            self.protocol_specification.name,
        )
        for custom_type in self._all_custom_types:
            cls_str += str.format(
                "from {}.{}.{}.{}.custom_types import (\n    {},\n)\n",
                PATH_TO_PACKAGES,
                self.protocol_specification.author,
                "protocols",
                self.protocol_specification.name,
                custom_type,
            )
        cls_str += str.format(
            "from {}.{}.{}.{}.message import (\n    {}Message,\n)\n",
            PATH_TO_PACKAGES,
            self.protocol_specification.author,
            "protocols",
            self.protocol_specification.name,
            self.protocol_specification_in_camel_case,
        )

        # Class Header
        cls_str += "\n\nclass {}Serializer(Serializer):\n".format(
            self.protocol_specification_in_camel_case,
        )
        cls_str += str.format(
            '    """Serialization for the \'{}\' protocol."""\n\n',
            self.protocol_specification.name,
        )

        # encoder
        cls_str += str.format("    def encode(self, msg: Message) -> bytes:\n")
        cls_str += '        """\n'
        cls_str += "        Encode a '{}' message into bytes.\n\n".format(
            self.protocol_specification_in_camel_case,
        )
        cls_str += "        :param msg: the message object.\n"
        cls_str += "        :return: the bytes.\n"
        cls_str += '        """\n'
        cls_str += "        msg = cast({}Message, msg)\n".format(
            self.protocol_specification_in_camel_case
        )
        cls_str += "        {}_msg = {}_pb2.{}Message()\n".format(
            self.protocol_specification.name,
            self.protocol_specification.name,
            self.protocol_specification_in_camel_case,
        )
        cls_str += "        {}_msg.message_id = msg.message_id\n".format(
            self.protocol_specification.name
        )
        cls_str += "        dialogue_reference = msg.dialogue_reference\n"
        cls_str += "        {}_msg.dialogue_starter_reference = dialogue_reference[0]\n".format(
            self.protocol_specification.name
        )
        cls_str += "        {}_msg.dialogue_responder_reference = dialogue_reference[1]\n".format(
            self.protocol_specification.name
        )
        cls_str += "        {}_msg.target = msg.target\n\n".format(
            self.protocol_specification.name
        )
        cls_str += "        performative_id = msg.performative\n"
        indents = _get_indent_str(3)
        counter = 1
        for performative, contents in self._speech_acts.items():
            if counter == 1:
                cls_str += "        if performative_id == {}Message.Performative.{}:\n".format(
                    self.protocol_specification_in_camel_case, performative.upper()
                )
            else:
                cls_str += "        elif performative_id == {}Message.Performative.{}:\n".format(
                    self.protocol_specification_in_camel_case, performative.upper()
                )
            cls_str += "            performative = {}_pb2.{}Message.{}()  # type: ignore\n".format(
                self.protocol_specification.name,
                self.protocol_specification_in_camel_case,
                performative.title(),
            )
            for content_name, content_type in contents.items():
                cls_str += self._encoding_message_content_from_python_to_protobuf(
                    content_name, content_type, 3
                )
            cls_str += indents + "{}_msg.{}.CopyFrom(performative)\n".format(
                self.protocol_specification.name, performative
            )

            counter += 1
        indents = _get_indent_str(2)
        cls_str += indents + "else:\n"
        indents = _get_indent_str(3)
        cls_str += (
            indents
            + 'raise ValueError("Performative not valid: {}".format(performative_id))\n\n'
        )

        cls_str += "        {}_bytes = {}_msg.SerializeToString()\n".format(
            self.protocol_specification.name, self.protocol_specification.name
        )
        cls_str += "        return {}_bytes\n\n".format(
            self.protocol_specification.name
        )

        # decoder
        cls_str += str.format("    def decode(self, obj: bytes) -> Message:\n")
        cls_str += '        """\n'
        cls_str += "        Decode bytes into a '{}' message.\n\n".format(
            self.protocol_specification_in_camel_case,
        )
        cls_str += "        :param obj: the bytes object.\n"
        cls_str += "        :return: the '{}' message.\n".format(
            self.protocol_specification_in_camel_case
        )
        cls_str += '        """\n'
        cls_str += "        {}_pb = {}_pb2.{}Message()\n".format(
            self.protocol_specification.name,
            self.protocol_specification.name,
            self.protocol_specification_in_camel_case,
        )
        cls_str += "        {}_pb.ParseFromString(obj)\n".format(
            self.protocol_specification.name
        )
        cls_str += "        message_id = {}_pb.message_id\n".format(
            self.protocol_specification.name
        )
        cls_str += "        dialogue_reference = (\n"
        cls_str += "            {}_pb.dialogue_starter_reference,\n".format(
            self.protocol_specification.name
        )
        cls_str += "            {}_pb.dialogue_responder_reference,\n".format(
            self.protocol_specification.name
        )
        cls_str += "        )\n"
        cls_str += "        target = {}_pb.target\n\n".format(
            self.protocol_specification.name
        )
        cls_str += '        performative = {}_pb.WhichOneof("performative")\n'.format(
            self.protocol_specification.name
        )
        cls_str += "        performative_id = {}Message.Performative(str(performative))\n".format(
            self.protocol_specification_in_camel_case
        )
        cls_str += "        performative_content = dict()\n"
        counter = 1
        for performative, contents in self._speech_acts.items():
            if counter == 1:
                cls_str += "        if performative_id == {}Message.Performative.{}:\n".format(
                    self.protocol_specification_in_camel_case, performative.upper()
                )
            else:
                cls_str += "        elif performative_id == {}Message.Performative.{}:\n".format(
                    self.protocol_specification_in_camel_case, performative.upper()
                )
            if len(contents.keys()) == 0:
                indents = _get_indent_str(3)
                cls_str += indents + "pass\n"
            else:
                for content_name, content_type in contents.items():
                    cls_str += self._decoding_message_content_from_protobuf_to_python(
                        performative, content_name, content_type, 3
                    )
            counter += 1
        indents = _get_indent_str(2)
        cls_str += indents + "else:\n"
        indents = _get_indent_str(3)
        cls_str += (
            indents
            + 'raise ValueError("Performative not valid: {}.".format(performative_id))\n\n'
        )

        cls_str += str.format(
            "        return {}Message(\n", self.protocol_specification_in_camel_case,
        )
        cls_str += "            message_id=message_id,\n"
        cls_str += "            dialogue_reference=dialogue_reference,\n"
        cls_str += "            target=target,\n"
        cls_str += "            performative=performative,\n"
        cls_str += "            **performative_content\n"
        cls_str += "        )\n"

        return cls_str

    def _content_to_proto_field_str(
        self, content_name: str, content_type: str, tag_no: int, no_of_indents: int,
    ) -> Tuple[str, int]:
        """
        Convert a message content to its representation in a protocol buffer schema.

        :param content_name: the name of the content
        :param content_type: the type of the content
        :param content_type: the tag number
        :param no_of_indents: the number of indents based on the previous sections of the code
        :return: the content in protocol buffer schema
        """
        indents = _get_indent_str(no_of_indents)
        entry = ""

        if content_type.startswith("FrozenSet") or content_type.startswith(
            "Tuple"
        ):  # it is a <PCT>
            element_type = _get_sub_types_of_compositional_types(content_type)[0]
            proto_type = _python_pt_or_ct_type_to_proto_type(element_type)
            entry = indents + "repeated {} {} = {};\n".format(
                proto_type, content_name, tag_no
            )
            tag_no += 1
        elif content_type.startswith("Dict"):  # it is a <PMT>
            key_type = _get_sub_types_of_compositional_types(content_type)[0]
            value_type = _get_sub_types_of_compositional_types(content_type)[1]
            proto_key_type = _python_pt_or_ct_type_to_proto_type(key_type)
            proto_value_type = _python_pt_or_ct_type_to_proto_type(value_type)
            entry = indents + "map<{}, {}> {} = {};\n".format(
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
                    sub_type_name, sub_type, tag_no, no_of_indents
                )
                entry += content_to_proto_field_str
        elif content_type.startswith("Optional"):  # it is an <O>
            sub_type = _get_sub_types_of_compositional_types(content_type)[0]
            content_to_proto_field_str, tag_no = self._content_to_proto_field_str(
                content_name, sub_type, tag_no, no_of_indents
            )
            entry = content_to_proto_field_str
            entry += indents + "bool {}_is_set = {};\n".format(content_name, tag_no)
            tag_no += 1
        else:  # it is a <CT> or <PT>
            proto_type = _python_pt_or_ct_type_to_proto_type(content_type)
            entry = indents + "{} {} = {};\n".format(proto_type, content_name, tag_no)
            tag_no += 1
        return entry, tag_no

    def _protocol_buffer_schema_str(self) -> str:
        """
        Produce the content of the Protocol Buffers schema.

        :return: the protocol buffers schema content
        """
        indents = _get_indent_str(0)

        # heading
        proto_buff_schema_str = ""
        proto_buff_schema_str += indents + 'syntax = "proto3";\n\n'
        proto_buff_schema_str += indents + "package fetch.aea.{};\n\n".format(
            self.protocol_specification_in_camel_case
        )
        proto_buff_schema_str += indents + "message {}Message{{\n\n".format(
            self.protocol_specification_in_camel_case
        )

        # custom types
        indents = _get_indent_str(1)
        if (len(self._all_custom_types) != 0) and (
            self.protocol_specification.protobuf_snippets is not None
        ):
            proto_buff_schema_str += indents + "// Custom Types\n"
            for custom_type in self._all_custom_types:
                proto_buff_schema_str += indents + "message {}{{\n".format(custom_type)
                indents = _get_indent_str(2)

                # formatting and adding the custom type protobuf entry
                specification_custom_type = "ct:" + custom_type
                proto_part = self.protocol_specification.protobuf_snippets[
                    specification_custom_type
                ]
                number_of_new_lines = proto_part.count("\n")
                if number_of_new_lines != 0:
                    formatted_proto_part = proto_part.replace(
                        "\n", "\n" + indents, number_of_new_lines - 1
                    )
                else:
                    formatted_proto_part = proto_part
                proto_buff_schema_str += indents + formatted_proto_part

                indents = _get_indent_str(1)
                proto_buff_schema_str += indents + "}\n\n"
            proto_buff_schema_str += "\n"

        # performatives
        proto_buff_schema_str += indents + "// Performatives and contents\n"
        for performative, contents in self._speech_acts.items():
            proto_buff_schema_str += indents + "message {}{{".format(
                performative.title()
            )
            tag_no = 1
            if len(contents.keys()) == 0:
                proto_buff_schema_str += "}\n\n"
            else:
                proto_buff_schema_str += "\n"
                for content_name, content_type in contents.items():
                    (
                        content_to_proto_field_str,
                        tag_no,
                    ) = self._content_to_proto_field_str(
                        content_name, content_type, tag_no, 2
                    )
                    proto_buff_schema_str += content_to_proto_field_str
                proto_buff_schema_str += indents + "}\n\n"
        proto_buff_schema_str += "\n"

        # meta-data
        proto_buff_schema_str += indents + "// Standard {}Message fields\n".format(
            self.protocol_specification_in_camel_case
        )
        proto_buff_schema_str += indents + "int32 message_id = 1;\n"
        proto_buff_schema_str += indents + "string dialogue_starter_reference = 2;\n"
        proto_buff_schema_str += indents + "string dialogue_responder_reference = 3;\n"
        proto_buff_schema_str += indents + "int32 target = 4;\n"
        proto_buff_schema_str += indents + "oneof performative{\n"
        indents = _get_indent_str(2)
        tag_no = 5
        for performative in self._all_performatives:
            proto_buff_schema_str += indents + "{} {} = {};\n".format(
                performative.title(), performative, tag_no
            )
            tag_no += 1
        indents = _get_indent_str(1)
        proto_buff_schema_str += indents + "}\n"

        indents = _get_indent_str(0)
        proto_buff_schema_str += indents + "}\n"
        return proto_buff_schema_str

    def _protocol_yaml_str(self) -> str:
        """
        Produce the content of the protocol.yaml file.

        :return: the protocol.yaml content
        """
        protocol_yaml_str = "name: {}\n".format(self.protocol_specification.name)
        protocol_yaml_str += "author: {}\n".format(self.protocol_specification.author)
        protocol_yaml_str += "version: {}\n".format(self.protocol_specification.version)
        protocol_yaml_str += "license: {}\n".format(self.protocol_specification.license)
        protocol_yaml_str += "aea_version: '{}'\n".format(
            self.protocol_specification.aea_version
        )
        protocol_yaml_str += "fingerprint: {}\n"
        protocol_yaml_str += "dependencies: \n"
        protocol_yaml_str += "    protobuf: {} \n"
        protocol_yaml_str += "description: {}\n".format(
            self.protocol_specification.description
        )

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
        if len(self._all_custom_types) > 0:
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
        if len(self._all_custom_types) != 0:
            incomplete_generation_warning_msg = "The generated protocol is incomplete, because the protocol specification contains the following custom types: {}\n".format(
                self._all_custom_types
            )
            incomplete_generation_warning_msg += "Update the generated '{}' file with the appropriate implementations of these custom types.".format(
                CUSTOM_TYPES_DOT_PY_FILE_NAME
            )
            print(incomplete_generation_warning_msg)

        # Compile protobuf schema
        cmd = "protoc --python_out=. protocols/{}/{}.proto".format(
            self.protocol_specification.name, self.protocol_specification.name,
        )
        os.system(cmd)  # nosec
