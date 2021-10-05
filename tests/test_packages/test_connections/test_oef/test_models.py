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

import pickle  # nosec
from unittest import mock

import pytest

from aea.helpers.search.models import (
    And,
    Attribute,
    Constraint,
    ConstraintType,
    DataModel,
    Description,
    Location,
    Not,
    Or,
    Query,
)

from packages.fetchai.connections.oef.connection import OEFObjectTranslator


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
        data_model_foobar = DataModel(
            "foobar", [attribute_foo, attribute_bar], "A foobar data model."
        )
        oef_data_model = OEFObjectTranslator.to_oef_data_model(data_model_foobar)
        expected_data_model = OEFObjectTranslator.from_oef_data_model(oef_data_model)
        actual_data_model = data_model_foobar
        assert expected_data_model == actual_data_model

    def test_description(self):
        """Test that the translation for the Description class works."""
        attribute_foo = Attribute("foo", int, True, "a foo attribute.")
        attribute_bar = Attribute("bar", str, True, "a bar attribute.")
        data_model_foobar = DataModel(
            "foobar", [attribute_foo, attribute_bar], "A foobar data model."
        )
        description_foobar = Description(
            {"foo": 1, "bar": "baz"}, data_model=data_model_foobar
        )
        oef_description = OEFObjectTranslator.to_oef_description(description_foobar)
        expected_description = OEFObjectTranslator.from_oef_description(oef_description)
        actual_description = description_foobar
        assert expected_description == actual_description
        m_desc = iter(description_foobar.values)
        assert next(m_desc) == "foo"
        assert {"foo", "bar"} == set(iter(description_foobar))

    def test_query(self):
        """Test that the translation for the Query class works."""
        attribute_foo = Attribute("foo", int, True, "a foo attribute.")
        attribute_bar = Attribute("bar", str, True, "a bar attribute.")
        data_model_foobar = DataModel(
            "foobar", [attribute_foo, attribute_bar], "A foobar data model."
        )

        query = Query(
            [
                And(
                    [
                        Or(
                            [
                                Not(Constraint("foo", ConstraintType("==", 1))),
                                Not(Constraint("bar", ConstraintType("==", "baz"))),
                            ]
                        ),
                        Constraint("foo", ConstraintType("<", 2)),
                    ]
                )
            ],
            data_model_foobar,
        )

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
        data_model_foobar = DataModel(
            "foobar", [attribute_foo, attribute_bar], "A foobar data model."
        )
        try:
            pickle.dumps(data_model_foobar)
        except Exception:
            pytest.fail("Error during pickling.")

    def test_pickable_description(self):
        """Test that an istance of the Description class is pickable."""
        attribute_foo = Attribute("foo", int, True, "a foo attribute.")
        attribute_bar = Attribute("bar", str, True, "a bar attribute.")
        data_model_foobar = DataModel(
            "foobar", [attribute_foo, attribute_bar], "A foobar data model."
        )
        description_foobar = Description(
            {"foo": 1, "bar": "baz"}, data_model=data_model_foobar
        )
        try:
            pickle.dumps(description_foobar)
        except Exception:
            pytest.fail("Error during pickling.")

    def test_pickable_query(self):
        """Test that an istance of the Query class is pickable."""
        attribute_foo = Attribute("foo", int, True, "a foo attribute.")
        attribute_bar = Attribute("bar", str, True, "a bar attribute.")
        data_model_foobar = DataModel(
            "foobar", [attribute_foo, attribute_bar], "A foobar data model."
        )

        query = Query(
            [
                And(
                    [
                        Or(
                            [
                                Not(Constraint("foo", ConstraintType("==", 1))),
                                Not(Constraint("bar", ConstraintType("==", "baz"))),
                            ]
                        ),
                        Constraint("foo", ConstraintType("<", 2)),
                    ]
                )
            ],
            data_model_foobar,
        )
        try:
            pickle.dumps(query)
        except Exception:
            pytest.fail("Error during pickling.")


