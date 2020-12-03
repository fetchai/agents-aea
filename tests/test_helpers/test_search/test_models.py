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
"""This module contains the tests for the helpers.search.models."""
import pytest

from aea.exceptions import AEAEnforceError
from aea.helpers.search.models import (
    And,
    Attribute,
    AttributeInconsistencyException,
    Constraint,
    ConstraintType,
    ConstraintTypes,
    DataModel,
    Description,
    Location,
    Not,
    Or,
    Query,
    generate_data_model,
)


def test_location():
    """Test Location type."""
    location = Location(1.1, 2.2)
    assert location is not None

    assert location.tuple == (location.latitude, location.longitude)
    assert location.distance(Location(1.1, 2.2)) == 0
    assert location == Location(1.1, 2.2)
    assert str(location) == "Location(latitude=1.1,longitude=2.2)"

    location_pb = location.encode()
    actual_location = Location.decode(location_pb)
    assert actual_location == location


def test_attribute():
    """Test data model Attribute."""
    params = dict(name="test", type_=str, is_required=True)
    attribute = Attribute(**params)
    assert attribute is not None

    assert attribute == Attribute(**params)
    assert attribute != Attribute(name="another", type_=int, is_required=True)

    assert str(attribute) == "Attribute(name=test,type=<class 'str'>,is_required=True)"

    attribute_pb = attribute.encode()
    actual_attribute = Attribute.decode(attribute_pb)
    assert actual_attribute == attribute


def test_data_model():
    """Test data model definitions."""
    params = dict(name="test", type_=str, is_required=True)
    data_model = DataModel("test", [Attribute(**params)])

    data_model._check_validity()
    with pytest.raises(
        ValueError,
        match="Invalid input value for type 'DataModel': duplicated attribute name.",
    ):
        data_model = DataModel("test", [Attribute(**params), Attribute(**params)])
        data_model._check_validity()

    assert data_model == DataModel("test", [Attribute(**params)])
    assert data_model != DataModel("not test", [Attribute(**params)])

    assert (
        str(data_model)
        == "DataModel(name=test,attributes={'test': \"Attribute(name=test,type=<class 'str'>,is_required=True)\"},description=)"
    )

    data_model_pb = data_model.encode()
    actual_data_model = DataModel.decode(data_model_pb)
    assert actual_data_model == data_model


def test_generate_data_model():
    """Test model generated from description."""
    params = dict(name="test", type_=str, is_required=True)

    data_model = DataModel("test", [Attribute(**params)])

    assert generate_data_model("test", {"test": "str"}) == data_model


def test_description():
    """Test model description."""
    values = {"test": "test"}
    description = Description(
        values=values, data_model=generate_data_model("test", values)
    )

    assert description.values == values
    assert description == Description(
        values=values, data_model=generate_data_model("test", values)
    )
    assert list(description) == list(values.values())

    with pytest.raises(
        AttributeInconsistencyException, match=r"Missing required attribute."
    ):
        Description(
            values=values, data_model=generate_data_model("test", {"extra_key": "key"})
        )
    with pytest.raises(
        AttributeInconsistencyException,
        match=r"Have extra attribute not in data model.",
    ):
        Description(values=values, data_model=generate_data_model("test", {}))
    with pytest.raises(
        AttributeInconsistencyException, match=r".* has incorrect type:.*"
    ):
        Description(values=values, data_model=generate_data_model("test", {"test": 12}))

    with pytest.raises(
        AttributeInconsistencyException, match=r".* has unallowed type:.*"
    ):
        Description(
            values={"test": object()},
            data_model=generate_data_model("test", {"test": object()}),
        )

    assert (
        str(description)
        == "Description(values={'test': 'test'},data_model=DataModel(name=test,attributes={'test': \"Attribute(name=test,type=<class 'str'>,is_required=True)\"},description=))"
    )

    description_pb = description.encode()
    actual_description = Description.decode(description_pb)
    assert actual_description == description


