<a name="aea.configurations.pypi"></a>
# aea.configurations.pypi

This module contains a checker for PyPI version consistency.

<a name="aea.configurations.pypi.and_"></a>
#### and`_`

```python
and_(s1: SpecifierSet, s2: SpecifierSet) -> SpecifierSet
```

Do the and between two specifier sets.

<a name="aea.configurations.pypi.is_satisfiable"></a>
#### is`_`satisfiable

```python
is_satisfiable(specifier_set: SpecifierSet) -> bool
```

Check if the specifier set is satisfiable.

Satisfiable means that there exists a version number
that satisfies all the constraints. It is worth
noticing that it doesn't mean that that version
number with that package actually exists.

>>> from packaging.specifiers import SpecifierSet

The specifier set ">0.9, ==1.0" is satisfiable:
the version number "1.0" satisfies the constraints

>>> s1 = SpecifierSet(">0.9,==1.0")
>>> "1.0" in s1
True
>>> is_satisfiable(s1)
True

The specifier set "==1.0, >1.1" is not satisfiable:

>>> s1 = SpecifierSet("==1.0,>1.1")
>>> is_satisfiable(s1)
False

For other details, please refer to PEP440:

    https://www.python.org/dev/peps/pep-0440

**Arguments**:

- `specifier_set`: the specifier set.

**Returns**:

False if the constraints are surely non-satisfiable, True if we don't know.

<a name="aea.configurations.pypi.is_simple_dep"></a>
#### is`_`simple`_`dep

```python
is_simple_dep(dep: Dependency) -> bool
```

Check if it is a simple dependency.

Namely, if it has no field specified, or only the 'version' field set.

**Arguments**:

- `dep`: the dependency

**Returns**:

whether it is a simple dependency or not

<a name="aea.configurations.pypi.to_set_specifier"></a>
#### to`_`set`_`specifier

```python
to_set_specifier(dep: Dependency) -> SpecifierSet
```

Get the set specifier. It assumes to be a simple dependency (see above).

<a name="aea.configurations.pypi.merge_dependencies"></a>
#### merge`_`dependencies

```python
merge_dependencies(dep1: Dependencies, dep2: Dependencies) -> Dependencies
```

Merge two groups of dependencies.

If some of them are not "simple" (see above), and there is no risk
of conflict because there is no other package with the same name,
we leave them; otherwise we raise an error.

**Arguments**:

- `dep1`: the first operand
- `dep2`: the second operand.

**Returns**:

the merged dependencies.

<a name="aea.configurations.pypi.merge_dependencies_list"></a>
#### merge`_`dependencies`_`list

```python
merge_dependencies_list(*deps: Dependencies) -> Dependencies
```

Merge a list of dependencies.

**Arguments**:

- `deps`: the list of dependencies

**Returns**:

the merged dependencies.

