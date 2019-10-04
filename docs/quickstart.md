## Preliminaries

Create and cd into a new working directory.

``` bash
mkdir aea/
cd aea/
```

Check you have `pipenv`.

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

However, you can run this demo by installing the AEA cli alone.

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

### Run the agent locally

Run the agent with the connection.

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
