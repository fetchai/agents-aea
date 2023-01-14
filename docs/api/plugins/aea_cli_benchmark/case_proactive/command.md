<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_proactive.command"></a>

# plugins.aea-cli-benchmark.aea`_`cli`_`benchmark.case`_`proactive.command

Envelopes generation speed for Behaviour act test.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_proactive.command.main"></a>

#### main

```python
@click.command(name="proactive")
@click.option(
    "--duration",
    default=3,
    help="Run time in seconds.",
    show_default=True,
)
@runtime_mode_deco
@number_of_runs_deco
@output_format_deco
def main(duration: int, runtime_mode: str, number_of_runs: int,
         output_format: str) -> Any
```

Check envelopes send/receive rate within behaviour.