def test_constraint_type():
    """Test ConstraintType."""
    for cons_type in [
        ConstraintTypes.EQUAL,
        ConstraintTypes.NOT_EQUAL,
        ConstraintTypes.LESS_THAN,
        ConstraintTypes.LESS_THAN_EQ,
        ConstraintTypes.GREATER_THAN,
        ConstraintTypes.GREATER_THAN_EQ,
    ]:
        constraint_type = ConstraintType(cons_type, 12)
        constraint_type.is_valid(Attribute("test", int, True))
        constraint_type.check(13)
        assert constraint_type == ConstraintType(cons_type, 12)
        assert str(constraint_type) == f"ConstraintType(value={12},type={cons_type})"

        constraint_type_pb = constraint_type.encode()
        actual_constraint_type = ConstraintType.decode(constraint_type_pb, "relation")
        assert actual_constraint_type == constraint_type

    constraint_range = (1, 2)
    constraint_type_within = ConstraintType(ConstraintTypes.WITHIN, constraint_range)
    constraint_type_within.is_valid(Attribute("test", int, True))
    constraint_type_within.check(13)
    assert constraint_type_within == ConstraintType(
        ConstraintTypes.WITHIN, constraint_range
    )
    assert (
        str(constraint_type_within)
        == f"ConstraintType(value={constraint_range},type=within)"
    )
    constraint_type_within_pb = constraint_type_within.encode()
    actual_constraint_type_within = ConstraintType.decode(
        constraint_type_within_pb, "range"
    )
    assert actual_constraint_type_within == constraint_type_within

    constraint_set = (1, 2)
    constraint_type_in = ConstraintType(ConstraintTypes.IN, constraint_set)
    constraint_type_in.is_valid(Attribute("test", int, True))
    constraint_type_in.check(13)
    assert constraint_type_in == ConstraintType(ConstraintTypes.IN, constraint_set)
    assert str(constraint_type_in) == f"ConstraintType(value={constraint_set},type=in)"
    constraint_type_in_pb = constraint_type_in.encode()
    actual_constraint_type_in = ConstraintType.decode(constraint_type_in_pb, "set")
    assert actual_constraint_type_in == constraint_type_in

    constraint_type_not_in = ConstraintType(ConstraintTypes.NOT_IN, constraint_set)
    constraint_type_not_in.is_valid(Attribute("test", int, True))
    constraint_type_not_in.check(13)
    assert constraint_type_not_in == ConstraintType(
        ConstraintTypes.NOT_IN, constraint_set
    )
    assert (
        str(constraint_type_not_in)
        == f"ConstraintType(value={constraint_set},type=not_in)"
    )
    constraint_type_not_in_pb = constraint_type_not_in.encode()
    actual_constraint_type_not_in = ConstraintType.decode(
        constraint_type_not_in_pb, "set"
    )
    assert actual_constraint_type_not_in == constraint_type_not_in

    constraint_location = (Location(1.1, 2.2), 2.2)
    constraint_type_distance = ConstraintType(
        ConstraintTypes.DISTANCE, constraint_location
    )
    constraint_type_distance.is_valid(Attribute("test", int, True))
    constraint_type_distance.check(Location(1.1, 2.2))
    assert constraint_type_distance == ConstraintType(
        ConstraintTypes.DISTANCE, constraint_location
    )
    constraint_type_distance_pb = constraint_type_distance.encode()
    actual_constraint_type_distance = ConstraintType.decode(
        constraint_type_distance_pb, "distance"
    )
    assert actual_constraint_type_distance == constraint_type_distance

    with pytest.raises(ValueError):
        ConstraintType("something", [Location(1.1, 2.2), 2.2]).is_valid(
            Attribute("test", int, True)
        )

    with pytest.raises(AEAEnforceError, match=""):
        ConstraintType(ConstraintTypes.GREATER_THAN, str)

    list_value = [1, 2]
    set_value = {1, 2}
    list_location = [Location(1.1, 2.2), 2.2]

    with pytest.raises(
        AEAEnforceError, match=f"Expected tuple, got {type(list_value)}"
    ):
        ConstraintType(ConstraintTypes.WITHIN, list_value)

    with pytest.raises(
        AEAEnforceError, match=f"Expected tuple, got {type(list_value)}"
    ):
        ConstraintType(ConstraintTypes.IN, list_value)

    with pytest.raises(AEAEnforceError, match=f"Expected tuple, got {type(set_value)}"):
        ConstraintType(ConstraintTypes.IN, set_value)

    with pytest.raises(
        AEAEnforceError, match=f"Expected tuple, got {type(list_value)}"
    ):
        ConstraintType(ConstraintTypes.NOT_IN, list_value)

    with pytest.raises(AEAEnforceError, match=f"Expected tuple, got {type(set_value)}"):
        ConstraintType(ConstraintTypes.NOT_IN, set_value)

    with pytest.raises(
        AEAEnforceError, match=f"Expected tuple, got {type(list_location)}"
    ):
        ConstraintType(ConstraintTypes.DISTANCE, list_location)


