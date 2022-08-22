``` bash
mkdir gym_skill_agent
svn export https://github.com/fetchai/agents-aea.git/trunk/examples
```
``` bash
pip install numpy gym
```
``` bash
aea fetch fetchai/gym_aea:0.26.1 --alias my_gym_aea
cd my_gym_aea
aea install
```
``` bash
aea create my_gym_aea
cd my_gym_aea
```
``` bash
aea add skill fetchai/gym:0.21.2
```
``` bash
aea config set agent.default_connection fetchai/gym:0.20.2
```
``` bash
aea install
```
``` bash
mkdir gyms
cp -a ../examples/gym_ex/gyms/. gyms/
```
``` bash
aea config set vendor.fetchai.connections.gym.config.env 'gyms.env.BanditNArmedRandom'
```
``` bash
aea generate-key fetchai
aea add-key fetchai
```
``` bash
aea run
```
``` bash
cd ..
aea delete my_gym_aea
```
