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
import os
import re
from os import path
from pathlib import Path
from typing import Dict, List, Set

from aea.configurations.base import ProtocolSpecification

CUSTOM_TYPE_PATTERN = "ct:[A-Z][a-zA-Z0-9]*"

MESSAGE_IMPORT = "from aea.protocols.base import Message"
SERIALIZER_IMPORT = "from aea.protocols.base import Serializer"
PATH_TO_PACKAGES = "packages"
INIT_FILE_NAME = "__init__.py"
MESSAGE_FILE_NAME = "message.py"
SERIALIZATION_FILE_NAME = "serialization.py"
PROTOCOL_FILE_NAME = "protocol.yaml"

BASIC_FIELDS_AND_TYPES = {
    "name": str,
    "author": str,
    "version": str,
    "license": str,
    "description": str,
}


def to_camel_case(text):
    """Convert a text in snake_case format into the CamelCase format."""
    return "".join(word.title() for word in text.split("_"))


class ProtocolGenerator:
    """This class generates a protocol_verification package from a ProtocolTemplate object."""

    def __init__(
        self, protocol_specification: ProtocolSpecification, output_path: str = "."
    ) -> None:
        """
        Instantiate a protocol generator.

        :param protocol_specification: the protocol specification object
        :param output_path: the path to the location in which the protocol module is to be generated.
        :return: None
        """
        self.protocol_specification = protocol_specification
        self.output_folder_path = os.path.join(output_path, protocol_specification.name)

        self._imports = {
            "Set": True,
            "Tuple": True,
            "cast": True,
            "Dict": False,
            "Union": False,
            "Optional": False,
            "FrozenSet": False,
        }

        self._speech_acts = dict()  # type: Dict[str, Dict[str, str]]
        self._all_performatives = list()  # type: List[str]
        self._all_unique_contents = dict()  # type: Dict[str, str]
        self._all_custom_types = list()  # type: List[str]

        self._setup()

    def _setup(self) -> None:
        """
        Extract all relevant data structures from the specification.

        :return: Dict[performatives, Dict[content names, content types]]
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
                for custom_type in custom_types:
                    all_custom_types_set.add(
                        self._specification_type_to_python_type(custom_type)
                    )
                pythonic_content_type = self._specification_type_to_python_type(
                    content_type
                )
                self._all_unique_contents[content_name] = pythonic_content_type
                self._speech_acts[performative][content_name] = pythonic_content_type
        self._all_performatives = sorted(all_performatives_set)
        self._all_custom_types = sorted(all_custom_types_set)

    def _handle_o(self, specification_type: str) -> str:
        """
        Handle an optional type.

        :param specification_type: the type described in the specification
        :return: The Python equivalent
        """
        self._imports["Optional"] = True
        element_type = specification_type[
            specification_type.index("[") + 1 : specification_type.rindex("]")
        ]
        element_type_in_python = self._specification_type_to_python_type(element_type)
        python_type = "Optional[{}]".format(element_type_in_python)
        return python_type

    def _handle_ct(self, specification_type: str) -> str:
        """
        Handle a custom type.

        :param specification_type: the type described in the specification
        :return: The Python equivalent
        """
        python_type = specification_type[3:]
        return python_type

    def _handle_pt(self, specification_type: str) -> str:
        """
        Handle a primitive type.

        :param specification_type: the type described in the specification
        :return: The Python equivalent
        """
        python_type = specification_type[3:]
        return python_type

    def _handle_pct(self, specification_type: str) -> str:
        """
        Handle a primitive collection type.

        :param specification_type: the type described in the specification
        :return: The Python equivalent
        """
        element_type = specification_type[
            specification_type.index("[") + 1 : specification_type.rindex("]")
        ]
        element_type_in_python = self._specification_type_to_python_type(element_type)
        if specification_type.startswith("pt:set"):
            self._imports["FrozenSet"] = True
            python_type = "FrozenSet[{}]".format(element_type_in_python)
        else:
            self._imports["Tuple"] = True
            python_type = "Tuple[{}]".format(element_type_in_python)
        return python_type

    def _handle_pmt(self, specification_type: str) -> str:
        """
        Handle a primitive mapping type.

        :param specification_type: the type described in the specification
        :return: The Python equivalent
        """
        self._imports["Dict"] = True
        element1_type = specification_type[
            specification_type.index("[") + 1 : specification_type.index(",")
        ]
        element2_type = specification_type[
            specification_type.index(",") + 1 : specification_type.rindex("]")
        ].strip()
        element1_type_in_python = self._specification_type_to_python_type(element1_type)
        element2_type_in_python = self._specification_type_to_python_type(element2_type)
        python_type = "Dict[{}, {}]".format(
            element1_type_in_python, element2_type_in_python
        )
        return python_type

    def _handle_mt(self, specification_types: Set[str]) -> str:
        """
        Handle a multi type.

        :param specification_types: the set of types which were separated with "or" in the protocol specification.
        :return: The Python equivalent
        """
        self._imports["Union"] = True
        python_type = "Union["
        for t in specification_types:
            python_type += "{}, ".format(self._specification_type_to_python_type(t))
        python_type = python_type[:-2]
        python_type += "]"
        return python_type

    def _specification_type_to_python_type(self, specification_type: str) -> str:
        """
        Convert a data type in protocol specification into its Python equivalent using the _handle_...() methods.

        :param specification_type: the type described in the specification
        :return: The Python equivalent
        """
        python_type = ""
        if specification_type.startswith("pt:optional"):
            python_type = self._handle_o(specification_type)
        else:
            specification_types = set(specification_type.split(" or "))
            if len(specification_types) == 1:  # just one type (not a Union[])
                if specification_type.startswith("ct:"):
                    python_type = self._handle_ct(specification_type)
                elif specification_type in [
                    "pt:bytes",
                    "pt:int",
                    "pt:float",
                    "pt:bool",
                    "pt:str",
                ]:
                    python_type = self._handle_pt(specification_type)
                elif specification_type.startswith(
                    "pt:set"
                ) or specification_type.startswith("pt:list"):
                    python_type = self._handle_pct(specification_type)
                elif specification_type.startswith("pt:dict"):
                    python_type = self._handle_pmt(specification_type)
                else:
                    raise TypeError("Unsupported type: '{}'".format(specification_type))
            elif len(specification_types) > 1:  # has more than one type 'or' separated
                python_type = self._handle_mt(specification_types)
        return python_type

    def _import_from_typing_str(self) -> str:
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

    def _performatives_str(self) -> str:
        """
        Generate the speech-act dictionary where content types are actual types (not strings).

        :return: the speech-act dictionary string
        """
        performatives_str = "{"
        for performative in self._all_performatives:
            performatives_str += '"{}", '.format(performative)
        performatives_str = performatives_str[:-2]
        performatives_str += "}"
        return performatives_str

    def _custom_types_classes_str(self) -> str:
        """
        Generate classes for every custom type.

        :return: the string containing class signatures and NotImplemented for every custom type
        """
        cls_str = ""

        if len(self._all_custom_types) == 0:
            return cls_str

        # class code per custom type
        for custom_type in self._all_custom_types:
            cls_str += str.format("class {}:\n", custom_type)
            cls_str += str.format(
                '    """This class represents an instance of {}."""\n\n', custom_type
            )
            cls_str += "    def __init__(self):\n"
            cls_str += str.format(
                '        """Initialise an instance of {}."""\n', custom_type
            )
            cls_str += "        raise NotImplementedError\n\n\n"
        return cls_str

    def _performatives_enum_str(self) -> str:
        """
        Generate the performatives Enum class.

        :return: the performatives Enum class set string
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
        enum_str += '            """Get string representation."""\n'
        enum_str += "            return self.value\n"
        enum_str += "\n"

        return enum_str

    @staticmethod
    def _check_content_type_str(no_of_indents: int, content_name, content_type) -> str:
        check_str = ""
        indents = ""
        for _ in itertools.repeat(None, no_of_indents):
            indents += "    "
        if content_type.startswith("Optional["):
            # check if the content exists then...
            check_str += indents + 'if self.is_set("{}"):\n'.format(content_name)
            indents += "    "
            content_type = content_type[
                content_type.index("[") + 1 : content_type.rindex("]")
            ]
        if content_type.startswith("FrozenSet["):
            # check the type
            check_str += (
                indents
                + "assert type(self.{}) == frozenset, \"{} is not 'frozenset'.\"\n".format(
                    content_name, content_name
                )
            )
            element_type = content_type[
                content_type.index("[") + 1 : content_type.rindex("]")
            ]
            # check the elements types
            check_str += indents + "assert all(\n"
            check_str += (
                indents
                + "    type(element) == {} for element in self.{}\n".format(
                    element_type, content_name
                )
            )
            check_str += indents + "), \"Elements of {} are not '{}'.\"\n".format(
                content_name, element_type
            )
        elif content_type.startswith("Tuple["):
            # check the type
            check_str += (
                indents
                + "assert type(self.{}) == tuple, \"{} is not 'tuple'.\"\n".format(
                    content_name, content_name
                )
            )
            element_type = content_type[
                content_type.index("[") + 1 : content_type.rindex("]")
            ]
            # check the elements types
            check_str += indents + "assert all(\n"
            check_str += (
                indents
                + "    type(element) == {} for element in self.{}\n".format(
                    element_type, content_name
                )
            )
            check_str += indents + "), \"Elements of {} are not '{}'.\"\n".format(
                content_name, element_type
            )
        elif content_type.startswith("Dict["):
            # check the type
            check_str += (
                indents
                + "assert type(self.{}) == dict, \"{} is not 'dict'.\"\n".format(
                    content_name, content_name
                )
            )
            element1_type = content_type[
                content_type.index("[") + 1 : content_type.index(",")
            ]
            element2_type = content_type[
                content_type.index(",") + 2 : content_type.rindex("]")
            ]
            # check the keys type then check the values type
            check_str += indents + "for key, value in self.{}.items():\n".format(
                content_name
            )
            check_str += indents + "    assert (\n"
            check_str += indents + "        type(key) == {}\n".format(element1_type)
            check_str += (
                indents
                + "    ), \"Keys of {} dictionary are not '{}'.\"\n".format(
                    content_name, element1_type
                )
            )

            check_str += indents + "    assert (\n"
            check_str += indents + "        type(value) == {}\n".format(element2_type)
            check_str += (
                indents
                + "    ), \"Values of {} dictionary are not '{}'.\"\n".format(
                    content_name, element2_type
                )
            )
        else:
            # check the type
            check_str += (
                indents
                + "assert type(self.{}) == {}, \"{} is not '{}'.\"\n".format(
                    content_name, content_type, content_name, content_type
                )
            )
        return check_str

    def _message_class_str(self) -> str:
        """
        Produce the content of the Message class.

        :return: the message class string
        """
        # Module docstring
        cls_str = str.format(
            '"""This module contains {}\'s message definition."""\n\n'.format(
                self.protocol_specification.name
            )
        )

        # Imports
        cls_str += "from enum import Enum\n"
        cls_str += "{}\n\n".format(self._import_from_typing_str())
        cls_str += "from aea.configurations.base import ProtocolId\n"
        cls_str += MESSAGE_IMPORT
        cls_str += "\n\nDEFAULT_BODY_SIZE = 4\n\n\n"

        # Custom classes
        cls_str += self._custom_types_classes_str()

        # Class Header
        cls_str += str.format(
            "class {}Message(Message):\n",
            to_camel_case(self.protocol_specification.name),
        )
        cls_str += str.format(
            '    """{}"""\n\n', self.protocol_specification.description
        )

        # Class attribute
        cls_str += '    protocol_id = ProtocolId("{}", "{}", "{}")\n\n'.format(
            self.protocol_specification.author,
            self.protocol_specification.name,
            self.protocol_specification.version,
        )

        # Performatives Enum
        cls_str += self._performatives_enum_str()

        # __init__
        cls_str += "    def __init__(\n"
        cls_str += "        self,\n"
        cls_str += "        dialogue_reference: Tuple[str, str],\n"
        cls_str += "        message_id: int,\n"
        cls_str += "        target: int,\n"
        cls_str += "        performative: str,\n"
        cls_str += "        **kwargs,\n"
        cls_str += "    ):\n"
        cls_str += '        """Initialise."""\n'
        cls_str += "        super().__init__(\n"
        cls_str += "            dialogue_reference=dialogue_reference,\n"
        cls_str += "            message_id=message_id,\n"
        cls_str += "            target=target,\n"
        cls_str += "            performative=performative,\n"
        cls_str += "            **kwargs,\n"
        cls_str += "        )\n"
        cls_str += "        self._performatives = {}\n".format(
            self._performatives_str()
        )
        cls_str += "        assert (\n"
        cls_str += "            self._is_consistent()\n"
        cls_str += "        ), \"This message is invalid according to the '{}' protocol\"\n\n".format(
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
        cls_str += '        assert self.is_set("dialogue_reference"), "dialogue_reference is not set"\n'
        cls_str += (
            '        return cast(Tuple[str, str], self.get("dialogue_reference"))\n\n'
        )
        cls_str += "    @property\n"
        cls_str += "    def message_id(self) -> int:\n"
        cls_str += '        """Get the message_id of the message."""\n'
        cls_str += '        assert self.is_set("message_id"), "message_id is not set"\n'
        cls_str += '        return cast(int, self.get("message_id"))\n\n'
        cls_str += "    @property\n"
        cls_str += "    def performative(self) -> Performative:  # noqa: F821\n"
        cls_str += '        """Get the performative of the message."""\n'
        cls_str += (
            '        assert self.is_set("performative"), "performative is not set"\n'
        )
        cls_str += '        return cast({}Message.Performative, self.get("performative"))\n\n'.format(
            to_camel_case(self.protocol_specification.name)
        )
        cls_str += "    @property\n"
        cls_str += "    def target(self) -> int:\n"
        cls_str += '        """Get the target of the message."""\n'
        cls_str += '        assert self.is_set("target"), "target is not set."\n'
        cls_str += '        return cast(int, self.get("target"))\n\n'
        for content_name in sorted(self._all_unique_contents.keys()):
            content_type = self._all_unique_contents[content_name]
            cls_str += "    @property\n"
            cls_str += "    def {}(self) -> {}:\n".format(content_name, content_type)
            cls_str += '        """Get the {} from the message."""\n'.format(
                content_name
            )
            cls_str += '        assert self.is_set("{}"), "{} is not set"\n'.format(
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
        cls_str += (
            "            ), \"dialogue_reference must be 'tuple' but it is not.\"\n"
        )
        cls_str += "            assert (\n"
        cls_str += "                type(self.dialogue_reference[0]) == str\n"
        cls_str += "            ), \"The first element of dialogue_reference must be 'str' but it is not.\"\n"
        cls_str += "            assert (\n"
        cls_str += "                type(self.dialogue_reference[1]) == str\n"
        cls_str += "            ), \"The second element of dialogue_reference must be 'str' but it is not.\"\n"
        cls_str += (
            '            assert type(self.message_id) == int, "message_id is not int"\n'
        )
        cls_str += (
            '            assert type(self.target) == int, "target is not int"\n\n'
        )

        cls_str += "            # Light Protocol 2\n"
        cls_str += "            # # Check correct performative\n"
        cls_str += "            assert (\n"
        cls_str += "                type(self.performative) == {}Message.Performative\n".format(
            to_camel_case(self.protocol_specification.name)
        )
        cls_str += "            ), \"'{}' is not in the list of valid performatives: {}\".format(\n"
        cls_str += "                self.performative, self.valid_performatives\n"
        cls_str += "            )\n\n"
        cls_str += "            # # Check correct contents\n"
        cls_str += (
            "            actual_nb_of_contents = len(self.body) - DEFAULT_BODY_SIZE\n"
        )
        counter = 1
        for performative, contents in self._speech_acts.items():
            if counter == 1:
                cls_str += "            if self.performative == {}Message.Performative.{}:\n".format(
                    to_camel_case(self.protocol_specification.name),
                    performative.upper(),
                )
            else:
                cls_str += "            elif self.performative == {}Message.Performative.{}:\n".format(
                    to_camel_case(self.protocol_specification.name),
                    performative.upper(),
                )
            cls_str += "                expected_nb_of_contents = {}\n".format(
                len(contents)
            )
            if len(contents) == 0:
                continue
            for content_name, content_type in contents.items():
                cls_str += self._check_content_type_str(4, content_name, content_type)
            counter += 1
        cls_str += "\n            # # Check correct content count\n"
        cls_str += "            assert (\n"
        cls_str += "                expected_nb_of_contents == actual_nb_of_contents\n"
        cls_str += '            ), "Incorrect number of contents. Expected {} contents. Found {}".format(\n'
        cls_str += "                expected_nb_of_contents, actual_nb_of_contents\n"
        cls_str += "            )\n\n"

        cls_str += "            # Light Protocol 3\n"
        cls_str += "            if self.message_id == 1:\n"
        cls_str += "                assert (\n"
        cls_str += "                    self.target == 0\n"
        cls_str += '                ), "Expected target to be 0 when message_id is 1. Found {}.".format(\n'
        cls_str += "                    self.target\n"
        cls_str += "                )\n"
        cls_str += "            else:\n"
        cls_str += "                assert (\n"
        cls_str += "                    0 < self.target < self.message_id\n"
        cls_str += '                ), "Expected target to be between 1 to (message_id -1) inclusive. Found {}".format(\n'
        cls_str += "                    self.target\n"
        cls_str += "                )\n"
        cls_str += "        except (AssertionError, ValueError, KeyError) as e:\n"
        cls_str += "            print(str(e))\n"
        cls_str += "            return False\n\n"
        cls_str += "        return True\n"

        return cls_str

    def _serialization_class_str(self) -> str:
        """
        Produce the content of the Serialization class.

        :return: the serialization class string
        """
        cls_str = str.format(
            '"""Serialization for {} protocol."""\n\n'.format(
                self.protocol_specification.name
            )
        )

        # Imports
        cls_str += "import base64\n"
        cls_str += "import json\n"
        cls_str += "import pickle\n\n"
        cls_str += MESSAGE_IMPORT + "\n"
        cls_str += SERIALIZER_IMPORT + "\n\n"
        cls_str += str.format(
            "from {}.{}.{}.{}.message import (\n    {}Message,\n)\n\n\n",
            PATH_TO_PACKAGES,
            self.protocol_specification.author,
            "protocols",
            self.protocol_specification.name,
            to_camel_case(self.protocol_specification.name),
        )

        # Class Header
        cls_str += str.format(
            "class {}Serializer(Serializer):\n",
            to_camel_case(self.protocol_specification.name),
        )
        cls_str += str.format(
            '    """Serialization for {} protocol."""\n\n',
            self.protocol_specification.name,
        )

        # encoder
        cls_str += str.format("    def encode(self, msg: Message) -> bytes:\n")
        cls_str += str.format(
            '        """Encode a \'{}\' message into bytes."""\n',
            to_camel_case(self.protocol_specification.name),
        )
        cls_str += "        body = {}  # Dict[str, Any]\n"
        cls_str += '        body["message_id"] = msg.get("message_id")\n'
        cls_str += '        body["target"] = msg.get("target")\n'
        cls_str += '        body["performative"] = msg.get("performative")\n\n'
        cls_str += '        contents_dict = msg.get("contents")\n'
        cls_str += "        contents_dict_bytes = base64.b64encode(pickle.dumps(contents_dict)).decode(\n"
        cls_str += '            "utf-8"\n'
        cls_str += "        )\n"
        cls_str += '        body["contents"] = contents_dict_bytes\n\n'
        cls_str += '        bytes_msg = json.dumps(body).encode("utf-8")\n'
        cls_str += "        return bytes_msg\n\n"

        # decoder
        cls_str += str.format("    def decode(self, obj: bytes) -> Message:\n")
        cls_str += str.format(
            '        """Decode bytes into a \'{}\' message."""\n',
            to_camel_case(self.protocol_specification.name),
        )
        cls_str += '        json_body = json.loads(obj.decode("utf-8"))\n'
        cls_str += '        message_id = json_body["message_id"]\n'
        cls_str += '        target = json_body["target"]\n'
        cls_str += '        performative = json_body["performative"]\n\n'
        cls_str += (
            '        contents_dict_bytes = base64.b64decode(json_body["contents"])\n'
        )
        cls_str += "        contents_dict = pickle.loads(contents_dict_bytes)\n\n"
        cls_str += str.format(
            "        return {}Message(\n",
            to_camel_case(self.protocol_specification.name),
        )
        cls_str += "            message_id=message_id,\n"
        cls_str += "            target=target,\n"
        cls_str += "            performative=performative,\n"
        cls_str += "            contents=contents_dict,\n"
        cls_str += "        )\n"

        return cls_str

    def _generate_message_class(self) -> None:
        """
        Create the Message class file.

        :return: None
        """
        pathname = path.join(self.output_folder_path, MESSAGE_FILE_NAME)
        message_class = self._message_class_str()

        with open(pathname, "w") as pyfile:
            pyfile.write(message_class)

    def _generate_serialisation_class(self) -> None:
        """
        Create the Serialization class file.

        :return: None
        """
        pathname = path.join(self.output_folder_path, SERIALIZATION_FILE_NAME)
        serialization_class = self._serialization_class_str()

        with open(pathname, "w") as pyfile:
            pyfile.write(serialization_class)

    def _generate_init_file(self) -> None:
        """
        Create the __init__ file.

        :return: None
        """
        pathname = path.join(self.output_folder_path, INIT_FILE_NAME)

        with open(pathname, "w") as pyfile:
            pyfile.write(
                str.format(
                    '"""This module contains the support resources for the {} protocol."""\n',
                    self.protocol_specification.name,
                )
            )

    def _generate_protocol_yaml(self) -> None:
        """
        Create the protocol.yaml file.

        :return: None
        """
        pathname = path.join(self.output_folder_path, PROTOCOL_FILE_NAME)

        with open(pathname, "w") as yamlfile:
            yamlfile.write(str.format("name: {}\n", self.protocol_specification.name))
            yamlfile.write(
                str.format("author: {}\n", self.protocol_specification.author)
            )
            yamlfile.write(
                str.format("version: {}\n", self.protocol_specification.version)
            )
            yamlfile.write(
                str.format("license: {}\n", self.protocol_specification.license)
            )
            yamlfile.write(
                str.format("description: {}\n", self.protocol_specification.description)
            )

    def generate(self) -> None:
        """
        Create the protocol package with Message, Serialization, __init__, protocol.yaml files.

        :return: None
        """
        # Create the output folder
        output_folder = Path(self.output_folder_path)
        if not output_folder.exists():
            os.mkdir(output_folder)

        self._generate_message_class()
        self._generate_serialisation_class()
        self._generate_init_file()
        self._generate_protocol_yaml()
