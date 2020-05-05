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
