<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.exceptions"></a>

# plugins.aea-ledger-ethereum-hwi.aea`_`ledger`_`ethereum`_`hwi.exceptions

Custom exceptions for hardware wallet interface

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.exceptions.HWIError"></a>

## HWIError Objects

```python
class HWIError(Exception)
```

Hardware wallet interface error

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.exceptions.HWIError.__init__"></a>

#### `__`init`__`

```python
def __init__(message: str, sw: int, data=None) -> None
```

Initialize object.

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.exceptions.HWIError.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

Serialize message to string

