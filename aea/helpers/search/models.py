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

"""Useful classes for the OEF search."""

import pickle  # nosec
from abc import ABC, abstractmethod
from copy import deepcopy
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union

ATTRIBUTE_TYPES = Union[float, str, bool, int]


class Attribute:
    """Implements an attribute for an OEF data model."""

    def __init__(
        self,
        name: str,
        type: Type[ATTRIBUTE_TYPES],
        is_required: bool,
        description: str = "",
    ):
        """
        Initialize an attribute.

        :param name: the name of the attribute.
        :param type: the type of the attribute.
        :param is_required: whether the attribute is required by the data model.
        :param description: an (optional) human-readable description for the attribute.
        """
        self.name: str = name
        self.type: Type[ATTRIBUTE_TYPES] = type
        self.is_required: bool = is_required
        self.description: str = description

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, Attribute)
            and self.name == other.name
            and self.type == other.type
            and self.is_required == other.is_required
        )


class DataModel:
    """Implements an OEF data model."""

    def __init__(self, name: str, attributes: List[Attribute], description: str = ""):
        """
        Initialize a data model.

        :param name: the name of the data model.
        :param attributes:  the attributes of the data model.
        """
        self.name: str = name
        self.attributes: List[Attribute] = sorted(attributes, key=lambda x: x.name)
        self.attributes_by_name = {a.name: a for a in attributes}
        self.description = description

    def __eq__(self, other) -> bool:
        """Compare with another object."""
        return (
            isinstance(other, DataModel)
            and self.name == other.name
            and self.attributes == other.attributes
        )


