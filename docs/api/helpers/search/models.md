<a name="aea.helpers.search.models"></a>
# aea.helpers.search.models

Useful classes for the OEF search.

<a name="aea.helpers.search.models.Location"></a>
## Location Objects

```python
class Location()
```

Data structure to represent locations (i.e. a pair of latitude and longitude).

<a name="aea.helpers.search.models.Location.__init__"></a>
#### `__`init`__`

```python
 | __init__(latitude: float, longitude: float) -> None
```

Initialize a location.

**Arguments**:

- `latitude`: the latitude of the location.
- `longitude`: the longitude of the location.

<a name="aea.helpers.search.models.Location.tuple"></a>
#### tuple

```python
 | @property
 | tuple() -> Tuple[float, float]
```

Get the tuple representation of a location.

<a name="aea.helpers.search.models.Location.distance"></a>
#### distance

```python
 | distance(other: "Location") -> float
```

Get the distance to another location.

**Arguments**:

- `other`: the other location

**Returns**:

the distance

<a name="aea.helpers.search.models.Location.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other: Any) -> bool
```

Compare equality of two locations.

<a name="aea.helpers.search.models.Location.__str__"></a>
#### `__`str`__`

```python
 | __str__() -> str
```

Get the string representation of the data model.

<a name="aea.helpers.search.models.Location.encode"></a>
#### encode

```python
 | encode() -> models_pb2.Query.Location
```

Encode an instance of this class into a protocol buffer object.

**Returns**:

the matching protocol buffer object

<a name="aea.helpers.search.models.Location.decode"></a>
#### decode

```python
 | @classmethod
 | decode(cls, location_pb: Any) -> "Location"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

**Arguments**:

- `location_pb`: the protocol buffer object corresponding with this class.

**Returns**:

A new instance of this class matching the protocol buffer object

<a name="aea.helpers.search.models.AttributeInconsistencyException"></a>
## AttributeInconsistencyException Objects

```python
class AttributeInconsistencyException(Exception)
```

Raised when the attributes in a Description are inconsistent.

Inconsistency is defined when values do not meet their respective schema, or if the values
are not of an allowed type.

<a name="aea.helpers.search.models.Attribute"></a>
## Attribute Objects

```python
class Attribute()
```

Implements an attribute for an OEF data model.

<a name="aea.helpers.search.models.Attribute.__init__"></a>
#### `__`init`__`

```python
 | __init__(name: str, type_: Type[ATTRIBUTE_TYPES], is_required: bool, description: str = "") -> None
```

Initialize an attribute.

**Arguments**:

- `name`: the name of the attribute.
- `type_`: the type of the attribute.
- `is_required`: whether the attribute is required by the data model.
- `description`: an (optional) human-readable description for the attribute.

<a name="aea.helpers.search.models.Attribute.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other: Any) -> bool
```

Compare with another object.

<a name="aea.helpers.search.models.Attribute.__str__"></a>
#### `__`str`__`

```python
 | __str__() -> str
```

Get the string representation of the data model.

<a name="aea.helpers.search.models.Attribute.encode"></a>
#### encode

```python
 | encode() -> models_pb2.Query.Attribute
```

Encode an instance of this class into a protocol buffer object.

**Returns**:

the matching protocol buffer object

<a name="aea.helpers.search.models.Attribute.decode"></a>
#### decode

```python
 | @classmethod
 | decode(cls, attribute_pb: models_pb2.Query.Attribute) -> "Attribute"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

**Arguments**:

- `attribute_pb`: the protocol buffer object corresponding with this class.

**Returns**:

A new instance of this class matching the protocol buffer object

<a name="aea.helpers.search.models.DataModel"></a>
## DataModel Objects

```python
class DataModel()
```

Implements an OEF data model.

<a name="aea.helpers.search.models.DataModel.__init__"></a>
#### `__`init`__`

```python
 | __init__(name: str, attributes: List[Attribute], description: str = "") -> None
```

Initialize a data model.

**Arguments**:

