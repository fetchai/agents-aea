We recommend reading <a href="../defining-data-model">Defining a Data Model</a> before reading this section.

Along with the Data Model language, the AEA framework offers the possibility to specify `queries` defined over data models.

The `aea.helpers.search` module implements the API that allows you to build queries.

In one sentence, a `query` is a set of `constraints`, defined over a `data model`.
The outcome is a set of `description` (that is, instances of `Description`)
`matching` with the query. That is, all the description whose attributes satisfy the constraints in the query.

In the next sections, we describe how to build queries with the SDK.

## Constraints

A `constraint` is associated with an `attribute name` and imposes restrictions on the domain of that attribute.
That is, it imposes some limitations on the values the attribute can assume.

We have different types of constraints:

* `relation` constraints:

  * the author of the book must be `Stephen King`
  * the publication year must be greater than 1990

* `set` constraints:

  * the genre must fall into the following set of genres: `Horror`, `Science fiction`, `Non-fiction`.

* `range` constraints:

  * the average rating must be between 3.5 and 4.5

* `distance` constraints:

  * the nearest bookshop must be within a distance from a given location.

The class that implements the constraint concept is :class:`~oef.query.Constraint`
In the following, we show how to define them in the Python SDK.

### Relation

There are several constraint types that allows you to impose specific values for the attributes.

The types of relation constraints are:

* Equal: `==`
* Not Equal: `!=`
* Less than: `<`
* Less than or Equal: `<=`
* Greater than: `>`
* Greater than or Equal: `>=`

**Examples**: using the attributes we used before: 

``` python
from aea.helpers.search.models import Constraint, ConstraintType

# all the books whose author is Stephen King
Constraint("author", ConstraintType("==", "Stephen King"))

# all the books that are not of the genre Horror
Constraint("genre", ConstraintType("!=", "Horror"))

# all the books published before 1990
Constraint("year", ConstraintType("<", 1990))

# the same of before, but including 1990
Constraint("year", ConstraintType("<=", 1990))

# all the books with rating greater than 4.0
Constraint("average_rating", ConstraintType(">", 4.0))

# all the books published after 2000, included
Constraint("year", ConstraintType(">=", 2000))
```

### Set

The `set` is a constraint type that allows you to restrict the values of the attribute
in a specific set.

There are two kind of ``set`` constraints:

* In (a set of values): `in`
* Not in (a set of values): `not_in`


**Examples**:

``` python
from aea.helpers.search.models import Constraint, ConstraintType

# all the books whose genre is one of `Horror`, `Science fiction`, `Non-fiction`
Constraint("genre", ConstraintType("in", ["horror", "science fiction", "non-fiction"]))

# all the books that have not been published neither in 1990, nor in 1995, nor in 2000
Constraint("year", ConstraintType("not_in", [1990, 1995, 2000]))
```

## Range

The `range` is a constraint type that allows you to restrict the values of the attribute in a given range.


**Examples**:

``` python
from aea.helpers.search.models import Constraint, ConstraintType

# all the books whose title is between 'A' and 'B' (alphanumeric order)
Constraint("title", ConstraintType("within", ("A", "B")))

# all the books that have been published between 1960 and 1970
Constraint("genre", ConstraintType("within", (1960, 1970))
```

### Distance

The `distance` is a constraint type that allows you to put a limit on a `Location` attribute type. More specifically, you can set a maximum distance from a given location (the `center`), such that will be considered only the instances whose location attribute value is within a distance from the center.

**Examples**:

``` python
from aea.helpers.search.models import Constraint, ConstraintType, Description, Location, 

# define a location of interest, e.g. the Tour Eiffel
tour_eiffel = Location(48.8581064, 2.29447)

# find all the locations close to the Tour Eiffel within 1 km
close_to_tour_eiffel = Constraint("position", ConstraintType("distance", (tour_eiffel, 1.0)))

# Le Jules Verne, a famous restaurant close to the Tour Eiffel, satisfies the constraint.
le_jules_verne_restaurant = Location(48.8579675, 2.2951849)
close_to_tour_eiffel.check(Description({"position": le_jules_verne_restaurant}))  # gives `True`

# The Colosseum does not satisfy the constraint (farther than 1 km from the Tour Eiffel).
colosseum = Location(41.8902102, 12.4922309)
close_to_tour_eiffel.check(Description({"position": colosseum}))  # gives `False`
```

## Constraint Expressions

The constraints above mentioned can be combined with the common logical operators (i.e. and, or and not), yielding more complex expression.

In particular we can specify any conjunction/disjunction/negations of the previous constraints or composite constraint expressions, e.g.:

* books that belong to `Horror` **and** has been published after 2000, but **not** published by `Stephen King`.
* books whose author is **either** `J. K. Rowling` **or** `J. R. R. Tolkien`

