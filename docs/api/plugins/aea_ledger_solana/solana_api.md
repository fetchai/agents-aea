<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana_api"></a>

# plugins.aea-ledger-solana.aea`_`ledger`_`solana.solana`_`api

This module contains the Solana API Client implementation for the solana ledger.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana_api.SolanaApiClient"></a>

## SolanaApiClient Objects

```python
@dataclass
class SolanaApiClient(ApiClient)
```

Class to interact with the Solana ledger APIs.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana_api.SolanaApiClient.__init__"></a>

#### `__`init`__`

```python
def __init__(*args, **kwargs)
```

Instantiate the client.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana_api.SolanaApiClient.transfer"></a>

#### transfer

```python
def transfer(*args, **kwargs)
```

Transfer tokens.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana_api.SolanaApiClient.get_create_account_instructions"></a>

#### get`_`create`_`account`_`instructions

```python
def get_create_account_instructions(sender_address,
                                    destination_address,
                                    lamports: int = 100000,
                                    space: int = 1)
```

Create a new account.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana_api.SolanaApiClient.get_transfer_tx"></a>

#### get`_`transfer`_`tx

```python
def get_transfer_tx(from_account, to_account, amount)
```

Create a transfer tx.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana_api.SolanaApiClient.get_account_state"></a>

#### get`_`account`_`state

```python
def get_account_state(account_address: str)
```

Get account state.

