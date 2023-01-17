<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_agent_construction_time.command"></a>

# plugins.aea-cli-benchmark.aea`_`cli`_`benchmark.case`_`agent`_`construction`_`time.command

Check amount of time and mem for agent setup.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_agent_construction_time.command.main"></a>

#### main

```python
@click.command(name="agent_construction_time")
@click.option("--agents",
              default=25,
              help="Amount of agents to construct.",
              show_default=True)
@number_of_runs_deco
@output_format_deco
def main(agents: int, number_of_runs: int, output_format: str) -> Any
```

Check agents construction time and memory usage.