The classes that implement these operators are `Not`, `And` and `Or`.

### Not

The `Not` is a constraint expression that allows you to specify a negation of a constraint expression. The `Not` constraint is satisfied whenever its subexpression is `not` satisfied.

**Example**:

``` python
from aea.helpers.search.models import Constraint, ConstraintType, Not

# all the books whose year of publication is not between 1990 and 2000
Not(Constraint("year", ConstraintType("within", (1990, 2000)))
```

### And

The `And` is a constraint type that allows you to specify a conjunction of constraints over an attribute. That is, the `And` constraint is satisfied whenever all the subexpressions that constitute the `and` are satisfied.

Notice: the number of subexpressions must be **at least** 2.

**Example**:

``` python
from aea.helpers.search.models import Constraint, ConstraintType, And

# all the books whose title is between 'I' and 'J' (alphanumeric order) but not equal to 'It'
And([Constraint("title", ConstraintType("within", ("I", "J"))), Constraint("title", ConstraintType("!=", "It"))])
```

### Or

The class `Or` is a constraint type that allows you to specify a disjunction of constraints. That is, the ``Or`` constraint is satisfied whenever at least one of the constraints that constitute the ``or`` is satisfied.

Notice: the number of subexpressions must be **at least** 2.

**Example**:

``` python
from aea.helpers.search.models import Constraint, ConstraintType, Or

# all the books that have been published either before the year 1960 or after the year 1970
Or([Constraint("year", ConstraintType("<", 1960)), Constraint("year", ConstraintType(">", 1970))])
```

## Queries

A `query` is simply a `list of constraint expressions`, interpreted as a conjunction
(that is, a matching description with the query must satisfy `every` constraint expression.)

**Examples**:

``` python
from aea.helpers.search.models import Query, Constraint, ConstraintType

# query all the books written by Stephen King published after 1990, and available as an e-book:
Query([
    Constraint("author", ConstraintType("==", "Stephen King")),
    Constraint("year", ConstraintType(">=", 1990)),
    Constraint("ebook_available", ConstraintType("==", True))
], book_model)
```

Where ``book_model`` is the ``DataModel`` object defined in :ref:`defining-data-model`. However, the data model is
an optional parameter, but to avoid ambiguity is recommended to include it.

### The ``check`` method

The `Query` class supports a way to check whether a `Description` matches with the query. This method is called `Query.check`.

Examples:

``` python
from aea.helpers.search.models import Query, Constraint, ConstraintType
from aea.helpers.search.models import Description

q = Query([
    Constraint("author", ConstraintType("==", "Stephen King")),
    Constraint("year", ConstraintType(">=", 1990)),
    Constraint("ebook_available", ConstraintType("==", True))
    ])

# With a query, you can check that a `Description` object satisfies the constraints.
q.check(Description({"author": "Stephen King", "year": 1991, "ebook_available": True}))  # True
q.check(Description({"author": "George Orwell", "year": 1948, "ebook_available": False})) # False
```

### Validity

A `Query` object must satisfy some conditions in order to be instantiated.

- The list of constraints expressions can't be empty; must have at least one constraint expression.
- If the data model is specified:

    - For every constraint expression that constitute the query, check if they are `valid wrt the data model`.


A `ConstraintExpr` `c` (that is, one of `And`, `Or`, `Not`, `Constraint`) is `valid wrt a` `DataModel` if:

- If `c` is an instance of `And`, `Or` or `Not`, then
  every subexpression of `c` must be valid (wrt to the data model);
- If `c` is an instance of `Constraint`, then:
    - if the constraint type is one of `<`, `<=`, `>`,
      `>=`, the value in the constructor must be one of ``str``, ``int`` or ``float``.
    - if the constraint type is a `within`, then the types in the range must be one of ``int``, ``str``, ``float`` or `Location`.
    - if the constraint type is a `distance`, then the only valid type is `Location`.
    - if the constraint type is a `in`, then the types supported are
      ``str``, ``int``, ``float``, ``bool``, `Location`. Notice though that a set of ``bool`` is trivial, so you may find yourself more comfortable by using other alternatives.
    - for the other constraint types, i.e. `==` and `!=`, the value can be one of the allowed types for `Attribute`, that is ``str``, ``int``, ``float``, ``bool``, `Location`.

- Moreover, when `c` is a `Constraint`, the attribute must have a consistent type wrt the data model.
  E.g. consider a `Constraint` like:

``` python
Constraint("foo", ConstraintType("==", True))
```

Consider a `DataModel` where there is an `AttributeSchema` ``"foo"`` of type ``str``. Then the constraint is not compatible with the mentioned data model, because the constraint expect an equality comparison with a boolean ``True``, instead of a ``str``.

