# Reinforcement Learning and the AEA Framework

We provide two examples to demonstrate the utility of our framework to RL developers.

## Gym Example

The `train.py` file [here](../examples/gym_ex/train.py) shows that all the RL developer needs to do is add one line of code `(proxy_env = ...)` to introduce our agent as a proxy layer between an OpenAI `gym.Env` and a standard RL agent. The gym_ex just serves as a demonstration and helps on-boarding, there is no immediate use case for it as you can train your RL agent without our proxy layer just fine (and faster). However, it decouples the RL agent from the gym.Env allowing the two do run in separate environments, potentially owned by different entities.

## Gym Skill

The `gym_skill` [here](../examples/gym_skill) lets an RL developer embed their RL agent inside an AEA as a skill. 

