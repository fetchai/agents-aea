<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_reactive.command"></a>

# plugins.aea-cli-benchmark.aea`_`cli`_`benchmark.case`_`reactive.command

Latency and throughput check.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_reactive.command.main"></a>

#### main

```python
@click.command(name="reactive")
@click.option(
    "--duration",
    default=1,
    help="Run time in seconds.",
    show_default=True,
)
@runtime_mode_deco
@click.option(
    "--connection_mode",
    type=click.Choice(["sync", "nonsync"]),
    default="sync",
    help="Connection mode: sync or nonsync.",
    show_default=True,
)
@number_of_runs_deco
@output_format_deco
def main(duration: int, runtime_mode: str, connection_mode: str,
         number_of_runs: int, output_format: str) -> Any
```

Check envelopes send/received rate within connection.

