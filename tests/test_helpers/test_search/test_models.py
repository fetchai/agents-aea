# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2020 Fetch.AI Limited
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
import re
from unittest.mock import MagicMock

import pytest

from aea.exceptions import AEAEnforceError
from aea.helpers.search.models import (
    And,
    Attribute,
    AttributeInconsistencyException,
    Constraint,
    ConstraintExpr,
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
    location = Location(latitude=1.1, longitude=2.2)
    assert location is not None

    assert location.tuple == (location.latitude, location.longitude)
    assert location.distance(Location(1.1, 2.2)) == 0
    assert location == Location(1.1, 2.2)
    assert str(location) == "Location(latitude=1.1,longitude=2.2)"

    location_pb = location.encode()
    actual_location = Location.decode(location_pb)
    assert actual_location == location
    assert location.latitude == actual_location.latitude
    assert location.longitude == actual_location.longitude


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
    values = {
        "test": "test_value",
        "bool": True,
        "float": 1.1,
        "int": int(1),
        "loc": Location(1, 1),
    }
    description = Description(
        values=values, data_model=generate_data_model("test", values)
    )

    assert description.values == values
    assert description == Description(
        values=values, data_model=generate_data_model("test", values)
    )
    assert list(description.values.values()) == list(values.values())
    assert list(description) == list(values)

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
        Description(
            values=values,
            data_model=generate_data_model("test", {**values, "test": 12}),
        )

    with pytest.raises(
        AttributeInconsistencyException, match=r".* has unallowed type:.*"
    ):
        Description(
            values={"test": object()},
            data_model=generate_data_model("test", {"test": object()}),
        )

    assert re.match(r"Description\(values=.*data_model=.*", str(description))

    description_pb = description._encode()
    actual_description = Description._decode(description_pb)
    assert actual_description == description

    mock = MagicMock()
    mock.description_bytes = None
    Description.encode(mock, description)
    assert mock.description_bytes is not None
    description = Description.decode(mock)
    assert "test" in description.values


def test_constraint_type():
    """Test ConstraintType."""
    constraint_type_values = {
        "int": 12,
        "bool": True,
        "float": 10.4,
        "str": "some_string",
        "location": Location(1.1, 2.2),
    }
    constraint_type_types = {
        "int": int,
        "bool": bool,
        "float": float,
        "str": str,
        "location": Location,
    }
    to_check = {
        "int": 13,
        "bool": False,
        "float": 9.3,
        "str": "some_other_string",
        "location": Location(1.2, 2.3),
    }

    # = and !=
    for constraint_types_type in [ConstraintTypes.EQUAL, ConstraintTypes.NOT_EQUAL]:
        for allowed_type in ["int", "bool", "float", "str"]:
            constraint_type = ConstraintType(
                constraint_types_type, constraint_type_values[allowed_type]
            )
            constraint_type.is_valid(
                Attribute("test", constraint_type_types[allowed_type], True)
            )
            constraint_type.check(to_check[allowed_type])
            assert constraint_type == ConstraintType(
                constraint_types_type, constraint_type_values[allowed_type]
            )
            assert (
                str(constraint_type)
                == f"ConstraintType(value={constraint_type_values[allowed_type]},type={constraint_types_type})"
            )

            constraint_type_pb = constraint_type.encode()
            actual_constraint_type = ConstraintType.decode(
                constraint_type_pb, "relation"
            )
            assert actual_constraint_type == constraint_type

    # < and <= and > and >=
    for constraint_types_type in [
        ConstraintTypes.LESS_THAN,
        ConstraintTypes.LESS_THAN_EQ,
        ConstraintTypes.GREATER_THAN,
        ConstraintTypes.GREATER_THAN_EQ,
    ]:
        for allowed_type in ["int", "float", "str"]:
            constraint_type = ConstraintType(
                constraint_types_type, constraint_type_values[allowed_type]
            )
            constraint_type.is_valid(
                Attribute("test", constraint_type_types[allowed_type], True)
            )
            constraint_type.check(to_check[allowed_type])
            assert constraint_type == ConstraintType(
                constraint_types_type, constraint_type_values[allowed_type]
            )
            assert (
                str(constraint_type)
                == f"ConstraintType(value={constraint_type_values[allowed_type]},type={constraint_types_type})"
            )

            constraint_type_pb = constraint_type.encode()
            actual_constraint_type = ConstraintType.decode(
                constraint_type_pb, "relation"
            )
            assert actual_constraint_type == constraint_type

    # within
    constraint_type_values = {
        "int": (1, 2),
        "float": (2.4, 5.4),
        "str": ("str_1", "str_2"),
        "location": (Location(1.1, 2.2), Location(1.2, 5.2)),
    }
    constraint_type_types = {
        "int": int,
        "float": float,
        "str": str,
        "location": Location,
    }
    to_check = {
        "int": 13,
        "float": 9.3,
        "str": "some_other_string",
        "location": Location(1.2, 2.3),
    }

    for range_constraint_type in ["int", "float", "str"]:  # location is not working
        constraint_type = ConstraintType(
            ConstraintTypes.WITHIN, constraint_type_values[range_constraint_type]
        )
        constraint_type.is_valid(
            Attribute("test", constraint_type_types[range_constraint_type], True)
        )
        constraint_type.check(to_check[range_constraint_type])
        assert constraint_type == ConstraintType(
            ConstraintTypes.WITHIN, constraint_type_values[range_constraint_type]
        )
        assert (
            str(constraint_type)
            == f"ConstraintType(value={constraint_type_values[range_constraint_type]},type=within)"
        )
        constraint_type_pb = constraint_type.encode()
        actual_constraint_type = ConstraintType.decode(constraint_type_pb, "range")
        assert actual_constraint_type == constraint_type

    # in and not_in
    constraint_type_values = {
        "int": (1, 2),
        "bool": (True, False),
        "float": (2.4, 5.4),
        "str": ("str_1", "str_2"),
        "location": (Location(1.1, 2.2), Location(1.2, 5.2)),
    }
    constraint_type_types = {
        "int": int,
        "bool": bool,
        "float": float,
        "str": str,
        "location": Location,
    }
    to_check = {
        "int": 13,
        "bool": False,
        "float": 9.3,
        "str": "some_other_string",
        "location": Location(1.2, 2.3),
    }

    for constraint_types_type in [ConstraintTypes.IN, ConstraintTypes.NOT_IN]:
        for constraint_set in ["int", "bool", "float", "str", "location"]:
            constraint_type = ConstraintType(
                constraint_types_type, constraint_type_values[constraint_set]
            )
            constraint_type.is_valid(
                Attribute("test", constraint_type_types[constraint_set], True)
            )
            constraint_type.check(to_check[constraint_set])
            assert constraint_type == ConstraintType(
                constraint_types_type, constraint_type_values[constraint_set]
            )
            assert (
                str(constraint_type)
                == f"ConstraintType(value={constraint_type_values[constraint_set]},type={constraint_types_type})"
            )
            constraint_type_pb = constraint_type.encode()
            actual_constraint_type = ConstraintType.decode(constraint_type_pb, "set")
            assert actual_constraint_type == constraint_type

    # distance
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

    # failures
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

    incorrect_category = "some_incorrect_category"
    with pytest.raises(
        ValueError,
        match=r"Incorrect category. Expected either of .* Found some_incorrect_category.",
    ):
        constraint_type_distance_pb = constraint_type_distance.encode()
        ConstraintType.decode(constraint_type_distance_pb, incorrect_category)


def test_constraints_expression():
    """Test constraint expressions: And, Or, Not, Constraint."""
    and_expression = And(
        [
            Constraint("number", ConstraintType(ConstraintTypes.LESS_THAN, 15)),
            Constraint("number", ConstraintType(ConstraintTypes.GREATER_THAN, 10)),
        ]
    )
    and_expression.check_validity()
    assert and_expression.check(Description({"number": 12}))
    assert and_expression.is_valid(
        DataModel("some_name", [Attribute("number", int, True)])
    )
    and_expression_pb = ConstraintExpr._encode(and_expression)
    actual_and_expression = ConstraintExpr._decode(and_expression_pb)
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
    or_expression_pb = ConstraintExpr._encode(or_expression)
    actual_or_expression = ConstraintExpr._decode(or_expression_pb)
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
    not_expression_pb = ConstraintExpr._encode(not_expression)
    actual_not_expression = ConstraintExpr._decode(not_expression_pb)
    assert actual_not_expression == not_expression

    # constraint
    constraint_expression = Constraint("author", ConstraintType("==", "Stephen King"))
    constraint_expression.check_validity()
    assert constraint_expression.check(Description({"author": "Stephen King"}))
    assert constraint_expression.is_valid(
        DataModel("some_name", [Attribute("author", str, True)])
    )
    constraint_expression_pb = ConstraintExpr._encode(constraint_expression)
    actual_constraint_expression = ConstraintExpr._decode(constraint_expression_pb)
    assert actual_constraint_expression == constraint_expression

    incorrect_expression = Location(1.1, 2.2)
    with pytest.raises(
        ValueError,
        match=f"Invalid expression type. Expected either of 'And', 'Or', 'Not', 'Constraint'. Found {type(incorrect_expression)}.",
    ):
        ConstraintExpr._encode(incorrect_expression)


def test_constraints_and():
    """Test And."""
    and_expression = And(
        [
            Constraint("number", ConstraintType(ConstraintTypes.LESS_THAN, 15)),
            Constraint("number", ConstraintType(ConstraintTypes.GREATER_THAN, 10)),
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


def test_constraints_or():
    """Test Or."""
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


def test_constraints_not():
    """Test Not."""
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
    c2 = Constraint("year", ConstraintType("within", (2000, 2010)))
    c3 = Constraint("author", ConstraintType("in", ("Stephen King", "J. K. Rowling")))
    c4 = Constraint(
        "author", ConstraintType("not_in", ("Stephen King", "J. K. Rowling"))
    )
    c5 = Constraint("address", ConstraintType("distance", (Location(1.1, 2.2), 2.2)))

    book_1 = Description(
        {"author": "Stephen King", "year": 2005, "address": Location(1.1, 2.2)}
    )
    book_2 = Description(
        {"author": "George Orwell", "year": 1948, "address": Location(1.1, 2.2)}
    )

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
        == f"Constraint(attribute_name=year,constraint_type={c2.constraint_type})"
    )

    c1_pb = c1.encode()
    actual_c1 = Constraint.decode(c1_pb)
    assert actual_c1 == c1

    c2_pb = c2.encode()
    actual_c2 = Constraint.decode(c2_pb)
    assert actual_c2 == c2

    c3_pb = c3.encode()
    actual_c3 = Constraint.decode(c3_pb)
    assert actual_c3 == c3

    c4_pb = c4.encode()
    actual_c4 = Constraint.decode(c4_pb)
    assert actual_c4 == c4

    c5_pb = c5.encode()
    actual_c5 = Constraint.decode(c5_pb)
    assert actual_c5 == c5


def test_query():
    """Test Query."""
    c1 = Constraint("author", ConstraintType("==", "Stephen King"))
    model = generate_data_model("book_author", {"author": "author of the book"})
    query = Query([c1], model=model)

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

    assert query == Query(
        [c1], model=generate_data_model("book_author", {"author": "author of the book"})
    )

    assert (
        str(query)
        == f"Query(constraints=['Constraint(attribute_name=author,constraint_type=ConstraintType(value=Stephen King,type===))'],model={model})"
    )

    query_pb = query._encode()
    actual_query = Query._decode(query_pb)
    assert actual_query == query

    query_pb = MagicMock()
    query_pb.query_bytes = None
    Query.encode(query_pb, query)
    assert query_pb.query_bytes is not None
    query = Query.decode(query_pb)
    assert "author" in query.model.attributes_by_name