- `name`: the name of the data model.
- `attributes`: the attributes of the data model.
- `description`: the data model description.

<a name="aea.helpers.search.models.DataModel.attributes_by_name"></a>
#### attributes`_`by`_`name

```python
 | @property
 | attributes_by_name() -> Dict[str, Attribute]
```

Get the attributes by name.

<a name="aea.helpers.search.models.DataModel.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other: Any) -> bool
```

Compare with another object.

<a name="aea.helpers.search.models.DataModel.__str__"></a>
#### `__`str`__`

```python
 | __str__() -> str
```

Get the string representation of the data model.

<a name="aea.helpers.search.models.DataModel.encode"></a>
#### encode

```python
 | encode() -> models_pb2.Query.DataModel
```

Encode an instance of this class into a protocol buffer object.

**Returns**:

the matching protocol buffer object

<a name="aea.helpers.search.models.DataModel.decode"></a>
#### decode

```python
 | @classmethod
 | decode(cls, data_model_pb: Any) -> "DataModel"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

**Arguments**:

- `data_model_pb`: the protocol buffer object corresponding with this class.

**Returns**:

A new instance of this class matching the protocol buffer object

<a name="aea.helpers.search.models.generate_data_model"></a>
#### generate`_`data`_`model

```python
generate_data_model(model_name: str, attribute_values: Mapping[str, ATTRIBUTE_TYPES]) -> DataModel
```

Generate a data model that matches the values stored in this description.

That is, for each attribute (name, value), generate an Attribute.
It is assumed that each attribute is required.

**Arguments**:

- `model_name`: the name of the model.
- `attribute_values`: the values of each attribute

**Returns**:

the schema compliant with the values specified.

<a name="aea.helpers.search.models.Description"></a>
## Description Objects

```python
class Description()
```

Implements an OEF description.

<a name="aea.helpers.search.models.Description.__init__"></a>
#### `__`init`__`

```python
 | __init__(values: Mapping[str, ATTRIBUTE_TYPES], data_model: Optional[DataModel] = None, data_model_name: str = "") -> None
```

Initialize the description object.

**Arguments**:

- `values`: the values in the description.
- `data_model`: the data model (optional)
- `data_model_name`: the data model name if a datamodel is created on the fly.

<a name="aea.helpers.search.models.Description.values"></a>
#### values

```python
 | @property
 | values() -> Dict
```

Get the values.

<a name="aea.helpers.search.models.Description.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other: Any) -> bool
```

Compare with another object.

<a name="aea.helpers.search.models.Description.__iter__"></a>
#### `__`iter`__`

```python
 | __iter__() -> Iterator
```

Create an iterator.

<a name="aea.helpers.search.models.Description.__str__"></a>
#### `__`str`__`

```python
 | __str__() -> str
```

Get the string representation of the description.

<a name="aea.helpers.search.models.Description.encode"></a>
#### encode

```python
 | @classmethod
 | encode(cls, description_pb: Any, description: "Description") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the description_protobuf_object argument must be matched
with the instance of this class in the 'description_object' argument.

**Arguments**:

- `description_pb`: the protocol buffer object whose type corresponds with this class.
- `description`: an instance of this class to be encoded in the protocol buffer object.

<a name="aea.helpers.search.models.Description.decode"></a>
#### decode

```python
 | @classmethod
 | decode(cls, description_pb: Any) -> "Description"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class must be created that matches the protocol
buffer object in the 'description_protobuf_object' argument.

**Arguments**:

- `description_pb`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'description_protobuf_object' argument.

<a name="aea.helpers.search.models.ConstraintTypes"></a>
## ConstraintTypes Objects

```python
class ConstraintTypes(Enum)
```

Types of constraint.

<a name="aea.helpers.search.models.ConstraintTypes.__str__"></a>
#### `__`str`__`

```python
 | __str__() -> str
