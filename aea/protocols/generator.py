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
import re
from os import path
from pathlib import Path
import yaml
from typing import Any, Dict, List, Set
from aea.configurations.base import ProtocolSpecification

DEFAULT_TYPES = ["int", "float", "bool", "str", "bytes", "list", "dict", "tuple", "set"]

MESSAGE_IMPORT = "from aea.protocols.base import Message"
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


def to_snake_case(text):
    """Convert a text in a CamelCase format into the snake_case format."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


# class ProtocolTemplate:
#     """
#     Extract protocol specification data from YAML configuration file.
#
#     This class:
#     a) reads a protocol specification YAML file,
#     b) extracts the protocol specification data into a protocol template object,
#     c) performs consistency checking.
#     """
#
#     def __init__(self, config_address: str) -> None:
#         """
#         Instantiate a protocol template object.
#
#         :param config_address: the address of the protocol specification yaml file
#         :return: None
#         """
#         self.config_address = config_address
#         self.yaml_documents = list()  # type: List[Any]
#
#         self.protocol_config = ProtocolConfig(name="", author="", version="", license="", description="")
#
#         self.speech_acts = dict()  # type: Dict[str, List[Dict[str, str]]]
#
#     def load(self) -> bool:
#         """
#         Call the two methods that read and extract protocol specification Yaml file.
#
#         :return: None
#         """
#         try:
#             self._read_protocol_specification()
#             self._extract_specification()
#         except (OSError, IOError, yaml.YAMLError, ProtocolSpecificationParseError):
#             raise
#         return True
#
#     def _read_protocol_specification(self) -> None:
#         """
#         Read a protocol specification YAML file.
#
#         Open and read the specification YAML file, and extract the yaml documents.
#         Raise any exceptions caught during file handling and reading the yaml file.
#
#         :return: None
#         """
#         try:
#             with open(self.config_address, 'r') as stream:
#                 yaml_data = yaml.safe_load_all(stream)
#                 for document in yaml_data:
#                     self.yaml_documents.append(document)
#         except (OSError, IOError, yaml.MarkedYAMLError):
#             raise
#
#     def _extract_specification(self) -> None:
#         """
#         Extract protocol specification data.
#
#         Extract the protocol specification data form yaml document objects.
#         Raise protocol specification parsing exceptions if the specification's format is incorrect.
#
#         :return: None
#         """
#         if len(self.yaml_documents) >= 2 \
#                 and self.yaml_documents[0] is not None \
#                 and self.yaml_documents[1] is not None:
#             for field, field_type in BASIC_FIELDS_AND_TYPES.items():
#                 if field in self.yaml_documents[0]:
#                     document_field_value = self.yaml_documents[0][field]
#                     self.protocol_config.__setattr__(field, document_field_value)
#                     if type(document_field_value) is not field_type:
#                         raise ProtocolSpecificationParseError("Protocol's '{}' is not of type {}.".format(field, field_type))
#                     if document_field_value == "":
#                         raise ProtocolSpecificationParseError("Protocol's '{}' is empty.".format(field))
#                 else:
#                     raise ProtocolSpecificationParseError("Protocol's {} could not be found.".format(field))
#             if "speech-acts" in self.yaml_documents[1]:
#                 self.speech_acts = self.yaml_documents[1]["speech-acts"]
#                 # Check speech-act's type is dict
#                 if type(self.speech_acts) is not dict:
#                     raise ProtocolSpecificationParseError("Protocol's 'speech-acts' is not a dictionary.")
#                 # Check speech-act has at least 1 performative defined.
#                 if len(self.speech_acts) < 1:  # potentially useless
#                     raise ProtocolSpecificationParseError(
#                         "There should be at least one performative in the speech-act.")
#                 for performative in self.speech_acts.keys():
#                     # Check speech-act's keys (i.e. performatives) are str
#                     if type(performative) is not str:
#                         raise ProtocolSpecificationParseError("A 'performative' is not specified as a string.")
#                     # Check speech-act's keys (i.e. performatives) are not empty
#                     if performative == "":
#                         raise ProtocolSpecificationParseError("A 'performative' cannot be an empty string.")
#                 for content_list in self.speech_acts.values():
#                     # Check speech-act's values (i.e. content-sequences) are lists
#                     if type(content_list) is not list and content_list is not None:
#                         raise ProtocolSpecificationParseError(
#                             "The contents of performatives must be described as a list.")
#                     if content_list is not None:
#                         for content_dict in content_list:
#                             # Check each content definition is a dict
#                             if type(content_dict) is not dict:
#                                 raise ProtocolSpecificationParseError(
#                                     "Each content (i.e. name and type) must be specified as a dictionary ")
#                             # Check there is exactly 1 content dict per list element
#                             if len(content_dict) != 1:
#                                 raise ProtocolSpecificationParseError("Only one content dictionary per list element.")
#                             for content_name, content_type in content_dict.items():
#                                 # Check each content definition key/value (i.e. content name/type) is str
#                                 if type(content_name) is not str or type(content_type) is not str:
#                                     raise ProtocolSpecificationParseError("Contents' names and types must be string.")
#                                 # Check each content definition key/value (i.e. content name/type) is not empty
#                                 if content_name == "" or content_type == "":
#                                     raise ProtocolSpecificationParseError("Contents' names and types cannot be empty.")
#             else:
#                 raise ProtocolSpecificationParseError(
#                     "Protocol's 'speech-acts' could not be found.")
#         else:
#             raise ProtocolSpecificationParseError(
#                 "There must be at least two YAML documents in the protocol specification YAML file.")


