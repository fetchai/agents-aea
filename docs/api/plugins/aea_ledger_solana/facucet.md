<a id="plugins.aea-ledger-solana.aea_ledger_solana.facucet"></a>

# plugins.aea-ledger-solana.aea`_`ledger`_`solana.facucet

<a id="plugins.aea-ledger-solana.aea_ledger_solana.facucet.SolanaFaucetApi"></a>

## SolanaFaucetApi Objects

```python
class SolanaFaucetApi(FaucetApi)
```

Solana testnet faucet API.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.facucet.SolanaFaucetApi.get_wealth"></a>

#### get`_`wealth

```python
def get_wealth(address: Address, url: Optional[str] = None) -> None
```

Get wealth from the faucet for the provided address.

**Arguments**:

- `address`: the address.
- `url`: the url

