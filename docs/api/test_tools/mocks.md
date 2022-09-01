<a id="aea.test_tools.mocks"></a>

# aea.test`_`tools.mocks

This module contains mocking utils testing purposes.

<a id="aea.test_tools.mocks.AnyStringWith"></a>

## AnyStringWith Objects

```python
class AnyStringWith(str)
```

Helper class to assert calls of mocked method with string arguments.

It will use string inclusion as equality comparator.

<a id="aea.test_tools.mocks.AnyStringWith.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other: Any) -> bool
```

Check equality.

<a id="aea.test_tools.mocks.RegexComparator"></a>

## RegexComparator Objects

```python
class RegexComparator(str)
```

Helper class to assert calls of mocked method with string arguments.

It will use regex matching as equality comparator.

<a id="aea.test_tools.mocks.RegexComparator.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other: Any) -> bool
```

Check equality.

<a id="aea.test_tools.mocks.ctx_mock_Popen"></a>

#### ctx`_`mock`_`Popen

```python
@contextmanager
def ctx_mock_Popen() -> Generator
```

Mock subprocess.Popen.

Act as context manager.

:yield: mock generator.

