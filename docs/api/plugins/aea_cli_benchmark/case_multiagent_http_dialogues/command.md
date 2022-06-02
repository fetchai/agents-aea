<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_multiagent_http_dialogues.command"></a>

# plugins.aea-cli-benchmark.aea`_`cli`_`benchmark.case`_`multiagent`_`http`_`dialogues.command

Memory usage across the time.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_multiagent_http_dialogues.command.main"></a>

#### main

```python
@click.command(name="multiagent_http_dialogues")
@click.option(
    "--duration",
    default=1,
    help="Run time in seconds.",
    show_default=True,
)
@runtime_mode_deco
@click.option(
    "--runner_mode",
    type=click.Choice(["async", "threaded"]),
    default="async",
    help="Runtime mode: async or threaded.",
    show_default=True,
)
@click.option(
    "--start_messages",
    default=100,
    help="Amount of messages to prepopulate.",
    show_default=True,
)
@click.option(
    "--num_of_agents",
    default=2,
    help="Amount of agents to run.",
    show_default=True,
)
@number_of_runs_deco
@output_format_deco
def main(duration: int, runtime_mode: str, runner_mode: str,
         start_messages: int, num_of_agents: int, number_of_runs: int,
         output_format: str) -> Any
```

Check http dialogues memory usage for multiple agents set.

