# `aea` command-line tool

The `aea` command-line tool is an extra feature of the `aea` package, that provides a useful tool to
manage AEA agents.

## Installation

To use `aea`, install by including the `[cli]` extra dependencies when installing the package:
```
pip install aea[cli]
```

## Quick start

- in any directory, open a terminal and execute: 
    
      aea create my-first-agent
 
  a directory named `my-first-agent` will be created.

- enter into the agent's directory:

      cd my-first-agent

- add a protocol to the agent, e.g.:

      aea add protocol oef 

  This command will create the `my-first-agent/protocols` folder, with inside the `oef` protocol package.
  You can check the supported protocols in `aea/protocols`

- Run the agent. Assuming an OEF node is running at `127.0.0.1:10000`

      aea run

Press CTRL+C to stop the execution.

- Delete the agent:

      cd ..
      aea delete my-first-agent
