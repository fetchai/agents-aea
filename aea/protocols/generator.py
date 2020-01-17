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

import os
from os import path
from pathlib import Path
from typing import Dict, List, Set

from aea.configurations.base import ProtocolSpecification

DEFAULT_TYPES = ["int", "float", "bool", "str", "bytes", "list", "dict", "tuple", "set"]

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

    def _extract_all_contents(self) -> Dict[str, Dict[str, str]]:
        all_contents = {}  # type: Dict[str, Dict[str, str]]
        for performative, speech_act_content_config in self.protocol_specification.speech_acts.read_all():
            all_contents[performative] = {}
            for content_name, content_type in speech_act_content_config.args.items():
                all_contents[performative][content_name] = content_type
        return all_contents

    def _custom_types_classes_str(self) -> str:
        """
        Generate classes for every custom type.

        :return: the string containing class signatures and NotImplemented for every custom type
        """
        cls_str = ""
        type_set = set()
        custom_types_set = set()

        # extract contents' types and separate custom types
        for (
            performative,
            speech_act_content_config,
        ) in self.protocol_specification.speech_acts.read_all():
            for content_type in speech_act_content_config.args.values():
                type_set.add(content_type)
                if content_type not in DEFAULT_TYPES:
                    custom_types_set.add(content_type)

        # class code per custom type
        for custom_type in custom_types_set:
            cls_str += str.format("class {}:\n", custom_type)
            cls_str += str.format(
                '    """This class represents a {}."""\n\n', custom_type
            )
            cls_str += "    def __init__(self):\n"
            cls_str += str.format('        """Initialise a {}."""\n', custom_type)
            cls_str += "        raise NotImplementedError\n\n"
            cls_str += "    def __eq__(self, other):\n"
            cls_str += str.format(
                '        """Compare two instances of this class."""\n', custom_type
            )
            cls_str += "        if type(other) is type(self):\n"
            cls_str += "            raise NotImplementedError\n"
            cls_str += "        else:\n"
            cls_str += "            return False"

        return cls_str

    def _performatives_set(self) -> Set:
        """
        Generate the performatives set.

        :return: the performatives set string
        """
        performatives_set = set()
        for (
            performative,
            speech_act_content_config,
        ) in self.protocol_specification.speech_acts.read_all():
            performatives_set.add(performative)
        return performatives_set

    def _speech_acts_str(self) -> str:
        """
        Generate the speech-act dictionary where content types are actual types (not strings).

        :return: the speech-act dictionary string
        """
        speech_act_str = "{\n"
        for (
            performative,
            speech_act_content_config,
        ) in self.protocol_specification.speech_acts.read_all():
            speech_act_str += "        "
            speech_act_str += '"'
            speech_act_str += performative
            speech_act_str += '": {'
            if len(speech_act_content_config.args.items()) > 0:
                for key, value in speech_act_content_config.args.items():
                    speech_act_str += '"'
                    speech_act_str += key
                    speech_act_str += '"'
                    speech_act_str += ": "
                    speech_act_str += value
                    speech_act_str += ", "
                speech_act_str = speech_act_str[:-2]
            speech_act_str += "},\n"
        speech_act_str = speech_act_str[:-1]
        speech_act_str += "\n    }"
        return speech_act_str

    def _message_class_str(self) -> str:
        """
        Produce the content of the Message class.

        :return: the message class string
        """
        cls_str = ""
        cls_str = str.format(
            '"""This module contains {}\'s message definition."""\n\n'.format(
                self.protocol_specification.name
            )
        )

        # Imports
        cls_str += "from typing import Dict, Set, Tuple, cast\n\n"
        cls_str += MESSAGE_IMPORT
        cls_str += "\n\nDEFAULT_BODY_SIZE = 4\n\n\n"

        # Custom classes
        cls_str += self._custom_types_classes_str()
        cls_str += "\n\n\n"

        # Class Header
        cls_str += str.format(
            "class {}Message(Message):\n",
            to_camel_case(self.protocol_specification.name),
        )
        cls_str += str.format(
            '    """{}"""\n\n', self.protocol_specification.description
        )

        # Class attribute
        cls_str += str.format('    _speech_acts = {}\n\n', self._speech_acts_str())

        # __init__
        cls_str += "    def __init__(\n"
        cls_str += "        self, dialogue_reference: Tuple[str, str], message_id: int, target: int, performative: str, **kwargs\n"
        cls_str += "    ):\n"
        cls_str += '        """Initialise."""\n'
        cls_str += "        super().__init__(\n"
        cls_str += "            message_id=message_id,\n"
        cls_str += "            target=target,\n"
        cls_str += "            performative=performative,\n"
        cls_str += "            **kwargs\n"
        cls_str += "        )\n"
        cls_str += "        assert self._check_consistency()\n\n"

        # Class properties
        cls_str += '    @property\n'
        cls_str += '    def speech_acts(self) -> Dict[str, Dict[str, str]]:\n'
        cls_str += '        \"\"\"Get all speech acts.\"\"\"\n'
        cls_str += '        return self._speech_acts\n\n'
        cls_str += '    @property\n'
        cls_str += '    def valid_performatives(self) -> Set[str]:\n'
        cls_str += '        \"\"\"Get valid performatives.\"\"\"\n'
        cls_str += '        return set(self._speech_acts.keys())\n\n'

        # Instance properties
        cls_str += '    @property\n'
        cls_str += '    def dialogue_reference(self) -> Tuple[str, str]:\n'
        cls_str += '        \"\"\"Get the dialogue_reference of the message.\"\"\"\n'
        cls_str += '        assert self.is_set(\"dialogue_reference\"), \"dialogue_reference is not set\"\n'
        cls_str += '        return cast(Tuple[str, str], self.get(\"dialogue_reference\"))\n\n'
        cls_str += '    @property\n'
        cls_str += '    def message_id(self) -> int:\n'
        cls_str += '        \"\"\"Get the message_id of the message.\"\"\"\n'
        cls_str += '        assert self.is_set(\"message_id\"), \"message_id is not set\"\n'
        cls_str += '        return cast(int, self.get(\"message_id\"))\n\n'
        cls_str += '    @property\n'
        cls_str += '    def target(self) -> int:\n'
        cls_str += '        \"\"\"Get the target of the message.\"\"\"\n'
        cls_str += '        assert self.is_set(\"target\"), \"target is not set.\"\n'
        cls_str += '        return cast(int, self.get(\"target\"))\n\n'
        cls_str += '    @property\n'
        cls_str += '    def performative(self) -> str:\n'
        cls_str += '        \"\"\"Get the performative of the message.\"\"\"\n'
        cls_str += '        assert self.is_set(\"performative\"), \"performative is not set\"\n'
        cls_str += '        return cast(str, self.get(\"performative\"))\n\n'

        all_contents = self._extract_all_contents()
        covered = []  # type: List[str]
        for performative, contents in all_contents.items():
            for content_name, content_type in contents.items():
                if content_name in covered:
                    continue
                else:
                    covered.append(content_name)
                cls_str += '    @property\n'
                cls_str += "    def {}(self) -> {}:\n".format(content_name, content_type)
                cls_str += "        \"\"\"Get {} for performative {}.\"\"\"\n".format(content_name, performative)
                cls_str += '        assert self.is_set(\"{}\"), \"{} is not set\"\n'.format(content_name, content_name)
                cls_str += '        return cast({}, self.get(\"{}\"))\n\n'.format(content_type, content_name)

        # check_consistency method
        cls_str += "    def _check_consistency(self) -> bool:\n"
        cls_str += str.format(
            '        """Check that the message follows the {} protocol."""\n',
            self.protocol_specification.name,
        )
        cls_str += "        try:\n"

        cls_str += '            assert isinstance(self.dialogue_reference, Tuple), \"dialogue_reference must be \'Tuple\' but it is not.\"\n'
        cls_str += '            assert isinstance(self.dialogue_reference[0], str), \"The first element of dialogue_reference must be \'str\' but it is not.\"\n'
        cls_str += '            assert isinstance(self.dialogue_reference[1], str), \"The second element of dialogue_reference must be \'str\' but it is not.\"\n'
        cls_str += (
            '            assert type(self.message_id) == int, "message_id is not int"\n'
        )
        cls_str += '            assert type(self.target) == int, "target is not int"\n'
        cls_str += '            assert type(self.performative) == str, "performative is not str"\n\n'

        cls_str += "            # Light Protocol 2\n"
        cls_str += "            # Check correct performative\n"
        cls_str += "            assert (\n"
        cls_str += "                self.performative in self.valid_performatives\n"
        cls_str += '            ), \"\'{}\' is not in the list of valid performativs: {}\".format(self.performative, self.valid_performatives)\n\n'

        cls_str += "            # Check correct contents\n"
        cls_str += "            actual_nb_of_contents = len(self.body) - DEFAULT_BODY_SIZE\n"
        for performative, contents in all_contents.items():
            cls_str += '            if self.performative == "{}":\n'.format(performative)
            cls_str += "                expexted_nb_of_contents = {}\n".format(len(contents))
            if len(contents) == 0:
                continue
            for content_name, content_type in contents.items():
                cls_str += '                assert type(self.{}) == {}, "{} is not {}"\n'.format(content_name, content_type, content_name, content_type)
        cls_str += "\n            # Check body size\n"
        cls_str += "            assert (\n"
        cls_str += "                expexted_nb_of_contents == actual_nb_of_contents\n"
        cls_str += '            ), \"Incorrect number of contents. Expected {} contents. Found {}\".format(expexted_nb_of_contents, actual_nb_of_contents)\n\n'

        cls_str += "            # Light Protocol 3\n"
        cls_str += "            if self.message_id == 1:\n"
        cls_str += '                assert self.target == 0, "Expected target to be 0 when message_id is 1. Found {}.\".format(self.target)\n'
        cls_str += "            else:\n"
        cls_str += "                assert (\n"
        cls_str += "                    0 < self.target < self.message_id\n"
        cls_str += (
            '                ), "Expected target to be between 1 to (message_id -1) inclusive. Found {}\".format(self.target)\n'
        )
        cls_str += "        except (AssertionError, ValueError, KeyError) as e:\n"
        cls_str += "            print(str(e))\n"
        cls_str += "            return False\n\n"
        cls_str += "        return True\n"

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

    def _serialization_class_str(self) -> str:
        """
        Produce the content of the Serialization class.

        :return: the serialization class string
        """
        cls_str = ""
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