class TestCheckValidity:
    """Test the initialization of the Constraint type."""

    def test_validity(self):
        """Test the validity of the Constraint type."""
        m_constraint = ConstraintType("==", 3)
        assert m_constraint.check(3)
        assert str(m_constraint.type) == "=="
        m_constraint = ConstraintType("!=", "London")
        assert m_constraint.check("Paris")
        assert str(m_constraint.type) == "!="
        m_constraint = ConstraintType("<", 3.14)
        assert m_constraint.check(3.0)
        assert str(m_constraint.type) == "<"
        m_constraint = ConstraintType(">", 3.14)
        assert m_constraint.check(5.0)
        assert str(m_constraint.type) == ">"
        m_constraint = ConstraintType("<=", 5)
        assert m_constraint.check(5)
        assert str(m_constraint.type) == "<="
        m_constraint = ConstraintType(">=", 5)
        assert m_constraint.check(5)
        assert str(m_constraint.type) == ">="
        m_constraint = ConstraintType("within", (-10.0, 10.0))
        assert m_constraint.check(5)
        assert str(m_constraint.type) == "within"
        m_constraint = ConstraintType("in", (1, 2, 3))
        assert m_constraint.check(2)
        assert str(m_constraint.type) == "in"
        m_constraint = ConstraintType("not_in", ("C", "Java", "Python"))
        assert m_constraint.check("C++")
        assert str(m_constraint.type) == "not_in"

        tour_eiffel = Location(48.8581064, 2.29447)
        colosseum = Location(41.8902102, 12.4922309)
        le_jules_verne_restaurant = Location(48.8579675, 2.2951849)
        m_constraint = ConstraintType("distance", (tour_eiffel, 1.0))
        assert m_constraint.check(tour_eiffel)
        assert m_constraint.check(le_jules_verne_restaurant)
        assert not m_constraint.check(colosseum)

        m_constraint.type = "unknown"
        with pytest.raises(ValueError):
            m_constraint.check("HelloWorld")

        m_constraint = ConstraintType("==", 3)
        with mock.patch("aea.helpers.search.models.ConstraintTypes") as mocked_types:
            mocked_types.EQUAL.value = "unknown"
            assert not m_constraint.check_validity(), "My constraint must not be valid"

    def test_not_check(self):
        """Test the not().check function."""
        attribute_foo = Attribute("foo", int, True, "a foo attribute.")
        attribute_bar = Attribute("bar", str, True, "a bar attribute.")
        data_model_foobar = DataModel(
            "foobar", [attribute_foo, attribute_bar], "A foobar data model."
        )
        description_foobar = Description(
            {"foo": 1, "bar": "baz"}, data_model=data_model_foobar
        )

        no_constraint_1 = Not(Constraint("foo", ConstraintType("==", 5)))
        assert no_constraint_1.check(description_foobar)

        no_constraint_2 = Not(Constraint("bar", ConstraintType("==", "hi")))
        assert no_constraint_2.check(description_foobar)

        no_constraint_3 = Not(Constraint("foo", ConstraintType("==", 1)))
        assert not no_constraint_3.check(description_foobar)

        no_constraint_4 = Not(Constraint("bar", ConstraintType("==", "baz")))
        assert not no_constraint_4.check(description_foobar)

        no_constraint_5 = Constraint("foo", ConstraintType("!=", 98273))
        assert no_constraint_5.check(description_foobar)

        no_constraint_6 = Constraint("bar", ConstraintType("!=", "hello_again"))
        assert no_constraint_6.check(description_foobar)

        no_constraint_7 = Constraint("foo", ConstraintType("!=", 1))
        assert not no_constraint_7.check(description_foobar)

        no_constraint_8 = Constraint("bar", ConstraintType("!=", "baz"))
        assert not no_constraint_8.check(description_foobar)

    def test_or_check(self):
        """Test the or().check function."""
        attribute_foo = Attribute("foo", int, True, "a foo attribute.")
        attribute_bar = Attribute("bar", str, True, "a bar attribute.")
        data_model_foobar = DataModel(
            "foobar", [attribute_foo, attribute_bar], "A foobar data model."
        )
        description_foobar = Description(
            {"foo": 1, "bar": "baz"}, data_model=data_model_foobar
        )
        constraint = Or(
            [
                (Constraint("foo", ConstraintType("==", 1))),
                (Constraint("bar", ConstraintType("==", "baz"))),
            ]
        )
        assert constraint.check(description_foobar)

    def test_and_check(self):
        """Test the and().check function."""
        attribute_foo = Attribute("foo", int, True, "a foo attribute.")
        attribute_bar = Attribute("bar", str, True, "a bar attribute.")
        data_model_foobar = DataModel(
            "foobar", [attribute_foo, attribute_bar], "A foobar data model."
        )
        description_foobar = Description(
            {"foo": 1, "bar": "baz"}, data_model=data_model_foobar
        )
        constraint = And(
            [
                (Constraint("foo", ConstraintType("==", 1))),
                (Constraint("bar", ConstraintType("==", "baz"))),
            ]
        )
        assert constraint.check(description_foobar)

    def test_query_check(self):
        """Test that the query.check() method works."""
        attribute_foo = Attribute("foo", int, True, "a foo attribute.")
        attribute_bar = Attribute("bar", str, True, "a bar attribute.")
        data_model_foobar = DataModel(
            "foobar", [attribute_foo, attribute_bar], "A foobar data model."
        )
        description_foobar = Description(
            {"foo": 1, "bar": "baz"}, data_model=data_model_foobar
        )
        query = Query(
            [
                And(
                    [
                        Or(
                            [
                                Not(Constraint("foo", ConstraintType("==", 1))),
                                Not(Constraint("bar", ConstraintType("==", "baz"))),
                            ]
                        ),
                        Constraint("foo", ConstraintType("<", 2)),
                    ]
                )
            ],
            data_model_foobar,
        )
        assert not query.check(description=description_foobar)
