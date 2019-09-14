# gym_skill

A guide to create an AEA with the gym_skill.

## Quick start

- Create an agent:
    
      aea create my_gym_agent

- Cd into agent:

	  cd my_gym_agent

- Add the 'gym' skill:

      aea add skill gym ../examples/gym_skill

- Copy the gym environment to the agent directory:

	mkdir gym
	cp -a ../examples/gym_ex/gym/. gym/

- Add a gym connection to the `aea-config.yaml`:

      - connection:
        config:
          env: gym.env.BanditNArmedRandom
        name: gym
        type: gym

- Run the agent with the 'gym' connection:

      aea run --connection gym

- Delete the agent:

      cd ..
      aea delete my_gym_agent
