<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_multiagent.command"></a>

# plugins.aea-cli-benchmark.aea`_`cli`_`benchmark.case`_`multiagent.command

Envelopes generation speed for Behaviour act test.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_multiagent.command.main"></a>

#### main

```python
@click.command(name="multiagent_message_exchange")
@click.option("--duration", default=1, help="Run time in seconds.")
@click.option("--runtime_mode",
              default="async",
              help="Runtime mode: async or threaded.")
@click.option("--runner_mode",
              default="async",
              help="Runtime mode: async or threaded.")
@click.option("--start_messages",
              default=100,
              help="Amount of messages to prepopulate.")
@click.option("--num_of_agents", default=2, help="Amount of agents to run.")
@number_of_runs_deco
@output_format_deco
def main(duration: int, runtime_mode: str, runner_mode: str,
         start_messages: int, num_of_agents: int, number_of_runs: int,
         output_format: str) -> Any
```

Test multiagent message exchange.

