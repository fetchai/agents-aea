The original TAC has its own <a href="https://github.com/fetchai/agents-tac" target="_blank">repo</a>. 

Follow the instructions below to build and run the TAC demo.


## Requirements

Make sure you are running <a href="https://docs.docker.com/install/" target="_blank">Docker</a> and <a href="https://docs.docker.com/compose/install/" target="_blank">Docker Compose</a>.


## Quick start

Clone the repo to include sub-modules.

``` bash
git clone git@github.com:fetchai/agents-tac.git --recursive && cd agents-tac
```

Check you have `pipenv`.

``` bash
which pipenv
```

If you don't have it, install it. Instructions are <a href="https://pypi.org/project/pipenv/" target="_blank">here</a>.


Create and launch a virtual environment.

``` bash
pipenv --python 3.7 && pipenv shell
```

Install the dependencies.

``` bash
pipenv install
```


Install the package.
``` bash
python setup.py install
```


Run the launch script. This may take a while.

``` bash
python scripts/launch.py
```

The <a href="https://github.com/fossasia/visdom" target="_blank">Visdom</a> server is now running.

The controller GUI at <a href="http://localhost:8097" target="_blank">http://localhost:8097</a> provides real time insights.

In the Environment tab, make sure you have the `tac_controller` environment selected.

<img src="../assets/visdom_ui.png" alt="AEA Visdom UI" class="center">

## Alternative build and run

In a new terminal window, clone the repo, build the sandbox, and launch it.

``` bash
git clone git@github.com:fetchai/agents-tac.git --recursive && cd agents-tac
pipenv --python 3.7 && pipenv shell
python setup.py install
cd sandbox && docker-compose build
docker-compose up
```

In a new terminal window, enter the virtual environment, and connect a template agent to the sandbox.

``` bash
pipenv shell
python templates/v1/basic.py --name my_agent --dashboard
```

Click through to the <a href="http://localhost:8097" target="_blank">controller GUI</a>.

## Possible gotchas

Stop all running containers before restart.

``` bash
docker stop $(docker ps -q)
```

To remove all images, run the following command.

``` bash
# mac
docker ps -q | xargs docker stop ; docker system prune -a
```



<br/>