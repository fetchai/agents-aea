<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_dialogues_memory_usage.command"></a>

# plugins.aea-cli-benchmark.aea`_`cli`_`benchmark.case`_`dialogues`_`memory`_`usage.command

Memory usage of dialogues across the time.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_dialogues_memory_usage.command.main"></a>

#### main

```python
@click.command(name="dialogues_mem_usage")
@click.option(
    "--messages",
    default=1000,
    help="Run time in seconds.",
    show_default=True,
)
@number_of_runs_deco
@output_format_deco
def main(messages: str, number_of_runs: int, output_format: str) -> Any
```

Check dialogues memory usage.

