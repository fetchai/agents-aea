## Setup

Clone the repo to include submodules.

``` bash
git clone git@github.com:fetchai/agents-tac.git --recursive && cd agents-tac
```


Create and launch a virtual environment.

``` bash
pipenv --python 3.7 && pipenv shell
```


Install the package.
``` bash
python setup.py install
```

Error at this point.

``` bash
Installed /Users/katharinemurphy/.local/share/virtualenvs/agents-tac-YBffReos/lib/python3.7/site-packages/oef-0.6.7-py3.7.egg
Searching for aea@ git+https://github.com/fetchai/agents-aea.git@develop#egg=aea
Reading https://pypi.org/simple/aea/
Couldn't find index page for 'aea' (maybe misspelled?)
Scanning index of all packages (this may take a while)
Reading https://pypi.org/simple/
No local packages or working download links found for aea@ git+https://github.com/fetchai/agents-aea.git@develop#egg=aea
error: Could not find suitable distribution for Requirement.parse('aea@ git+https://github.com/fetchai/agents-aea.git@develop#egg=aea')
(agents-tac) bash-3.2$ python setup.py install
```

Install Docker and Docker Compose.

``` bash
pip install docker
pip install docker-compose
```


Pull the OEF Docker repo.

``` bash
docker pull fetchai/oef-search:latest
```

Run the launch script.

``` bash
python scripts/launch_alt.py
```

The controller GUI at <a href="http://localhost:8097" target=_blank>http://localhost:8097</a> provides real time insights.



## Quick start