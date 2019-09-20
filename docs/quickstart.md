## Setup


To get started, clone the repo, start a Python environment, and install all dependencies.

``` bash
git clone git@github.com:fetchai/agents-aea.git
cd agents-aea/
pipenv --python 3.7 && pipenv shell
pip install .[all]
```


## Alternative setup - many errors with dependencies.

``` bash
pip install cryptography base58 click click-log jsonschema pyyaml google
# error on yaml, changed to pyyaml
# error on google, didn't fix it
pip install -i https://test.pypi.org/simple/ aea
```


## Echo Agent demo
### Create a new agent

``` bash
aea create my_first_agent
```

### Add the OEF protocol

``` bash
cd my_first_agent
aea add protocol oef
```

### Add the echo skill 

``` bash
aea add skill echo_skill ../examples/echo_skill
```

### Launch the OEF 

!!!	Note
	This step will change soon and we will run the agent on a local OEF stub instead.

Open a new terminal at the repo root and launch the OEF.

``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

### Run the agent locally

Go back to the other terminal and run the agent.

``` bash
aea run
```



<br />