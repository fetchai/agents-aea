``` bash
git clone git@github.com:fetchai/agents-tac.git --recursive && cd agents-tac
```
``` bash
which pipenv
```
``` bash
pipenv --python 3.7 && pipenv shell
```
``` bash
pipenv install
```
``` bash
python setup.py install
```
``` bash
python scripts/launch.py
```
``` bash
git clone git@github.com:fetchai/agents-tac.git --recursive && cd agents-tac
pipenv --python 3.7 && pipenv shell
python setup.py install
cd sandbox && docker-compose build
docker-compose up
```
``` bash
pipenv shell
python templates/v1/basic.py --name my_agent --dashboard
```
``` bash
docker stop $(docker ps -q)
```
``` bash
# mac
docker ps -q | xargs docker stop ; docker system prune -a
```