```

Get the string representation.

<a name="aea.helpers.search.models.ConstraintType"></a>
## ConstraintType Objects

```python
class ConstraintType()
```

Type of constraint.

Used with the Constraint class, this class allows to specify constraint over attributes.

**Examples**:

  Equal to three
  >>> equal_3 = ConstraintType(ConstraintTypes.EQUAL, 3)
  
  You can also specify a type of constraint by using its string representation, e.g.:
  >>> equal_3 = ConstraintType("==", 3)
  >>> not_equal_london = ConstraintType("!=", "London")
  >>> less_than_pi = ConstraintType("<", 3.14)
  >>> within_range = ConstraintType("within", (-10.0, 10.0))
  >>> in_a_set = ConstraintType("in", (1, 2, 3))
  >>> not_in_a_set = ConstraintType("not_in", ("C", "Java", "Python"))

<a name="aea.helpers.search.models.ConstraintType.__init__"></a>
#### `__`init`__`

```python
 | __init__(type_: Union[ConstraintTypes, str], value: Any) -> None
```

Initialize a constraint type.

**Arguments**:

- `type_`: the type of the constraint.
           | Either an instance of the ConstraintTypes enum,
           | or a string representation associated with the type.
- `value`: the value that defines the constraint.

**Raises**:

- `AEAEnforceError`: if the type of the constraint is not  # noqa: DAR402

<a name="aea.helpers.search.models.ConstraintType.check_validity"></a>
#### check`_`validity

```python
 | check_validity() -> bool
```

Check the validity of the input provided.

**Returns**:

boolean to indicate validity

**Raises**:

- `AEAEnforceError`: if the value is not valid wrt the constraint type.  # noqa: DAR402

<a name="aea.helpers.search.models.ConstraintType.is_valid"></a>
#### is`_`valid

```python
 | is_valid(attribute: Attribute) -> bool
```

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

**Arguments**:

- `attribute`: the data model used to check the validity of the constraint type.

**Returns**:

``True`` if the constraint type is valid wrt the attribute, ``False`` otherwise.

<a name="aea.helpers.search.models.ConstraintType.get_data_type"></a>
#### get`_`data`_`type

```python
 | get_data_type() -> Type[ATTRIBUTE_TYPES]
```

Get the type of the data used to define the constraint type.

For instance:
>>> c = ConstraintType(ConstraintTypes.EQUAL, 1)
>>> c.get_data_type()
<class 'int'>

**Returns**:

data type

<a name="aea.helpers.search.models.ConstraintType.check"></a>
#### check

```python
 | check(value: ATTRIBUTE_TYPES) -> bool
```

Check if an attribute value satisfies the constraint.

The implementation depends on the constraint type.

**Arguments**:

- `value`: the value to check.

**Returns**:

True if the value satisfy the constraint, False otherwise.

**Raises**:

- `ValueError`: if the constraint type is not recognized.

<a name="aea.helpers.search.models.ConstraintType.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other: Any) -> bool
```

Check equality with another object.

<a name="aea.helpers.search.models.ConstraintType.__str__"></a>
#### `__`str`__`

```python
 | __str__() -> str
```

Get the string representation of the constraint type.

<a name="aea.helpers.search.models.ConstraintType.encode"></a>
#### encode

```python
 | encode() -> Optional[Any]
```

Encode an instance of this class into a protocol buffer object.

**Returns**:

the matching protocol buffer object

<a name="aea.helpers.search.models.ConstraintType.decode"></a>
#### decode

```python
 | @classmethod
 | decode(cls, constraint_type_pb: Any, category: str) -> "ConstraintType"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

**Arguments**:

- `constraint_type_pb`: the protocol buffer object corresponding with this class.
- `category`: the category of the constraint ('relation', 'set', 'range', 'distance).

**Returns**:

A new instance of this class matching the protocol buffer object

<a name="aea.helpers.search.models.ConstraintExpr"></a>
## ConstraintExpr Objects

```python
class ConstraintExpr(ABC)
```

Implementation of the constraint language to query the OEF node.

<a name="aea.helpers.search.models.ConstraintExpr.check"></a>
#### check

```python
 | @abstractmethod
 | check(description: Description) -> bool
