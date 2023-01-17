<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_acn_communication.command"></a>

# plugins.aea-cli-benchmark.aea`_`cli`_`benchmark.case`_`acn`_`communication.command

Check amount of time for acn connection start.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_acn_communication.command.main"></a>

#### main

```python
@click.command(name="acn_communicate")
@click.option(
    "--connection",
    default="p2pnode",
    help="Connection to use.",
    show_default=True,
    type=click.Choice(["p2pnode", "mailbox", "client"]),
)
@click.option(
    "--connect-times",
    default=10,
    help="How many connection attempts.",
    show_default=True,
)
@number_of_runs_deco
@output_format_deco
def main(connection: str, connect_times: int, number_of_runs: int,
         output_format: str) -> Any
```

Check connection connect time.

