<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.core"></a>

# plugins.aea-cli-benchmark.aea`_`cli`_`benchmark.case`_`tx`_`generate.core

This module contains the implementation of `benchmark` cli command.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.core.benchmark"></a>

#### benchmark

```python
@click.group()
@click.pass_context
def benchmark(click_context: click.Context) -> None
```

Run one of performance benchmark.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.core.run"></a>

#### run

```python
@click.command(name="run")
@click.argument(
    "file",
    metavar="FILE",
    type=click.Path(exists=True, file_okay=True, dir_okay=False,
                    readable=True),
    required=False,
)
def run(file: Optional[str])
```

Run benchmarks.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.core.make_config"></a>

#### make`_`config

```python
@click.command(name="make-config")
@click.argument(
    "file",
    metavar="FILE",
    type=click.Path(file_okay=True, dir_okay=False),
    required=False,
)
def make_config(file: Optional[str])
```

Make an example config.

