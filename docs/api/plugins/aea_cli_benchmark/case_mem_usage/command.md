<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_mem_usage.command"></a>

# plugins.aea-cli-benchmark.aea`_`cli`_`benchmark.case`_`mem`_`usage.command

Memory usage check.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_mem_usage.command.main"></a>

#### main

```python
@click.command(name="mem_usage")
@click.option("--duration",
              default=3,
              help="Run time in seconds.",
              show_default=True)
@runtime_mode_deco
@number_of_runs_deco
@output_format_deco
def main(duration: int, runtime_mode: str, number_of_runs: int,
         output_format: str) -> Any
```

Run memory usage benchmark.

