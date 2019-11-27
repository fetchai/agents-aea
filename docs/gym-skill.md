The AEA gym skill demonstrates how a custom Reinforcement Learning agent, that uses OpenAI's <a href="https://gym.openai.com" target=_blank>gym</a> library, may be embedded into an Autonomous Economic Agent.


## Demo instructions

### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

### Create the agent
In the root directory, create the gym agent.
``` bash
aea create my_gym_agent
```

### Add the gym skill 
``` bash
cd my_gym_agent
aea add skill gym
```


### Copy the gym environment to the agent directory
``` bash
mkdir gyms
cp -a ../examples/gym_ex/gyms/. gyms/
```


### Add a gym connection
``` bash
aea add connection gym
```


### Update the connection config
``` bash
nano connections/gym/connection.yaml
env: gyms.env.BanditNArmedRandom
```

### Install the skill dependencies

To install the `gym` package, a dependency of the gym skill, from Pypi run
``` bash
aea install
```


### Run the agent with the gym connection

``` bash
aea run --connection gym
```

You will see the gym training logs.


<center>![AEA gym training logs](assets/gym-training.png)</center>


### Delete the agent

When you're done, you can go up a level and delete the agent.

``` bash
cd ..
aea delete my_gym_agent
```


<br/>
