The AEA Gym Skill demonstrates how a custom Reinforcement Learning agent may be embedded into an Autonomous Economic Agent.


## Demo instructions

Make sure you have followed the Quick Start setup instructions <a href="../quickstart" target=_blank>here</a>, including downloading the `examples` and `scripts` directories.

Then, download the channels directory.
``` bash
svn export https://github.com/fetchai/agents-aea.git/trunk/aea/channels
```


### Create the agent
In the root directory, create the gym agent.
``` bash
aea create my_gym_agent
```


### Add the gym skill 
``` bash
cd my_gym_agent
aea add skill gym ../examples/gym_skill
```


### Launch the OEF 
If it is not already running, open a new terminal, *a directory level up*, and launch the OEF.

``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```


### Copy the gym environment to the agent directory
``` bash
mkdir gyms
cp -a ../examples/gym_ex/gyms/. gyms/
```


### Add a gym connection
``` bash
aea add connection ../channels/gym
```


### Update the connection config
``` bash
nano connections/gym/connection.yaml
env: gyms.env.BanditNArmedRandom
```



### Run the agent with the gym connection

``` bash
aea run --connection gym
```

<!--
You will see the echo task running in the terminal window.

<center>![AEA Visdom UI](assets/echo.png)</center>
-->


### Delete the agent

When you're done, you can delete the agent.

``` bash
aea delete my_first_agent
```


<br/>