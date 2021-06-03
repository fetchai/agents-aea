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

<a name="aea.exceptions.AEASetupError"></a>
## AEASetupError Objects

```python
class AEASetupError(AEAException)
```

Class for exceptions that are raised for setup errors of AEA packages.

<a name="aea.exceptions.AEATeardownError"></a>
## AEATeardownError Objects

```python
class AEATeardownError(AEAException)
```

Class for exceptions that are raised for teardown errors of AEA packages.

<a name="aea.exceptions.AEAActException"></a>
## AEAActException Objects

```python
class AEAActException(AEAException)
```

Class for exceptions that are raised for act errors of AEA packages.

<a name="aea.exceptions.AEAHandleException"></a>
## AEAHandleException Objects

```python
class AEAHandleException(AEAException)
```

Class for exceptions that are raised for handler errors of AEA packages.

<a name="aea.exceptions.AEAInstantiationException"></a>
## AEAInstantiationException Objects

```python
class AEAInstantiationException(AEAException)
```

Class for exceptions that are raised for instantiation errors of AEA packages.

<a name="aea.exceptions.AEAPluginError"></a>
## AEAPluginError Objects

```python
class AEAPluginError(AEAException)
```

Class for exceptions that are raised for wrong plugin setup of the working set.

<a name="aea.exceptions.AEAEnforceError"></a>
## AEAEnforceError Objects

```python
class AEAEnforceError(AEAException)
```

Class for enforcement errors.

<a name="aea.exceptions.AEAValidationError"></a>
## AEAValidationError Objects

```python
class AEAValidationError(AEAException)
```

Class for validation errors of an AEA.

<a name="aea.exceptions.AEAComponentLoadException"></a>
## AEAComponentLoadException Objects

```python
class AEAComponentLoadException(AEAException)
```

Class for component loading errors of an AEA.

<a name="aea.exceptions.AEAWalletNoAddressException"></a>
## AEAWalletNoAddressException Objects

```python
class AEAWalletNoAddressException(AEAException)
```

Class for attempts to instantiate a wallet without addresses.

<a name="aea.exceptions._StopRuntime"></a>
## `_`StopRuntime Objects

```python
class _StopRuntime(Exception)
```

Exception to stop runtime.

For internal usage only!
Used to perform asyncio call from sync callbacks.

<a name="aea.exceptions._StopRuntime.__init__"></a>
#### `__`init`__`

```python
 | __init__(reraise: Optional[Exception] = None) -> None
```

Init _StopRuntime exception.

**Arguments**:

- `reraise`: exception to reraise.

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

<a name="aea.exceptions.parse_exception"></a>
#### parse`_`exception

```python
parse_exception(exception: Exception, limit: int = -1) -> str
```

Parse an exception to get the relevant lines.

**Arguments**:

- `exception`: the exception to be parsed
- `limit`: the limit

**Returns**:

exception as string