class Description:
    """Implements an OEF description."""

    def __init__(self, values: Dict, data_model: Optional[DataModel] = None):
        """
        Initialize the description object.

        :param values: the values in the description.
        """
        _values = deepcopy(values)
        self.values = _values
        self.data_model = data_model

    def __eq__(self, other) -> bool:
        """Compare with another object."""
        return (
            isinstance(other, Description)
            and self.values == other.values
            and self.data_model == other.data_model
        )

    def __iter__(self):
        """Create an iterator."""
        return iter(self.values)

    @classmethod
    def encode(
        cls, description_protobuf_object, description_object: "Description"
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the description_protobuf_object argument must be matched with the instance of this class in the 'description_object' argument.

        :param description_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param description_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        description_from_message_bytes = pickle.dumps(description_object)  # nosec
        description_protobuf_object.description = description_from_message_bytes

    @classmethod
    def decode(cls, description_protobuf_object) -> "Description":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the protocol buffer object in the 'description_protobuf_object' argument.

        :param description_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'description_protobuf_object' argument.
        """
        service_description = pickle.loads(
            description_protobuf_object.description
        )  # nosec
        return service_description


class ConstraintTypes(Enum):
    """Types of constraint."""

    EQUAL = "=="
    NOT_EQUAL = "!="
    LESS_THAN = "<"
    LESS_THAN_EQ = "<="
    GREATER_THAN = ">"
    GREATER_THAN_EQ = ">="
    WITHIN = "within"
    IN = "in"
    NOT_IN = "not_in"

    def __str__(self):
        """Get the string representation."""
        return self.value


class ConstraintType:
    """
    Type of constraint.

    Used with the Constraint class, this class allows to specify constraint over attributes.

    Examples:
        Equal to three
        >>> equal_3 = ConstraintType(ConstraintTypes.EQUAL, 3)

    You can also specify a type of constraint by using its string representation, e.g.:
        >>> equal_3 = ConstraintType("==", 3)
        >>> not_equal_london = ConstraintType("!=", "London")
        >>> less_than_pi = ConstraintType("<", 3.14)
        >>> within_range = ConstraintType("within", (-10.0, 10.0))
        >>> in_a_set = ConstraintType("in", [1, 2, 3])
        >>> not_in_a_set = ConstraintType("not_in", {"C", "Java", "Python"})

    """

    def __init__(self, type: Union[ConstraintTypes, str], value: Any):
        """
        Initialize a constraint type.

        :param type: the type of the constraint.
                   | Either an instance of the ConstraintTypes enum,
                   | or a string representation associated with the type.
        :param value: the value that defines the constraint.
        :raises ValueError: if the type of the constraint is not
        """
        self.type = ConstraintTypes(type)
        self.value = value
        assert self._check_validity(), "ConstraintType initialization inconsistent."

    def _check_validity(self):
        """
        Check the validity of the input provided.

        :return: None
        :raises ValueError: if the value is not valid wrt the constraint type.
        """
        try:
            if self.type == ConstraintTypes.EQUAL:
                assert isinstance(self.value, (int, float, str, bool))
            elif self.type == ConstraintTypes.NOT_EQUAL:
                assert isinstance(self.value, (int, float, str, bool))
            elif self.type == ConstraintTypes.LESS_THAN:
                assert isinstance(self.value, (int, float, str))
            elif self.type == ConstraintTypes.LESS_THAN_EQ:
                assert isinstance(self.value, (int, float, str))
            elif self.type == ConstraintTypes.GREATER_THAN:
                assert isinstance(self.value, (int, float, str))
            elif self.type == ConstraintTypes.GREATER_THAN_EQ:
                assert isinstance(self.value, (int, float, str))
            elif self.type == ConstraintTypes.WITHIN:
                assert isinstance(self.value, (list, tuple))
                assert len(self.value) == 2
                assert isinstance(self.value[0], type(self.value[1]))
                assert isinstance(self.value[1], type(self.value[0]))
            elif self.type == ConstraintTypes.IN:
                assert isinstance(self.value, (list, tuple, set))
                if len(self.value) > 0:
                    _type = type(next(iter(self.value)))
                    assert all(isinstance(obj, _type) for obj in self.value)
            elif self.type == ConstraintTypes.NOT_IN:
                assert isinstance(self.value, (list, tuple, set))
                if len(self.value) > 0:
                    _type = type(next(iter(self.value)))
                    assert all(isinstance(obj, _type) for obj in self.value)
            else:
                raise ValueError("Type not recognized.")
        except (AssertionError, ValueError):
            return False

        return True

    def check(self, value: ATTRIBUTE_TYPES) -> bool:
        """
        Check if an attribute value satisfies the constraint.

        The implementation depends on the constraint type.

        :param value: the value to check.
        :return: True if the value satisfy the constraint, False otherwise.
        :raises ValueError: if the constraint type is not recognized.
        """
        if self.type == ConstraintTypes.EQUAL:
            return self.value == value
        elif self.type == ConstraintTypes.NOT_EQUAL:
            return self.value != value
        elif self.type == ConstraintTypes.LESS_THAN:
            return self.value < value
        elif self.type == ConstraintTypes.LESS_THAN_EQ:
            return self.value <= value
        elif self.type == ConstraintTypes.GREATER_THAN:
            return self.value > value
        elif self.type == ConstraintTypes.GREATER_THAN_EQ:
            return self.value >= value
        elif self.type == ConstraintTypes.WITHIN:
            low = self.value[0]
            high = self.value[1]
            return low <= value <= high
        elif self.type == ConstraintTypes.IN:
            return value in self.value
        elif self.type == ConstraintTypes.NOT_IN:
            return value not in self.value
        else:
            raise ValueError("Constraint type not recognized.")

    def __eq__(self, other):
        """Check equality with another object."""
        return (
            isinstance(other, ConstraintType)
            and self.value == other.value
            and self.type == other.type
        )


class ConstraintExpr(ABC):
    """Implementation of the constraint language to query the OEF node."""

    @abstractmethod
    def check(self, description: Description) -> bool:
        """
        Check if a description satisfies the constraint expression.

        :param description: the description to check.
        :return: True if the description satisfy the constraint expression, False otherwise.
        """


class And(ConstraintExpr):
    """Implementation of the 'And' constraint expression."""

    def __init__(self, constraints: List[ConstraintExpr]):
        """
        Initialize an 'And' expression.

        :param constraints: the list of constraints expression (in conjunction).
        """
        self.constraints = constraints

    def check(self, description: Description) -> bool:
        """
        Check if a value satisfies the 'And' constraint expression.

        :param description: the description to check.
        :return: True if the description satisfy the constraint expression, False otherwise.
        """
        return all(expr.check(description) for expr in self.constraints)

    def __eq__(self, other):
        """Compare with another object."""
        return isinstance(other, And) and self.constraints == other.constraints


class Or(ConstraintExpr):
    """Implementation of the 'Or' constraint expression."""

    def __init__(self, constraints: List[ConstraintExpr]):
        """
        Initialize an 'Or' expression.

        :param constraints: the list of constraints expressions (in disjunction).
        """
        self.constraints = constraints

    def check(self, description: Description) -> bool:
        """
        Check if a value satisfies the 'Or' constraint expression.

        :param description: the description to check.
        :return: True if the description satisfy the constraint expression, False otherwise.
        """
        return any(expr.check(description) for expr in self.constraints)

    def __eq__(self, other):
        """Compare with another object."""
        return isinstance(other, Or) and self.constraints == other.constraints


class Not(ConstraintExpr):
    """Implementation of the 'Not' constraint expression."""

    def __init__(self, constraint: ConstraintExpr):
        """
        Initialize a 'Not' expression.

        :param constraint: the constraint expression to negate.
        """
        self.constraint = constraint

    def check(self, description: Description) -> bool:
        """
        Check if a value satisfies the 'Not' constraint expression.

        :param description: the description to check.
        :return: True if the description satisfy the constraint expression, False otherwise.
        """
        return not self.constraint.check(description)

    def __eq__(self, other):
        """Compare with another object."""
        return isinstance(other, Not) and self.constraint == other.constraint


class Constraint(ConstraintExpr):
    """The atomic component of a constraint expression."""

    def __init__(self, attribute_name: str, constraint_type: ConstraintType):
        """
        Initialize a constraint.

        :param attribute_name: the name of the attribute to be constrained.
        :param constraint_type: the constraint type.
        """
        self.attribute_name = attribute_name
        self.constraint_type = constraint_type

    def check(self, description: Description) -> bool:
        """
        Check if a description satisfies the constraint. The implementation depends on the type of the constraint.

        :param description: the description to check.
        :return: True if the description satisfies the constraint, False otherwise.

        Examples:
            >>> attr_author = Attribute("author" , str, True, "The author of the book.")
            >>> attr_year   = Attribute("year",    int, True, "The year of publication of the book.")
            >>> attr_genre   = Attribute("genre",  str, True, "The genre of the book.")
            >>> c1 = Constraint("author", ConstraintType("==", "Stephen King"))
            >>> c2 = Constraint("year", ConstraintType(">", 1990))
            >>> c3 = Constraint("genre", ConstraintType("in", {"horror", "science_fiction"}))
            >>> book_1 = Description({"author": "Stephen King",  "year": 1991, "genre": "horror"})
            >>> book_2 = Description({"author": "George Orwell", "year": 1948, "genre": "horror"})

            The "author" attribute instantiation satisfies the constraint, so the result is True.

            >>> c1.check(book_1)
            True

            Here, the "author" does not satisfy the constraints. Hence, the result is False.

            >>> c1.check(book_2)
            False

            In this case, there is a missing field specified by the query, that is "year"
            So the result is False, even in the case it is not required by the schema:

            >>> c2.check(Description({"author": "Stephen King"}))
            False

            If the type of some attribute of the description is not correct, the result is False.
            In this case, the field "year" has a string instead of an integer:

            >>> c2.check(Description({"author": "Stephen King", "year": "1991"}))
            False

            >>> c3.check(Description({"author": "Stephen King", "genre": False}))
            False

        """
        # if the name of the attribute is not present, return false.
        name = self.attribute_name
        if name not in description.values:
            return False

        # if the type of the value is different from the type of the attribute, return false.
        value = description.values[name]
        if type(self.constraint_type.value) in {list, tuple, set} and not isinstance(
            value, type(next(iter(self.constraint_type.value)))
        ):
            return False
        if not isinstance(value, type(self.constraint_type.value)):
            return False

        # dispatch the check to the right implementation for the concrete constraint type.
        return self.constraint_type.check(value)

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, Constraint)
            and self.attribute_name == other.attribute_name
            and self.constraint_type == other.constraint_type
        )


class Query:
    """This class lets you build a query for the OEF."""

    def __init__(
        self, constraints: List[ConstraintExpr], model: Optional[DataModel] = None
    ) -> None:
        """
        Initialize a query.

        :param constraints: a list of constraint expressions.
        :param model: the data model that the query refers to.
        """
        self.constraints = constraints
        self.model = model

    def check(self, description: Description) -> bool:
        """
        Check if a description satisfies the constraints of the query.

        The constraints are interpreted as conjunction.

        :param description: the description to check.
        :return: True if the description satisfies all the constraints, False otherwise.
        """
        return all(c.check(description) for c in self.constraints)

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, Query)
            and self.constraints == other.constraints
            and self.model == other.model
        )

    @classmethod
    def encode(cls, query_protobuf_object, query_object: "Query") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the query_protobuf_object argument must be matched with the instance of this class in the 'query_object' argument.

        :param query_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param query_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        query_bytes = pickle.dumps(query_object)  # nosec
        query_protobuf_object.query_bytes = query_bytes

    @classmethod
    def decode(cls, query_protobuf_object) -> "Query":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the protocol buffer object in the 'query_protobuf_object' argument.

        :param query_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'query_protobuf_object' argument.
        """
        query = pickle.loads(query_protobuf_object.query_bytes)  # nosec
        return query
