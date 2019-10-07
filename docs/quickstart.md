## Preliminaries

Create and cd into a new working directory.

``` bash
mkdir my_aea/
cd my_aea/
```

We highly recommend using a virtual environment to ensure consistency across dependencies.

Check you have [`pipenv`](https://github.com/pypa/pipenv).

``` bash
which pipenv
```

If you don't have it, install it. Instructions are <a href="https://pypi.org/project/pipenv/" target=_blank>here</a>.

Once installed, create a new environment and open it.

``` bash
touch Pipfile && pipenv --python 3.7 && pipenv shell
```


## Installation

Install the Autonomous Economic Agent framework.

<!--

The following installs the basic application without the cli.
``` bash
pip install aea
```
-->

The following installs the entire AEA package which includes the cli too.

``` bash
pip install aea[all]

```

However, you can run this demo by installing the base AEA inclusive the CLI extension, alone.

``` bash
pip install aea[cli]

```


## Echo skill demo

The echo skill is a simple demo that prints logs from the agent's main loop as it calls registered `Task` and `Behaviour` code.



### Download the examples, scripts, and packages directories.
``` bash
svn export https://github.com/fetchai/agents-aea.git/trunk/scripts
svn export https://github.com/fetchai/agents-aea.git/trunk/packages
```

### Create a new agent
``` bash
aea create my_first_agent
```

### Add the echo skill 

``` bash
cd my_first_agent
aea add skill echo
```

### Add a local connection

``` bash
aea add connection local
```

A local connection provides a local stub for an OEF node instance.

### Run the agent

Run the agent with the `local` connection.

``` bash
aea run --connection local
```

You will see the echo task running in the terminal window.

<center>![The echo call and response log](assets/echo.png)</center>


### Delete the agent

When you're done, you can delete the agent.

``` bash
aea delete my_first_agent
```


<br />
