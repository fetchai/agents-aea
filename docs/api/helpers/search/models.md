<a name=".aea.helpers.search.models"></a>
## aea.helpers.search.models

Useful classes for the OEF search.

<a name=".aea.helpers.search.models.Attribute"></a>
### Attribute

```python
class Attribute()
```

Implements an attribute for an OEF data model.

<a name=".aea.helpers.search.models.Attribute.__init__"></a>
#### `__`init`__`

```python
 | __init__(name: str, type: Type[ATTRIBUTE_TYPES], is_required: bool, description: str = "")
```

Initialize an attribute.

**Arguments**:

- `name`: the name of the attribute.
- `type`: the type of the attribute.
- `is_required`: whether the attribute is required by the data model.
- `description`: an (optional) human-readable description for the attribute.

<a name=".aea.helpers.search.models.Attribute.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other)
```

Compare with another object.

<a name=".aea.helpers.search.models.DataModel"></a>
### DataModel

```python
class DataModel()
```

Implements an OEF data model.

<a name=".aea.helpers.search.models.DataModel.__init__"></a>
#### `__`init`__`

```python
 | __init__(name: str, attributes: List[Attribute], description: str = "")
```

Initialize a data model.

**Arguments**:

- `name`: the name of the data model.
- `attributes`: the attributes of the data model.

<a name=".aea.helpers.search.models.DataModel.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other) -> bool
```

Compare with another object.

<a name=".aea.helpers.search.models.Description"></a>
### Description

```python
class Description()
```

Implements an OEF description.

<a name=".aea.helpers.search.models.Description.__init__"></a>
#### `__`init`__`

```python
 | __init__(values: Dict, data_model: Optional[DataModel] = None)
```

Initialize the description object.

**Arguments**:

- `values`: the values in the description.

<a name=".aea.helpers.search.models.Description.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other) -> bool
```

Compare with another object.

<a name=".aea.helpers.search.models.Description.__iter__"></a>
#### `__`iter`__`

```python
 | __iter__()
```

Create an iterator.

<a name=".aea.helpers.search.models.Description.encode"></a>
#### encode

```python
 | @classmethod
 | encode(cls, performative_content, description_from_message: "Description") -> None
```

Encode an instance of this class into the protocol buffer object.

The content in the 'performative_content' argument must be matched with the message content in the 'description_from_message' argument.

**Arguments**:

- `performative_content`: the performative protocol buffer object containing a content whose type is this class.
- `description_from_message`: the message content to be encoded in the protocol buffer object.

**Returns**:

None

<a name=".aea.helpers.search.models.Description.decode"></a>
#### decode

```python
 | @classmethod
 | decode(cls, description_from_pb2) -> "Description"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class must be created that matches the content in the 'description_from_pb2' argument.

**Arguments**:

- `description_from_pb2`: the protocol buffer content object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'description_from_pb2' argument.

<a name=".aea.helpers.search.models.ConstraintTypes"></a>
### ConstraintTypes

```python
class ConstraintTypes(Enum)
```

Types of constraint.

<a name=".aea.helpers.search.models.ConstraintTypes.__str__"></a>
#### `__`str`__`

```python
 | __str__()
```

Get the string representation.

<a name=".aea.helpers.search.models.ConstraintType"></a>
### ConstraintType

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
  >>> in_a_set = ConstraintType("in", [1, 2, 3])
  >>> not_in_a_set = ConstraintType("not_in", {"C", "Java", "Python"})

<a name=".aea.helpers.search.models.ConstraintType.__init__"></a>
#### `__`init`__`

```python
 | __init__(type: Union[ConstraintTypes, str], value: Any)
```

Initialize a constraint type.

**Arguments**:

- `type`: the type of the constraint.
| Either an instance of the ConstraintTypes enum,
| or a string representation associated with the type.
- `value`: the value that defines the constraint.

**Raises**:

- `ValueError`: if the type of the constraint is not

<a name=".aea.helpers.search.models.ConstraintType.check"></a>
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

<a name=".aea.helpers.search.models.ConstraintType.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other)
```

Check equality with another object.

<a name=".aea.helpers.search.models.ConstraintExpr"></a>
### ConstraintExpr

```python
class ConstraintExpr(ABC)
```

Implementation of the constraint language to query the OEF node.

<a name=".aea.helpers.search.models.ConstraintExpr.check"></a>
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

<a name=".aea.helpers.search.models.And"></a>
### And

```python
class And(ConstraintExpr)
```

Implementation of the 'And' constraint expression.

<a name=".aea.helpers.search.models.And.__init__"></a>
#### `__`init`__`

```python
 | __init__(constraints: List[ConstraintExpr])
