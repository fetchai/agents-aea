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

"""Useful classes for the OEF protocol."""
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Dict, Type, Union, Optional, List, Any

from oef.query import ConstraintType

ATTRIBUTE_TYPES = Union[float, str, bool, int]


class JSONSerializable(ABC):
    """Interface for JSON-serializable objects."""

    @abstractmethod
    def to_json(self) -> Dict:
        """
        Return the JSON representation of the object.

        :return: the JSON object.
        """

    @classmethod
    @abstractmethod
    def from_json(cls, d: Dict) -> Any:
        """
        Parse the JSON representation of the object.

        :param d: the JSON object.
        :return: the equivalent Python object.
        """


class Attribute:
    """Implements an attribute for an OEF data model."""

    def __init__(self, name: str,
                 type: Type[ATTRIBUTE_TYPES],
                 is_required: bool,
                 description: str = ""):
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
        return isinstance(other, Attribute) \
            and self.name == other.name \
            and self.type == other.type \
            and self.is_required == other.is_required


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
        return isinstance(other, DataModel) \
            and self.name == other.name \
            and self.attributes == other.attributes


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
        return isinstance(other, Description) \
            and self.values == other.values \
            and self.data_model == other.data_model

    def __iter__(self):
        """Create an iterator."""
        return self


class ConstraintExpr(ABC):
    """Implementation of the constraint language to query the OEF node."""


class And(ConstraintExpr):
    """Implementation of the 'And' constraint expression."""

    def __init__(self, constraints: List[ConstraintExpr]):
        """
        Initialize an 'And' expression.

        :param constraints: the list of constraints expression (in conjunction).
        """
        self.constraints = constraints

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

    def __eq__(self, other):
        """Compare with another object."""
        return isinstance(other, Constraint) \
            and self.attribute_name == other.attribute_name \
            and self.constraint_type == other.constraint_type


class Query:
    """This class lets you build a query for the OEF."""

    def __init__(self, constraints: List[ConstraintExpr], model: Optional[DataModel] = None) -> None:
        """
        Initialize a query.

        :param constraints: a list of constraint expressions.
        :param model: the data model that the query refers to.
        """
        self.constraints = constraints
        self.model = model

    def __eq__(self, other):
        """Compare with another object."""
        return isinstance(other, Query) \
            and self.constraints == other.constraints \
            and self.model == other.model
