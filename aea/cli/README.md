# `aea` command-line tool

The `aea` command-line tool is an extra feature of the `aea` package, that provides a useful tool to manage AEA agents.

## Installation

To use `aea`, install by including the `[cli]` extra dependencies when installing the package:
```
pip install aea[cli]
```

## Quick start

This quick start explains how to create and launch an agent with the cli.

- in any directory, open a terminal and execute: 
    
      aea create my_first_agent
 
  a directory named `my_first_agent` will be created.

- enter into the agent's directory:

      cd my_first_agent

- add a protocol to the agent, e.g.:

      aea add protocol oef

  This command will create the `my_first_agent/protocols` folder, with the `oef` protocol package inside.
  You can find the supported protocols in `aea/protocols`.

- add a skill to the agent, e.g.:

      aea add skill echo_skill ../examples/echo_skill 

  This command will create the `my_first_agent/skills` folder, with the `echo_skill` skill package inside.

- start an oef

      python scripts/oef/launch.py -c ./scripts/oef/launch_config.json

- Run the agent. Assuming an OEF node is running at `127.0.0.1:10000`

      aea run

Press CTRL+C to stop the execution.

- Delete the agent:

      cd ..
      aea delete my_first_agent