def test_constraints_expressions():
    """Test constraint expressions: And, Or, Not."""
    and_expression = And(
        [
            Constraint("number", ConstraintType(ConstraintTypes.GREATER_THAN, 15)),
            Constraint("number", ConstraintType(ConstraintTypes.LESS_THAN, 10)),
        ]
    )
    and_expression.check_validity()
    assert and_expression.check(Description({"number": 12}))
    assert and_expression.is_valid(
        DataModel("some_name", [Attribute("number", int, True)])
    )
    and_expression_pb = and_expression.encode()
    actual_and_expression = And.decode(and_expression_pb)
    assert actual_and_expression == and_expression

    or_expression = Or(
        [
            Constraint("number", ConstraintType(ConstraintTypes.EQUAL, 12)),
            Constraint("number", ConstraintType(ConstraintTypes.EQUAL, 13)),
        ]
    )
    or_expression.check_validity()
    assert or_expression.check(Description({"number": 12}))
    assert or_expression.is_valid(
        DataModel("some_name", [Attribute("number", int, True)])
    )
    or_expression_pb = or_expression.encode()
    actual_or_expression = Or.decode(or_expression_pb)
    assert actual_or_expression == or_expression

    not_expression = Not(
        And(
            [
                Constraint("number", ConstraintType(ConstraintTypes.EQUAL, 12)),
                Constraint("number", ConstraintType(ConstraintTypes.EQUAL, 12)),
            ]
        )
    )
    not_expression.check_validity()
    assert not_expression.check(Description({"number": 13}))
    assert not_expression.is_valid(
        DataModel("some_name", [Attribute("number", int, True)])
    )
    not_expression_pb = not_expression.encode()
    actual_not_expression = Not.decode(not_expression_pb)
    assert actual_not_expression == not_expression


def test_constraint():
    """Test Constraint."""
    c1 = Constraint("author", ConstraintType("==", "Stephen King"))
    c2 = Constraint("author", ConstraintType("in", ("Stephen King",)))
    book_1 = Description({"author": "Stephen King", "year": 1991, "genre": "horror"})
    book_2 = Description({"author": "George Orwell", "year": 1948, "genre": "horror"})

    assert c1.check(book_1)
    assert not c1.check(book_2)
    # empty description
    assert not c1.check(Description({}))
    # bad type
    assert not c1.check(Description({"author": 12}))
    # bad type
    assert not c2.check(Description({"author": 12}))

    assert c1.is_valid(generate_data_model("test", {"author": "some author"}))
    assert not c1.is_valid(generate_data_model("test", {"not_author": "some author"}))

    assert c1 == c1
    assert c1 != c2

    assert (
        str(c1)
        == f"Constraint(attribute_name=author,constraint_type={c1.constraint_type})"
    )
    assert (
        str(c2)
        == f"Constraint(attribute_name=author,constraint_type={c2.constraint_type})"
    )

    c1_pb = c1.encode()
    actual_c1 = Constraint.decode(c1_pb)
    assert actual_c1 == c1

    c2_pb = c2.encode()
    actual_c2 = Constraint.decode(c2_pb)
    assert actual_c2 == c2


def test_query():
    """Test Query."""
    c1 = Constraint("author", ConstraintType("==", "Stephen King"))
    query = Query([c1])

    assert query.check(
        Description({"author": "Stephen King", "year": 1991, "genre": "horror"})
    )
    assert query.is_valid(generate_data_model("test", {"author": "some author"}))

    query.check_validity()
    with pytest.raises(ValueError, match=r"Constraints must be a list .*"):
        query = Query(c1)
    Query([]).check_validity()
    with pytest.raises(
        ValueError,
        match=r"Invalid input value for type 'Query': the query is not valid for the given data model.",
    ):
        Query(
            [c1], generate_data_model("test", {"notauthor": "not some author"})
        ).check_validity()

    assert query == Query([c1])

    assert (
        str(query)
        == "Query(constraints=['Constraint(attribute_name=author,constraint_type=ConstraintType(value=Stephen King,type===))'],model=None)"
    )

    query_pb = query.encode()
    actual_query = Query.decode(query_pb)
    assert actual_query == query
