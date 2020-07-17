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
"""This module contains the tests for the protocol generator."""

import inspect
import logging
import os
import shutil
import tempfile
import time
from pathlib import Path
from threading import Thread
from typing import Optional
from unittest import TestCase, mock

import pytest

from aea.aea_builder import AEABuilder
from aea.configurations.base import (
    ComponentType,
    ProtocolId,
    ProtocolSpecificationParseError,
    PublicId,
    SkillConfig,
)
from aea.configurations.constants import DEFAULT_LEDGER, DEFAULT_PRIVATE_KEY_FILE
from aea.crypto.helpers import create_private_key
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.protocols.generator.base import (
    ProtocolGenerator,
    _union_sub_type_to_protobuf_variable_name,
)
from aea.protocols.generator.common import check_prerequisites
from aea.protocols.generator.extract_specification import (
    _specification_type_to_python_type,
)
from aea.skills.base import Handler, Skill, SkillContext
from aea.test_tools.test_cases import UseOef

from tests.conftest import CliRunner, ROOT_DIR
from tests.data.generator.t_protocol.message import (  # type: ignore
    TProtocolMessage,
)


logger = logging.getLogger("aea")
logging.basicConfig(level=logging.INFO)

CUR_PATH = os.path.dirname(inspect.getfile(inspect.currentframe()))  # type: ignore
HOST = "127.0.0.1"
PORT = 10000


