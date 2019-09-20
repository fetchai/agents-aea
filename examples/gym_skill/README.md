# gym_skill

A guide to create an AEA with the gym_skill.

## Quick start

- Create an agent:
    
      aea create my_gym_agent

- Cd into agent:

      cd my_gym_agent

- Add the 'gym' skill:

      aea add skill gym ../examples/gym_skill

  This command will create the `my_gym_agent/skills` folder, with the `gym_skill` skill package inside. It will also create the `my_first_agent/protocols` folder, with the `gym` protocol package inside.

- Copy the gym environment to the agent directory:

	    mkdir gyms
	    cp -a ../examples/gym_ex/gyms/. gyms/

- Add a gym connection:

      aea add connection ../aea/channels/gym

- Update the connection config `my_gym_agent/connections/gym/connection.yaml`:

      env: gyms.env.BanditNArmedRandom

- Run the agent with the 'gym' connection:

      aea run --connection gym

- Delete the agent:

      cd ..
      aea delete my_gym_agent