```

Check if a description satisfies the constraint expression.

**Arguments**:

- `description`: the description to check.

**Returns**:

True if the description satisfy the constraint expression, False otherwise.

<a name="aea.helpers.search.models.ConstraintExpr.is_valid"></a>
#### is`_`valid

```python
 | @abstractmethod
 | is_valid(data_model: DataModel) -> bool
```

Check whether a constraint expression is valid wrt a data model.

Specifically, check the following conditions:
- If all the attributes referenced by the constraints are correctly associated with the Data Model attributes.

**Arguments**:

- `data_model`: the data model used to check the validity of the constraint expression.

**Returns**:

``True`` if the constraint expression is valid wrt the data model, ``False`` otherwise.

<a name="aea.helpers.search.models.ConstraintExpr.check_validity"></a>
#### check`_`validity

```python
 | check_validity() -> None
```

Check whether a Constraint Expression satisfies some basic requirements.

**Raises**:

- `AEAEnforceError`: if the object does not satisfy some requirements.  # noqa: DAR402

<a name="aea.helpers.search.models.And"></a>
## And Objects

```python
class And(ConstraintExpr)
```

Implementation of the 'And' constraint expression.

<a name="aea.helpers.search.models.And.__init__"></a>
#### `__`init`__`

```python
 | __init__(constraints: List[ConstraintExpr]) -> None
```

Initialize an 'And' expression.

**Arguments**:

- `constraints`: the list of constraints expression (in conjunction).

<a name="aea.helpers.search.models.And.check"></a>
#### check

```python
 | check(description: Description) -> bool
```

Check if a value satisfies the 'And' constraint expression.

**Arguments**:

- `description`: the description to check.

**Returns**:

True if the description satisfy the constraint expression, False otherwise.

<a name="aea.helpers.search.models.And.is_valid"></a>
#### is`_`valid

```python
 | is_valid(data_model: DataModel) -> bool
```

Check whether the constraint expression is valid wrt a data model.

**Arguments**:

- `data_model`: the data model used to check the validity of the constraint expression.

**Returns**:

``True`` if the constraint expression is valid wrt the data model, ``False`` otherwise.

<a name="aea.helpers.search.models.And.check_validity"></a>
#### check`_`validity

```python
 | check_validity() -> None
```

Check whether the Constraint Expression satisfies some basic requirements.

:return ``None``

**Raises**:

- `ValueError`: if the object does not satisfy some requirements.

<a name="aea.helpers.search.models.And.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other: Any) -> bool
```

Compare with another object.

<a name="aea.helpers.search.models.And.encode"></a>
#### encode

```python
 | encode() -> models_pb2.Query.ConstraintExpr.And
```

Encode an instance of this class into a protocol buffer object.

**Returns**:

the matching protocol buffer object

<a name="aea.helpers.search.models.And.decode"></a>
#### decode

```python
 | @classmethod
 | decode(cls, and_pb: Any) -> "And"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

**Arguments**:

- `and_pb`: the protocol buffer object corresponding with this class.

**Returns**:

A new instance of this class matching the protocol buffer object

<a name="aea.helpers.search.models.Or"></a>
## Or Objects

```python
class Or(ConstraintExpr)
```

Implementation of the 'Or' constraint expression.

<a name="aea.helpers.search.models.Or.__init__"></a>
#### `__`init`__`

```python
 | __init__(constraints: List[ConstraintExpr]) -> None
```

Initialize an 'Or' expression.

**Arguments**:

- `constraints`: the list of constraints expressions (in disjunction).

<a name="aea.helpers.search.models.Or.check"></a>
#### check

```python
 | check(description: Description) -> bool
```

Check if a value satisfies the 'Or' constraint expression.

**Arguments**:

- `description`: the description to check.

**Returns**:

True if the description satisfy the constraint expression, False otherwise.

<a name="aea.helpers.search.models.Or.is_valid"></a>
#### is`_`valid

```python
 | is_valid(data_model: DataModel) -> bool