```

Initialize an 'And' expression.

**Arguments**:

- `constraints`: the list of constraints expression (in conjunction).

<a name=".aea.helpers.search.models.And.check"></a>
#### check

```python
 | check(description: Description) -> bool
```

Check if a value satisfies the 'And' constraint expression.

**Arguments**:

- `description`: the description to check.

**Returns**:

True if the description satisfy the constraint expression, False otherwise.

<a name=".aea.helpers.search.models.And.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other)
```

Compare with another object.

<a name=".aea.helpers.search.models.Or"></a>
### Or

```python
class Or(ConstraintExpr)
```

Implementation of the 'Or' constraint expression.

<a name=".aea.helpers.search.models.Or.__init__"></a>
#### `__`init`__`

```python
 | __init__(constraints: List[ConstraintExpr])
```

Initialize an 'Or' expression.

**Arguments**:

- `constraints`: the list of constraints expressions (in disjunction).

<a name=".aea.helpers.search.models.Or.check"></a>
#### check

```python
 | check(description: Description) -> bool
```

Check if a value satisfies the 'Or' constraint expression.

**Arguments**:

- `description`: the description to check.

**Returns**:

True if the description satisfy the constraint expression, False otherwise.

<a name=".aea.helpers.search.models.Or.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other)
```

Compare with another object.

<a name=".aea.helpers.search.models.Not"></a>
### Not

```python
class Not(ConstraintExpr)
```

Implementation of the 'Not' constraint expression.

<a name=".aea.helpers.search.models.Not.__init__"></a>
#### `__`init`__`

```python
 | __init__(constraint: ConstraintExpr)
```

Initialize a 'Not' expression.

**Arguments**:

- `constraint`: the constraint expression to negate.

<a name=".aea.helpers.search.models.Not.check"></a>
#### check

```python
 | check(description: Description) -> bool
```

Check if a value satisfies the 'Not; constraint expression.

**Arguments**:

- `description`: the description to check.

**Returns**:

True if the description satisfy the constraint expression, False otherwise.

<a name=".aea.helpers.search.models.Not.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other)
```

Compare with another object.

<a name=".aea.helpers.search.models.Constraint"></a>
### Constraint

```python
class Constraint(ConstraintExpr)
```

The atomic component of a constraint expression.

<a name=".aea.helpers.search.models.Constraint.__init__"></a>
#### `__`init`__`

```python
 | __init__(attribute_name: str, constraint_type: ConstraintType)
```

Initialize a constraint.

**Arguments**:

- `attribute_name`: the name of the attribute to be constrained.
- `constraint_type`: the constraint type.

<a name=".aea.helpers.search.models.Constraint.check"></a>
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

<a name=".aea.helpers.search.models.Constraint.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other)
```

Compare with another object.

<a name=".aea.helpers.search.models.Query"></a>
### Query

```python
class Query()
```

This class lets you build a query for the OEF.

<a name=".aea.helpers.search.models.Query.__init__"></a>
#### `__`init`__`

```python
 | __init__(constraints: List[ConstraintExpr], model: Optional[DataModel] = None) -> None
```

Initialize a query.

**Arguments**:

- `constraints`: a list of constraint expressions.
- `model`: the data model that the query refers to.

<a name=".aea.helpers.search.models.Query.check"></a>
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

<a name=".aea.helpers.search.models.Query.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other)
```

Compare with another object.

<a name=".aea.helpers.search.models.Query.encode"></a>
#### encode

```python
 | @classmethod
 | encode(cls, performative_content, query_from_message: "Query") -> None
```

Encode an instance of this class into the protocol buffer object.

The content in the 'performative_content' argument must be matched with the message content in the 'query_from_message' argument.

**Arguments**:

- `performative_content`: the performative protocol buffer object containing a content whose type is this class.
- `query_from_message`: the message content to be encoded in the protocol buffer object.

**Returns**:

None

<a name=".aea.helpers.search.models.Query.decode"></a>
#### decode

```python
 | @classmethod
 | decode(cls, query_from_pb2) -> "Query"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class must be created that matches the content in the 'query_from_pb2' argument.

**Arguments**:

- `query_from_pb2`: the protocol buffer content object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'query_from_pb2' argument.

