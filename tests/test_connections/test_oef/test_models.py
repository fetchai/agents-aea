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

"""This test module contains the tests for the OEF models."""
import pickle

import pytest

from aea.connections.oef.connection import OEFObjectTranslator
from aea.protocols.oef.models import Attribute, DataModel, Description, Query, And, Or, Not, Constraint, ConstraintType


class TestTranslator:
    """Test that the translation of the OEF classes from and to the SDK classes works correctly."""

    def test_attribute(self):
        """Test that the translation for the Attribute class works."""
        attribute = Attribute("foo", int, True, "a foo attribute.")
        oef_attribute = OEFObjectTranslator.to_oef_attribute(attribute)
        expected_attribute = OEFObjectTranslator.from_oef_attribute(oef_attribute)
        actual_attribute = attribute
        assert expected_attribute == actual_attribute

    def test_data_model(self):
        """Test that the translation for the DataModel class works."""
        attribute_foo = Attribute("foo", int, True, "a foo attribute.")
        attribute_bar = Attribute("bar", str, True, "a bar attribute.")
        data_model_foobar = DataModel("foobar", [attribute_foo, attribute_bar], "A foobar data model.")
        oef_data_model = OEFObjectTranslator.to_oef_data_model(data_model_foobar)
        expected_data_model = OEFObjectTranslator.from_oef_data_model(oef_data_model)
        actual_data_model = data_model_foobar
        assert expected_data_model == actual_data_model

    def test_description(self):
        """Test that the translation for the Description class works."""
        attribute_foo = Attribute("foo", int, True, "a foo attribute.")
        attribute_bar = Attribute("bar", str, True, "a bar attribute.")
        data_model_foobar = DataModel("foobar", [attribute_foo, attribute_bar], "A foobar data model.")
        description_foobar = Description({"foo": 1, "bar": "baz"}, data_model=data_model_foobar)
        oef_description = OEFObjectTranslator.to_oef_description(description_foobar)
        expected_description = OEFObjectTranslator.from_oef_description(oef_description)
        actual_description = description_foobar
        assert expected_description == actual_description

    def test_query(self):
        """Test that the translation for the Query class works."""
        attribute_foo = Attribute("foo", int, True, "a foo attribute.")
        attribute_bar = Attribute("bar", str, True, "a bar attribute.")
        data_model_foobar = DataModel("foobar", [attribute_foo, attribute_bar], "A foobar data model.")

        query = Query([
            And([
                Or([
                    Not(Constraint("foo", ConstraintType("==", 1))),
                    Not(Constraint("bar", ConstraintType("==", "baz")))
                ]),
                Constraint("foo", ConstraintType("<", 2)),
            ])
        ], data_model_foobar)

        oef_query = OEFObjectTranslator.to_oef_query(query)
        expected_query = OEFObjectTranslator.from_oef_query(oef_query)
        actual_query = query
        assert expected_query == actual_query


class TestPickable:
    """Test that the OEF objects can be pickled."""

    def test_pickable_attribute(self):
        """Test that an istance of the Attribute class is pickable."""
        attribute_foo = Attribute("foo", int, True, "a foo attribute.")
        try:
            pickle.dumps(attribute_foo)
        except Exception:
            pytest.fail("Error during pickling.")

    def test_pickable_data_model(self):
        """Test that an istance of the DataModel class is pickable."""
        attribute_foo = Attribute("foo", int, True, "a foo attribute.")
        attribute_bar = Attribute("bar", str, True, "a bar attribute.")
        data_model_foobar = DataModel("foobar", [attribute_foo, attribute_bar], "A foobar data model.")
        try:
            pickle.dumps(data_model_foobar)
        except Exception:
            pytest.fail("Error during pickling.")

    def test_pickable_description(self):
        """Test that an istance of the Description class is pickable."""
        attribute_foo = Attribute("foo", int, True, "a foo attribute.")
        attribute_bar = Attribute("bar", str, True, "a bar attribute.")
        data_model_foobar = DataModel("foobar", [attribute_foo, attribute_bar], "A foobar data model.")
        description_foobar = Description({"foo": 1, "bar": "baz"}, data_model=data_model_foobar)
        try:
            pickle.dumps(description_foobar)
        except Exception:
            pytest.fail("Error during pickling.")

    def test_pickable_query(self):
        """Test that an istance of the Query class is pickable."""
        attribute_foo = Attribute("foo", int, True, "a foo attribute.")
        attribute_bar = Attribute("bar", str, True, "a bar attribute.")
        data_model_foobar = DataModel("foobar", [attribute_foo, attribute_bar], "A foobar data model.")

        query = Query([
            And([
                Or([
                    Not(Constraint("foo", ConstraintType("==", 1))),
                    Not(Constraint("bar", ConstraintType("==", "baz")))
                ]),
                Constraint("foo", ConstraintType("<", 2)),
            ])
        ],
            data_model_foobar)
        try:
            pickle.dumps(query)
        except Exception:
            pytest.fail("Error during pickling.")