```

Check whether the constraint expression is valid wrt a data model.

**Arguments**:

- `data_model`: the data model used to check the validity of the constraint expression.

**Returns**:

``True`` if the constraint expression is valid wrt the data model, ``False`` otherwise.

<a name="aea.helpers.search.models.Or.check_validity"></a>
#### check`_`validity

```python
 | check_validity() -> None
```

Check whether the Constraint Expression satisfies some basic requirements.

:return ``None``

**Raises**:

- `ValueError`: if the object does not satisfy some requirements.

<a name="aea.helpers.search.models.Or.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other: Any) -> bool
```

Compare with another object.

<a name="aea.helpers.search.models.Or.encode"></a>
#### encode

```python
 | encode() -> models_pb2.Query.ConstraintExpr.Or
```

Encode an instance of this class into a protocol buffer object.

**Returns**:

the matching protocol buffer object

<a name="aea.helpers.search.models.Or.decode"></a>
#### decode

```python
 | @classmethod
 | decode(cls, or_pb: Any) -> "Or"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

**Arguments**:

- `or_pb`: the protocol buffer object corresponding with this class.

**Returns**:

A new instance of this class matching the protocol buffer object

<a name="aea.helpers.search.models.Not"></a>
## Not Objects

```python
class Not(ConstraintExpr)
```

Implementation of the 'Not' constraint expression.

<a name="aea.helpers.search.models.Not.__init__"></a>
#### `__`init`__`

```python
 | __init__(constraint: ConstraintExpr) -> None
```

Initialize a 'Not' expression.

**Arguments**:

- `constraint`: the constraint expression to negate.

<a name="aea.helpers.search.models.Not.check"></a>
#### check

```python
 | check(description: Description) -> bool
```

Check if a value satisfies the 'Not' constraint expression.

**Arguments**:

- `description`: the description to check.

**Returns**:

True if the description satisfy the constraint expression, False otherwise.

<a name="aea.helpers.search.models.Not.is_valid"></a>
#### is`_`valid

```python
 | is_valid(data_model: DataModel) -> bool
```

Check whether the constraint expression is valid wrt a data model.

**Arguments**:

- `data_model`: the data model used to check the validity of the constraint expression.

**Returns**:

``True`` if the constraint expression is valid wrt the data model, ``False`` otherwise.

<a name="aea.helpers.search.models.Not.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other: Any) -> bool
```

Compare with another object.

<a name="aea.helpers.search.models.Not.encode"></a>
#### encode

```python
 | encode() -> models_pb2.Query.ConstraintExpr.Not
```

Encode an instance of this class into a protocol buffer object.

**Returns**:

the matching protocol buffer object

<a name="aea.helpers.search.models.Not.decode"></a>
#### decode

```python
 | @classmethod
 | decode(cls, not_pb: Any) -> "Not"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

**Arguments**:

- `not_pb`: the protocol buffer object corresponding with this class.

**Returns**:

A new instance of this class matching the protocol buffer object

<a name="aea.helpers.search.models.Constraint"></a>
## Constraint Objects

```python
class Constraint(ConstraintExpr)
```

The atomic component of a constraint expression.

<a name="aea.helpers.search.models.Constraint.__init__"></a>
#### `__`init`__`

```python
 | __init__(attribute_name: str, constraint_type: ConstraintType) -> None
```

Initialize a constraint.

**Arguments**:

- `attribute_name`: the name of the attribute to be constrained.
- `constraint_type`: the constraint type.

<a name="aea.helpers.search.models.Constraint.check"></a>
#### check

```python
 | check(description: Description) -> bool
```

Check if a description satisfies the constraint. The implementation depends on the type of the constraint.

**Arguments**:

- `description`: the description to check.

**Returns**:

True if the description satisfies the constraint, False otherwise.

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

<a name="aea.helpers.search.models.Constraint.is_valid"></a>
#### is`_`valid

```python
 | is_valid(data_model: DataModel) -> bool
