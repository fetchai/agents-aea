The command line interface is the easiest way to build an AEA.

## Installation

The following installs the AEA CLI package.

``` bash
pip install aea[cli]
```

The following installs the entire AEA package including the CLI.

``` bash
pip install aea[all]
```

If you are using `zsh` rather than `bash` type 
``` zsh
pip install 'aea[cli]'
```
and
``` zsh
pip install 'aea[all]'
```
respectively.

Be sure that the `bin` folder of your Python environment
is in the `PATH` variable. If so, you can execute the CLI tool as:
``` bash
aea
```

You might find useful the execution of the `aea.cli` package
as a script:
``` bash
python -m aea.cli
```
which is just an alternative entry-point to the CLI tool. 

## Troubleshooting

To ensure no cache is used run.

``` bash
pip install aea[all] --force --no-cache-dir
```

And for `zsh` run:
``` zsh
pip install 'aea[all]' --force --no-cache-dir
```

<br />
