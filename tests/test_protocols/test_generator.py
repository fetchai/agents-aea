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
"""This module contains the tests for the protocol generator"""

import inspect
import os
from unittest import TestCase
import yaml
import shutil
import tempfile

from aea.protocols.generator import ProtocolGenerator
from aea.configurations.base import ProtocolSpecificationParseError, ProtocolSpecification
from aea.configurations.loader import ConfigLoader

CUR_PATH = os.path.dirname(inspect.getfile(inspect.currentframe()))  # type: ignore


class TestGenerateProtocol:
    """Test that the generating a protocol works correctly in correct preconditions."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.protocol_name = 'two_party_negotiation'
        correct_specification = {
            'name': cls.protocol_name,
            'author': 'fetchai',
            'version': '0.1.0',
            'license': 'Apache 2.0',
            'description': 'A protocol for negotiation over a fixed set of resources involving two parties.',
            'speech_acts': {
                'cfp': {
                    'query': 'DataModel'
                },
                'propose': {
                    'query': 'DataModel',
                    'price': 'float'
                },
                'accept': {},
                'decline': {},
                'match_accept': {}
            }
        }

        # Dump the config
        cls.cwd = os.getcwd()
        cls.specification_file_name = "Spec.yaml"
        # cls.path_to_specification = os.path.join(".", cls.specification_file_name)
        cls.path_to_specification = os.path.join(CUR_PATH, cls.specification_file_name)
        cls.path_to_protocol = os.path.join(cls.cwd, cls.protocol_name)

        # os.mkdir(os.path.join(CUR_PATH, "temp"))
        # cls.cwd = os.getcwd()
        # cls.t = tempfile.mkdtemp()
        # os.chdir(cls.t)
        yaml.safe_dump(correct_specification, open(cls.path_to_specification, "w"))

        # Load the config
        cls.config_loader = ConfigLoader("protocol-specification_schema.json", ProtocolSpecification)
        cls.protocol_specification = cls.config_loader.load(open(cls.path_to_specification))

        # Generate the protocol
        cls.protocol_generator = ProtocolGenerator(cls.protocol_specification, cls.cwd)
        cls.protocol_generator.generate()
        # import pdb;pdb.set_trace()

    def test_exit_code_equal_to_0(self):
        """Test that the exit code is equal to 0."""
        from two_party_negotiation.message import TwoPartyNegotiationMessage
        from two_party_negotiation.serialization import TwoPartyNegotiationSerializer
        from two_party_negotiation.message import DataModel
        assert 0 == 0

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        # os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.path_to_protocol)
            os.remove(cls.path_to_specification)
        except (OSError, IOError):
            pass

# class TestCases(TestCase):
#     """Test class for the light protocol generator."""
#
#     def test_all_custom_data_types(self):
#         """Test all custom data types."""
#         test_protocol_specification_path = os.path.join(CUR_PATH, "data", "all_custom.yaml")
#         test_protocol_template = ProtocolTemplate(test_protocol_specification_path)
#         test_protocol_template.load()
#         test_protocol_generator = ProtocolGenerator(test_protocol_template, 'tests')
#         test_protocol_generator.generate()
#
#         from two_party_negotiation_protocol.message import TwoPartyNegotiationMessage
#         from two_party_negotiation_protocol.serialization import TwoPartyNegotiationSerializer
#         from two_party_negotiation_protocol.message import DataModel
#         from two_party_negotiation_protocol.message import Signature
#
#         data_model = DataModel()
#         signature = Signature()
#         content_list = [data_model, signature]
#
#         message = TwoPartyNegotiationMessage(message_id=5, target=4, performative="propose", contents=content_list)
#         print(str.format("message is {}", message))
#         message.check_consistency()
#         serialized_message = TwoPartyNegotiationSerializer().encode(msg=message)
#         print(str.format("serialized message is {}", serialized_message))
#         deserialised_message = TwoPartyNegotiationSerializer().decode(obj=serialized_message)
#         print(str.format("deserialized message is {}", deserialised_message))
#
#         assert message == deserialised_message, "Failure"
#
#     def test_correct_functionality(self):
#         """End to end test of functionality."""
#         test_protocol_specification_path = os.path.join(CUR_PATH, "data", "correct_spec.yaml")
#         test_protocol_template = ProtocolTemplate(test_protocol_specification_path)
#         test_protocol_template.load()
#         test_protocol_generator = ProtocolGenerator(test_protocol_template, 'tests')
#         test_protocol_generator.generate()
#
#         from two_party_negotiation_protocol.message import TwoPartyNegotiationMessage
#         from two_party_negotiation_protocol.serialization import TwoPartyNegotiationSerializer
#         from two_party_negotiation_protocol.message import DataModel
#
#         data_model = DataModel()
#         content_list = [data_model, 10.5]
#
#         message = TwoPartyNegotiationMessage(message_id=5, target=4, performative="propose", contents=content_list)
#         print(str.format("message is {}", message))
#         message.check_consistency()
#         serialized_message = TwoPartyNegotiationSerializer().encode(msg=message)
#         print(str.format("serialized message is {}", serialized_message))
#         deserialised_message = TwoPartyNegotiationSerializer().decode(obj=serialized_message)
#         print(str.format("deserialized message is {}", deserialised_message))
#
#         assert message == deserialised_message, "Failure"
#
#     def test_missing_name(self):
#         """Test missing name handling."""
#         test_protocol_specification_path = os.path.join(CUR_PATH, "data", "missing_name.yaml")
#         test_protocol_template = ProtocolTemplate(test_protocol_specification_path)
#
#         self.assertRaises(ProtocolSpecificationParseError, test_protocol_template.load)
#
#     def test_missing_description(self):
#         """Test missing description handling."""
#         test_protocol_specification_path = os.path.join(CUR_PATH, "data", "missing_description.yaml")
#         test_protocol_template = ProtocolTemplate(test_protocol_specification_path)
#
#         assert test_protocol_template.load(), "Failure"
#
#     def test_missing_speech_acts(self):
#         """Test missing speech acts handling."""
#         test_protocol_specification_path = os.path.join(CUR_PATH, "data", "missing_speech_acts.yaml")
#         test_protocol_template = ProtocolTemplate(test_protocol_specification_path)
#
#         self.assertRaises(ProtocolSpecificationParseError, test_protocol_template.load)
#
#     def test_extra_fields(self):
#         """Test extra fields handling."""
#         test_protocol_specification_path = os.path.join(CUR_PATH, "data", "extra_fields.yaml")
#         test_protocol_template = ProtocolTemplate(test_protocol_specification_path)
#
#         assert test_protocol_template.load(), "Failure"
#
#     def test_one_document(self):
#         """Test one document handling."""
#         test_protocol_specification_path = os.path.join(CUR_PATH, "data", "one_document.yaml")
#         test_protocol_template = ProtocolTemplate(test_protocol_specification_path)
#
#         self.assertRaises(ProtocolSpecificationParseError, test_protocol_template.load)
#
#     def test_wrong_speech_act_type_sequence_performatives(self):
#         """Test wrong speech act handling."""
#         test_protocol_specification_path = os.path.join(CUR_PATH, "data", "wrong_speech_act_type_sequence_performatives.yaml")
#         test_protocol_template = ProtocolTemplate(test_protocol_specification_path)
#
#         self.assertRaises(ProtocolSpecificationParseError, test_protocol_template.load)
#
#     def test_wrong_speech_act_type_dictionary_contents(self):
#         """Test wrong speech act dictionary contents handling."""
#         test_protocol_specification_path = os.path.join(CUR_PATH, "data", "wrong_speech_act_type_dictionary_contents.yaml")
#         test_protocol_template = ProtocolTemplate(test_protocol_specification_path)
#
#         self.assertRaises(ProtocolSpecificationParseError, test_protocol_template.load)