```

Check whether the constraint expression is valid wrt a data model.

**Arguments**:

- `data_model`: the data model used to check the validity of the constraint expression.

**Returns**:

``True`` if the constraint expression is valid wrt the data model, ``False`` otherwise.

<a name="aea.helpers.search.models.Constraint.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other: Any) -> bool
```

Compare with another object.

<a name="aea.helpers.search.models.Constraint.__str__"></a>
#### `__`str`__`

```python
 | __str__() -> str
```

Get the string representation of the constraint.

<a name="aea.helpers.search.models.Constraint.encode"></a>
#### encode

```python
 | encode() -> models_pb2.Query.ConstraintExpr.Constraint
```

Encode an instance of this class into a protocol buffer object.

**Returns**:

the matching protocol buffer object

<a name="aea.helpers.search.models.Constraint.decode"></a>
#### decode

```python
 | @classmethod
 | decode(cls, constraint_pb: Any) -> "Constraint"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

**Arguments**:

- `constraint_pb`: the protocol buffer object corresponding with this class.

**Returns**:

A new instance of this class matching the protocol buffer object

<a name="aea.helpers.search.models.Query"></a>
## Query Objects

```python
class Query()
```

This class lets you build a query for the OEF.

<a name="aea.helpers.search.models.Query.__init__"></a>
#### `__`init`__`

```python
 | __init__(constraints: List[ConstraintExpr], model: Optional[DataModel] = None) -> None
```

Initialize a query.

**Arguments**:

- `constraints`: a list of constraint expressions.
- `model`: the data model that the query refers to.

<a name="aea.helpers.search.models.Query.check"></a>
#### check

```python
 | check(description: Description) -> bool
```

Check if a description satisfies the constraints of the query.

The constraints are interpreted as conjunction.

**Arguments**:

- `description`: the description to check.

**Returns**:

True if the description satisfies all the constraints, False otherwise.

<a name="aea.helpers.search.models.Query.is_valid"></a>
#### is`_`valid

```python
 | is_valid(data_model: Optional[DataModel]) -> bool
```

Given a data model, check whether the query is valid for that data model.

**Arguments**:

- `data_model`: optional datamodel

**Returns**:

``True`` if the query is compliant with the data model, ``False`` otherwise.

<a name="aea.helpers.search.models.Query.check_validity"></a>
#### check`_`validity

```python
 | check_validity() -> None
```

Check whether the` object is valid.

:return ``None``

**Raises**:

- `ValueError`: if the query does not satisfy some sanity requirements.

<a name="aea.helpers.search.models.Query.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other: Any) -> bool
```

Compare with another object.

<a name="aea.helpers.search.models.Query.__str__"></a>
#### `__`str`__`

```python
 | __str__() -> str
```

Get the string representation of the constraint.

<a name="aea.helpers.search.models.Query.encode"></a>
#### encode

```python
 | @classmethod
 | encode(cls, query_pb: Any, query: "Query") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the query_protobuf_object argument must be matched
with the instance of this class in the 'query_object' argument.

**Arguments**:

- `query_pb`: the protocol buffer object wrapping an object that corresponds with this class.
- `query`: an instance of this class to be encoded in the protocol buffer object.

<a name="aea.helpers.search.models.Query.decode"></a>
#### decode

```python
 | @classmethod
 | decode(cls, query_pb: Any) -> "Query"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class must be created that matches the protocol
buffer object in the 'query_protobuf_object' argument.

**Arguments**:

- `query_pb`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'query_protobuf_object' argument.

<a name="aea.helpers.search.models.haversine"></a>
#### haversine

```python
haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float
```

Compute the Haversine distance between two locations (i.e. two pairs of latitude and longitude).

**Arguments**:

- `lat1`: the latitude of the first location.
- `lon1`: the longitude of the first location.
- `lat2`: the latitude of the second location.
- `lon2`: the longitude of the second location.

**Returns**:

the Haversine distance.

