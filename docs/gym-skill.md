The AEA gym skill demonstrates how a custom Reinforcement Learning agent may be embedded into an Autonomous Economic Agent.


## Demo instructions

Make sure you have done the `aea` pip install. Instructions are <a href="../quickstart" target=_blank>here</a>.

Create and launch a virtual environment.

``` bash
pipenv --python 3.7 && pipenv shell
```

Then, download the examples and channels directory.
``` bash
svn export https://github.com/fetchai/agents-aea.git/trunk/examples
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



### Run the agent with the gym connection

``` bash
aea run --connection gym
```

<!--
You will see...

<center>![AEA Visdom UI](assets/***.png)</center>
-->


### Delete the agent

When you're done, you can delete the agent.

``` bash
aea delete my_first_agent
```


<br/>