``` bash
aea fetch open_aea/gym_aea:0.1.0:bafybeib3ezmhbsnq6s66xtgofhwwg2rcrj7he5n37wouytdga3kp5ute6m --remote
cd gym_aea
aea install
```
``` bash
aea create my_gym_aea
cd my_gym_aea
```
``` bash
aea add skill fetchai/gym:0.20.0:bafybeiaxkoymzkrgi5pmaxb26ewwmcfricbzqxl4bnitqqzsggl5juyv64 --remote
```
``` bash
aea config set agent.default_connection fetchai/gym:0.19.0
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
aea generate-key ethereum
aea add-key ethereum
```
``` bash
aea run
```
``` bash
cd ..
aea delete my_gym_aea
```
