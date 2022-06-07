<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.ledger_utils"></a>

# plugins.aea-cli-benchmark.aea`_`cli`_`benchmark.case`_`tx`_`generate.ledger`_`utils

Ledger TX generation and processing benchmark.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.ledger_utils.fund_accounts_from_local_validator"></a>

#### fund`_`accounts`_`from`_`local`_`validator

```python
def fund_accounts_from_local_validator(addresses: List[str],
                                       amount: int,
                                       denom: str = DEFAULT_DENOMINATION)
```

Send funds to local accounts from the local genesis validator.

