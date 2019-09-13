# gym_skill

A quick guide to the gym_skill

## Quick start

- Create an agent:
    
      aea create my_gym_agent

- Cd into agent:

	  cd my_gym_agent

- Add the 'gym' skill:

      aea add skill gym ../examples/gym_skill

- Add a gym connection to the agent config:

      - connection:
        config:
          env: examples.gym_ex.rl.env.BanditNArmedRandom
        name: gym
        type: gym

- Run the agent with the 'gym' connection:

      aea run --connection gym
