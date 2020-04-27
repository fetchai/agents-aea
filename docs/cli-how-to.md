The command line interface is the easiest way to build an AEA.

## Installation

The following installs the AEA cli package.

``` bash
pip install aea[cli]
```

The following installs the entire AEA package including the cli.

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
