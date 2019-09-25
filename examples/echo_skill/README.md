# echo_skill

A guide to create an AEA with the echo_skill.

## Quick start

This quick start explains how to create and launch an agent with the cli.

- in any directory, open a terminal and execute: 
    
      aea create my_first_agent
 
  This command will create a directory named `my_first_agent`. It will further create the `my_first_agent/skills` folder, with the `error` skill package inside. It will also create the `my_first_agent/protocols` folder, with the `default` protocol package inside. Finally, it will create the `my_first_agent/connections` folder, with the `oef` connection package inside.

- enter into the agent's directory:

      cd my_first_agent

- add a skill to the agent, e.g.:

      aea add skill echo

  This command will add the `echo` skill package to the `my_first_agent/skills` folder.

- start an oef from a separate terminal:

      python scripts/oef/launch.py -c ./scripts/oef/launch_config.json

- Run the agent. Assuming an OEF node is running at `127.0.0.1:10000`

      aea run

- For debugging run with:

      aea -v DEBUG run

- Press CTRL+C to stop the execution.

- Delete the agent:

      cd ..
      aea delete my_first_agent