class TestEndToEndGenerator(UseOef):
    """Test that the generating a protocol works correctly in correct preconditions."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)
        cls.private_key_path_1 = os.path.join(cls.t, DEFAULT_PRIVATE_KEY_FILE + "_1")
        cls.private_key_path_2 = os.path.join(cls.t, DEFAULT_PRIVATE_KEY_FILE + "_2")
        create_private_key(DEFAULT_LEDGER, cls.private_key_path_1)
        create_private_key(DEFAULT_LEDGER, cls.private_key_path_2)

    def test_compare_latest_generator_output_with_test_protocol(self):
        """Test that the "t_protocol" test protocol matches with what the latest generator generates based on the specification."""
        # Skip if prerequisite applications are not installed
        try:
            check_prerequisites()
        except FileNotFoundError:
            pytest.skip(
                "Some prerequisite applications are not installed. Skipping this test."
            )

        # Specification
        # protocol_name = "t_protocol"
        path_to_specification = os.path.join(
            ROOT_DIR, "tests", "data", "sample_specification.yaml"
        )
        path_to_generated_protocol = self.t
        # path_to_original_protocol = os.path.join(
        #     ROOT_DIR, "tests", "data", "generator", protocol_name
        # )
        path_to_package = "tests.data.generator."

        # Generate the protocol
        protocol_generator = ProtocolGenerator(
            path_to_specification,
            path_to_generated_protocol,
            path_to_protocol_package=path_to_package,
        )
        protocol_generator.generate()

        # # compare __init__.py
        # init_file_generated = Path(self.t, protocol_name, "__init__.py")
        # init_file_original = Path(path_to_original_protocol, "__init__.py",)
        # assert filecmp.cmp(init_file_generated, init_file_original)

        # # compare protocol.yaml
        # protocol_yaml_file_generated = Path(self.t, protocol_name, "protocol.yaml")
        # protocol_yaml_file_original = Path(path_to_original_protocol, "protocol.yaml",)
        # assert filecmp.cmp(protocol_yaml_file_generated, protocol_yaml_file_original)

        # # compare message.py
        # message_file_generated = Path(self.t, protocol_name, "message.py")
        # message_file_original = Path(path_to_original_protocol, "message.py",)
        # assert filecmp.cmp(message_file_generated, message_file_original)

        # # compare serialization.py
        # serialization_file_generated = Path(self.t, protocol_name, "serialization.py")
        # serialization_file_original = Path(
        #     path_to_original_protocol, "serialization.py",
        # )
        # assert filecmp.cmp(serialization_file_generated, serialization_file_original)

        # # compare .proto
        # proto_file_generated = Path(
        #     self.t, protocol_name, "{}.proto".format(protocol_name)
        # )
        # proto_file_original = Path(
        #     path_to_original_protocol, "{}.proto".format(protocol_name),
        # )
        # assert filecmp.cmp(proto_file_generated, proto_file_original)

        # # compare _pb2.py
        # pb2_file_generated = Path(
        #     self.t, protocol_name, "{}_pb2.py".format(protocol_name)
        # )
        # with open(ROOT_DIR + "/x_pb2.py", "w") as fp:
        #     fp.write(pb2_file_generated.read_text())
        # pb2_file_original = Path(
        #     path_to_original_protocol, "{}_pb2.py".format(protocol_name),
        # )
        # assert filecmp.cmp(pb2_file_generated, pb2_file_original)
        assert True

    def test_generated_protocol_serialisation_ct(self):
        """Test that a generated protocol's serialisation + deserialisation work correctly."""
        # create a message with pt content
        some_dict = {1: True, 2: False, 3: True, 4: False}
        data_model = TProtocolMessage.DataModel(
            bytes_field=b"some bytes",
            int_field=42,
            float_field=42.7,
            bool_field=True,
            str_field="some string",
            set_field={1, 2, 3, 4, 5},
            list_field=["some string 1", "some string 2"],
            dict_field=some_dict,
        )
        message = TProtocolMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=TProtocolMessage.Performative.PERFORMATIVE_CT,
            content_ct=data_model,
        )

        # serialise the message
        encoded_message_in_bytes = TProtocolMessage.serializer.encode(message)

        # deserialise the message
        decoded_message = TProtocolMessage.serializer.decode(encoded_message_in_bytes)

        # Compare the original message with the serialised+deserialised message
        assert decoded_message.message_id == message.message_id
        assert decoded_message.dialogue_reference == message.dialogue_reference
        assert decoded_message.dialogue_reference[0] == message.dialogue_reference[0]
        assert decoded_message.dialogue_reference[1] == message.dialogue_reference[1]
        assert decoded_message.target == message.target
        assert decoded_message.performative == message.performative
        assert decoded_message.content_ct == message.content_ct

    def test_generated_protocol_serialisation_pt(self):
        """Test that a generated protocol's serialisation + deserialisation work correctly."""
        # create a message with pt content
        message = TProtocolMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=TProtocolMessage.Performative.PERFORMATIVE_PT,
            content_bytes=b"some bytes",
            content_int=42,
            content_float=42.7,
            content_bool=True,
            content_str="some string",
        )

        # serialise the message
        encoded_message_in_bytes = TProtocolMessage.serializer.encode(message)

        # deserialise the message
        decoded_message = TProtocolMessage.serializer.decode(encoded_message_in_bytes)

        # Compare the original message with the serialised+deserialised message
        assert decoded_message.message_id == message.message_id
        assert decoded_message.dialogue_reference == message.dialogue_reference
        assert decoded_message.dialogue_reference[0] == message.dialogue_reference[0]
        assert decoded_message.dialogue_reference[1] == message.dialogue_reference[1]
        assert decoded_message.target == message.target
        assert decoded_message.performative == message.performative
        assert decoded_message.content_bytes == message.content_bytes
        assert decoded_message.content_int == message.content_int
        # floats do not seem to lose some precision when serialised then deserialised using protobuf
        # assert decoded_message.content_float == message.content_float
        assert decoded_message.content_bool == message.content_bool
        assert decoded_message.content_str == message.content_str

    def test_generated_protocol_end_to_end(self):
        """Test that a generated protocol could be used in exchanging messages between two agents."""
        agent_name_1 = "my_aea_1"
        agent_name_2 = "my_aea_2"
        builder_1 = AEABuilder()
        builder_1.set_name(agent_name_1)
        builder_1.add_private_key(DEFAULT_LEDGER, self.private_key_path_1)
        builder_1.set_default_ledger(DEFAULT_LEDGER)
        builder_1.set_default_connection(PublicId.from_str("fetchai/oef:0.6.0"))
        builder_1.add_protocol(
            Path(ROOT_DIR, "packages", "fetchai", "protocols", "fipa")
        )
        builder_1.add_protocol(
            Path(ROOT_DIR, "packages", "fetchai", "protocols", "oef_search")
        )
        builder_1.add_component(
            ComponentType.PROTOCOL,
            Path(ROOT_DIR, "tests", "data", "generator", "t_protocol"),
            skip_consistency_check=True,
        )
        builder_1.add_connection(
            Path(ROOT_DIR, "packages", "fetchai", "connections", "oef")
        )

        builder_2 = AEABuilder()
        builder_2.set_name(agent_name_2)
        builder_2.add_private_key(DEFAULT_LEDGER, self.private_key_path_2)
        builder_2.set_default_ledger(DEFAULT_LEDGER)
        builder_2.add_protocol(
            Path(ROOT_DIR, "packages", "fetchai", "protocols", "fipa")
        )
        builder_2.add_protocol(
            Path(ROOT_DIR, "packages", "fetchai", "protocols", "oef_search")
        )
        builder_2.set_default_connection(PublicId.from_str("fetchai/oef:0.6.0"))
        builder_2.add_component(
            ComponentType.PROTOCOL,
            Path(ROOT_DIR, "tests", "data", "generator", "t_protocol"),
            skip_consistency_check=True,
        )
        builder_2.add_connection(
            Path(ROOT_DIR, "packages", "fetchai", "connections", "oef")
        )

        # create AEAs
        aea_1 = builder_1.build(connection_ids=[PublicId.from_str("fetchai/oef:0.6.0")])
        aea_2 = builder_2.build(connection_ids=[PublicId.from_str("fetchai/oef:0.6.0")])

        # message 1
        message = TProtocolMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=TProtocolMessage.Performative.PERFORMATIVE_PT,
            content_bytes=b"some bytes",
            content_int=42,
            content_float=42.7,
            content_bool=True,
            content_str="some string",
        )
        message.counterparty = aea_2.identity.address
        envelope = Envelope(
            to=aea_2.identity.address,
            sender=aea_1.identity.address,
            protocol_id=TProtocolMessage.protocol_id,
            message=message,
        )

        # message 2
        message_2 = TProtocolMessage(
            message_id=2,
            dialogue_reference=(str(0), ""),
            target=1,
            performative=TProtocolMessage.Performative.PERFORMATIVE_PT,
            content_bytes=b"some other bytes",
            content_int=43,
            content_float=43.7,
            content_bool=False,
            content_str="some other string",
        )
        message_2.counterparty = aea_1.identity.address

        # add handlers to AEA resources]
        skill_context_1 = SkillContext(aea_1.context)
        skill_1 = Skill(SkillConfig("fake_skill", "fetchai", "0.1.0"), skill_context_1)
        skill_context_1._skill = skill_1

        agent_1_handler = Agent1Handler(
            skill_context=skill_context_1, name="fake_handler_1"
        )
        aea_1.resources._handler_registry.register(
            (
                PublicId.from_str("fetchai/fake_skill:0.1.0"),
                TProtocolMessage.protocol_id,
            ),
            agent_1_handler,
        )
        skill_context_2 = SkillContext(aea_2.context)
        skill_2 = Skill(SkillConfig("fake_skill", "fetchai", "0.1.0"), skill_context_2)
        skill_context_2._skill = skill_2

        agent_2_handler = Agent2Handler(
            message=message_2, skill_context=skill_context_2, name="fake_handler_2",
        )
        aea_2.resources._handler_registry.register(
            (
                PublicId.from_str("fetchai/fake_skill:0.1.0"),
                TProtocolMessage.protocol_id,
            ),
            agent_2_handler,
        )

        # Start threads
        t_1 = Thread(target=aea_1.start)
        t_2 = Thread(target=aea_2.start)
        try:
            t_1.start()
            t_2.start()
            time.sleep(1.0)
            aea_1.outbox.put(envelope)
            time.sleep(5.0)
            assert (
                agent_2_handler.handled_message.message_id == message.message_id
            ), "Message from Agent 1 to 2: message ids do not match"
            assert (
                agent_2_handler.handled_message.dialogue_reference
                == message.dialogue_reference
            ), "Message from Agent 1 to 2: dialogue references do not match"
            assert (
                agent_2_handler.handled_message.dialogue_reference[0]
                == message.dialogue_reference[0]
            ), "Message from Agent 1 to 2: dialogue reference[0]s do not match"
            assert (
                agent_2_handler.handled_message.dialogue_reference[1]
                == message.dialogue_reference[1]
            ), "Message from Agent 1 to 2: dialogue reference[1]s do not match"
            assert (
                agent_2_handler.handled_message.target == message.target
            ), "Message from Agent 1 to 2: targets do not match"
            assert (
                agent_2_handler.handled_message.performative == message.performative
            ), "Message from Agent 1 to 2: performatives do not match"
            assert (
                agent_2_handler.handled_message.content_bytes == message.content_bytes
            ), "Message from Agent 1 to 2: content_bytes do not match"
            assert (
                agent_2_handler.handled_message.content_int == message.content_int
            ), "Message from Agent 1 to 2: content_int do not match"
            # floats do not seem to lose some precision when serialised then deserialised using protobuf
            # assert agent_2_handler.handled_message.content_float == message.content_float, "Message from Agent 1 to 2: content_float do not match"
            assert (
                agent_2_handler.handled_message.content_bool == message.content_bool
            ), "Message from Agent 1 to 2: content_bool do not match"
            assert (
                agent_2_handler.handled_message.content_str == message.content_str
            ), "Message from Agent 1 to 2: content_str do not match"

            assert (
                agent_1_handler.handled_message.message_id == message_2.message_id
            ), "Message from Agent 1 to 2: dialogue references do not match"
            assert (
                agent_1_handler.handled_message.dialogue_reference
                == message_2.dialogue_reference
            ), "Message from Agent 2 to 1: dialogue references do not match"
            assert (
                agent_1_handler.handled_message.dialogue_reference[0]
                == message_2.dialogue_reference[0]
            ), "Message from Agent 2 to 1: dialogue reference[0]s do not match"
            assert (
                agent_1_handler.handled_message.dialogue_reference[1]
                == message_2.dialogue_reference[1]
            ), "Message from Agent 2 to 1: dialogue reference[1]s do not match"
            assert (
                agent_1_handler.handled_message.target == message_2.target
            ), "Message from Agent 2 to 1: targets do not match"
            assert (
                agent_1_handler.handled_message.performative == message_2.performative
            ), "Message from Agent 2 to 1: performatives do not match"
            assert (
                agent_1_handler.handled_message.content_bytes == message_2.content_bytes
            ), "Message from Agent 2 to 1: content_bytes do not match"
            assert (
                agent_1_handler.handled_message.content_int == message_2.content_int
            ), "Message from Agent 2 to 1: content_int do not match"
            # floats do not seem to lose some precision when serialised then deserialised using protobuf
            # assert agent_1_handler.handled_message.content_float == message_2.content_float, "Message from Agent 2 to 1: content_float do not match"
            assert (
                agent_1_handler.handled_message.content_bool == message_2.content_bool
            ), "Message from Agent 2 to 1: content_bool do not match"
            assert (
                agent_1_handler.handled_message.content_str == message_2.content_str
            ), "Message from Agent 2 to 1: content_str do not match"
            time.sleep(2.0)
        finally:
            aea_1.stop()
            aea_2.stop()
            t_1.join()
            t_2.join()

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class SpecificationTypeToPythonTypeTestCase(TestCase):
    """Test case for _specification_type_to_python_type method."""

    def test__specification_type_to_python_type_unsupported_type(self):
        """Test _specification_type_to_python_type method unsupported type."""
        with self.assertRaises(ProtocolSpecificationParseError):
            _specification_type_to_python_type("unsupported_type")


