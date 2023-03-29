<a id="plugins.aea-ledger-solana.aea_ledger_solana.faucet"></a>

# plugins.aea-ledger-solana.aea`_`ledger`_`solana.faucet

This module contains the Faucet implementation for the solana ledger.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.faucet.SolanaFaucetApi"></a>

## SolanaFaucetApi Objects

```python
class SolanaFaucetApi(FaucetApi)
```

Solana testnet faucet API.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.faucet.SolanaFaucetApi.get_wealth"></a>

#### get`_`wealth

```python
def get_wealth(address: Address, url: Optional[str] = None) -> None
```

Get wealth from the faucet for the provided address.

**Arguments**:

- `address`: the address.
- `url`: the url

<a id="plugins.aea-ledger-solana.aea_ledger_solana.faucet.SolanaFaucetApi.try_get_wealth"></a>

#### try`_`get`_`wealth

```python
@staticmethod
@try_decorator(
    "An error occurred while attempting to generate wealth:\n{}",
    logger_method="error",
)
def try_get_wealth(address: Address,
                   amount: Optional[int] = None,
                   url: Optional[str] = None) -> Optional[str]
```

Get wealth from the faucet for the provided address.

**Arguments**:

- `address`: the address.
- `amount`: optional int
- `url`: the url

**Returns**:

optional string

<a id="plugins.aea-ledger-solana.aea_ledger_solana.faucet.SolanaFaucetApi.generate_wealth_if_needed"></a>

#### generate`_`wealth`_`if`_`needed

```python
@staticmethod
def generate_wealth_if_needed(api,
                              address,
                              min_amount=None) -> Union[str, None]
```

Check the balance prior to generating wealth.

