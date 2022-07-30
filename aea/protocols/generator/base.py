# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
import os
import shutil

# pylint: skip-file
from datetime import date
from pathlib import Path
from typing import Optional, Tuple

# pylint: skip-file
from aea.configurations.base import ProtocolSpecificationParseError
from aea.configurations.constants import (
    PROTOCOL_LANGUAGE_PYTHON,
    SUPPORTED_PROTOCOL_LANGUAGES,
)
from aea.configurations.data_types import PublicId
from aea.protocols import PROTOCOL_GENERATOR_VERSION
from aea.protocols.generator.common import (
    CUSTOM_TYPES_DOT_PY_FILE_NAME,
    DIALOGUE_DOT_PY_FILE_NAME,
    INIT_FILE_NAME,
    MESSAGE_DOT_PY_FILE_NAME,
    MESSAGE_IMPORT,
    PATH_TO_PACKAGES,
    PROTOCOL_YAML_FILE_NAME,
    PYTHON_TYPE_TO_PROTO_TYPE,
    SERIALIZATION_DOT_PY_FILE_NAME,
    SERIALIZER_IMPORT,
    _camel_case_to_snake_case,
    _create_protocol_file,
    _get_sub_types_of_compositional_types,
    _includes_custom_type,
    _python_pt_or_ct_type_to_proto_type,
    _to_camel_case,
    _union_sub_type_to_protobuf_variable_name,
    apply_protolint,
    check_prerequisites,
    compile_protobuf_using_protoc,
    get_protoc_version,
    load_protocol_specification,
    try_run_black_formatting,
    try_run_isort_formatting,
)
from aea.protocols.generator.extract_specification import extract
from aea.protocols.generator.validate import validate


PYLINT_DISABLE_SERIALIZATION_PY = [
    "too-many-statements",
    "too-many-locals",
    "no-member",
    "too-few-public-methods",
    "redefined-builtin",
]
PYLINT_DISABLE_MESSAGE_PY = [
    "too-many-statements",
    "too-many-locals",
    "no-member",
    "too-few-public-methods",
    "too-many-branches",
    "not-an-iterable",
    "unidiomatic-typecheck",
    "unsubscriptable-object",
]


def _type_check(variable_name: str, variable_type: str) -> str:
    """
    Return the type check Python instruction.

    If variable_type == int:

        type(variable_name) == int

    else:

        isinstance(variable_name, variable_type)

    :param variable_name: the variable name.
    :param variable_type: the variable type.
    :return: the Python instruction to check the type, in string form.
    """
    if variable_type != "int":
        return f"isinstance({variable_name}, {variable_type})"
    else:
        return f"type({variable_name}) is {variable_type}"


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


