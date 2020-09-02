<a name="aea.exceptions"></a>
# aea.exceptions

Exceptions for the AEA package.

<a name="aea.exceptions.AEAException"></a>
## AEAException Objects

```python
class AEAException(Exception)
```

User-defined exception for the AEA framework.

<a name="aea.exceptions.AEAPackageLoadingError"></a>
## AEAPackageLoadingError Objects

```python
class AEAPackageLoadingError(AEAException)
```

Class for exceptions that are raised for loading errors of AEA packages.

<a name="aea.exceptions.AEAEnforceError"></a>
## AEAEnforceError Objects

```python
class AEAEnforceError(AEAException)
```

Class for enforcement errors.

<a name="aea.exceptions.enforce"></a>
#### enforce

```python
enforce(is_valid_condition: bool, exception_text: str, exception_class: Type[Exception] = AEAEnforceError) -> None
```

Evaluate a condition and raise an exception with the provided text if it is not satisfied.

**Arguments**:

- `is_valid_condition`: the valid condition
- `exception_text`: the exception to be raised
- `exception_class`: the class of exception

