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

import logging
import pickle  # nosec
from abc import ABC, abstractmethod
from copy import deepcopy
from enum import Enum
from math import asin, cos, radians, sin, sqrt
from typing import Any, Dict, List, Mapping, Optional, Type, Union, cast

logger = logging.getLogger(__name__)


class Location:
    """Data structure to represent locations (i.e. a pair of latitude and longitude)."""

    def __init__(self, latitude: float, longitude: float):
        """
        Initialize a location.

        :param latitude: the latitude of the location.
        :param longitude: the longitude of the location.
        """
        self.latitude = latitude
        self.longitude = longitude

    def distance(self, other: "Location") -> float:
        """
        Get the distance to another location.

        :param other: the other location
        :retun: the distance
        """
        return haversine(self.latitude, self.longitude, other.latitude, other.longitude)

    def __eq__(self, other):
        """Compare equality of two locations."""
        if not isinstance(other, Location):
            return False  # pragma: nocover
        else:
            return self.latitude == other.latitude and self.longitude == other.longitude


"""
The allowable types that an Attribute can have
"""
ATTRIBUTE_TYPES = Union[float, str, bool, int, Location]
ALLOWED_ATTRIBUTE_TYPES = [float, str, bool, int, Location]


class AttributeInconsistencyException(Exception):
    """
    Raised when the attributes in a Description are inconsistent.

    Inconsistency is defined when values do not meet their respective schema, or if the values
    are not of an allowed type.
    """

    pass


