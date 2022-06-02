<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_messages_memory_usage.command"></a>

# plugins.aea-cli-benchmark.aea`_`cli`_`benchmark.case`_`messages`_`memory`_`usage.command

Memory usage of huge amount of messages.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_messages_memory_usage.command.main"></a>

#### main

```python
@click.command(name="messages_mem_usage")
@click.option(
    "--messages",
    default=10**6,
    help="Amount of messages.",
    show_default=True,
)
@number_of_runs_deco
@output_format_deco
def main(messages: int, number_of_runs: int, output_format: str) -> Any
```

Check messages memory usage.

