<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.command"></a>

# plugins.aea-cli-benchmark.aea`_`cli`_`benchmark.case`_`tx`_`generate.command

Ledger TX generation and processing benchmark.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.command.main"></a>

#### main

```python
@click.command(name="tx_generate")
@click.option(
    "--ledger_id",
    type=click.Choice(["ethereum", "fetchai"]),
    default="fetchai",
    help="Ledger id",
    show_default=True,
)
@click.option(
    "--test-time",
    default=30,
    help="Time to generate txs in seconds",
    show_default=True,
    type=float,
)
@number_of_runs_deco
@output_format_deco
def main(ledger_id: str, test_time: float, number_of_runs: int,
         output_format: str) -> Any
```

Check performance of decision maker on signature signing.