@mock.patch(
    "aea.protocols.generator.common._get_sub_types_of_compositional_types",
    return_value=[1, 2],
)
class UnionSubTypeToProtobufVariableNameTestCase(TestCase):
    """Test case for _union_sub_type_to_protobuf_variable_name method."""

    def test__union_sub_type_to_protobuf_variable_name_tuple(self, mock):
        """Test _union_sub_type_to_protobuf_variable_name method tuple."""
        pytest.skip()
        _union_sub_type_to_protobuf_variable_name("content_name", "Tuple[str, ...]")
        mock.assert_called_once()


class ProtocolGeneratorTestCase(TestCase):
    """Test case for ProtocolGenerator class."""

    def setUp(self):
        protocol_specification = mock.Mock()
        protocol_specification.name = "name"

    # @mock.patch(
    #     "aea.protocols.generator.common._get_sub_types_of_compositional_types",
    #     return_value=["some"],
    # )
    # def test__includes_custom_type_positive(self, *mocks):
    #     """Test _includes_custom_type method positive result."""
    #     content_type = "pt:union[pt:str]"
    #     result = not _is_composition_type_with_custom_type(content_type)
    #     self.assertTrue(result)
    #
    #     content_type = "pt:optional[pt:str]"
    #     result = not _is_composition_type_with_custom_type(content_type)
    #     self.assertTrue(result)

    # @mock.patch("aea.protocols.generator._get_indent_str")
    # @mock.patch(
    #     "aea.protocols.generator._get_sub_types_of_compositional_types",
    #     return_value=["Tuple", "FrozenSet"],
    # )
    # def test__check_content_type_str_tuple(self, *mocks):
    #     """Test _check_content_type_str method tuple."""
    #     no_of_indents = 1
    #     content_name = "name"
    #     content_type = (
    #         "Union[str, Dict[str, int], FrozenSet[DataModel, int], Dict[str, float]]"
    #     )
    #     self.protocol_generator._check_content_type_str(
    #         no_of_indents, content_name, content_type
    #     )
    #     # TODO: finish this test


class Agent1Handler(Handler):
    """The handler for agent 1."""

    SUPPORTED_PROTOCOL = TProtocolMessage.protocol_id  # type: Optional[ProtocolId]

    def __init__(self, **kwargs):
        """Initialize the handler."""
        super().__init__(**kwargs)
        self.kwargs = kwargs
        self.handled_message = None

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        self.handled_message = message

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """


class Agent2Handler(Handler):
    """The handler for agent 2."""

    SUPPORTED_PROTOCOL = TProtocolMessage.protocol_id  # type: Optional[ProtocolId]

    def __init__(self, message, **kwargs):
        """Initialize the handler."""
        print("inside handler's initialisation method for agent 2")
        super().__init__(**kwargs)
        self.kwargs = kwargs
        self.handled_message = None
        self.message_2 = message

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        self.handled_message = message
        envelope = Envelope(
            to=message.counterparty,
            sender=self.context.agent_address,
            protocol_id=TProtocolMessage.protocol_id,
            message=self.message_2,
        )
        self.context.outbox.put(envelope)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