class ProtocolGenerator:
    """This class generates a protocol_verification package from a ProtocolTemplate object."""

    def __init__(
        self,
        path_to_protocol_specification: str,
        output_path: str = ".",
        dotted_path_to_protocol_package: Optional[str] = None,
    ) -> None:
        """
        Instantiate a protocol generator.

        :param path_to_protocol_specification: path to protocol specification file
        :param output_path: the path to the location in which the protocol module is to be generated.
        :param dotted_path_to_protocol_package: the path to the protocol package

        :raises FileNotFoundError if any prerequisite application is not installed
        :raises yaml.YAMLError if yaml parser encounters an error condition
        :raises ProtocolSpecificationParseError if specification fails generator's validation
        """
        # Check the prerequisite applications are installed
        try:
            check_prerequisites()
        except FileNotFoundError:
            raise

        self.protoc_version = get_protoc_version()

        # Load protocol specification yaml file
        self.protocol_specification = load_protocol_specification(
            path_to_protocol_specification
        )

        # Validate the specification
        result_bool, result_msg = validate(self.protocol_specification)
        if not result_bool:
            raise ProtocolSpecificationParseError(result_msg)

        # Extract specification fields
        self.spec = extract(self.protocol_specification)

        # Helper fields
        self.path_to_protocol_specification = path_to_protocol_specification
        self.protocol_specification_in_camel_case = _to_camel_case(
            self.protocol_specification.name
        )
        self.path_to_generated_protocol_package = os.path.join(
            output_path, self.protocol_specification.name
        )
        self.dotted_path_to_protocol_package = (
            dotted_path_to_protocol_package + self.protocol_specification.name
            if dotted_path_to_protocol_package is not None
            else "{}.{}.protocols.{}".format(
                PATH_TO_PACKAGES,
                self.protocol_specification.author,
                self.protocol_specification.name,
            )
        )
        self.indent = ""

    def _change_indent(self, number: int, mode: str = None) -> None:
        """
        Update the value of 'indent' global variable.

        This function controls the indentation of the code produced throughout the generator.

        There are two modes:
        - Setting the indent to a desired 'number' level. In this case, 'mode' has to be set to "s".
        - Updating the incrementing/decrementing the indentation level by 'number' amounts. In this case 'mode' is None.

        :param number: the number of indentation levels to set/increment/decrement
        :param mode: the mode of indentation change
        """
        if mode and mode == "s":
            if number >= 0:
                self.indent = number * "    "
            else:
                raise ValueError("Error: setting indent to be a negative number.")
        else:
            if number >= 0:
                for _ in itertools.repeat(None, number):
                    self.indent += "    "
            else:
                if abs(number) <= len(self.indent) / 4:
                    self.indent = self.indent[abs(number) * 4 :]
                else:
                    raise ValueError(
                        "Not enough spaces in the 'indent' variable to remove."
                    )

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
        import_str = "from typing import Any, "
        for package in ordered_packages:
            if self.spec.typing_imports[package]:
                import_str += "{}, ".format(package)
        import_str = import_str[:-2]
        return import_str

    def _import_from_custom_types_module(self) -> str:
        """
        Manage import statement from custom_types module.

        :return: import statement for the custom_types module
        """
        import_str = ""
        if len(self.spec.all_custom_types) == 0:
            pass
        else:
            for custom_class in self.spec.all_custom_types:
                import_str += "from {}.custom_types import {} as Custom{}\n".format(
                    self.dotted_path_to_protocol_package,
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
        for performative in self.spec.all_performatives:
            performatives_str += '"{}", '.format(performative)
        performatives_str = performatives_str[:-2]
        performatives_str += "}"
        return performatives_str

    def _performatives_enum_str(self) -> str:
        """
        Generate the performatives Enum class.

        :return: the performatives Enum string
        """
        enum_str = self.indent + "class Performative(Message.Performative):\n"
        self._change_indent(1)
        enum_str += self.indent + '"""Performatives for the {} protocol."""\n\n'.format(
            self.protocol_specification.name
        )
        for performative in self.spec.all_performatives:
            enum_str += self.indent + '{} = "{}"\n'.format(
                performative.upper(), performative
            )
        enum_str += "\n"
        enum_str += self.indent + "def __str__(self) -> str:\n"
        self._change_indent(1)
        enum_str += self.indent + '"""Get the string representation."""\n'
        enum_str += self.indent + "return str(self.value)\n"
        self._change_indent(-1)
        enum_str += "\n"
        self._change_indent(-1)

        return enum_str

    def _to_custom_custom(self, content_type: str) -> str:
        """
        Evaluate whether a content type is a custom type or has a custom type as a sub-type.

        :param content_type: the content type.
        :return: Boolean result
        """
        new_content_type = content_type
        if _includes_custom_type(content_type):
            for custom_type in self.spec.all_custom_types:
                new_content_type = new_content_type.replace(
                    custom_type, self.spec.custom_custom_types[custom_type]
                )
        return new_content_type

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
            check_str += self.indent + 'if self.is_set("{}"):\n'.format(content_name)
            self._change_indent(1)
            check_str += self.indent + "expected_nb_of_contents += 1\n"
            content_type = _get_sub_types_of_compositional_types(content_type)[0]
            check_str += self.indent + "{} = cast({}, self.{})\n".format(
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
            check_str += self.indent
            check_str += "enforce("
            for unique_type in unique_standard_types_list:
                check_str += "{} or ".format(
                    _type_check(content_variable, self._to_custom_custom(unique_type))
                )
            check_str = check_str[:-4]
            check_str += ", \"Invalid type for content '{}'. Expected either of '{}'. Found '{{}}'.\".format(type({})))\n".format(
                content_name,
                [
                    unique_standard_type
                    for unique_standard_type in unique_standard_types_list
                ],
                content_variable,
            )
            if "frozenset" in unique_standard_types_list:
                check_str += self.indent + "if isinstance({}, frozenset):\n".format(
                    content_variable
                )
                self._change_indent(1)
                check_str += self.indent + "enforce(\n"
                self._change_indent(1)
                frozen_set_element_types_set = set()
                for element_type in element_types:
                    if element_type.startswith("FrozenSet"):
                        frozen_set_element_types_set.add(
                            _get_sub_types_of_compositional_types(element_type)[0]
                        )
                frozen_set_element_types = sorted(frozen_set_element_types_set)
                for frozen_set_element_type in frozen_set_element_types:
                    check_str += self.indent + "all({} for element in {}) or\n".format(
                        _type_check(
                            "element", self._to_custom_custom(frozen_set_element_type)
                        ),
                        content_variable,
                    )
                check_str = check_str[:-4]
                check_str += "\n"
                self._change_indent(-1)
                if len(frozen_set_element_types) == 1:
                    check_str += (
                        self.indent
                        + ", \"Invalid type for elements of content '{}'. Expected ".format(
                            content_name
                        )
                    )
                    for frozen_set_element_type in frozen_set_element_types:
                        check_str += "'{}'".format(
                            self._to_custom_custom(frozen_set_element_type)
                        )
                    check_str += '.")\n'
                else:
                    check_str += (
                        self.indent
                        + ", \"Invalid type for frozenset elements in content '{}'. Expected either ".format(
                            content_name
                        )
                    )
                    for frozen_set_element_type in frozen_set_element_types:
                        check_str += "'{}' or ".format(
                            self._to_custom_custom(frozen_set_element_type)
                        )
                    check_str = check_str[:-4]
                    check_str += '.")\n'
                self._change_indent(-1)
            if "tuple" in unique_standard_types_list:
                check_str += self.indent + "if isinstance({}, tuple):\n".format(
                    content_variable
                )
                self._change_indent(1)
                check_str += self.indent + "enforce(\n"
                self._change_indent(1)
                tuple_element_types_set = set()
                for element_type in element_types:
                    if element_type.startswith("Tuple"):
                        tuple_element_types_set.add(
                            _get_sub_types_of_compositional_types(element_type)[0]
                        )
                tuple_element_types = sorted(tuple_element_types_set)
                for tuple_element_type in tuple_element_types:
                    check_str += self.indent + "all({} for element in {}) or \n".format(
                        _type_check(
                            "element", self._to_custom_custom(tuple_element_type)
                        ),
                        content_variable,
                    )
                check_str = check_str[:-4]
                check_str += "\n"
                self._change_indent(-1)
                if len(tuple_element_types) == 1:
                    check_str += (
                        self.indent
                        + ", \"Invalid type for tuple elements in content '{}'. Expected ".format(
                            content_name
                        )
                    )
                    for tuple_element_type in tuple_element_types:
                        check_str += "'{}'".format(
                            self._to_custom_custom(tuple_element_type)
                        )
                    check_str += '.")\n'
                else:
                    check_str += (
                        self.indent
                        + ", \"Invalid type for tuple elements in content '{}'. Expected either ".format(
                            content_name
                        )
                    )
                    for tuple_element_type in tuple_element_types:
                        check_str += "'{}' or ".format(
                            self._to_custom_custom(tuple_element_type)
                        )
                    check_str = check_str[:-4]
                    check_str += '.")\n'
                self._change_indent(-1)
            if "dict" in unique_standard_types_list:
                check_str += self.indent + "if isinstance({}, dict):\n".format(
                    content_variable
                )
                self._change_indent(1)
                check_str += (
                    self.indent
                    + "for key_of_{}, value_of_{} in {}.items():\n".format(
                        content_name, content_name, content_variable
                    )
                )
                self._change_indent(1)
                check_str += self.indent + "enforce(\n"
                self._change_indent(1)
                dict_key_value_types = dict()
                for element_type in element_types:
                    if element_type.startswith("Dict"):
                        dict_key_value_types[
                            _get_sub_types_of_compositional_types(element_type)[0]
                        ] = _get_sub_types_of_compositional_types(element_type)[1]
                for element1_type in sorted(dict_key_value_types.keys()):
                    check_str += self.indent + "({} and {}) or\n".format(
                        _type_check(
                            "key_of_" + content_name,
                            self._to_custom_custom(element1_type),
                        ),
                        _type_check(
                            "value_of_" + content_name,
                            self._to_custom_custom(dict_key_value_types[element1_type]),
                        ),
                    )
                check_str = check_str[:-4]
                check_str += "\n"
                self._change_indent(-1)

                if len(dict_key_value_types) == 1:
                    check_str += (
                        self.indent
                        + ", \"Invalid type for dictionary key, value in content '{}'. Expected ".format(
                            content_name
                        )
                    )
                    for key in sorted(dict_key_value_types.keys()):
                        check_str += "'{}', '{}'".format(key, dict_key_value_types[key])
                    check_str += '.")\n'
                else:
                    check_str += (
                        self.indent
                        + ", \"Invalid type for dictionary key, value in content '{}'. Expected ".format(
                            content_name
                        )
                    )
                    for key in sorted(dict_key_value_types.keys()):
                        check_str += "'{}','{}' or ".format(
                            key, dict_key_value_types[key]
                        )
                    check_str = check_str[:-4]
                    check_str += '.")\n'
                self._change_indent(-2)
        elif content_type.startswith("FrozenSet["):
            # check the type
            check_str += (
                self.indent
                + "enforce(isinstance({}, frozenset), \"Invalid type for content '{}'. Expected 'frozenset'. Found '{{}}'.\".format(type({})))\n".format(
                    content_variable, content_name, content_variable
                )
            )
            element_type = _get_sub_types_of_compositional_types(content_type)[0]
            check_str += self.indent + "enforce(all(\n"
            self._change_indent(1)
            check_str += self.indent + "{} for element in {}\n".format(
                _type_check("element", self._to_custom_custom(element_type)),
                content_variable,
            )
            self._change_indent(-1)
            check_str += (
                self.indent
                + "), \"Invalid type for frozenset elements in content '{}'. Expected '{}'.\")\n".format(
                    content_name, element_type
                )
            )
        elif content_type.startswith("Tuple["):
            # check the type
            check_str += (
                self.indent
                + "enforce(isinstance({}, tuple), \"Invalid type for content '{}'. Expected 'tuple'. Found '{{}}'.\".format(type({})))\n".format(
                    content_variable, content_name, content_variable
                )
            )
            element_type = _get_sub_types_of_compositional_types(content_type)[0]
            check_str += self.indent + "enforce(all(\n"
            self._change_indent(1)
            check_str += self.indent + "{} for element in {}\n".format(
                _type_check("element", self._to_custom_custom(element_type)),
                content_variable,
            )
            self._change_indent(-1)
            check_str += (
                self.indent
                + "), \"Invalid type for tuple elements in content '{}'. Expected '{}'.\")\n".format(
                    content_name, element_type
                )
            )
        elif content_type.startswith("Dict["):
            # check the type
            check_str += (
                self.indent
                + "enforce(isinstance({}, dict), \"Invalid type for content '{}'. Expected 'dict'. Found '{{}}'.\".format(type({})))\n".format(
                    content_variable, content_name, content_variable
                )
            )
            element_type_1 = _get_sub_types_of_compositional_types(content_type)[0]
            element_type_2 = _get_sub_types_of_compositional_types(content_type)[1]
            # check the keys type then check the values type
            check_str += (
                self.indent
                + "for key_of_{}, value_of_{} in {}.items():\n".format(
                    content_name, content_name, content_variable
                )
            )
            self._change_indent(1)
            check_str += self.indent + "enforce(\n"
            self._change_indent(1)
            check_str += self.indent + "{}\n".format(
                _type_check(
                    "key_of_" + content_name, self._to_custom_custom(element_type_1)
                )
            )
            self._change_indent(-1)
            check_str += (
                self.indent
                + ", \"Invalid type for dictionary keys in content '{}'. Expected '{}'. Found '{{}}'.\".format(type(key_of_{})))\n".format(
                    content_name, element_type_1, content_name
                )
            )

            check_str += self.indent + "enforce(\n"
            self._change_indent(1)
            check_str += self.indent + "{}\n".format(
                _type_check(
                    "value_of_" + content_name, self._to_custom_custom(element_type_2)
                )
            )
            self._change_indent(-1)
            check_str += (
                self.indent
                + ", \"Invalid type for dictionary values in content '{}'. Expected '{}'. Found '{{}}'.\".format(type(value_of_{})))\n".format(
                    content_name, element_type_2, content_name
                )
            )
            self._change_indent(-1)
        else:
            check_str += (
                self.indent
                + "enforce({}, \"Invalid type for content '{}'. Expected '{}'. Found '{{}}'.\".format(type({})))\n".format(
                    _type_check(content_variable, self._to_custom_custom(content_type)),
                    content_name,
                    content_type,
                    content_variable,
                )
            )
        if optional:
            self._change_indent(-1)
        return check_str

    def _message_class_str(self) -> str:
        """
        Produce the content of the Message class.

        :return: the message.py file content
        """
        self._change_indent(0, "s")

        # Header
        cls_str = _copyright_header_str(self.protocol_specification.author) + "\n"

        # Module docstring
        cls_str += (
            self.indent
            + '"""This module contains {}\'s message definition."""\n\n'.format(
                self.protocol_specification.name
            )
        )

        cls_str += f"# pylint: disable={','.join(PYLINT_DISABLE_MESSAGE_PY)}\n"

        # Imports
        cls_str += self.indent + "import logging\n"
        cls_str += self._import_from_typing_module() + "\n\n"
        cls_str += self.indent + "from aea.configurations.base import PublicId\n"
        cls_str += self.indent + "from aea.exceptions import AEAEnforceError, enforce\n"
        cls_str += MESSAGE_IMPORT + "\n"
        if self._import_from_custom_types_module() != "":
            cls_str += "\n" + self._import_from_custom_types_module() + "\n"
        else:
            cls_str += self._import_from_custom_types_module()
        cls_str += (
            self.indent
            + '\n_default_logger = logging.getLogger("aea.packages.{}.protocols.{}.message")\n'.format(
                self.protocol_specification.author, self.protocol_specification.name
            )
        )
        cls_str += self.indent + "\nDEFAULT_BODY_SIZE = 4\n"

        # Class Header
        cls_str += self.indent + "\n\nclass {}Message(Message):\n".format(
            self.protocol_specification_in_camel_case
        )
        self._change_indent(1)
        cls_str += self.indent + '"""{}"""\n\n'.format(
            self.protocol_specification.description
        )

        # Class attributes
        cls_str += self.indent + 'protocol_id = PublicId.from_str("{}/{}:{}")\n'.format(
            self.protocol_specification.author,
            self.protocol_specification.name,
            self.protocol_specification.version,
        )

        cls_str += (
            self.indent
            + 'protocol_specification_id = PublicId.from_str("{}/{}:{}")\n'.format(
                self.protocol_specification.protocol_specification_id.author,
                self.protocol_specification.protocol_specification_id.name,
                self.protocol_specification.protocol_specification_id.version,
            )
        )

        for custom_type in self.spec.all_custom_types:
            cls_str += "\n"
            cls_str += self.indent + "{} = Custom{}\n".format(custom_type, custom_type)

        # Performatives Enum
        cls_str += "\n" + self._performatives_enum_str()
        cls_str += self.indent + "_performatives = {}\n".format(
            self._performatives_str()
        )

        # slots
        cls_str += self.indent + "__slots__: Tuple[str, ...] = tuple()\n"

        cls_str += self.indent + "class _SlotsCls():\n"
        self._change_indent(1)
        cls_str += self.indent + "__slots__ = (\n"
        self._change_indent(1)
        # default fields
        default_slots = ["performative", "dialogue_reference", "message_id", "target"]
        slots = list(self.spec.all_unique_contents.keys()) + default_slots
        for field_name in sorted(slots):
            cls_str += self.indent + f'"{field_name}",'
        self._change_indent(-1)
        cls_str += self.indent + ")\n"
        self._change_indent(-1)

        # __init__
        cls_str += self.indent + "def __init__(\n"
        self._change_indent(1)
        cls_str += self.indent + "self,\n"
        cls_str += self.indent + "performative: Performative,\n"
        cls_str += self.indent + 'dialogue_reference: Tuple[str, str] = ("", ""),\n'
        cls_str += self.indent + "message_id: int = 1,\n"
        cls_str += self.indent + "target: int = 0,\n"
        cls_str += self.indent + "**kwargs: Any,\n"
        self._change_indent(-1)
        cls_str += self.indent + "):\n"
        self._change_indent(1)
        cls_str += self.indent + '"""\n'
        cls_str += self.indent + "Initialise an instance of {}Message.\n\n".format(
            self.protocol_specification_in_camel_case
        )
        cls_str += self.indent + ":param message_id: the message id.\n"
        cls_str += self.indent + ":param dialogue_reference: the dialogue reference.\n"
        cls_str += self.indent + ":param target: the message target.\n"
        cls_str += self.indent + ":param performative: the message performative.\n"
        cls_str += self.indent + ":param **kwargs: extra options.\n"
        cls_str += self.indent + '"""\n'

        cls_str += self.indent + "super().__init__(\n"
        self._change_indent(1)
        cls_str += self.indent + "dialogue_reference=dialogue_reference,\n"
        cls_str += self.indent + "message_id=message_id,\n"
        cls_str += self.indent + "target=target,\n"
        cls_str += (
            self.indent
            + "performative={}Message.Performative(performative),\n".format(
                self.protocol_specification_in_camel_case
            )
        )
        cls_str += self.indent + "**kwargs,\n"
        self._change_indent(-1)
        cls_str += self.indent + ")\n"

        self._change_indent(-1)

        # Instance properties
        cls_str += self.indent + "@property\n"
        cls_str += self.indent + "def valid_performatives(self) -> Set[str]:\n"
        self._change_indent(1)
        cls_str += self.indent + '"""Get valid performatives."""\n'
        cls_str += self.indent + "return self._performatives\n\n"
        self._change_indent(-1)
        cls_str += self.indent + "@property\n"
        cls_str += self.indent + "def dialogue_reference(self) -> Tuple[str, str]:\n"
        self._change_indent(1)
        cls_str += self.indent + '"""Get the dialogue_reference of the message."""\n'
        cls_str += (
            self.indent
            + 'enforce(self.is_set("dialogue_reference"), "dialogue_reference is not set.")\n'
        )
        cls_str += (
            self.indent
            + 'return cast(Tuple[str, str], self.get("dialogue_reference"))\n\n'
        )
        self._change_indent(-1)
        cls_str += self.indent + "@property\n"
        cls_str += self.indent + "def message_id(self) -> int:\n"
        self._change_indent(1)
        cls_str += self.indent + '"""Get the message_id of the message."""\n'
        cls_str += (
            self.indent
            + 'enforce(self.is_set("message_id"), "message_id is not set.")\n'
        )
        cls_str += self.indent + 'return cast(int, self.get("message_id"))\n\n'
        self._change_indent(-1)
        cls_str += self.indent + "@property\n"
        cls_str += (
            self.indent
            + "def performative(self) -> Performative:  # type: ignore # noqa: F821\n"
        )
        self._change_indent(1)
        cls_str += self.indent + '"""Get the performative of the message."""\n'
        cls_str += (
            self.indent
            + 'enforce(self.is_set("performative"), "performative is not set.")\n'
        )
        cls_str += (
            self.indent
            + 'return cast({}Message.Performative, self.get("performative"))\n\n'.format(
                self.protocol_specification_in_camel_case
            )
        )
        self._change_indent(-1)
        cls_str += self.indent + "@property\n"
        cls_str += self.indent + "def target(self) -> int:\n"
        self._change_indent(1)
        cls_str += self.indent + '"""Get the target of the message."""\n'
        cls_str += (
            self.indent + 'enforce(self.is_set("target"), "target is not set.")\n'
        )
        cls_str += self.indent + 'return cast(int, self.get("target"))\n\n'
        self._change_indent(-1)

        for content_name in sorted(self.spec.all_unique_contents.keys()):
            content_type = self.spec.all_unique_contents[content_name]
            cls_str += self.indent + "@property\n"
            cls_str += self.indent + "def {}(self) -> {}:\n".format(
                content_name, self._to_custom_custom(content_type)
            )
            self._change_indent(1)
            cls_str += (
                self.indent
                + '"""Get the \'{}\' content from the message."""\n'.format(
                    content_name
                )
            )
            if not content_type.startswith("Optional"):
                cls_str += (
                    self.indent
                    + 'enforce(self.is_set("{}"), "\'{}\' content is not set.")\n'.format(
                        content_name, content_name
                    )
                )
            cls_str += self.indent + 'return cast({}, self.get("{}"))\n\n'.format(
                self._to_custom_custom(content_type), content_name
            )
            self._change_indent(-1)

        # check_consistency method
        cls_str += self.indent + "def _is_consistent(self) -> bool:\n"
        self._change_indent(1)
        cls_str += (
            self.indent
            + '"""Check that the message follows the {} protocol."""\n'.format(
                self.protocol_specification.name
            )
        )
        cls_str += self.indent + "try:\n"
        self._change_indent(1)
        cls_str += (
            self.indent
            + "enforce(isinstance(self.dialogue_reference, tuple), \"Invalid type for 'dialogue_reference'. Expected 'tuple'. Found '{}'.\""
            ".format(type(self.dialogue_reference)))\n"
        )
        cls_str += (
            self.indent
            + "enforce(isinstance(self.dialogue_reference[0], str), \"Invalid type for 'dialogue_reference[0]'. Expected 'str'. Found '{}'.\""
            ".format(type(self.dialogue_reference[0])))\n"
        )
        cls_str += (
            self.indent
            + "enforce(isinstance(self.dialogue_reference[1], str), \"Invalid type for 'dialogue_reference[1]'. Expected 'str'. Found '{}'.\""
            ".format(type(self.dialogue_reference[1])))\n"
        )
        cls_str += (
            self.indent
            + "enforce("
            + _type_check("self.message_id", "int")
            + ", \"Invalid type for 'message_id'. Expected 'int'. Found '{}'.\""
            ".format(type(self.message_id)))\n"
        )
        cls_str += (
            self.indent
            + "enforce("
            + _type_check("self.target", "int")
            + ", \"Invalid type for 'target'. Expected 'int'. Found '{}'.\""
            ".format(type(self.target)))\n\n"
        )

        cls_str += self.indent + "# Light Protocol Rule 2\n"
        cls_str += self.indent + "# Check correct performative\n"
        cls_str += (
            self.indent
            + "enforce(isinstance(self.performative, {}Message.Performative)".format(
                self.protocol_specification_in_camel_case
            )
        )
        cls_str += (
            ", \"Invalid 'performative'. Expected either of '{}'. Found '{}'.\".format("
        )
        cls_str += "self.valid_performatives, self.performative"
        cls_str += "))\n\n"

        cls_str += self.indent + "# Check correct contents\n"
        cls_str += (
            self.indent
            + "actual_nb_of_contents = len(self._body) - DEFAULT_BODY_SIZE\n"
        )
        cls_str += self.indent + "expected_nb_of_contents = 0\n"
        counter = 1
        for performative, contents in self.spec.speech_acts.items():
            if counter == 1:
                cls_str += self.indent + "if "
            else:
                cls_str += self.indent + "elif "
            cls_str += "self.performative == {}Message.Performative.{}:\n".format(
                self.protocol_specification_in_camel_case,
                performative.upper(),
            )
            self._change_indent(1)
            nb_of_non_optional_contents = 0
            for content_type in contents.values():
                if not content_type.startswith("Optional"):
                    nb_of_non_optional_contents += 1

            cls_str += self.indent + "expected_nb_of_contents = {}\n".format(
                nb_of_non_optional_contents
            )
            for content_name, content_type in contents.items():
                cls_str += self._check_content_type_str(content_name, content_type)
            counter += 1
            self._change_indent(-1)

        cls_str += "\n"
        cls_str += self.indent + "# Check correct content count\n"
        cls_str += (
            self.indent + "enforce(expected_nb_of_contents == actual_nb_of_contents, "
            '"Incorrect number of contents. Expected {}. Found {}"'
            ".format(expected_nb_of_contents, actual_nb_of_contents))\n\n"
        )

        cls_str += self.indent + "# Light Protocol Rule 3\n"
        cls_str += self.indent + "if self.message_id == 1:\n"
        self._change_indent(1)
        cls_str += (
            self.indent
            + "enforce(self.target == 0, \"Invalid 'target'. Expected 0 (because 'message_id' is 1). Found {}.\".format(self.target))\n"
        )
        self._change_indent(-2)
        cls_str += (
            self.indent + "except (AEAEnforceError, ValueError, KeyError) as e:\n"
        )
        self._change_indent(1)
        cls_str += self.indent + "_default_logger.error(str(e))\n"
        cls_str += self.indent + "return False\n\n"
        self._change_indent(-1)
        cls_str += self.indent + "return True\n"

        return cls_str

    def _valid_replies_str(self) -> str:
        """
        Generate the `valid replies` dictionary.

        :return: the `valid replies` dictionary string
        """
        valid_replies_str = (
            self.indent
            + "VALID_REPLIES: Dict[Message.Performative, FrozenSet[Message.Performative]] = {\n"
        )
        self._change_indent(1)
        for performative in sorted(self.spec.reply.keys()):
            valid_replies_str += (
                self.indent
                + "{}Message.Performative.{}: frozenset(".format(
                    self.protocol_specification_in_camel_case, performative.upper()
                )
            )
            if len(self.spec.reply[performative]) > 0:
                valid_replies_str += "\n"
                self._change_indent(1)
                valid_replies_str += self.indent + "{"
                for reply in self.spec.reply[performative]:
                    valid_replies_str += "{}Message.Performative.{}, ".format(
                        self.protocol_specification_in_camel_case, reply.upper()
                    )
                valid_replies_str = valid_replies_str[:-2]
                valid_replies_str += "}\n"
                self._change_indent(-1)
            valid_replies_str += self.indent + "),\n"

        self._change_indent(-1)
        valid_replies_str += self.indent + "}"
        return valid_replies_str

    def _end_state_enum_str(self) -> str:
        """
        Generate the end state Enum class.

        :return: the end state Enum string
        """
        enum_str = self.indent + "class EndState(Dialogue.EndState):\n"
        self._change_indent(1)
        enum_str += (
            self.indent
            + '"""This class defines the end states of a {} dialogue."""\n\n'.format(
                self.protocol_specification.name
            )
        )
        tag = 0
        for end_state in self.spec.end_states:
            enum_str += self.indent + "{} = {}\n".format(end_state.upper(), tag)
            tag += 1
        self._change_indent(-1)
        return enum_str

    def _agent_role_enum_str(self) -> str:
        """
        Generate the agent role Enum class.

        :return: the agent role Enum string
        """
        enum_str = self.indent + "class Role(Dialogue.Role):\n"
        self._change_indent(1)
        enum_str += (
            self.indent
            + '"""This class defines the agent\'s role in a {} dialogue."""\n\n'.format(
                self.protocol_specification.name
            )
        )
        for role in self.spec.roles:
            enum_str += self.indent + '{} = "{}"\n'.format(role.upper(), role)
        self._change_indent(-1)
        return enum_str

    def _dialogue_class_str(self) -> str:
        """
        Produce the content of the Message class.

        :return: the message.py file content
        """
        self._change_indent(0, "s")

        # Header
        cls_str = _copyright_header_str(self.protocol_specification.author) + "\n"

        # Module docstring
        cls_str += self.indent + '"""\n'
        cls_str += (
            self.indent
            + "This module contains the classes required for {} dialogue management.\n\n".format(
                self.protocol_specification.name
            )
        )
        cls_str += (
            self.indent
            + "- {}Dialogue: The dialogue class maintains state of a dialogue and manages it.\n".format(
                self.protocol_specification_in_camel_case
            )
        )
        cls_str += (
            self.indent
            + "- {}Dialogues: The dialogues class keeps track of all dialogues.\n".format(
                self.protocol_specification_in_camel_case
            )
        )
        cls_str += self.indent + '"""\n\n'

        # Imports
        cls_str += self.indent + "from abc import ABC\n"
        cls_str += (
            self.indent + "from typing import Callable, Dict, FrozenSet, Type, cast\n\n"
        )
        cls_str += self.indent + "from aea.common import Address\n"
        cls_str += self.indent + "from aea.protocols.base import Message\n"
        cls_str += (
            self.indent
            + "from aea.protocols.dialogue.base import Dialogue, DialogueLabel, Dialogues\n\n"
        )
        cls_str += self.indent + "from {}.message import {}Message\n".format(
            self.dotted_path_to_protocol_package,
            self.protocol_specification_in_camel_case,
        )

        # Class Header
        cls_str += "\nclass {}Dialogue(Dialogue):\n".format(
            self.protocol_specification_in_camel_case
        )
        self._change_indent(1)
        cls_str += (
            self.indent
            + '"""The {} dialogue class maintains state of a dialogue and manages it."""\n'.format(
                self.protocol_specification.name
            )
        )

        # Class Constants
        initial_performatives_str = ", ".join(
            [
                "{}Message.Performative.{}".format(
                    self.protocol_specification_in_camel_case, initial_performative
                )
                for initial_performative in self.spec.initial_performatives
            ]
        )
        terminal_performatives_str = ", ".join(
            [
                "{}Message.Performative.{}".format(
                    self.protocol_specification_in_camel_case, terminal_performative
                )
                for terminal_performative in self.spec.terminal_performatives
            ]
        )
        cls_str += (
            self.indent
            + "INITIAL_PERFORMATIVES: FrozenSet[Message.Performative] = frozenset({"
            + initial_performatives_str
            + "})\n"
            + self.indent
            + "TERMINAL_PERFORMATIVES: FrozenSet[Message.Performative] = frozenset({"
            + terminal_performatives_str
            + "})\n"
            + self._valid_replies_str()
        )

        # Enums
        cls_str += "\n" + self._agent_role_enum_str()
        cls_str += "\n" + self._end_state_enum_str()
        cls_str += "\n"

        # initializer
        cls_str += self.indent + "def __init__(\n"
        self._change_indent(1)
        cls_str += self.indent + "self,\n"
        cls_str += self.indent + "dialogue_label: DialogueLabel,\n"
        cls_str += self.indent + "self_address: Address,\n"
        cls_str += self.indent + "role: Dialogue.Role,\n"
        cls_str += self.indent + "message_class: Type[{}Message] = {}Message,\n".format(
            self.protocol_specification_in_camel_case,
            self.protocol_specification_in_camel_case,
        )
        self._change_indent(-1)
        cls_str += self.indent + ") -> None:\n"
        self._change_indent(1)
        cls_str += self.indent + '"""\n'
        cls_str += self.indent + "Initialize a dialogue.\n\n"
        cls_str += (
            self.indent + ":param dialogue_label: the identifier of the dialogue\n"
        )
        cls_str += (
            self.indent
            + ":param self_address: the address of the entity for whom this dialogue is maintained\n"
        )
        cls_str += (
            self.indent
            + ":param role: the role of the agent this dialogue is maintained for\n"
        )
        cls_str += self.indent + ":param message_class: the message class used\n"
        cls_str += self.indent + '"""\n'
        cls_str += self.indent + "Dialogue.__init__(\n"
        cls_str += self.indent + "self,\n"
        cls_str += self.indent + "dialogue_label=dialogue_label,\n"
        cls_str += self.indent + "message_class=message_class,\n"
        cls_str += self.indent + "self_address=self_address,\n"
        cls_str += self.indent + "role=role,\n"
        cls_str += self.indent + ")\n"
        self._change_indent(-2)

        # dialogues class
        cls_str += self.indent + "class {}Dialogues(Dialogues, ABC):\n".format(
            self.protocol_specification_in_camel_case
        )
        self._change_indent(1)
        cls_str += (
            self.indent
            + '"""This class keeps track of all {} dialogues."""\n\n'.format(
                self.protocol_specification.name
            )
        )
        end_states_str = ", ".join(
            [
                "{}Dialogue.EndState.{}".format(
                    self.protocol_specification_in_camel_case, end_state.upper()
                )
                for end_state in self.spec.end_states
            ]
        )
        cls_str += self.indent + "END_STATES = frozenset(\n"
        cls_str += self.indent + "{" + end_states_str + "}"
        cls_str += self.indent + ")\n\n"

        cls_str += (
            self.indent
            + f"_keep_terminal_state_dialogues = {repr(self.spec.keep_terminal_state_dialogues)}\n\n"
        )

        cls_str += self.indent + "def __init__(\n"
        self._change_indent(1)
        cls_str += self.indent + "self,\n"
        cls_str += self.indent + "self_address: Address,\n"
        cls_str += (
            self.indent
            + "role_from_first_message: Callable[[Message, Address], Dialogue.Role],\n"
        )
        cls_str += (
            self.indent
            + "dialogue_class: Type[{}Dialogue] = {}Dialogue,\n".format(
                self.protocol_specification_in_camel_case,
                self.protocol_specification_in_camel_case,
            )
        )
        self._change_indent(-1)
        cls_str += self.indent + ") -> None:\n"
        self._change_indent(1)
        cls_str += self.indent + '"""\n'
        cls_str += self.indent + "Initialize dialogues.\n\n"
        cls_str += (
            self.indent
            + ":param self_address: the address of the entity for whom dialogues are maintained\n"
        )
        cls_str += self.indent + ":param dialogue_class: the dialogue class used\n"
        cls_str += (
            self.indent
            + ":param role_from_first_message: the callable determining role from first message\n"
        )
        cls_str += self.indent + '"""\n'
        cls_str += self.indent + "Dialogues.__init__(\n"
        self._change_indent(1)
        cls_str += self.indent + "self,\n"
        cls_str += self.indent + "self_address=self_address,\n"
        cls_str += (
            self.indent
            + "end_states=cast(FrozenSet[Dialogue.EndState], self.END_STATES),\n"
        )
        cls_str += self.indent + "message_class={}Message,\n".format(
            self.protocol_specification_in_camel_case
        )
        cls_str += self.indent + "dialogue_class=dialogue_class,\n"
        cls_str += self.indent + "role_from_first_message=role_from_first_message,\n"
        self._change_indent(-1)
        cls_str += self.indent + ")\n"
        self._change_indent(-2)
        cls_str += self.indent + "\n"

        return cls_str

    def _custom_types_module_str(self) -> str:
        """
        Produce the contents of the custom_types module, containing classes corresponding to every custom type in the protocol specification.

        :return: the custom_types.py file content
        """
        self._change_indent(0, "s")

        # Header
        cls_str = _copyright_header_str(self.protocol_specification.author) + "\n"

        # Module docstring
        cls_str += '"""This module contains class representations corresponding to every custom type in the protocol specification."""\n'

        # class code per custom type
        for custom_type in self.spec.all_custom_types:
            cls_str += self.indent + "\n\nclass {}:\n".format(custom_type)
            self._change_indent(1)
            cls_str += (
                self.indent
                + '"""This class represents an instance of {}."""\n\n'.format(
                    custom_type
                )
            )
            cls_str += self.indent + "def __init__(self):\n"
            self._change_indent(1)
            cls_str += self.indent + '"""Initialise an instance of {}."""\n'.format(
                custom_type
            )
            cls_str += self.indent + "raise NotImplementedError\n\n"
            self._change_indent(-1)
            cls_str += self.indent + "@staticmethod\n"
            cls_str += (
                self.indent
                + 'def encode({}_protobuf_object, {}_object: "{}") -> None:\n'.format(
                    _camel_case_to_snake_case(custom_type),
                    _camel_case_to_snake_case(custom_type),
                    custom_type,
                )
            )
            self._change_indent(1)
            cls_str += self.indent + '"""\n'
            cls_str += (
                self.indent
                + "Encode an instance of this class into the protocol buffer object.\n\n"
            )
            cls_str += (
                self.indent
                + "The protocol buffer object in the {}_protobuf_object argument is matched with the instance of this class in the '{}_object' argument.\n\n".format(
                    _camel_case_to_snake_case(custom_type),
                    _camel_case_to_snake_case(custom_type),
                )
            )
            cls_str += (
                self.indent
                + ":param {}_protobuf_object: the protocol buffer object whose type corresponds with this class.\n".format(
                    _camel_case_to_snake_case(custom_type)
                )
            )
            cls_str += (
                self.indent
                + ":param {}_object: an instance of this class to be encoded in the protocol buffer object.\n".format(
                    _camel_case_to_snake_case(custom_type)
                )
            )
            cls_str += self.indent + '"""\n'
            cls_str += self.indent + "raise NotImplementedError\n\n"
            self._change_indent(-1)

            cls_str += self.indent + "@classmethod\n"
            cls_str += (
                self.indent
                + 'def decode(cls, {}_protobuf_object) -> "{}":\n'.format(
                    _camel_case_to_snake_case(custom_type),
                    custom_type,
                )
            )
            self._change_indent(1)
            cls_str += self.indent + '"""\n'
            cls_str += (
                self.indent
                + "Decode a protocol buffer object that corresponds with this class into an instance of this class.\n\n"
            )
            cls_str += (
                self.indent
                + "A new instance of this class is created that matches the protocol buffer object in the '{}_protobuf_object' argument.\n\n".format(
                    _camel_case_to_snake_case(custom_type)
                )
            )
            cls_str += (
                self.indent
                + ":param {}_protobuf_object: the protocol buffer object whose type corresponds with this class.\n".format(
                    _camel_case_to_snake_case(custom_type)
                )
            )
            cls_str += (
                self.indent
                + ":return: A new instance of this class that matches the protocol buffer object in the '{}_protobuf_object' argument.\n".format(
                    _camel_case_to_snake_case(custom_type)
                )
            )
            cls_str += self.indent + '"""\n'
            cls_str += self.indent + "raise NotImplementedError\n\n"
            self._change_indent(-1)

            cls_str += self.indent + "def __eq__(self, other):\n"
            self._change_indent(1)
            cls_str += self.indent + "raise NotImplementedError\n"
            self._change_indent(-2)
        return cls_str

    def _encoding_message_content_from_python_to_protobuf(
        self,
        content_name: str,
        content_type: str,
    ) -> str:
        """
        Produce the encoding of message contents for the serialisation class.

        :param content_name: the name of the content to be encoded
        :param content_type: the type of the content to be encoded

        :return: the encoding string
        """
        encoding_str = ""
        if content_type in PYTHON_TYPE_TO_PROTO_TYPE.keys():
            encoding_str += self.indent + "{} = msg.{}\n".format(
                content_name, content_name
            )
            encoding_str += self.indent + "performative.{} = {}\n".format(
                content_name, content_name
            )
        elif content_type.startswith("FrozenSet") or content_type.startswith("Tuple"):
            encoding_str += self.indent + "{} = msg.{}\n".format(
                content_name, content_name
            )
            encoding_str += self.indent + "performative.{}.extend({})\n".format(
                content_name, content_name
            )
        elif content_type.startswith("Dict"):
            encoding_str += self.indent + "{} = msg.{}\n".format(
                content_name, content_name
            )
            encoding_str += self.indent + "performative.{}.update({})\n".format(
                content_name, content_name
            )
        elif content_type.startswith("Union"):
            sub_types = _get_sub_types_of_compositional_types(content_type)
            for sub_type in sub_types:
                sub_type_name_in_protobuf = _union_sub_type_to_protobuf_variable_name(
                    content_name, sub_type
                )
                encoding_str += self.indent + 'if msg.is_set("{}"):\n'.format(
                    sub_type_name_in_protobuf
                )
                self._change_indent(1)
                encoding_str += self.indent + "performative.{}_is_set = True\n".format(
                    sub_type_name_in_protobuf
                )
                encoding_str += self._encoding_message_content_from_python_to_protobuf(
                    sub_type_name_in_protobuf, sub_type
                )
                self._change_indent(-1)
        elif content_type.startswith("Optional"):
            sub_type = _get_sub_types_of_compositional_types(content_type)[0]
            if not sub_type.startswith("Union"):
                encoding_str += self.indent + 'if msg.is_set("{}"):\n'.format(
                    content_name
                )
                self._change_indent(1)
                encoding_str += self.indent + "performative.{}_is_set = True\n".format(
                    content_name
                )
            encoding_str += self._encoding_message_content_from_python_to_protobuf(
                content_name, sub_type
            )
            if not sub_type.startswith("Union"):
                self._change_indent(-1)
        else:
            encoding_str += self.indent + "{} = msg.{}\n".format(
                content_name, content_name
            )
            encoding_str += self.indent + "{}.encode(performative.{}, {})\n".format(
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
        :param variable_name_in_protobuf: the name of the variable in the protobuf schema

        :return: the decoding string
        """
        decoding_str = ""
        variable_name = (
            content_name
            if variable_name_in_protobuf == ""
            else variable_name_in_protobuf
        )
        if content_type in PYTHON_TYPE_TO_PROTO_TYPE.keys():
            decoding_str += self.indent + "{} = {}_pb.{}.{}\n".format(
                content_name,
                self.protocol_specification.name,
                performative,
                variable_name,
            )
            decoding_str += self.indent + 'performative_content["{}"] = {}\n'.format(
                content_name, content_name
            )
        elif content_type.startswith("FrozenSet"):
            decoding_str += self.indent + "{} = {}_pb.{}.{}\n".format(
                content_name,
                self.protocol_specification.name,
                performative,
                content_name,
            )
            decoding_str += self.indent + "{}_frozenset = frozenset({})\n".format(
                content_name, content_name
            )
            decoding_str += (
                self.indent
                + 'performative_content["{}"] = {}_frozenset\n'.format(
                    content_name, content_name
                )
            )
        elif content_type.startswith("Tuple"):
            decoding_str += self.indent + "{} = {}_pb.{}.{}\n".format(
                content_name,
                self.protocol_specification.name,
                performative,
                content_name,
            )
            decoding_str += self.indent + "{}_tuple = tuple({})\n".format(
                content_name, content_name
            )
            decoding_str += (
                self.indent
                + 'performative_content["{}"] = {}_tuple\n'.format(
                    content_name, content_name
                )
            )
        elif content_type.startswith("Dict"):
            decoding_str += self.indent + "{} = {}_pb.{}.{}\n".format(
                content_name,
                self.protocol_specification.name,
                performative,
                content_name,
            )
            decoding_str += self.indent + "{}_dict = dict({})\n".format(
                content_name, content_name
            )
            decoding_str += (
                self.indent
                + 'performative_content["{}"] = {}_dict\n'.format(
                    content_name, content_name
                )
            )
        elif content_type.startswith("Union"):
            sub_types = _get_sub_types_of_compositional_types(content_type)
            for sub_type in sub_types:
                sub_type_name_in_protobuf = _union_sub_type_to_protobuf_variable_name(
                    content_name, sub_type
                )
                decoding_str += self.indent + "if {}_pb.{}.{}_is_set:\n".format(
                    self.protocol_specification.name,
                    performative,
                    sub_type_name_in_protobuf,
                )
                self._change_indent(1)
                decoding_str += self._decoding_message_content_from_protobuf_to_python(
                    performative=performative,
                    content_name=content_name,
                    content_type=sub_type,
                    variable_name_in_protobuf=sub_type_name_in_protobuf,
                )
                self._change_indent(-1)
        elif content_type.startswith("Optional"):
            sub_type = _get_sub_types_of_compositional_types(content_type)[0]
            if not sub_type.startswith("Union"):
                decoding_str += self.indent + "if {}_pb.{}.{}_is_set:\n".format(
                    self.protocol_specification.name, performative, content_name
                )
                self._change_indent(1)
            decoding_str += self._decoding_message_content_from_protobuf_to_python(
                performative, content_name, sub_type
            )
            if not sub_type.startswith("Union"):
                self._change_indent(-1)
        else:
            decoding_str += self.indent + "pb2_{} = {}_pb.{}.{}\n".format(
                variable_name,
                self.protocol_specification.name,
                performative,
                variable_name,
            )
            decoding_str += self.indent + "{} = {}.decode(pb2_{})\n".format(
                content_name,
                content_type,
                variable_name,
            )
            decoding_str += self.indent + 'performative_content["{}"] = {}\n'.format(
                content_name, content_name
            )
        return decoding_str

    def _serialization_class_str(self) -> str:
        """
        Produce the content of the Serialization class.

        :return: the serialization.py file content
        """
        self._change_indent(0, "s")

        # Header
        cls_str = _copyright_header_str(self.protocol_specification.author) + "\n"

        # Module docstring
        cls_str += (
            self.indent
            + '"""Serialization module for {} protocol."""\n\n'.format(
                self.protocol_specification.name
            )
        )

        cls_str += f"# pylint: disable={','.join(PYLINT_DISABLE_SERIALIZATION_PY)}\n"

        # Imports
        cls_str += self.indent + "from typing import Any, Dict, cast\n\n"
        cls_str += (
            self.indent
            + "from aea.mail.base_pb2 import DialogueMessage, Message as ProtobufMessage\n"
        )
        cls_str += MESSAGE_IMPORT + "\n"
        cls_str += SERIALIZER_IMPORT + "\n\n"
        cls_str += self.indent + "from {} import (\n    {}_pb2,\n)\n".format(
            self.dotted_path_to_protocol_package,
            self.protocol_specification.name,
        )
        for custom_type in self.spec.all_custom_types:
            cls_str += (
                self.indent
                + "from {}.custom_types import (\n    {},\n)\n".format(
                    self.dotted_path_to_protocol_package,
                    custom_type,
                )
            )
        cls_str += self.indent + "from {}.message import (\n    {}Message,\n)\n".format(
            self.dotted_path_to_protocol_package,
            self.protocol_specification_in_camel_case,
        )

        # Class Header
        cls_str += self.indent + "\n\nclass {}Serializer(Serializer):\n".format(
            self.protocol_specification_in_camel_case,
        )
        self._change_indent(1)
        cls_str += (
            self.indent
            + '"""Serialization for the \'{}\' protocol."""\n\n'.format(
                self.protocol_specification.name,
            )
        )

        # encoder
        cls_str += self.indent + "@staticmethod\n"
        cls_str += self.indent + "def encode(msg: Message) -> bytes:\n"
        self._change_indent(1)
        cls_str += self.indent + '"""\n'
        cls_str += self.indent + "Encode a '{}' message into bytes.\n\n".format(
            self.protocol_specification_in_camel_case,
        )
        cls_str += self.indent + ":param msg: the message object.\n"
        cls_str += self.indent + ":return: the bytes.\n"
        cls_str += self.indent + '"""\n'
        cls_str += self.indent + "msg = cast({}Message, msg)\n".format(
            self.protocol_specification_in_camel_case
        )
        cls_str += self.indent + "message_pb = ProtobufMessage()\n"
        cls_str += self.indent + "dialogue_message_pb = DialogueMessage()\n"
        cls_str += self.indent + "{}_msg = {}_pb2.{}Message()\n\n".format(
            self.protocol_specification.name,
            self.protocol_specification.name,
            self.protocol_specification_in_camel_case,
        )
        cls_str += self.indent + "dialogue_message_pb.message_id = msg.message_id\n"
        cls_str += self.indent + "dialogue_reference = msg.dialogue_reference\n"
        cls_str += (
            self.indent
            + "dialogue_message_pb.dialogue_starter_reference = dialogue_reference[0]\n"
        )
        cls_str += (
            self.indent
            + "dialogue_message_pb.dialogue_responder_reference = dialogue_reference[1]\n"
        )
        cls_str += self.indent + "dialogue_message_pb.target = msg.target\n\n"
        cls_str += self.indent + "performative_id = msg.performative\n"
        counter = 1
        for performative, contents in self.spec.speech_acts.items():
            if counter == 1:
                cls_str += self.indent + "if "
            else:
                cls_str += self.indent + "elif "
            cls_str += "performative_id == {}Message.Performative.{}:\n".format(
                self.protocol_specification_in_camel_case, performative.upper()
            )
            self._change_indent(1)
            cls_str += (
                self.indent
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
            cls_str += self.indent + "{}_msg.{}.CopyFrom(performative)\n".format(
                self.protocol_specification.name, performative
            )

            counter += 1
            self._change_indent(-1)
        cls_str += self.indent + "else:\n"
        self._change_indent(1)
        cls_str += (
            self.indent
            + 'raise ValueError("Performative not valid: {}".format(performative_id))\n\n'
        )
        self._change_indent(-1)

        cls_str += (
            self.indent
            + "dialogue_message_pb.content = {}_msg.SerializeToString()\n\n".format(
                self.protocol_specification.name,
            )
        )
        cls_str += (
            self.indent + "message_pb.dialogue_message.CopyFrom(dialogue_message_pb)\n"
        )
        cls_str += self.indent + "message_bytes = message_pb.SerializeToString()\n"
        cls_str += self.indent + "return message_bytes\n"
        self._change_indent(-1)

        # decoder
        cls_str += self.indent + "@staticmethod\n"
        cls_str += self.indent + "def decode(obj: bytes) -> Message:\n"
        self._change_indent(1)
        cls_str += self.indent + '"""\n'
        cls_str += self.indent + "Decode bytes into a '{}' message.\n\n".format(
            self.protocol_specification_in_camel_case,
        )
        cls_str += self.indent + ":param obj: the bytes object.\n"
        cls_str += self.indent + ":return: the '{}' message.\n".format(
            self.protocol_specification_in_camel_case
        )
        cls_str += self.indent + '"""\n'
        cls_str += self.indent + "message_pb = ProtobufMessage()\n"
        cls_str += self.indent + "{}_pb = {}_pb2.{}Message()\n".format(
            self.protocol_specification.name,
            self.protocol_specification.name,
            self.protocol_specification_in_camel_case,
        )
        cls_str += self.indent + "message_pb.ParseFromString(obj)\n"
        cls_str += self.indent + "message_id = message_pb.dialogue_message.message_id\n"
        cls_str += (
            self.indent
            + "dialogue_reference = (message_pb.dialogue_message.dialogue_starter_reference, message_pb.dialogue_message.dialogue_responder_reference)\n"
        )
        cls_str += self.indent + "target = message_pb.dialogue_message.target\n\n"
        cls_str += (
            self.indent
            + "{}_pb.ParseFromString(message_pb.dialogue_message.content)\n".format(
                self.protocol_specification.name
            )
        )
        cls_str += (
            self.indent
            + 'performative = {}_pb.WhichOneof("performative")\n'.format(
                self.protocol_specification.name
            )
        )
        cls_str += (
            self.indent
            + "performative_id = {}Message.Performative(str(performative))\n".format(
                self.protocol_specification_in_camel_case
            )
        )
        cls_str += (
            self.indent + "performative_content = dict()  # type: Dict[str, Any]\n"
        )
        counter = 1
        for performative, contents in self.spec.speech_acts.items():
            if counter == 1:
                cls_str += self.indent + "if "
            else:
                cls_str += self.indent + "elif "
            cls_str += "performative_id == {}Message.Performative.{}:\n".format(
                self.protocol_specification_in_camel_case, performative.upper()
            )
            self._change_indent(1)
            if len(contents.keys()) == 0:
                cls_str += self.indent + "pass\n"
            else:
                for content_name, content_type in contents.items():
                    cls_str += self._decoding_message_content_from_protobuf_to_python(
                        performative, content_name, content_type
                    )
            counter += 1
            self._change_indent(-1)
        cls_str += self.indent + "else:\n"
        self._change_indent(1)
        cls_str += (
            self.indent
            + 'raise ValueError("Performative not valid: {}.".format(performative_id))\n\n'
        )
        self._change_indent(-1)

        cls_str += self.indent + "return {}Message(\n".format(
            self.protocol_specification_in_camel_case,
        )
        self._change_indent(1)
        cls_str += self.indent + "message_id=message_id,\n"
        cls_str += self.indent + "dialogue_reference=dialogue_reference,\n"
        cls_str += self.indent + "target=target,\n"
        cls_str += self.indent + "performative=performative,\n"
        cls_str += self.indent + "**performative_content\n"
        self._change_indent(-1)
        cls_str += self.indent + ")\n"
        self._change_indent(-2)

        return cls_str

    def _content_to_proto_field_str(
        self,
        content_name: str,
        content_type: str,
        tag_no: int,
    ) -> Tuple[str, int]:
        """
        Convert a message content to its representation in a protocol buffer schema.

        :param content_name: the name of the content
        :param content_type: the type of the content
        :param tag_no: the tag number

        :return: the content in protocol buffer schema and the next tag number to be used
        """
        entry = ""

        if content_type.startswith("FrozenSet") or content_type.startswith(
            "Tuple"
        ):  # it is a <PCT>
            element_type = _get_sub_types_of_compositional_types(content_type)[0]
            proto_type = _python_pt_or_ct_type_to_proto_type(element_type)
            entry = self.indent + "repeated {} {} = {};\n".format(
                proto_type, content_name, tag_no
            )
            tag_no += 1
        elif content_type.startswith("Dict"):  # it is a <PMT>
            key_type = _get_sub_types_of_compositional_types(content_type)[0]
            value_type = _get_sub_types_of_compositional_types(content_type)[1]
            proto_key_type = _python_pt_or_ct_type_to_proto_type(key_type)
            proto_value_type = _python_pt_or_ct_type_to_proto_type(value_type)
            entry = self.indent + "map<{}, {}> {} = {};\n".format(
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
            entry += self.indent + "bool {}_is_set = {};\n".format(content_name, tag_no)
            tag_no += 1
        else:  # it is a <CT> or <PT>
            proto_type = _python_pt_or_ct_type_to_proto_type(content_type)
            entry = self.indent + "{} {} = {};\n".format(
                proto_type, content_name, tag_no
            )
            tag_no += 1
        return entry, tag_no

    def _protocol_buffer_schema_str(self) -> str:
        """
        Produce the content of the Protocol Buffers schema.

        :return: the protocol buffers schema content
        """
        self._change_indent(0, "s")

        # heading
        proto_buff_schema_str = self.indent + 'syntax = "proto3";\n\n'
        proto_buff_schema_str += self.indent + "package {};\n\n".format(
            public_id_to_package_name(
                self.protocol_specification.protocol_specification_id
            )
        )
        proto_buff_schema_str += self.indent + "message {}Message{{\n\n".format(
            self.protocol_specification_in_camel_case
        )
        self._change_indent(1)

        # custom types
        if (
            (len(self.spec.all_custom_types) != 0)
            and (self.protocol_specification.protobuf_snippets is not None)
            and (self.protocol_specification.protobuf_snippets != "")
        ):
            proto_buff_schema_str += self.indent + "// Custom Types\n"
            for custom_type in self.spec.all_custom_types:
                proto_buff_schema_str += self.indent + "message {}{{\n".format(
                    custom_type
                )
                self._change_indent(1)

                # formatting and adding the custom type protobuf entry
                specification_custom_type = "ct:" + custom_type
                proto_part = self.protocol_specification.protobuf_snippets[
                    specification_custom_type
                ]
                number_of_new_lines = proto_part.count("\n")
                if number_of_new_lines != 0:
                    formatted_proto_part = proto_part.replace(
                        "\n", "\n" + self.indent, number_of_new_lines - 1
                    )
                else:
                    formatted_proto_part = proto_part
                proto_buff_schema_str += self.indent + formatted_proto_part
                self._change_indent(-1)

                proto_buff_schema_str += self.indent + "}\n\n"
            proto_buff_schema_str += "\n"

        # performatives
        proto_buff_schema_str += self.indent + "// Performatives and contents\n"
        for performative, contents in self.spec.speech_acts.items():
            proto_buff_schema_str += self.indent + "message {}_Performative{{".format(
                performative.title()
            )
            self._change_indent(1)
            tag_no = 1
            if len(contents) == 0:
                proto_buff_schema_str += "}\n\n"
                self._change_indent(-1)
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
                self._change_indent(-1)
                proto_buff_schema_str += self.indent + "}\n\n"
        proto_buff_schema_str += "\n"

        proto_buff_schema_str += self.indent + "oneof performative{\n"
        self._change_indent(1)
        tag_no = 5
        for performative in self.spec.all_performatives:
            proto_buff_schema_str += self.indent + "{}_Performative {} = {};\n".format(
                performative.title(), performative, tag_no
            )
            tag_no += 1
        self._change_indent(-1)
        proto_buff_schema_str += self.indent + "}\n"
        self._change_indent(-1)

        proto_buff_schema_str += self.indent + "}\n"
        return proto_buff_schema_str

    def _protocol_yaml_str(self) -> str:
        """
        Produce the content of the protocol.yaml file.

        :return: the protocol.yaml content
        """
        protocol_yaml_str = "name: {}\n".format(self.protocol_specification.name)
        protocol_yaml_str += "author: {}\n".format(self.protocol_specification.author)
        protocol_yaml_str += "version: {}\n".format(self.protocol_specification.version)
        protocol_yaml_str += "protocol_specification_id: {}\n".format(
            str(self.protocol_specification.protocol_specification_id)
        )
        protocol_yaml_str += "type: {}\n".format(
            self.protocol_specification.component_type
        )
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
        init_str += '"""\nThis module contains the support resources for the {} protocol.\n\nIt was created with protocol buffer compiler version `{}` and aea protocol generator version `{}`.\n"""\n\n'.format(
            self.protocol_specification.name,
            self.protoc_version,
            PROTOCOL_GENERATOR_VERSION,
        )
        init_str += "from {}.message import {}Message\n".format(
            self.dotted_path_to_protocol_package,
            self.protocol_specification_in_camel_case,
        )
        init_str += "from {}.serialization import {}Serializer\n".format(
            self.dotted_path_to_protocol_package,
            self.protocol_specification_in_camel_case,
        )
        init_str += "{}Message.serializer = {}Serializer\n".format(
            self.protocol_specification_in_camel_case,
            self.protocol_specification_in_camel_case,
        )

        return init_str

    def generate_protobuf_only_mode(
        self,
        language: str = PROTOCOL_LANGUAGE_PYTHON,
        run_protolint: bool = True,
    ) -> Optional[str]:
        """
        Run the generator in "protobuf only" mode:

        a) validate the protocol specification.
        b) create the protocol buffer schema file.
        c) create the protocol buffer implementation file via 'protoc'.

        :param language: the target language in which to generate the package.
        :param run_protolint: whether to run protolint or not.

        :return: None
        """
        if language not in SUPPORTED_PROTOCOL_LANGUAGES:
            raise ValueError(
                f"Unsupported language. Expected one of {SUPPORTED_PROTOCOL_LANGUAGES}. Found {language}."
            )

        protobuf_output = None  # type: Optional[str]

        # Create the output folder
        output_folder = Path(self.path_to_generated_protocol_package)
        if not output_folder.exists():
            os.mkdir(output_folder)

        # Generate protocol buffer schema file
        _create_protocol_file(
            self.path_to_generated_protocol_package,
            "{}.proto".format(self.protocol_specification.name),
            self._protocol_buffer_schema_str(),
        )

        # Try to compile protobuf schema file
        is_compiled, msg = compile_protobuf_using_protoc(
            self.path_to_generated_protocol_package,
            self.protocol_specification.name,
            language,
        )
        if not is_compiled:
            # Remove the generated folder and files
            shutil.rmtree(output_folder)
            raise SyntaxError(
                "Error when trying to compile the protocol buffer schema file:\n" + msg
            )

        # Run protolint
        if run_protolint:
            is_correctly_formatted, protolint_output = apply_protolint(
                self.path_to_generated_protocol_package,
                self.protocol_specification.name,
            )
            if not is_correctly_formatted and protolint_output != "":
                protobuf_output = "Protolint warnings:\n" + protolint_output

        # Run black and isort formatting for python
        if language == PROTOCOL_LANGUAGE_PYTHON:
            try_run_black_formatting(self.path_to_generated_protocol_package)
            try_run_isort_formatting(self.path_to_generated_protocol_package)

        return protobuf_output

    def generate_full_mode(self, language: str) -> Optional[str]:
        """
        Run the generator in "full" mode:

        Runs the generator in protobuf only mode:
            a) validate the protocol specification.
            b) create the protocol buffer schema file.
            c) create the protocol buffer implementation file via 'protoc'.
        Additionally:
        d) generates python modules.
        e) applies black formatting
        f) applies isort formatting

        :param language: the language for which to create protobuf files
        :return: optional warning message
        """
        if language != PROTOCOL_LANGUAGE_PYTHON:
            raise ValueError(
                f"Unsupported language. Expected 'python' because currently the framework supports full generation of protocols only in Python. Found {language}."
            )

        # Run protobuf only mode
        full_mode_output = self.generate_protobuf_only_mode(
            language=PROTOCOL_LANGUAGE_PYTHON
        )

        # Generate Python protocol package
        _create_protocol_file(
            self.path_to_generated_protocol_package, INIT_FILE_NAME, self._init_str()
        )
        _create_protocol_file(
            self.path_to_generated_protocol_package,
            PROTOCOL_YAML_FILE_NAME,
            self._protocol_yaml_str(),
        )
        _create_protocol_file(
            self.path_to_generated_protocol_package,
            MESSAGE_DOT_PY_FILE_NAME,
            self._message_class_str(),
        )
        if (
            self.protocol_specification.dialogue_config is not None
            and self.protocol_specification.dialogue_config != {}
        ):
            _create_protocol_file(
                self.path_to_generated_protocol_package,
                DIALOGUE_DOT_PY_FILE_NAME,
                self._dialogue_class_str(),
            )
        if len(self.spec.all_custom_types) > 0:
            _create_protocol_file(
                self.path_to_generated_protocol_package,
                CUSTOM_TYPES_DOT_PY_FILE_NAME,
                self._custom_types_module_str(),
            )
        _create_protocol_file(
            self.path_to_generated_protocol_package,
            SERIALIZATION_DOT_PY_FILE_NAME,
            self._serialization_class_str(),
        )

        # Run black formatting
        try_run_black_formatting(self.path_to_generated_protocol_package)

        # Run isort formatting
        try_run_isort_formatting(self.path_to_generated_protocol_package)

        # Warn if specification has custom types
        if len(self.spec.all_custom_types) > 0:
            incomplete_generation_warning_msg = "The generated protocol is incomplete, because the protocol specification contains the following custom types: {}. Update the generated '{}' file with the appropriate implementations of these custom types.".format(
                self.spec.all_custom_types, CUSTOM_TYPES_DOT_PY_FILE_NAME
            )
            if full_mode_output is not None:
                full_mode_output += incomplete_generation_warning_msg
            else:
                full_mode_output = incomplete_generation_warning_msg
        return full_mode_output

    def generate(
        self, protobuf_only: bool = False, language: str = PROTOCOL_LANGUAGE_PYTHON
    ) -> Optional[str]:
        """
        Run the generator either in "full" or "protobuf only" mode.

        :param protobuf_only: mode of running the generator.
        :param language: the target language in which to generate the protocol package.

        :return: optional warning message.
        """
        if protobuf_only:
            output = self.generate_protobuf_only_mode(language)  # type: Optional[str]

            # Warn about the protobuf only mode
            protobuf_mode_warning_msg = (
                "The generated protocol is incomplete. It only includes the protocol buffer definitions. "
                + "You must implement and add other definitions (e.g. messages, serialisation, dialogue, etc) to this package."
            )
            if output is not None:
                output += protobuf_mode_warning_msg
            else:
                output = protobuf_mode_warning_msg
        else:
            output = self.generate_full_mode(language)
        return output


def public_id_to_package_name(public_id: PublicId) -> str:
    """Make package name string from public_id provided."""
    return f'aea.{public_id.author}.{public_id.name}.v{public_id.version.replace(".", "_")}'
