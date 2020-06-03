``` bash
aea create my_gym_aea
cd my_gym_aea
```
``` bash
aea add skill fetchai/gym:0.2.0
```
``` bash
mkdir gyms
cp -a ../examples/gym_ex/gyms/. gyms/
```
``` bash
aea add connection fetchai/gym:0.2.0
aea config set agent.default_connection fetchai/gym:0.2.0
```
``` bash
aea config set vendor.fetchai.connections.gym.config.env 'gyms.env.BanditNArmedRandom'
```
``` bash
aea install
```
``` bash
aea run --connections fetchai/gym:0.2.0
```
``` bash
cd ..
aea delete my_gym_aea
```
