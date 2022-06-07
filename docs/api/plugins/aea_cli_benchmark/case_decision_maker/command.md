<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_decision_maker.command"></a>

# plugins.aea-cli-benchmark.aea`_`cli`_`benchmark.case`_`decision`_`maker.command

Memory usage check.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_decision_maker.command.main"></a>

#### main

```python
@click.command(name="decision_maker")
@click.option(
    "--ledger_id",
    type=click.Choice(["ethereum", "cosmos", "fetchai"]),
    default="fetchai",
    help="Ledger id",
    show_default=True,
)
@click.option("--amount_of_tx",
              default=100,
              help="Amount of tx to sign",
              show_default=True)
@number_of_runs_deco
@output_format_deco
def main(ledger_id: str, amount_of_tx: int, number_of_runs: int,
         output_format: str) -> Any
```

Check performance of decision maker on signature signing.