class Attribute:
    """Implements an attribute for an OEF data model."""

    def __init__(
        self,
        name: str,
        type_: Type[ATTRIBUTE_TYPES],
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
        self.name = name
        self.type = type_
        self.is_required = is_required
        self.description = description

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
        self.attributes = sorted(
            attributes, key=lambda x: x.name
        )  # type: List[Attribute]
        self._check_validity()
        self.attributes_by_name = {a.name: a for a in attributes}
        self.description = description

    def _check_validity(self):
        # check if there are duplicated attribute names
        attribute_names = [attribute.name for attribute in self.attributes]
        if len(attribute_names) != len(set(attribute_names)):
            raise ValueError(
                "Invalid input value for type '{}': duplicated attribute name.".format(
                    type(self).__name__
                )
            )

    def __eq__(self, other) -> bool:
        """Compare with another object."""
        return (
            isinstance(other, DataModel)
            and self.name == other.name
            and self.attributes == other.attributes
        )


def generate_data_model(
    model_name: str, attribute_values: Mapping[str, ATTRIBUTE_TYPES]
) -> DataModel:
    """
    Generate a data model that matches the values stored in this description.

    That is, for each attribute (name, value), generate an Attribute.
    It is assumed that each attribute is required.

    :param model_name: the name of the model.
    :param attribute_values: the values of each attribute
    :return: the schema compliant with the values specified.
    """
    return DataModel(
        model_name,
        [Attribute(key, type(value), True) for key, value in attribute_values.items()],
    )


class Description:
    """Implements an OEF description."""

    def __init__(
        self,
        values: Mapping[str, ATTRIBUTE_TYPES],
        data_model: Optional[DataModel] = None,
        data_model_name: str = "",
    ):
        """
        Initialize the description object.

        :param values: the values in the description.
        :param data_model: the data model (optional)
        :pram data_model_name: the data model name if a datamodel is created on the fly.
        """
        _values = deepcopy(values)
        self._values = _values
        if data_model is not None:
            self.data_model = data_model
        else:
            self.data_model = generate_data_model(data_model_name, values)
        self._check_consistency()

    @property
    def values(self) -> Dict:
        """Get the values."""
        return cast(Dict, self._values)

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

    def _check_consistency(self):
        """
        Check the consistency of the values of this description.

        If an attribute has been provided, values are checked against that. If no attribute
        schema has been provided then minimal checking is performed based on the values in the
        provided attribute_value dictionary.
        :raises AttributeInconsistencyException: if values do not meet the schema, or if no schema is present
                                               | if they have disallowed types.
        """
        # check that all required attributes in the schema are contained in the description
        required_attributes = [
            attribute.name
            for attribute in self.data_model.attributes
            if attribute.is_required
        ]
        if not all(
            attribute_name in self.values for attribute_name in required_attributes
        ):
            raise AttributeInconsistencyException("Missing required attribute.")

        # check that all values are defined in the data model
        all_attributes = [attribute.name for attribute in self.data_model.attributes]
        if not all(key in all_attributes for key in self.values.keys()):
            raise AttributeInconsistencyException(
                "Have extra attribute not in data model."
            )

        # check that each of the provided values are consistent with that specified in the data model
        for key, value in self.values.items():
            attribute = next(
                (
                    attribute
                    for attribute in self.data_model.attributes
                    if attribute.name == key
                ),
                None,
            )
            if not isinstance(value, attribute.type):
                # values does not match type in data model
                raise AttributeInconsistencyException(
                    "Attribute {} has incorrect type: {}".format(
                        attribute.name, attribute.type
                    )
                )
            elif not type(value) in ALLOWED_ATTRIBUTE_TYPES:
                # value type matches data model, but it is not an allowed type
                raise AttributeInconsistencyException(
                    "Attribute {} has unallowed type: {}. Allowed types: {}".format(
                        attribute.name, type(value), ALLOWED_ATTRIBUTE_TYPES,
                    )
                )

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
        service_description = pickle.loads(  # nosec
            description_protobuf_object.description
        )
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
    DISTANCE = "distance"

    def __str__(self):  # pragma: nocover
        """Get the string representation."""
        return str(self.value)


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

    def __init__(self, type_: Union[ConstraintTypes, str], value: Any):
        """
        Initialize a constraint type.

        :param type: the type of the constraint.
                   | Either an instance of the ConstraintTypes enum,
                   | or a string representation associated with the type.
        :param value: the value that defines the constraint.
        :raises ValueError: if the type of the constraint is not
        """
        self.type = ConstraintTypes(type_)
        self.value = value
        assert self.check_validity(), "ConstraintType initialization inconsistent."

    def check_validity(self):
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
            elif self.type == ConstraintTypes.DISTANCE:
                assert isinstance(self.value, (list, tuple))
                assert len(self.value) == 2
                assert isinstance(self.value[0], Location)
                assert isinstance(self.value[1], float)
            else:  # pragma: nocover
                raise ValueError("Type not recognized.")
        except (AssertionError, ValueError):
            return False

        return True

    def is_valid(self, attribute: Attribute) -> bool:
        """
        Check if the constraint type is valid wrt a given attribute.

        A constraint type is valid wrt an attribute if the
        type of its operand(s) is the same of the attribute type.

        >>> attribute = Attribute("year", int, True)
        >>> valid_constraint_type = ConstraintType(ConstraintTypes.GREATER_THAN, 2000)
        >>> valid_constraint_type.is_valid(attribute)
        True

        >>> valid_constraint_type = ConstraintType(ConstraintTypes.WITHIN, (2000, 2001))
        >>> valid_constraint_type.is_valid(attribute)
        True

        The following constraint is invalid: the year is in a string variable,
        whereas the attribute is defined over integers.

        >>> invalid_constraint_type = ConstraintType(ConstraintTypes.GREATER_THAN, "2000")
        >>> invalid_constraint_type.is_valid(attribute)
        False

        :param attribute: the data model used to check the validity of the constraint type.
        :return: ``True`` if the constraint type is valid wrt the attribute, ``False`` otherwise.
        """
        return self.get_data_type() == attribute.type

    def get_data_type(self) -> Type[ATTRIBUTE_TYPES]:
        """
        Get the type of the data used to define the constraint type.

        For instance:
        >>> c = ConstraintType(ConstraintTypes.EQUAL, 1)
        >>> c.get_data_type()
        <class 'int'>

        """
        if isinstance(self.value, (list, tuple, set)):
            value = next(iter(self.value))
        else:
            value = self.value
        value = cast(ATTRIBUTE_TYPES, value)
        return type(value)

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
        elif self.type == ConstraintTypes.DISTANCE:
            assert isinstance(value, Location), "Value must be of type Location."
            location = cast(Location, self.value[0])
            distance = self.value[1]
            return location.distance(value) <= distance
        else:  # pragma: nocover
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

    @abstractmethod
    def is_valid(self, data_model: DataModel) -> bool:
        """
        Check whether a constraint expression is valid wrt a data model.

         Specifically, check the following conditions:
        - If all the attributes referenced by the constraints are correctly associated with the Data Model attributes.

        :param data_model: the data model used to check the validity of the constraint expression.
        :return: ``True`` if the constraint expression is valid wrt the data model, ``False`` otherwise.
        """

    def check_validity(self) -> None:  # pylint: disable=no-self-use  # pragma: nocover
        """
        Check whether a Constraint Expression satisfies some basic requirements.

        :return ``None``
        :raises ValueError: if the object does not satisfy some requirements.
        """
        return None


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

    def is_valid(self, data_model: DataModel) -> bool:
        """
        Check whether the constraint expression is valid wrt a data model.

        :param data_model: the data model used to check the validity of the constraint expression.
        :return: ``True`` if the constraint expression is valid wrt the data model, ``False`` otherwise.
        """
        return all(constraint.is_valid(data_model) for constraint in self.constraints)

    def check_validity(self):
        """
        Check whether the Constraint Expression satisfies some basic requirements.

        :return ``None``
        :raises ValueError: if the object does not satisfy some requirements.
        """
        if len(self.constraints) < 2:  # pragma: nocover  # TODO: do we need this check?
            raise ValueError(
                "Invalid input value for type '{}': number of "
                "subexpression must be at least 2.".format(type(self).__name__)
            )
        for constraint in self.constraints:
            constraint.check_validity()

    def __eq__(self, other):  # pragma: nocover
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

    def is_valid(self, data_model: DataModel) -> bool:
        """
        Check whether the constraint expression is valid wrt a data model.

        :param data_model: the data model used to check the validity of the constraint expression.
        :return: ``True`` if the constraint expression is valid wrt the data model, ``False`` otherwise.
        """
        return all(constraint.is_valid(data_model) for constraint in self.constraints)

    def check_validity(self):
        """
        Check whether the Constraint Expression satisfies some basic requirements.

        :return ``None``
        :raises ValueError: if the object does not satisfy some requirements.
        """
        if len(self.constraints) < 2:  # pragma: nocover # TODO: do we need this check?
            raise ValueError(
                "Invalid input value for type '{}': number of "
                "subexpression must be at least 2.".format(type(self).__name__)
            )
        for constraint in self.constraints:
            constraint.check_validity()

    def __eq__(self, other):  # pragma: nocover
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

    def is_valid(self, data_model: DataModel) -> bool:
        """
        Check whether the constraint expression is valid wrt a data model.

        :param data_model: the data model used to check the validity of the constraint expression.
        :return: ``True`` if the constraint expression is valid wrt the data model, ``False`` otherwise.
        """
        return self.constraint.is_valid(data_model)

    def __eq__(self, other):  # pragma: nocover
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
        if type(self.constraint_type.value) not in {
            list,
            tuple,
            set,
        } and not isinstance(value, type(self.constraint_type.value)):
            return False

        # dispatch the check to the right implementation for the concrete constraint type.
        return self.constraint_type.check(value)

    def is_valid(self, data_model: DataModel) -> bool:
        """
        Check whether the constraint expression is valid wrt a data model.

        :param data_model: the data model used to check the validity of the constraint expression.
        :return: ``True`` if the constraint expression is valid wrt the data model, ``False`` otherwise.
        """
        # if the attribute name of the constraint is not present in the data model, the constraint is not valid.
        if self.attribute_name not in data_model.attributes_by_name:
            return False

        attribute = data_model.attributes_by_name[self.attribute_name]
        return self.constraint_type.is_valid(attribute)

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
        self.check_validity()

    def check(self, description: Description) -> bool:
        """
        Check if a description satisfies the constraints of the query.

        The constraints are interpreted as conjunction.

        :param description: the description to check.
        :return: True if the description satisfies all the constraints, False otherwise.
        """
        return all(c.check(description) for c in self.constraints)

    def is_valid(self, data_model: DataModel) -> bool:
        """
        Given a data model, check whether the query is valid for that data model.

        :return: ``True`` if the query is compliant with the data model, ``False`` otherwise.
        """
        if data_model is None:
            return True

        return all(c.is_valid(data_model) for c in self.constraints)

    def check_validity(self):
        """
        Check whether the` object is valid.

        :return ``None``
        :raises ValueError: if the query does not satisfy some sanity requirements.
        """
        if not isinstance(self.constraints, list):
            raise ValueError(
                "Constraints must be a list (`List[Constraint]`). Instead is of type '{}'.".format(
                    type(self.constraints).__name__
                )
            )
        if len(self.constraints) < 1:
            logger.warning(
                "DEPRECATION WARNING: "
                "Invalid input value for type '{}': empty list of constraints. The number of "
                "constraints must be at least 1.".format(type(self).__name__)
            )
        if not self.is_valid(self.model):
            raise ValueError(
                "Invalid input value for type '{}': the query is not valid "
                "for the given data model.".format(type(self).__name__)
            )

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


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Compute the Haversine distance between two locations (i.e. two pairs of latitude and longitude).

    :param lat1: the latitude of the first location.
    :param lon1: the longitude of the first location.
    :param lat2: the latitude of the second location.
    :param lon2: the longitude of the second location.
    :return: the Haversine distance.
    """
    lat1, lon1, lat2, lon2, = map(radians, [lat1, lon1, lat2, lon2])
    # average earth radius
    R = 6372.8
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    sin_lat_squared = sin(dlat * 0.5) * sin(dlat * 0.5)
    sin_lon_squared = sin(dlon * 0.5) * sin(dlon * 0.5)
    computation = asin(sqrt(sin_lat_squared + sin_lon_squared * cos(lat1) * cos(lat2)))
    d = 2 * R * computation
    return d
