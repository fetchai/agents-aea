There are multiple ways in which to configure your AEA for debugging during development. We focus on the standard Python approach here.

## Using `pdb` stdlib

You can add a debugger anywhere in your code:

``` python
import pdb; pdb.set_trace()
```

Then simply run you aea with the `--skip-consistency-check` mode:

``` bash
aea -s run
```

For more guidance on how to use `pdb` check out <a href="https://docs.python.org/3/library/pdb.html" target="_blank">the documentation</a>.
