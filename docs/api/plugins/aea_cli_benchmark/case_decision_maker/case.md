<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_decision_maker.case"></a>

# plugins.aea-cli-benchmark.aea`_`cli`_`benchmark.case`_`decision`_`maker.case

Memory usage check.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_decision_maker.case.SigningDialogues"></a>

## SigningDialogues Objects

```python
class SigningDialogues(BaseSigningDialogues)
```

This class keeps track of all oef_search dialogues.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_decision_maker.case.SigningDialogues.__init__"></a>

#### `__`init`__`

```python
def __init__(self_address: Address) -> None
```

Initialize dialogues.

**Arguments**:

- `self_address`: the address of the entity for whom dialogues are maintained

**Returns**:

None

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_decision_maker.case.make_desc_maker_wallet"></a>

#### make`_`desc`_`maker`_`wallet

```python
def make_desc_maker_wallet(ledger_id: str,
                           key_path: str) -> Tuple[DecisionMaker, Wallet]
```

Construct decision maker and wallet.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_decision_maker.case.sign_txs"></a>

#### sign`_`txs

```python
def sign_txs(decision_maker: DecisionMaker, wallet: Wallet, num_runs: int,
             ledger_id: str) -> float
```

Sign txs sprcified amount fo runs and return time taken (seconds).

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_decision_maker.case.run"></a>

#### run

```python
def run(ledger_id: str,
        amount_of_tx: int) -> List[Tuple[str, Union[int, float]]]
```

Check memory usage.

