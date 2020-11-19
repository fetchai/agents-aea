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

## Using an IDE:

- For VSCode modify the `launch.json` to include the following information:

``` json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "aea run",
            "type": "python",
            "request": "launch",
            "program": "PATH_TO_VIRTUAL_ENV_PACKAGES/aea/cli/__main__.py",
            "args": ["-v","DEBUG","--skip-consistency-check","run"],
            "cwd": "CWD",
            "console": "integratedTerminal"
        }
    ]
}
```
where `PATH_TO_VIRTUAL_ENV_PACKAGES` should be replaced with the path to the virtual environment's packages and `CWD` with the working directory for the agent to debug (where the `aea-config.yaml` file is).
