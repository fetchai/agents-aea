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
# pylint: disable=no-member
"""Useful classes for the OEF search."""

import logging
from abc import ABC, abstractmethod
from copy import deepcopy
from enum import Enum
from math import asin, cos, radians, sin, sqrt
from typing import (
    Any,
    Dict,
    Iterator,
    List,
    Mapping,
    Optional,
    Tuple,
    Type,
    Union,
    cast,
)

import aea.helpers.search.models_pb2 as models_pb2
from aea.exceptions import enforce


_default_logger = logging.getLogger(__name__)

proto_value = {
    "string": "string",
    "double": "double",
    "boolean": "boolean",
    "integer": "integer",
    "location": "location",
}

proto_range_pairs = {
    "string": "string_pair",
    "integer": "integer_pair",
    "double": "double_pair",
    "location": "location_pair",
}

proto_set_values = {
    "string": "string",
    "double": "double",
    "boolean": "boolean",
    "integer": "integer",
    "location": "location",
}

proto_constraint = {
    "set": "set_",
    "range": "range_",
    "relation": "relation",
    "distance": "distance",
}

proto_expression = {
    "or": "or_",
    "and": "and_",
    "not": "not_",
    "constraint": "constraint",
}

CONSTRAINT_CATEGORY_RELATION = "relation"
CONSTRAINT_CATEGORY_RANGE = "range"
CONSTRAINT_CATEGORY_SET = "set"
CONSTRAINT_CATEGORY_DISTANCE = "distance"

CONSTRAINT_CATEGORIES = [
    CONSTRAINT_CATEGORY_RELATION,
    CONSTRAINT_CATEGORY_RANGE,
    CONSTRAINT_CATEGORY_SET,
    CONSTRAINT_CATEGORY_DISTANCE,
]


class Location:
    """Data structure to represent locations (i.e. a pair of latitude and longitude)."""

    __slots__ = ("latitude", "longitude")

    def __init__(self, latitude: float, longitude: float) -> None:
        """
        Initialize a location.

        :param latitude: the latitude of the location.
        :param longitude: the longitude of the location.
        """
        self.latitude = latitude
        self.longitude = longitude

    @property
    def tuple(self) -> Tuple[float, float]:
        """Get the tuple representation of a location."""
        return self.latitude, self.longitude

    def distance(self, other: "Location") -> float:
        """
        Get the distance to another location.

        :param other: the other location
        :return: the distance
        """
        return haversine(self.latitude, self.longitude, other.latitude, other.longitude)

    def __eq__(self, other: Any) -> bool:
        """Compare equality of two locations."""
        if not isinstance(other, Location):
            return False  # pragma: nocover
        return self.latitude == other.latitude and self.longitude == other.longitude

    def __str__(self) -> str:
        """Get the string representation of the data model."""
        return "Location(latitude={},longitude={})".format(
            self.latitude, self.longitude
        )

    def encode(self) -> models_pb2.Query.Location:  # type: ignore
        """
        Encode an instance of this class into a protocol buffer object.

        :return: the matching protocol buffer object
        """
        location_pb = models_pb2.Query.Location()  # type: ignore
        location_pb.lat = self.latitude
        location_pb.lon = self.longitude
        return location_pb

    @classmethod
    def decode(cls, location_pb: Any) -> "Location":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        :param location_pb: the protocol buffer object corresponding with this class.
        :return: A new instance of this class matching the protocol buffer object
        """
        latitude = location_pb.lat
        longitude = location_pb.lon
        return cls(latitude, longitude)


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


class Attribute:
    """Implements an attribute for an OEF data model."""

    _attribute_type_to_pb = {
        bool: models_pb2.Query.Attribute.BOOL,  # type: ignore
        int: models_pb2.Query.Attribute.INT,  # type: ignore
        float: models_pb2.Query.Attribute.DOUBLE,  # type: ignore
        str: models_pb2.Query.Attribute.STRING,  # type: ignore
        Location: models_pb2.Query.Attribute.LOCATION,  # type: ignore
    }

    __slots__ = ("name", "type", "is_required", "description")

    def __init__(
        self,
        name: str,
        type_: Type[ATTRIBUTE_TYPES],
        is_required: bool,
        description: str = "",
    ) -> None:
        """
        Initialize an attribute.

        :param name: the name of the attribute.
        :param type_: the type of the attribute.
        :param is_required: whether the attribute is required by the data model.
        :param description: an (optional) human-readable description for the attribute.
        """
        self.name = name
        self.type = type_
        self.is_required = is_required
        self.description = description

    def __eq__(self, other: Any) -> bool:
        """Compare with another object."""
        return (
            isinstance(other, Attribute)
            and self.name == other.name
            and self.type == other.type
            and self.is_required == other.is_required
        )

    def __str__(self) -> str:
        """Get the string representation of the data model."""
        return "Attribute(name={},type={},is_required={})".format(
            self.name, self.type, self.is_required
        )

    def encode(self) -> models_pb2.Query.Attribute:  # type: ignore
        """
        Encode an instance of this class into a protocol buffer object.

        :return: the matching protocol buffer object
        """
        attribute = models_pb2.Query.Attribute()  # type: ignore
        attribute.name = self.name
        attribute.type = self._attribute_type_to_pb[self.type]
        attribute.required = self.is_required
        if self.description is not None:
            attribute.description = self.description
        return attribute

    @classmethod
    def decode(cls, attribute_pb: models_pb2.Query.Attribute) -> "Attribute":  # type: ignore
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        :param attribute_pb: the protocol buffer object corresponding with this class.
        :return: A new instance of this class matching the protocol buffer object
        """
        _pb_to_attribute_type = {v: k for k, v in cls._attribute_type_to_pb.items()}
        return cls(
            attribute_pb.name,
            _pb_to_attribute_type[attribute_pb.type],
            attribute_pb.required,
            attribute_pb.description if attribute_pb.description else None,
        )


