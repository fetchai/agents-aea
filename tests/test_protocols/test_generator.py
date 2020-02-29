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
import os
from unittest import TestCase, mock

from aea.protocols.generator import (
    ProtocolGenerator,
    _specification_type_to_python_type,
    _union_sub_type_to_protobuf_variable_name,
)


CUR_PATH = os.path.dirname(inspect.getfile(inspect.currentframe()))  # type: ignore


class SpecificationTypeToPythonTypeTestCase(TestCase):
    """Test case for _specification_type_to_python_type method."""

    def test__specification_type_to_python_type_unsupported_type(self):
        """Test _specification_type_to_python_type method unsupported type."""
        with self.assertRaises(TypeError):
            _specification_type_to_python_type("unsupported_type")


@mock.patch(
    "aea.protocols.generator._get_sub_types_of_compositional_types", return_value=[1, 2]
)
class UnionSubTypeToProtobufVariableNameTestCase(TestCase):
    """Test case for _union_sub_type_to_protobuf_variable_name method."""

    def test__union_sub_type_to_protobuf_variable_name_tuple(self, mock):
        """Test _union_sub_type_to_protobuf_variable_name method tuple."""
        _union_sub_type_to_protobuf_variable_name("content_name", "Tuple")
        mock.assert_called_once()


class ProtocolGeneratorTestCase(TestCase):
    """Test case for ProtocolGenerator class."""

    def setUp(self):
        protocol_specification = mock.Mock()
        protocol_specification.name = "name"
        ProtocolGenerator._setup = mock.Mock()
        self.protocol_generator = ProtocolGenerator(protocol_specification)

    def test__custom_types_classes_str_positive(self):
        """Test _custom_types_classes_str method positive result."""
        self.protocol_generator._custom_types_classes_str()

    @mock.patch(
        "aea.protocols.generator._get_sub_types_of_compositional_types",
        return_value=["Tuple"],
    )
    def test__includes_custom_type_positive(self, *mocks):
        """Test _includes_custom_type method positive result."""
        pass  # TODO: finish this test

    @mock.patch("aea.protocols.generator.get_indent_str")
    @mock.patch(
        "aea.protocols.generator._get_sub_types_of_compositional_types",
        return_value=["Tuple", "FrozenSet"],
    )
    def test__check_content_type_str_tuple(self, *mocks):
        """Test _check_content_type_str method tuple."""
        no_of_indents = 1
        content_name = "name"
        content_type = (
            "Union[str, Dict[str, int], FrozenSet[DataModel, int], Dict[str, float]]"
        )
        self.protocol_generator._check_content_type_str(
            no_of_indents, content_name, content_type
        )
        # TODO: finish this test