class ProtocolGenerator:
    """This class generates a protocol_verification package from a ProtocolTemplate object."""

    def __init__(self, protocol_specification: ProtocolSpecification, output_path: str = '.') -> None:
        """
        Instantiate a protocol generator.

        :param protocol_specification: the protocol template object that encapsulates the protocol specification
        :return: None
        """
        self.protocol_template = protocol_specification
        self.output_folder_path = os.path.join(output_path, to_snake_case(protocol_specification.name) + "_protocol")

    def _custom_types_classes_str(self) -> str:
        """
        Generate classes for every custom type.

        :return: the string containing class signatures and NotImplemented for every custom type
        """
        cls_str = ""
        type_set = set()
        custom_types_set = set()

        # extract contents' types and separate custom types
        for content_list in self.protocol_template.speech_acts.values():
            if content_list is not None and content_list != []:
                for content_dict in content_list:
                    for content_type in content_dict.values():
                        type_set.add(content_type)
                        if content_type not in DEFAULT_TYPES:
                            custom_types_set.add(content_type)

        # class code per custom type
        for custom_type in custom_types_set:
            cls_str += str.format('class {}:\n', custom_type)
            cls_str += '    def __init__(self):\n'
            cls_str += '        pass\n\n'
            cls_str += '    def __eq__(self, other):\n'
            cls_str += '        if type(other) is type(self):\n'
            cls_str += '            return self.__dict__ == other.__dict__\n'
            cls_str += '        else:\n'
            cls_str += '            return False\n\n'
            cls_str += '    def __ne__(self, other):\n'
            cls_str += '        return not self.__eq__(other)\n\n\n'

        return cls_str

    def _performatives_set(self) -> Set:
        """
        Generate the performatives set.

        :return: the performatives set string
        """
        performatives_set = set()
        for performative in self.protocol_template.speech_acts:
            performatives_set.add(performative)
        return performatives_set

    def _speech_acts_str(self) -> str:
        """
        Generate the speech-act dictionary where content types are actual types (not strings).

        :return: the speech-act dictionary string
        """
        speech_act_str = "{"
        for performative in self.protocol_template.speech_acts:
            speech_act_str += "\'"
            speech_act_str += performative
            speech_act_str += "\': ["
            if self.protocol_template.speech_acts[performative] is not None \
                    and self.protocol_template.speech_acts[performative] != []:
                for content_list in self.protocol_template.speech_acts[performative]:
                    speech_act_str += "("
                    for content_name in content_list.keys():
                        speech_act_str += "\'"
                        speech_act_str += content_name
                        speech_act_str += "\'"
                        speech_act_str += ", "
                        speech_act_str += content_list[content_name]
                    speech_act_str += "), "
                speech_act_str = speech_act_str[:-2]
            speech_act_str += "], "
        speech_act_str = speech_act_str[:-2]
        speech_act_str += "}"
        return speech_act_str

    def _message_class_str(self) -> str:
        """
        Produce the content of the Message class.

        :return: the message class string
        """
        cls_str = ""

        # Imports
        cls_str += 'from typing import cast, List\n\n'
        cls_str += MESSAGE_IMPORT
        cls_str += '\n\n\n'

        # Custom classes
        cls_str += self._custom_types_classes_str()

        # Class Header
        cls_str += str.format('class {}Message(Message):\n', self.protocol_template.name)
        cls_str += str.format('    \"\"\"{}\"\"\"\n\n', self.protocol_template.description)

        # __init__
        cls_str += '    def __init__(self, message_id: int = None, target: int = None, performative: str = None, ' \
                   'contents: List = None, **kwargs):\n'
        cls_str += '        \"\"\"Initialise.\"\"\"\n'
        cls_str += '        super().__init__(message_id=message_id, target=target, performative=performative, ' \
                   'contents=contents, **kwargs)\n\n'

        # variables
        cls_str += str.format('        self.name = \"{}\"\n', self.protocol_template.name)
        cls_str += str.format('        self.author = \"{}\"\n', self.protocol_template.author)
        cls_str += str.format('        self.version = \"{}\"\n', self.protocol_template.version)
        cls_str += str.format('        self.license = \"{}\"\n', self.protocol_template.license)
        cls_str += str.format('        self.description = \"{}\"\n\n', self.protocol_template.description)
        cls_str += str.format('        self.performatives = {}\n', self._performatives_set())
        cls_str += str.format('        self.speech_acts = {}\n\n', self._speech_acts_str())
        cls_str += '#        assert self.check_consistency()\n\n'

        # check_consistency method
        cls_str += '    def check_consistency(self) -> bool:\n'
        cls_str += str.format('        \"\"\"Check that the message follows the {} protocol\"\"\"\n',
                              self.protocol_template.name)
        cls_str += '        try:\n'

        cls_str += '            assert self.is_set(\"message_id\"), \"message_id is not set\"\n'
        cls_str += '            message_id = self.get(\"message_id\")\n'
        cls_str += '            assert type(message_id) == int, \"message_id is not int\"\n\n'

        cls_str += '            assert self.is_set(\"target\"), \"target is not set\"\n'
        cls_str += '            target = self.get(\"target\")\n'
        cls_str += '            assert type(target) == int, \"target is not int\"\n\n'

        cls_str += '            assert self.is_set(\"performative\"), \"performative is not set\"\n'
        cls_str += '            performative = self.get(\"performative\")\n'
        cls_str += '            assert type(performative) == str, \"performative is not str\"\n\n'

        cls_str += '            assert self.is_set(\"contents\"), \"contents is not set\"\n'
        cls_str += '            contents = self.get(\"contents\")\n'
        cls_str += '            assert type(contents) == list, \"contents is not list\"\n'
        cls_str += '            contents = cast(List, contents)\n\n'

        cls_str += '            # Light Protocol 2\n'
        cls_str += '            # Check correct performative\n'
        cls_str += '            assert performative in self.performatives,' \
                   ' \"performative is not in the list of allowed performative\"\n\n'

        cls_str += '            # Check correct contents\n'
        cls_str += '            content_sequence_definition = self.speech_acts[performative]  # type is List\n'
        cls_str += '            # Check number of contents\n'
        cls_str += '            assert len(contents) == len(content_sequence_definition), ' \
                   '\"incorrect number of contents\"\n'
        cls_str += '            # Check the content is of the correct type\n'
        cls_str += '            for content in range(len(content_sequence_definition)):\n'
        cls_str += '                assert isinstance(contents[content], content_sequence_definition[content][1]), ' \
                   '\"incorrect content type\"\n\n'

        cls_str += '            # Light Protocol 3\n'
        cls_str += '            if message_id == 1:\n'
        cls_str += '                assert target == 0, \"target should be 0\"\n'
        cls_str += '            else:\n'
        cls_str += '                assert 1 < target < message_id, \"target should be between 1 and message_id\"\n'
        cls_str += '        except (AssertionError, ValueError, KeyError) as e:\n'
        cls_str += '            print(str(e))\n'
        cls_str += '            return False\n\n'
        cls_str += '        return True\n'

        return cls_str

    def _generate_message_class(self) -> None:
        """
        Create the Message class file.

        :return: None
        """
        pathname = path.join(self.output_folder_path, MESSAGE_FILE_NAME)
        message_class = self._message_class_str()

        with open(pathname, 'w') as pyfile:
            pyfile.write(message_class)

    def _serialization_class_str(self) -> str:
        """
        Produce the content of the Serialization class.

        :return: the serialization class string
        """
        cls_str = ""
        # Imports
        cls_str += "from aea.protocols.base import Message\n"
        cls_str += "from aea.protocols.base import Serializer\n"
        cls_str += str.format("from {}.message import {}Message\n\n", self.output_folder_path,
                              self.protocol_template.name)
        cls_str += "import json\n"
        cls_str += "import base64\n"
        cls_str += "import pickle\n"
        cls_str += "from typing import cast, List\n\n\n"

        # Class Header
        cls_str += str.format('class {}Serializer(Serializer):\n', self.protocol_template.name)
        cls_str += str.format('    \"\"\"Serialization for {} protocol\"\"\"\n\n',
                              self.protocol_template.description.lower())

        # encoder
        cls_str += str.format('    def encode(self, msg: Message) -> bytes:\n')
        cls_str += str.format('        \"\"\"Encode a \'{}\' message into bytes.\"\"\"\n',
                              self.protocol_template.name)
        cls_str += "        body = {}  # Dict[str, Any]\n"
        cls_str += "        body[\"message_id\"] = msg.get(\"message_id\")\n"
        cls_str += "        body[\"target\"] = msg.get(\"target\")\n"
        cls_str += "        body[\"performative\"] = msg.get(\"performative\")\n\n"
        cls_str += "        contents_list = msg.get(\"contents\")\n"
        cls_str += "        contents_list_bytes = base64.b64encode(pickle.dumps(contents_list)).decode(\"utf-8\")\n"
        cls_str += "        body[\"contents\"] = contents_list_bytes\n\n"
        cls_str += "        bytes_msg = json.dumps(body).encode(\"utf-8\")\n"
        cls_str += "        return bytes_msg\n\n"

        # decoder
        cls_str += str.format('    def decode(self, obj: bytes) -> Message:\n')
        cls_str += str.format('        \"\"\"Decode bytes into a \'{}\' message.\"\"\"\n',
                              self.protocol_template.name)
        cls_str += "        json_body = json.loads(obj.decode(\"utf-8\"))\n"
        cls_str += "        message_id = json_body[\"message_id\"]\n"
        cls_str += "        target = json_body[\"target\"]\n"
        cls_str += "        performative = json_body[\"performative\"]\n\n"
        cls_str += "        contents_list_bytes = base64.b64decode(json_body[\"contents\"])\n"
        cls_str += "        contents_list = pickle.loads(contents_list_bytes)\n\n"
        cls_str += str.format("        return {}Message(message_id=message_id, target=target, "
                              "performative=performative, contents=contents_list)\n", self.protocol_template.name)

        return cls_str

    def _generate_serialisation_class(self) -> None:
        """
        Create the Serialization class file.

        :return: None
        """
        pathname = path.join(self.output_folder_path, SERIALIZATION_FILE_NAME)
        serialization_class = self._serialization_class_str()

        with open(pathname, 'w') as pyfile:
            pyfile.write(serialization_class)

    def _generate_init_file(self) -> None:
        """
        Create the __init__ file.

        :return: None
        """
        pathname = path.join(self.output_folder_path, INIT_FILE_NAME)

        with open(pathname, 'w') as pyfile:
            pyfile.write(str.format('\"\"\"This module contains the support resources for the {} protocol.\"\"\"\n',
                                    self.protocol_template.name))

    def _generate_protocol_yaml(self) -> None:
        """
        Create the protocol.yaml file.

        :return: None
        """
        pathname = path.join(self.output_folder_path, PROTOCOL_FILE_NAME)

        with open(pathname, 'w') as yamlfile:
            yamlfile.write(str.format('name: {}\n', self.protocol_template.name))
            yamlfile.write(str.format('author: {}\n', self.protocol_template.author))
            yamlfile.write(str.format('version: {}\n', self.protocol_template.version))
            yamlfile.write(str.format('license: {}\n', self.protocol_template.license))
            yamlfile.write(str.format('description: {}\n', self.protocol_template.description))

        # Can do this once protocol specification schema is created
        # config_loader = ConfigLoader(PATH_TO_SPEC_SCHEMA, ProtocolConfig)
        # config_loader.dump(self.protocol_template.protocol_config, open(pathname, "w"))

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
