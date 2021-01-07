Test AEA framework performance.

## What is it?

The benchmark module is a set of tools to measure execution time, CPU load and memory usage of the AEA Python code. It produces text reports and draws charts to present the results.

## How does it work?

The framework:

* spawns a dedicated process for each test run to execute the function to test.
* measures CPU and RAM usage periodically.
* waits for function exits or terminates them by timeout.
* repeats test execution multiple times to get more accurate results.



## How to use

Steps to run a test:

* Write a function you would like to test with all arguments you would like to parametrise, add some doc strings.
* Split the function into two parts: prepare part and performance part. The prepare part will not be included in the measurement.
* Add `BenchmarkControl` support, to notify framework to start measurement.
* Import `TestCli` class,  `TestCli().run(function_to_be_tested)`
* Call it from console to get text results.

### Simple example

`cpuburn` - simple test of CPU load depends on idle sleep time. Shows how much CPU consumed during the execution.

``` python
import time

from benchmark.framework.benchmark import BenchmarkControl
from benchmark.framework.cli import TestCli


def cpu_burn(benchmark: BenchmarkControl, run_time=10, sleep=0.0001) -> None:
    """
    Do nothing, just burn cpu to check cpu load changed on sleep.

    :param benchmark: benchmark special parameter to communicate with executor
    :param run_time: time limit to run this function
    :param sleep: time to sleep in loop

    :return: None
    """
    benchmark.start()
    start_time = time.time()

    while True:
        time.sleep(sleep)
        if time.time() - start_time >= run_time:
            break


if __name__ == "__main__":
    TestCli(cpu_burn).run()
```


Run it with `python ./benchmark/cases/cpu_burn.py --help` to get help about usage.
``` bash
Usage: cpu_burn.py [OPTIONS] [ARGS]...

       Do nothing, just burn cpu to check cpu load changed on sleep.

  :param benchmark: benchmark special parameter to communicate with executor
  :param run_time: time limit to run this function :param sleep: time to sleep in loop

  :return: None

      ARGS is function arguments in format: `run_time,sleep`

      default ARGS is `10,0.0001`

Options:
  --timeout FLOAT               Executor timeout in seconds  [default: 10.0]
  --period FLOAT                Period for measurement  [default: 0.1]
  -N, --num-executions INTEGER  Number of runs for each case  [default: 1]
  -P, --plot INTEGER            X axis parameter idx
  --help                        Show this message and exit.
```


Run it with `python ./benchmark/cases/cpu_burn.py` to start with default parameters.
``` bash
Test execution timeout: 10.0
Test execution measure period: 0.1
Tested function name: cpu_burn
Tested function description:
    Do nothing, just burn cpu to check cpu load changed on sleep.

    :param benchmark: benchmark special parameter to communicate with executor
    :param run_time: time limit to run this function
    :param sleep: time to sleep in loop

    :return: None

Tested function argument names: ['run_time', 'sleep']
Tested function argument default values: [10, 0.0001]

== Report created 2020-04-27 15:14:56.076549 ==
Arguments are `[10, 0.0001]`
Number of runs: 1
Number of time terminated: 0
Time passed (seconds): 10.031443119049072 ± 0
cpu min (%): 0.0 ± 0
cpu max (%): 10.0 ± 0
cpu mean (%): 3.4 ± 0
mem min (kb): 53.98828125 ± 0
mem max (kb): 53.98828125 ± 0
mem mean (kb): 53.98828125 ± 0
```

Here you can see test report for default arguments set.


Run with multiple arguments set, multiple repeats and draw a chart on resources
`python ./benchmark/cases/cpu_burn.py -N 5 -P 1 3,0.00001 3,0.001 3,0.01`