class DataModel:
    """Implements an OEF data model."""

    __slots__ = ("name", "attributes", "description")

    def __init__(
        self, name: str, attributes: List[Attribute], description: str = ""
    ) -> None:
        """
        Initialize a data model.

        :param name: the name of the data model.
        :param attributes: the attributes of the data model.
        :param description: the data model description.
        """
        self.name: str = name
        self.attributes = sorted(
            attributes, key=lambda x: x.name
        )  # type: List[Attribute]
        self._check_validity()
        self.description = description

    @property
    def attributes_by_name(self) -> Dict[str, Attribute]:
        """Get the attributes by name."""
        return {a.name: a for a in self.attributes}

    def _check_validity(self) -> None:
        # check if there are duplicated attribute names
        attribute_names = [attribute.name for attribute in self.attributes]
        if len(attribute_names) != len(set(attribute_names)):
            raise ValueError(
                "Invalid input value for type '{}': duplicated attribute name.".format(
                    type(self).__name__
                )
            )

    def __eq__(self, other: Any) -> bool:
        """Compare with another object."""
        return (
            isinstance(other, DataModel)
            and self.name == other.name
            and self.attributes == other.attributes
        )

    def __str__(self) -> str:
        """Get the string representation of the data model."""
        return "DataModel(name={},attributes={},description={})".format(
            self.name, {a.name: str(a) for a in self.attributes}, self.description
        )

    def encode(self) -> models_pb2.Query.DataModel:  # type: ignore
        """
        Encode an instance of this class into a protocol buffer object.

        :return: the matching protocol buffer object
        """
        model = models_pb2.Query.DataModel()  # type: ignore
        model.name = self.name
        model.attributes.extend([attr.encode() for attr in self.attributes])
        if self.description is not None:
            model.description = self.description
        return model

    @classmethod
    def decode(cls, data_model_pb: Any) -> "DataModel":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        :param data_model_pb: the protocol buffer object corresponding with this class.
        :return: A new instance of this class matching the protocol buffer object
        """
        name = data_model_pb.name
        attributes = [Attribute.decode(attr_pb) for attr_pb in data_model_pb.attributes]
        description = data_model_pb.description
        return cls(name, attributes, description)


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

    __slots__ = ("_values", "data_model")

    def __init__(
        self,
        values: Mapping[str, ATTRIBUTE_TYPES],
        data_model: Optional[DataModel] = None,
        data_model_name: str = "",
    ) -> None:
        """
        Initialize the description object.

        :param values: the values in the description.
        :param data_model: the data model (optional)
        :param data_model_name: the data model name if a datamodel is created on the fly.
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

    def __eq__(self, other: Any) -> bool:
        """Compare with another object."""
        return (
            isinstance(other, Description)
            and self.values == other.values
            and self.data_model == other.data_model
        )

    def __iter__(self) -> Iterator:
        """Create an iterator."""
        return iter(self.values)

    def _check_consistency(self) -> None:
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
            if attribute is None:  # pragma: nocover
                # looks like this check is redundant, cause checks done above for all attributes
                raise ValueError("Attribute {} not found!".format(key))
            if not isinstance(value, attribute.type):
                # values does not match type in data model
                raise AttributeInconsistencyException(
                    "Attribute {} has incorrect type: {}".format(
                        attribute.name, attribute.type
                    )
                )
            if not type(value) in ALLOWED_ATTRIBUTE_TYPES:
                # value type matches data model, but it is not an allowed type
                raise AttributeInconsistencyException(
                    "Attribute {} has unallowed type: {}. Allowed types: {}".format(
                        attribute.name, type(value), ALLOWED_ATTRIBUTE_TYPES,
                    )
                )

    def __str__(self) -> str:
        """Get the string representation of the description."""
        return "Description(values={},data_model={})".format(
            self._values, self.data_model
        )

    @staticmethod
    def _to_key_value_pb(key: str, value: ATTRIBUTE_TYPES) -> models_pb2.Query.KeyValue:  # type: ignore
        """
        From a (key, attribute value) pair to the associated Protobuf object.

        :param key: the key of the attribute.
        :param value: the value of the attribute.

        :return: the associated Protobuf object.
        """

        kv = models_pb2.Query.KeyValue()  # type: ignore
        kv.key = key
        if type(value) == bool:  # pylint: disable=unidiomatic-typecheck
            kv.value.boolean = value
        elif type(value) == int:  # pylint: disable=unidiomatic-typecheck
            kv.value.integer = value
        elif type(value) == float:  # pylint: disable=unidiomatic-typecheck
            kv.value.double = value
        elif type(value) == str:  # pylint: disable=unidiomatic-typecheck
            kv.value.string = value
        elif type(value) == Location:  # pylint: disable=unidiomatic-typecheck
            kv.value.location.CopyFrom(value.encode())  # type: ignore

        return kv

    def _encode(self) -> models_pb2.Query.Instance:  # type: ignore
        """
        Encode an instance of this class into a protocol buffer object.

        :return: the matching protocol buffer object
        """
        instance = models_pb2.Query.Instance()  # type: ignore
        instance.model.CopyFrom(self.data_model.encode())
        instance.values.extend(
            [self._to_key_value_pb(key, value) for key, value in self.values.items()]
        )
        return instance

    @classmethod
    def encode(cls, description_pb: Any, description: "Description") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the description_protobuf_object argument must be matched
        with the instance of this class in the 'description_object' argument.

        :param description_pb: the protocol buffer object whose type corresponds with this class.
        :param description: an instance of this class to be encoded in the protocol buffer object.
        """
        description_bytes_pb = description._encode()  # pylint: disable=protected-access
        description_bytes_bytes = description_bytes_pb.SerializeToString()
        description_pb.description_bytes = description_bytes_bytes

    @staticmethod
    def _extract_value(value: models_pb2.Query.Value) -> ATTRIBUTE_TYPES:  # type: ignore
        """
        From a Protobuf query value object to attribute type.

        :param value: an instance of models_pb2.Query.Value.
        :return: the associated attribute type.
        """
        value_case = value.WhichOneof("value")

        if value_case == proto_value["string"]:
            result = value.string
        elif value_case == proto_value["boolean"]:
            result = bool(value.boolean)
        elif value_case == proto_value["integer"]:
            result = value.integer
        elif value_case == proto_value["double"]:
            result = value.double
        elif value_case == proto_value["location"]:
            result = Location.decode(value.location)
        else:
            raise ValueError(  # pragma: nocover
                f"Incorrect value. Expected either of {list(proto_value.values())}. Found {value_case}."
            )

        return result

    @classmethod
    def _decode(cls, description_pb: Any) -> "Description":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        :param description_pb: the protocol buffer object corresponding with this class.
        :return: A new instance of this class matching the protocol buffer object
        """
        model = DataModel.decode(description_pb.model)
        values = {
            attr.key: cls._extract_value(attr.value) for attr in description_pb.values
        }
        return cls(values, model)

    @classmethod
    def decode(cls, description_pb: Any) -> "Description":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the protocol
        buffer object in the 'description_protobuf_object' argument.

        :param description_pb: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'description_protobuf_object' argument.
        """
        description_bytes_pb = models_pb2.Query.Instance()  # type: ignore
        description_bytes_pb.ParseFromString(description_pb.description_bytes)
        description = cls._decode(description_bytes_pb)
        return description


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

    def __str__(self) -> str:  # pragma: nocover
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
        >>> in_a_set = ConstraintType("in", (1, 2, 3))
        >>> not_in_a_set = ConstraintType("not_in", ("C", "Java", "Python"))

    """

    __slots__ = ("type", "value")

    def __init__(self, type_: Union[ConstraintTypes, str], value: Any) -> None:
        """
        Initialize a constraint type.

        :param type_: the type of the constraint.
                   | Either an instance of the ConstraintTypes enum,
                   | or a string representation associated with the type.
        :param value: the value that defines the constraint.
        :raises AEAEnforceError: if the type of the constraint is not  # noqa: DAR402
        """
        self.type = ConstraintTypes(type_)
        self.value = value
        enforce(self.check_validity(), "ConstraintType initialization inconsistent.")

    def check_validity(self) -> bool:
        """
        Check the validity of the input provided.

        :return: boolean to indicate validity
        :raises AEAEnforceError: if the value is not valid wrt the constraint type.  # noqa: DAR402
        """
        try:
            if self.type == ConstraintTypes.EQUAL:
                enforce(
                    isinstance(self.value, (int, float, str, bool)),
                    f"Expected one of type in (int, float, str, bool), got {self.value}",
                )
            elif self.type == ConstraintTypes.NOT_EQUAL:
                enforce(
                    isinstance(self.value, (int, float, str, bool)),
                    f"Expected one of type in (int, float, str, bool), got {self.value}",
                )
            elif self.type == ConstraintTypes.LESS_THAN:
                enforce(
                    isinstance(self.value, (int, float, str)),
                    f"Expected one of type in (int, float, str), got {self.value}",
                )
            elif self.type == ConstraintTypes.LESS_THAN_EQ:
                enforce(
                    isinstance(self.value, (int, float, str)),
                    f"Expected one of type in (int, float, str), got {self.value}",
                )
            elif self.type == ConstraintTypes.GREATER_THAN:
                enforce(
                    isinstance(self.value, (int, float, str)),
                    f"Expected one of type in (int, float, str), got {self.value}",
                )
            elif self.type == ConstraintTypes.GREATER_THAN_EQ:
                enforce(
                    isinstance(self.value, (int, float, str)),
                    f"Expected one of type in (int, float, str), got {self.value}",
                )
            elif self.type == ConstraintTypes.WITHIN:
                allowed_sub_types = (int, float, str)
                enforce(
                    isinstance(self.value, tuple),
                    f"Expected tuple, got {type(self.value)}",
                )
                enforce(
                    len(self.value) == 2, f"Expected length=2, got {len(self.value)}"
                )
                enforce(
                    isinstance(self.value[0], type(self.value[1])), "Invalid types."
                )
                enforce(
                    isinstance(self.value[1], type(self.value[0])), "Invalid types."
                )
                enforce(
                    isinstance(self.value[0], allowed_sub_types),
                    f"Invalid type for first element. Expected either of {allowed_sub_types}. Found {type(self.value[0])}.",
                )
                enforce(
                    isinstance(self.value[1], allowed_sub_types),
                    f"Invalid type for second element. Expected either of {allowed_sub_types}. Found {type(self.value[1])}.",
                )
            elif self.type == ConstraintTypes.IN:
                enforce(
                    isinstance(self.value, tuple),
                    f"Expected tuple, got {type(self.value)}",
                )
                if len(self.value) > 0:
                    _type = type(next(iter(self.value)))
                    enforce(
                        all(isinstance(obj, _type) for obj in self.value),
                        "Invalid types.",
                    )
            elif self.type == ConstraintTypes.NOT_IN:
                enforce(
                    isinstance(self.value, tuple),
                    f"Expected tuple, got {type(self.value)}",
                )
                if len(self.value) > 0:
                    _type = type(next(iter(self.value)))
                    enforce(
                        all(isinstance(obj, _type) for obj in self.value),
                        "Invalid types.",
                    )
            elif self.type == ConstraintTypes.DISTANCE:
                enforce(
                    isinstance(self.value, tuple),
                    f"Expected tuple, got {type(self.value)}",
                )
                enforce(
                    len(self.value) == 2, f"Expected length=2, got {len(self.value)}"
                )
                enforce(
                    isinstance(self.value[0], Location),
                    "Invalid type, expected Location.",
                )
                enforce(
                    isinstance(self.value[1], float), "Invalid type, expected Location."
                )
            else:  # pragma: nocover
                raise ValueError("Type not recognized.")
        except ValueError:
            return False  # pragma: nocover

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

        :return: data type
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
            return value == self.value
        if self.type == ConstraintTypes.NOT_EQUAL:
            return value != self.value
        if self.type == ConstraintTypes.LESS_THAN:
            return value < self.value
        if self.type == ConstraintTypes.LESS_THAN_EQ:
            return value <= self.value
        if self.type == ConstraintTypes.GREATER_THAN:
            return value > self.value
        if self.type == ConstraintTypes.GREATER_THAN_EQ:
            return value >= self.value
        if self.type == ConstraintTypes.WITHIN:
            low = self.value[0]
            high = self.value[1]
            return low <= value <= high
        if self.type == ConstraintTypes.IN:
            return value in self.value
        if self.type == ConstraintTypes.NOT_IN:
            return value not in self.value
        if self.type == ConstraintTypes.DISTANCE:
            if not isinstance(value, Location):  # pragma: nocover
                raise ValueError("Value must be of type Location.")
            location = cast(Location, self.value[0])
            distance = self.value[1]
            return location.distance(value) <= distance
        raise ValueError("Constraint type not recognized.")  # pragma: nocover

    def __eq__(self, other: Any) -> bool:
        """Check equality with another object."""
        return (
            isinstance(other, ConstraintType)
            and self.value == other.value
            and self.type == other.type
        )

    def __str__(self) -> str:
        """Get the string representation of the constraint type."""
        return "ConstraintType(value={},type={})".format(self.value, self.type)

    def encode(self) -> Optional[Any]:
        """
        Encode an instance of this class into a protocol buffer object.

        :return: the matching protocol buffer object
        """
        encoding: Optional[Any] = None

        if (
            self.type == ConstraintTypes.EQUAL
            or self.type == ConstraintTypes.NOT_EQUAL
            or self.type == ConstraintTypes.LESS_THAN
            or self.type == ConstraintTypes.LESS_THAN_EQ
            or self.type == ConstraintTypes.GREATER_THAN
            or self.type == ConstraintTypes.GREATER_THAN_EQ
        ):
            relation = models_pb2.Query.Relation()  # type: ignore

            if self.type == ConstraintTypes.EQUAL:
                relation.operator = models_pb2.Query.Relation.EQ  # type: ignore
            elif self.type == ConstraintTypes.NOT_EQUAL:
                relation.operator = models_pb2.Query.Relation.NOTEQ  # type: ignore
            elif self.type == ConstraintTypes.LESS_THAN:
                relation.operator = models_pb2.Query.Relation.LT  # type: ignore
            elif self.type == ConstraintTypes.LESS_THAN_EQ:
                relation.operator = models_pb2.Query.Relation.LTEQ  # type: ignore
            elif self.type == ConstraintTypes.GREATER_THAN:
                relation.operator = models_pb2.Query.Relation.GT  # type: ignore
            elif self.type == ConstraintTypes.GREATER_THAN_EQ:
                relation.operator = models_pb2.Query.Relation.GTEQ  # type: ignore

            query_value = models_pb2.Query.Value()  # type: ignore

            if isinstance(self.value, bool):
                query_value.boolean = self.value
            elif isinstance(self.value, int):
                query_value.integer = self.value
            elif isinstance(self.value, float):
                query_value.double = self.value
            elif isinstance(self.value, str):
                query_value.string = self.value
            relation.value.CopyFrom(query_value)

            encoding = relation

        elif self.type == ConstraintTypes.WITHIN:
            range_ = models_pb2.Query.Range()  # type: ignore

            if type(self.value[0]) == str:  # pylint: disable=unidiomatic-typecheck
                values = models_pb2.Query.StringPair()  # type: ignore
                values.first = self.value[0]
                values.second = self.value[1]
                range_.string_pair.CopyFrom(values)
            elif type(self.value[0]) == int:  # pylint: disable=unidiomatic-typecheck
                values = models_pb2.Query.IntPair()  # type: ignore
                values.first = self.value[0]
                values.second = self.value[1]
                range_.integer_pair.CopyFrom(values)
            elif type(self.value[0]) == float:  # pylint: disable=unidiomatic-typecheck
                values = models_pb2.Query.DoublePair()  # type: ignore
                values.first = self.value[0]
                values.second = self.value[1]
                range_.double_pair.CopyFrom(values)
            encoding = range_

        elif self.type == ConstraintTypes.IN or self.type == ConstraintTypes.NOT_IN:
            set_ = models_pb2.Query.Set()  # type: ignore

            if self.type == ConstraintTypes.IN:
                set_.operator = models_pb2.Query.Set.IN  # type: ignore
            elif self.type == ConstraintTypes.NOT_IN:
                set_.operator = models_pb2.Query.Set.NOTIN  # type: ignore

            value_type = type(self.value[0]) if len(self.value) > 0 else str

            if value_type == str:
                values = models_pb2.Query.Set.Values.Strings()  # type: ignore
                values.values.extend(self.value)
                set_.values.string.CopyFrom(values)
            elif value_type == bool:
                values = models_pb2.Query.Set.Values.Bools()  # type: ignore
                values.values.extend(self.value)
                set_.values.boolean.CopyFrom(values)
            elif value_type == int:
                values = models_pb2.Query.Set.Values.Ints()  # type: ignore
                values.values.extend(self.value)
                set_.values.integer.CopyFrom(values)
            elif value_type == float:
                values = models_pb2.Query.Set.Values.Doubles()  # type: ignore
                values.values.extend(self.value)
                set_.values.double.CopyFrom(values)
            elif value_type == Location:
                values = models_pb2.Query.Set.Values.Locations()  # type: ignore
                values.values.extend([value.encode() for value in self.value])
                set_.values.location.CopyFrom(values)

            encoding = set_

        elif self.type == ConstraintTypes.DISTANCE:
            distance_pb = models_pb2.Query.Distance()  # type: ignore
            distance_pb.distance = self.value[1]
            distance_pb.center.CopyFrom(self.value[0].encode())

            encoding = distance_pb

        return encoding

    @classmethod
    def decode(cls, constraint_type_pb: Any, category: str) -> "ConstraintType":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        :param constraint_type_pb: the protocol buffer object corresponding with this class.
        :param category: the category of the constraint ('relation', 'set', 'range', 'distance).

        :return: A new instance of this class matching the protocol buffer object
        """
        decoding: ConstraintType

        relation_type_from_pb = {
            models_pb2.Query.Relation.Operator.GTEQ: ConstraintTypes.GREATER_THAN_EQ,  # type: ignore
            models_pb2.Query.Relation.Operator.GT: ConstraintTypes.GREATER_THAN,  # type: ignore
            models_pb2.Query.Relation.Operator.LTEQ: ConstraintTypes.LESS_THAN_EQ,  # type: ignore
            models_pb2.Query.Relation.Operator.LT: ConstraintTypes.LESS_THAN,  # type: ignore
            models_pb2.Query.Relation.Operator.NOTEQ: ConstraintTypes.NOT_EQUAL,  # type: ignore
            models_pb2.Query.Relation.Operator.EQ: ConstraintTypes.EQUAL,  # type: ignore
        }
        set_type_from_pb = {
            models_pb2.Query.Set.Operator.IN: ConstraintTypes.IN,  # type: ignore
            models_pb2.Query.Set.Operator.NOTIN: ConstraintTypes.NOT_IN,  # type: ignore
        }

        if category == CONSTRAINT_CATEGORY_RELATION:
            relation_enum = relation_type_from_pb[constraint_type_pb.operator]
            value_case = constraint_type_pb.value.WhichOneof("value")
            if value_case == proto_value["string"]:
                decoding = ConstraintType(
                    relation_enum, constraint_type_pb.value.string
                )
            elif value_case == proto_value["boolean"]:
                decoding = ConstraintType(
                    relation_enum, constraint_type_pb.value.boolean
                )
            elif value_case == proto_value["integer"]:
                decoding = ConstraintType(
                    relation_enum, constraint_type_pb.value.integer
                )
            elif value_case == proto_value["double"]:
                decoding = ConstraintType(
                    relation_enum, constraint_type_pb.value.double
                )
        elif category == CONSTRAINT_CATEGORY_RANGE:
            range_enum = ConstraintTypes.WITHIN
            range_case = constraint_type_pb.WhichOneof("pair")
            if range_case == proto_range_pairs["string"]:
                decoding = ConstraintType(
                    range_enum,
                    (
                        constraint_type_pb.string_pair.first,
                        constraint_type_pb.string_pair.second,
                    ),
                )
            elif range_case == proto_range_pairs["integer"]:
                decoding = ConstraintType(
                    range_enum,
                    (
                        constraint_type_pb.integer_pair.first,
                        constraint_type_pb.integer_pair.second,
                    ),
                )
            elif range_case == proto_range_pairs["double"]:
                decoding = ConstraintType(
                    range_enum,
                    (
                        constraint_type_pb.double_pair.first,
                        constraint_type_pb.double_pair.second,
                    ),
                )
        elif category == CONSTRAINT_CATEGORY_SET:
            set_enum = set_type_from_pb[constraint_type_pb.operator]
            value_case = constraint_type_pb.values.WhichOneof("values")
            if value_case == proto_set_values["string"]:
                decoding = ConstraintType(
                    set_enum, tuple(constraint_type_pb.values.string.values),
                )
            elif value_case == proto_set_values["boolean"]:
                decoding = ConstraintType(
                    set_enum, tuple(constraint_type_pb.values.boolean.values),
                )
            elif value_case == proto_set_values["integer"]:
                decoding = ConstraintType(
                    set_enum, tuple(constraint_type_pb.values.integer.values),
                )
            elif value_case == proto_set_values["double"]:
                decoding = ConstraintType(
                    set_enum, tuple(constraint_type_pb.values.double.values),
                )
            elif value_case == proto_set_values["location"]:
                locations = [
                    Location.decode(loc)
                    for loc in constraint_type_pb.values.location.values
                ]
                location_tuple = tuple(locations)
                decoding = ConstraintType(set_enum, location_tuple)
        elif category == CONSTRAINT_CATEGORY_DISTANCE:
            distance_enum = ConstraintTypes.DISTANCE
            center = Location.decode(constraint_type_pb.center)
            distance = constraint_type_pb.distance
            decoding = ConstraintType(distance_enum, (center, distance))
        else:
            raise ValueError(
                f"Incorrect category. Expected either of {CONSTRAINT_CATEGORIES}. Found {category}."
            )
        return decoding


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

        :raises AEAEnforceError: if the object does not satisfy some requirements.  # noqa: DAR402
        """

    @staticmethod
    def _encode(expression: Any) -> models_pb2.Query.ConstraintExpr:  # type: ignore
        """
        Encode an instance of this class into a protocol buffer object.

        :param expression: an expression
        :return: the matching protocol buffer object
        """
        constraint_expression_pb = models_pb2.Query.ConstraintExpr()  # type: ignore
        expression_pb = expression.encode()
        if isinstance(expression, And):
            constraint_expression_pb.and_.CopyFrom(expression_pb)
        elif isinstance(expression, Or):
            constraint_expression_pb.or_.CopyFrom(expression_pb)
        elif isinstance(expression, Not):
            constraint_expression_pb.not_.CopyFrom(expression_pb)
        elif isinstance(expression, Constraint):
            constraint_expression_pb.constraint.CopyFrom(expression_pb)
        else:
            raise ValueError(
                f"Invalid expression type. Expected either of 'And', 'Or', 'Not', 'Constraint'. Found {type(expression)}."
            )

        return constraint_expression_pb

    @staticmethod
    def _decode(constraint_expression_pb: Any) -> "ConstraintExpr":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        :param constraint_expression_pb: the protocol buffer object corresponding with this class.
        :return: A new instance of this class matching the protocol buffer object
        """
        expression = constraint_expression_pb.WhichOneof("expression")

        result: Optional[Union[And, Or, Not, Constraint]] = None

        if expression == proto_expression["and"]:
            result = And.decode(constraint_expression_pb.and_)
        elif expression == proto_expression["or"]:
            result = Or.decode(constraint_expression_pb.or_)
        elif expression == proto_expression["not"]:
            result = Not.decode(constraint_expression_pb.not_)
        elif expression == proto_expression["constraint"]:
            result = Constraint.decode(constraint_expression_pb.constraint)
        else:  # pragma: nocover
            raise ValueError(
                f"Incorrect argument. Expected either of {list(proto_expression.keys())}. Found {expression}."
            )

        return result


class And(ConstraintExpr):
    """Implementation of the 'And' constraint expression."""

    __slots__ = ("constraints",)

    def __init__(self, constraints: List[ConstraintExpr]) -> None:
        """
        Initialize an 'And' expression.

        :param constraints: the list of constraints expression (in conjunction).
        """
        self.constraints = constraints
        self.check_validity()

    def check(self, description: Description) -> bool:
        """
        Check if a value satisfies the 'And' constraint expression.

        :param description: the description to check.
        :return: True if the description satisfy the constraint expression, False otherwise.
        """
        return all(expression.check(description) for expression in self.constraints)

    def is_valid(self, data_model: DataModel) -> bool:
        """
        Check whether the constraint expression is valid wrt a data model.

        :param data_model: the data model used to check the validity of the constraint expression.
        :return: ``True`` if the constraint expression is valid wrt the data model, ``False`` otherwise.
        """
        return all(constraint.is_valid(data_model) for constraint in self.constraints)

    def check_validity(self) -> None:
        """
        Check whether the Constraint Expression satisfies some basic requirements.

        :return ``None``
        :raises ValueError: if the object does not satisfy some requirements.
        """
        if len(self.constraints) < 2:  # pragma: nocover
            raise ValueError(
                "Invalid input value for type '{}': number of "
                "subexpression must be at least 2.".format(type(self).__name__)
            )
        for constraint in self.constraints:
            constraint.check_validity()

    def __eq__(self, other: Any) -> bool:  # pragma: nocover
        """Compare with another object."""
        return isinstance(other, And) and self.constraints == other.constraints

    def encode(self) -> models_pb2.Query.ConstraintExpr.And:  # type: ignore
        """
        Encode an instance of this class into a protocol buffer object.

        :return: the matching protocol buffer object
        """
        and_pb = models_pb2.Query.ConstraintExpr.And()  # type: ignore
        constraint_expression_pbs = [
            ConstraintExpr._encode(constraint) for constraint in self.constraints
        ]
        and_pb.expression.extend(constraint_expression_pbs)
        return and_pb

    @classmethod
    def decode(cls, and_pb: Any) -> "And":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        :param and_pb: the protocol buffer object corresponding with this class.
        :return: A new instance of this class matching the protocol buffer object
        """
        expression = [cls._decode(c) for c in and_pb.expression]
        return cls(expression)


class Or(ConstraintExpr):
    """Implementation of the 'Or' constraint expression."""

    __slots__ = ("constraints",)

    def __init__(self, constraints: List[ConstraintExpr]) -> None:
        """
        Initialize an 'Or' expression.

        :param constraints: the list of constraints expressions (in disjunction).
        """
        self.constraints = constraints
        self.check_validity()

    def check(self, description: Description) -> bool:
        """
        Check if a value satisfies the 'Or' constraint expression.

        :param description: the description to check.
        :return: True if the description satisfy the constraint expression, False otherwise.
        """
        return any(expression.check(description) for expression in self.constraints)

    def is_valid(self, data_model: DataModel) -> bool:
        """
        Check whether the constraint expression is valid wrt a data model.

        :param data_model: the data model used to check the validity of the constraint expression.
        :return: ``True`` if the constraint expression is valid wrt the data model, ``False`` otherwise.
        """
        return all(constraint.is_valid(data_model) for constraint in self.constraints)

    def check_validity(self) -> None:
        """
        Check whether the Constraint Expression satisfies some basic requirements.

        :return ``None``
        :raises ValueError: if the object does not satisfy some requirements.
        """
        if len(self.constraints) < 2:  # pragma: nocover
            raise ValueError(
                "Invalid input value for type '{}': number of "
                "subexpression must be at least 2.".format(type(self).__name__)
            )
        for constraint in self.constraints:
            constraint.check_validity()

    def __eq__(self, other: Any) -> bool:  # pragma: nocover
        """Compare with another object."""
        return isinstance(other, Or) and self.constraints == other.constraints

    def encode(self) -> models_pb2.Query.ConstraintExpr.Or:  # type: ignore
        """
        Encode an instance of this class into a protocol buffer object.

        :return: the matching protocol buffer object
        """
        or_pb = models_pb2.Query.ConstraintExpr.Or()  # type: ignore
        constraint_expression_pbs = [
            ConstraintExpr._encode(constraint) for constraint in self.constraints
        ]
        or_pb.expression.extend(constraint_expression_pbs)
        return or_pb

    @classmethod
    def decode(cls, or_pb: Any) -> "Or":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        :param or_pb: the protocol buffer object corresponding with this class.
        :return: A new instance of this class matching the protocol buffer object
        """
        expression = [ConstraintExpr._decode(c) for c in or_pb.expression]
        return cls(expression)


class Not(ConstraintExpr):
    """Implementation of the 'Not' constraint expression."""

    __slots__ = ("constraint",)

    def __init__(self, constraint: ConstraintExpr) -> None:
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

    def __eq__(self, other: Any) -> bool:  # pragma: nocover
        """Compare with another object."""
        return isinstance(other, Not) and self.constraint == other.constraint

    def encode(self) -> models_pb2.Query.ConstraintExpr.Not:  # type: ignore
        """
        Encode an instance of this class into a protocol buffer object.

        :return: the matching protocol buffer object
        """
        not_pb = models_pb2.Query.ConstraintExpr.Not()  # type: ignore
        constraint_expression_pb = ConstraintExpr._encode(self.constraint)
        not_pb.expression.CopyFrom(constraint_expression_pb)
        return not_pb

    @classmethod
    def decode(cls, not_pb: Any) -> "Not":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        :param not_pb: the protocol buffer object corresponding with this class.
        :return: A new instance of this class matching the protocol buffer object
        """
        expression = ConstraintExpr._decode(not_pb.expression)
        return cls(expression)


class Constraint(ConstraintExpr):
    """The atomic component of a constraint expression."""

    __slots__ = ("attribute_name", "constraint_type")

    def __init__(self, attribute_name: str, constraint_type: ConstraintType) -> None:
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
            >>> c3 = Constraint("genre", ConstraintType("in", ("horror", "science_fiction")))
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

    def __eq__(self, other: Any) -> bool:
        """Compare with another object."""
        return (
            isinstance(other, Constraint)
            and self.attribute_name == other.attribute_name
            and self.constraint_type == other.constraint_type
        )

    def __str__(self) -> str:
        """Get the string representation of the constraint."""
        return "Constraint(attribute_name={},constraint_type={})".format(
            self.attribute_name, self.constraint_type
        )

    def encode(self) -> models_pb2.Query.ConstraintExpr.Constraint:  # type: ignore
        """
        Encode an instance of this class into a protocol buffer object.

        :return: the matching protocol buffer object
        """
        constraint = models_pb2.Query.ConstraintExpr.Constraint()  # type: ignore
        constraint.attribute_name = self.attribute_name

        if (
            self.constraint_type.type == ConstraintTypes.EQUAL
            or self.constraint_type.type == ConstraintTypes.NOT_EQUAL
            or self.constraint_type.type == ConstraintTypes.LESS_THAN
            or self.constraint_type.type == ConstraintTypes.LESS_THAN_EQ
            or self.constraint_type.type == ConstraintTypes.GREATER_THAN
            or self.constraint_type.type == ConstraintTypes.GREATER_THAN_EQ
        ):
            constraint.relation.CopyFrom(self.constraint_type.encode())
        elif self.constraint_type.type == ConstraintTypes.WITHIN:
            constraint.range_.CopyFrom(self.constraint_type.encode())
        elif (
            self.constraint_type.type == ConstraintTypes.IN
            or self.constraint_type.type == ConstraintTypes.NOT_IN
        ):
            constraint.set_.CopyFrom(self.constraint_type.encode())
        elif self.constraint_type.type == ConstraintTypes.DISTANCE:
            constraint.distance.CopyFrom(self.constraint_type.encode())
        else:  # pragma: nocover
            raise ValueError(
                f"Incorrect constraint type. Expected a ConstraintTypes. Found {self.constraint_type.type}."
            )
        return constraint

    @classmethod
    def decode(cls, constraint_pb: Any) -> "Constraint":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        :param constraint_pb: the protocol buffer object corresponding with this class.
        :return: A new instance of this class matching the protocol buffer object
        """
        constraint_case = constraint_pb.WhichOneof("constraint")
        if constraint_case == proto_constraint["relation"]:
            constraint_type = ConstraintType.decode(constraint_pb.relation, "relation")
        elif constraint_case == proto_constraint["set"]:
            constraint_type = ConstraintType.decode(constraint_pb.set_, "set")
        elif constraint_case == proto_constraint["range"]:
            constraint_type = ConstraintType.decode(constraint_pb.range_, "range")
        elif constraint_case == proto_constraint["distance"]:
            constraint_type = ConstraintType.decode(constraint_pb.distance, "distance")
        else:
            raise ValueError(  # pragma: nocover
                f"Incorrect argument. Expected either of ['relation', 'set_', 'range_', 'distance']. Found {constraint_case}."
            )

        return cls(constraint_pb.attribute_name, constraint_type)


class Query:
    """This class lets you build a query for the OEF."""

    __slots__ = ("constraints", "model")

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

    def is_valid(self, data_model: Optional[DataModel]) -> bool:
        """
        Given a data model, check whether the query is valid for that data model.

        :param data_model: optional datamodel
        :return: ``True`` if the query is compliant with the data model, ``False`` otherwise.
        """
        if data_model is None:
            return True

        return all(c.is_valid(data_model) for c in self.constraints)

    def check_validity(self) -> None:
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
            _default_logger.warning(
                "DEPRECATION WARNING: "
                "Invalid input value for type '{}': empty list of constraints. The number of "
                "constraints must be at least 1.".format(type(self).__name__)
            )
        if not self.is_valid(self.model):
            raise ValueError(
                "Invalid input value for type '{}': the query is not valid "
                "for the given data model.".format(type(self).__name__)
            )

    def __eq__(self, other: Any) -> bool:
        """Compare with another object."""
        return (
            isinstance(other, Query)
            and self.constraints == other.constraints
            and self.model == other.model
        )

    def __str__(self) -> str:
        """Get the string representation of the constraint."""
        return "Query(constraints={},model={})".format(
            [str(c) for c in self.constraints], self.model
        )

    def _encode(self) -> models_pb2.Query.Model:  # type: ignore
        """
        Encode an instance of this class into a protocol buffer object.

        :return: the matching protocol buffer object
        """
        query = models_pb2.Query.Model()  # type: ignore
        constraint_expression_pbs = [
            ConstraintExpr._encode(constraint)  # pylint: disable=protected-access
            for constraint in self.constraints
        ]
        query.constraints.extend(constraint_expression_pbs)

        if self.model is not None:
            query.model.CopyFrom(self.model.encode())
        return query

    @classmethod
    def encode(cls, query_pb: Any, query: "Query") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the query_protobuf_object argument must be matched
        with the instance of this class in the 'query_object' argument.

        :param query_pb: the protocol buffer object wrapping an object that corresponds with this class.
        :param query: an instance of this class to be encoded in the protocol buffer object.
        """
        query_bytes_pb = query._encode()  # pylint: disable=protected-access
        query_bytes_bytes = query_bytes_pb.SerializeToString()
        query_pb.query_bytes = query_bytes_bytes

    @classmethod
    def _decode(cls, query_pb: Any) -> "Query":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        :param query_pb: the protocol buffer object corresponding with this class.
        :return: A new instance of this class matching the protocol buffer object
        """
        constraints = [
            ConstraintExpr._decode(c)  # pylint: disable=protected-access
            for c in query_pb.constraints
        ]
        data_model = DataModel.decode(query_pb.model)

        return cls(constraints, data_model if query_pb.HasField("model") else None,)

    @classmethod
    def decode(cls, query_pb: Any) -> "Query":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the protocol
        buffer object in the 'query_protobuf_object' argument.

        :param query_pb: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'query_protobuf_object' argument.
        """
        query_bytes_pb = models_pb2.Query.Model()  # type: ignore
        query_bytes_pb.ParseFromString(query_pb.query_bytes)
        query = cls._decode(query_bytes_pb)
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
    earth_radius = 6372.8  # average earth radius
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    sin_lat_squared = sin(dlat * 0.5) * sin(dlat * 0.5)
    sin_lon_squared = sin(dlon * 0.5) * sin(dlon * 0.5)
    computation = asin(sqrt(sin_lat_squared + sin_lon_squared * cos(lat1) * cos(lat2)))
    distance = 2 * earth_radius * computation
    return distance
