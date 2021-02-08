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

"""Extension to the OEF Python SDK."""

import logging
from typing import Tuple

from oef.query import And as OEFAnd
from oef.query import Constraint as OEFConstraint
from oef.query import ConstraintExpr as OEFConstraintExpr
from oef.query import ConstraintType as OEFConstraintType
from oef.query import Distance, Eq, Gt, GtEq, In
from oef.query import Location as OEFLocation
from oef.query import Lt, LtEq
from oef.query import Not as OEFNot
from oef.query import NotEq, NotIn
from oef.query import Or as OEFOr
from oef.query import Query as OEFQuery
from oef.query import Range
from oef.schema import AttributeSchema as OEFAttribute
from oef.schema import DataModel as OEFDataModel
from oef.schema import Description as OEFDescription

from aea.helpers.search.models import (
    And,
    Attribute,
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
)


_default_logger = logging.getLogger("aea.packages.fetchai.connections.oef")


class OEFObjectTranslator:
    """Translate our OEF object to object of OEF SDK classes."""

    @classmethod
    def to_oef_description(cls, desc: Description) -> OEFDescription:
        """From our description to OEF description."""
        oef_data_model = (
            cls.to_oef_data_model(desc.data_model)
            if desc.data_model is not None
            else None
        )

        new_values = {}
        location_keys = set()
        loggers_by_key = {}
        for key, value in desc.values.items():
            if isinstance(value, Location):
                oef_location = OEFLocation(
                    latitude=value.latitude, longitude=value.longitude
                )
                location_keys.add(key)
                new_values[key] = oef_location
            else:
                new_values[key] = value

        # this is a workaround to make OEFLocation objects deep-copyable.
        # Indeed, there is a problem in deep-copying such objects
        # because of the logger object they have attached.
        # Steps:
        # 1) we remove the loggers attached to each Location obj,
        # 2) then we instantiate the description (it runs deepcopy on the values),
        # 3) and then we reattach the loggers.
        for key in location_keys:
            loggers_by_key[key] = new_values[key].log
            # in this way we remove the logger
            new_values[key].log = None

        description = OEFDescription(new_values, oef_data_model)

        for key in location_keys:
            new_values[key].log = loggers_by_key[key]

        return description

    @classmethod
    def to_oef_data_model(cls, data_model: DataModel) -> OEFDataModel:
        """From our data model to OEF data model."""
        oef_attributes = [
            cls.to_oef_attribute(attribute) for attribute in data_model.attributes
        ]
        return OEFDataModel(data_model.name, oef_attributes, data_model.description)

    @classmethod
    def to_oef_attribute(cls, attribute: Attribute) -> OEFAttribute:
        """From our attribute to OEF attribute."""
        # in case the attribute type is Location, replace with the `oef` class.
        attribute_type = OEFLocation if attribute.type == Location else attribute.type
        return OEFAttribute(
            attribute.name, attribute_type, attribute.is_required, attribute.description
        )

    @classmethod
    def to_oef_query(cls, query: Query) -> OEFQuery:
        """From our query to OEF query."""
        oef_data_model = (
            cls.to_oef_data_model(query.model) if query.model is not None else None
        )
        constraints = [cls.to_oef_constraint_expr(c) for c in query.constraints]
        return OEFQuery(constraints, oef_data_model)

    @classmethod
    def to_oef_location(cls, location: Location) -> OEFLocation:
        """From our location to OEF location."""
        return OEFLocation(latitude=location.latitude, longitude=location.longitude)  # type: ignore

    @classmethod
    def to_oef_constraint_expr(
        cls, constraint_expr: ConstraintExpr
    ) -> OEFConstraintExpr:
        """From our constraint expression to the OEF constraint expression."""
        if isinstance(constraint_expr, And):
            return OEFAnd(
                [cls.to_oef_constraint_expr(c) for c in constraint_expr.constraints]
            )
        if isinstance(constraint_expr, Or):
            return OEFOr(
                [cls.to_oef_constraint_expr(c) for c in constraint_expr.constraints]
            )
        if isinstance(constraint_expr, Not):
            return OEFNot(cls.to_oef_constraint_expr(constraint_expr.constraint))
        if isinstance(constraint_expr, Constraint):
            oef_constraint_type = cls.to_oef_constraint_type(
                constraint_expr.constraint_type
            )
            return OEFConstraint(constraint_expr.attribute_name, oef_constraint_type)
        raise ValueError("Constraint expression not supported.")

    @classmethod
    def to_oef_constraint_type(
        cls, constraint_type: ConstraintType
    ) -> OEFConstraintType:
        """From our constraint type to OEF constraint type."""
        value = constraint_type.value

        def distance(value: Tuple) -> Distance:
            location = cls.to_oef_location(location=value[0])
            return Distance(center=location, distance=value[1])

        CONSTRAINT_MAP = {
            ConstraintTypes.EQUAL: Eq,
            ConstraintTypes.NOT_EQUAL: NotEq,
            ConstraintTypes.LESS_THAN: Lt,
            ConstraintTypes.LESS_THAN_EQ: LtEq,
            ConstraintTypes.GREATER_THAN: Gt,
            ConstraintTypes.GREATER_THAN_EQ: GtEq,
            ConstraintTypes.WITHIN: Range,
            ConstraintTypes.IN: In,
            ConstraintTypes.NOT_IN: NotIn,
            ConstraintTypes.DISTANCE: distance,
        }

        if constraint_type.type not in CONSTRAINT_MAP:
            raise ValueError("Constraint type not recognized.")

        return CONSTRAINT_MAP[constraint_type.type](value)

    @classmethod
    def from_oef_description(cls, oef_desc: OEFDescription) -> Description:
        """From an OEF description to our description."""
        data_model = (
            cls.from_oef_data_model(oef_desc.data_model)
            if oef_desc.data_model is not None
            else None
        )

        new_values = {}
        for key, value in oef_desc.values.items():
            if isinstance(value, OEFLocation):
                new_values[key] = Location(
                    latitude=value.latitude, longitude=value.longitude
                )
            else:
                new_values[key] = value

        return Description(new_values, data_model=data_model)

    @classmethod
    def from_oef_data_model(cls, oef_data_model: OEFDataModel) -> DataModel:
        """From an OEF data model to our data model."""
        attributes = [
            cls.from_oef_attribute(oef_attribute)
            for oef_attribute in oef_data_model.attribute_schemas
        ]
        return DataModel(oef_data_model.name, attributes, oef_data_model.description)

    @classmethod
    def from_oef_attribute(cls, oef_attribute: OEFAttribute) -> Attribute:
        """From an OEF attribute to our attribute."""
        oef_attribute_type = (
            Location if oef_attribute.type == OEFLocation else oef_attribute.type
        )
        return Attribute(
            oef_attribute.name,
            oef_attribute_type,
            oef_attribute.required,
            oef_attribute.description,
        )

    @classmethod
    def from_oef_query(cls, oef_query: OEFQuery) -> Query:
        """From our query to OrOEF query."""
        data_model = (
            cls.from_oef_data_model(oef_query.model)
            if oef_query.model is not None
            else None
        )
        constraints = [cls.from_oef_constraint_expr(c) for c in oef_query.constraints]
        return Query(constraints, data_model)

    @classmethod
    def from_oef_location(cls, oef_location: OEFLocation) -> Location:
        """From oef location to our location."""
        return Location(
            latitude=oef_location.latitude, longitude=oef_location.longitude
        )

    @classmethod
    def from_oef_constraint_expr(
        cls, oef_constraint_expr: OEFConstraintExpr
    ) -> ConstraintExpr:
        """From our query to OEF query."""
        if isinstance(oef_constraint_expr, OEFAnd):
            return And(
                [
                    cls.from_oef_constraint_expr(c)
                    for c in oef_constraint_expr.constraints
                ]
            )
        if isinstance(oef_constraint_expr, OEFOr):
            return Or(
                [
                    cls.from_oef_constraint_expr(c)
                    for c in oef_constraint_expr.constraints
                ]
            )
        if isinstance(oef_constraint_expr, OEFNot):
            return Not(cls.from_oef_constraint_expr(oef_constraint_expr.constraint))
        if isinstance(oef_constraint_expr, OEFConstraint):
            constraint_type = cls.from_oef_constraint_type(
                oef_constraint_expr.constraint
            )
            return Constraint(oef_constraint_expr.attribute_name, constraint_type)
        raise ValueError("OEF Constraint not supported.")

    @classmethod
    def from_oef_constraint_type(
        cls, constraint_type: OEFConstraintType
    ) -> ConstraintType:
        """From OEF constraint type to our constraint type."""
        if isinstance(constraint_type, Eq):
            return ConstraintType(ConstraintTypes.EQUAL, constraint_type.value)
        if isinstance(constraint_type, NotEq):
            return ConstraintType(ConstraintTypes.NOT_EQUAL, constraint_type.value)
        if isinstance(constraint_type, Lt):
            return ConstraintType(ConstraintTypes.LESS_THAN, constraint_type.value)
        if isinstance(constraint_type, LtEq):
            return ConstraintType(ConstraintTypes.LESS_THAN_EQ, constraint_type.value)
        if isinstance(constraint_type, Gt):
            return ConstraintType(ConstraintTypes.GREATER_THAN, constraint_type.value)
        if isinstance(constraint_type, GtEq):
            return ConstraintType(
                ConstraintTypes.GREATER_THAN_EQ, constraint_type.value
            )
        if isinstance(constraint_type, Range):
            return ConstraintType(ConstraintTypes.WITHIN, constraint_type.values)
        if isinstance(constraint_type, In):
            return ConstraintType(ConstraintTypes.IN, constraint_type.values)
        if isinstance(constraint_type, NotIn):
            return ConstraintType(ConstraintTypes.NOT_IN, constraint_type.values)
        if isinstance(constraint_type, Distance):
            location = cls.from_oef_location(constraint_type.center)
            return ConstraintType(
                ConstraintTypes.DISTANCE, (location, constraint_type.distance)
            )
        raise ValueError("Constraint type not recognized.")