Report is:
``` bash
Test execution timeout: 10.0
Test execution measure period: 0.1
Tested function name: cpu_burn
Tested function description:
    Do nothing, just burn cpu to check cpu load changed on sleep.

    :param benchmark: benchmark special parameter to communicate with executor
    :param run_time: time limit to run this function
    :param sleep: time to sleep in loop

    :return: None

Tested function argument names: ['run_time', 'sleep']
Tested function argument default values: [10, 0.0001]

== Report created 2020-04-27 15:38:17.849535 ==
Arguments are `(3, 1e-05)`
Number of runs: 5
Number of time terminated: 0
Time passed (seconds): 3.0087939262390138 ± 0.0001147521277690166
cpu min (%): 0.0 ± 0.0
cpu max (%): 11.0 ± 2.23606797749979
cpu mean (%): 6.2 ± 0.18257418583505522
mem min (kb): 54.0265625 ± 0.11180339887498948
mem max (kb): 54.0265625 ± 0.11180339887498948
mem mean (kb): 54.0265625 ± 0.11180339887498948
== Report created 2020-04-27 15:38:32.947308 ==
Arguments are `(3, 0.001)`
Number of runs: 5
Number of time terminated: 0
Time passed (seconds): 3.014109659194946 ± 0.0004416575764579524
cpu min (%): 0.0 ± 0.0
cpu max (%): 8.0 ± 2.7386127875258306
cpu mean (%): 1.9986666666666666 ± 0.002981423969999689
mem min (kb): 53.9890625 ± 0.10431954926750306
mem max (kb): 53.9890625 ± 0.10431954926750306
mem mean (kb): 53.9890625 ± 0.10431954926750306
== Report created 2020-04-27 15:38:48.067511 ==
Arguments are `(3, 0.01)`
Number of runs: 5
Number of time terminated: 0
Time passed (seconds): 3.0181806087493896 ± 0.0022409499756841883
cpu min (%): 0.0 ± 0.0
cpu max (%): 1.0 ± 2.23606797749979
cpu mean (%): 0.06666666666666667 ± 0.14907119849998599
mem min (kb): 53.9078125 ± 0.11487297672320501
mem max (kb): 53.9078125 ± 0.11487297672320501
mem mean (kb): 53.9078125 ± 0.11487297672320501
```

Chart is drawn for argument 1: sleep:

<img src="../assets/benchmark_chart.png" alt="Char over argument 1 - sleep value" class="center">

The most interesting part is CPU usage, as you can see  CPU usage decreases with increasing value of idle sleep.
Memory usage and execution time can slightly differ per case execution.


## Requirements for tested function

* The first function's argument has to be `benchmark: BenchmarkControl` which is passed by default by the framework.
* All arguments except the fist one have to set default values.
* Function doc string is required, it used for help information.
* `benchmark.start()` has to be called once in the function body to start measurement. The timeout is counted from this point!
* All the "prepare part" in the function that should not be measured has to be placed before `benchmark.start()`
* Code to be measured has to go after `benchmark.start()`
* Try to avoid infinitive loops and assume the test should exit after a while.


## Execution options

* To pass an arguments set just provide it as a comma separated string like `10,0.1`
* To pass several argument sets just separate them by white space `10,0.1 20,0.2`
* `--timeout FLOAT` is test execution timeout in seconds. If the test takes more time, it will be terminated.
* `--period FLOAT` is measurement interval in seconds, how often to make CPU and RAM usage measurements.
* `-N, --num-executions INTEGER` - how many time to run the same argument set to make result more accurate.
* `-P, --plot INTEGER` -  Draw a chart using, using values of argument specified as values for axis X. argument positions started with 0, argument benchmark does not counted. for example `-P 0` will use `run_time` values, `-P 1` will use `sleep` values.


## Limitations

Currently, the benchmark framework does not measure resources consumed by subprocess spawned in python code. So try to keep one process solutions during tests.

Asynchronous functions or coroutines are not supported directly. So you have to set up an event loop inside test function and start loop manually.



## Testing AEA: handlers example

Test react speed on specific messages amount.

``` python
def react_speed_in_loop(benchmark: BenchmarkControl, inbox_amount=1000) -> None:
    """
    Test inbox message processing in a loop.

    :param benchmark: benchmark special parameter to communicate with executor
    :param inbox_amount: num of inbox messages for every agent

    :return: None
    """

    skill_definition = {
        "handlers": {"dummy_handler": DummyHandler}
    }
    aea_test_wrapper = AEATestWrapper(
        name="dummy agent",
        skills=[skill_definition],
    )

    for _ in range(inbox_amount):
        aea_test_wrapper.put_inbox(aea_test_wrapper.dummy_envelope())

    aea_test_wrapper.set_loop_timeout(0.0)

    benchmark.start()

    aea_test_wrapper.start_loop()

    while not aea_test_wrapper.is_inbox_empty():
        time.sleep(0.1)

    aea_test_wrapper.stop_loop()
```


Create AEA wrapper with specified handler:
``` python
skill_definition = {
    "handlers": {"dummy_handler": DummyHandler}
}
aea_test_wrapper = AEATestWrapper(
    name="dummy agent",
    skills=[skill_definition],
)
```


Populate inbox with dummy messages:
``` python
for _ in range(inbox_amount):
    aea_test_wrapper.put_inbox(aea_test_wrapper.dummy_envelope())
```

Set timeout `0`, for maximum messages processing speed: `aea_test_wrapper.set_loop_timeout(0.0)`

Start benchmark: `benchmark.start()`

Start/stop AEA:
``` python
aea_test_wrapper.start()
...
aea_test_wrapper.stop()
```

Wait till messages present in inbox:
``` python
while not aea_test_wrapper.is_inbox_empty():
    time.sleep(0.1)
```
