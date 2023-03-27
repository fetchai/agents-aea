<a id="plugins.aea-ledger-solana.aea_ledger_solana.transaction"></a>

# plugins.aea-ledger-solana.aea`_`ledger`_`solana.transaction

This module contains the transaction helper for the solana module.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.transaction.SolanaTransaction"></a>

## SolanaTransaction Objects

```python
class SolanaTransaction(Transaction)
```

Class to represent a solana ledger transaction.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.transaction.SolanaTransaction.from_json"></a>

#### from`_`json

```python
@classmethod
def from_json(cls, json_data: dict) -> "SolanaTransaction"
```

Convert from a json.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.transaction.SolanaTransaction.to_json"></a>

#### to`_`json

```python
def to_json() -> dict
```

Convert to json.

