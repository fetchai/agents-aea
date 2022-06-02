<a id="aea.crypto.ledger_apis"></a>

# aea.crypto.ledger`_`apis

Module wrapping all the public and private keys cryptography.

<a id="aea.crypto.ledger_apis.LedgerApis"></a>

## LedgerApis Objects

```python
class LedgerApis()
```

Store all the ledger apis we initialise.

<a id="aea.crypto.ledger_apis.LedgerApis.has_ledger"></a>

#### has`_`ledger

```python
@staticmethod
def has_ledger(identifier: str) -> bool
```

Check if it has the api.

<a id="aea.crypto.ledger_apis.LedgerApis.get_api"></a>

#### get`_`api

```python
@classmethod
def get_api(cls, identifier: str) -> LedgerApi
```

Get the ledger API.

<a id="aea.crypto.ledger_apis.LedgerApis.get_balance"></a>

#### get`_`balance

```python
@classmethod
def get_balance(cls, identifier: str, address: str) -> Optional[int]
```

Get the token balance.

**Arguments**:

- `identifier`: the identifier of the ledger
- `address`: the address to check for

**Returns**:

the token balance

<a id="aea.crypto.ledger_apis.LedgerApis.get_transfer_transaction"></a>

#### get`_`transfer`_`transaction

