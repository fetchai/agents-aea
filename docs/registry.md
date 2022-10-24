# Component Registry

Individual components are stored on the  <a href="https://ipfs.tech" target="_blank">`IPFS registry`</a>. This registry allows other developer to reuse these components. Anyone case register a new component which is uniquely identifiable by a hash of the contents of the component.

## Creating a Project
We can create a new agent with the bare minimal components as so;

```
aea create agent
Initializing AEA project 'agent'
Creating project directory './agent'
Creating config file aea-config.yaml
Adding default packages ...
Adding protocol 'open_aea/signing:latest'...
Using registry: ipfs
Downloading open_aea/signing:latest from IPFS.
Successfully added protocol 'open_aea/signing:1.0.0'.
```


## Adding Individual Components
Once we have an agent, we can add individual components to the agent as so;

```
aea add skill fetchai/echo:0.19.0:bafybeia3ovoxmnipktwnyztie55itsuempnfeircw72jn62uojzry5pwsu --remote
Registry path not provided and local registry `packages` not found in current (.) and parent directory.
Trying remote registry (`--remote`).
Adding skill 'fetchai/echo:latest'...
Using registry: ipfs
Downloading fetchai/echo:latest from IPFS.
Adding protocol 'fetchai/default:1.0.0'...
Using registry: ipfs
Downloading fetchai/default:1.0.0 from IPFS.
Successfully added protocol 'fetchai/default:1.0.0'.
Successfully added skill 'fetchai/echo:0.19.0'.
```

## Adding a Package to Local IPFS Node
To generate the hash of a component, we use a local IPFS node which allows use to create the same hash as generated upon deployment of the component to main net IPFS.

```bash
aea ipfs add packages/fetchai/connections/gym/
Starting processing: /root/open-aea/packages/fetchai/connections/gym
Registered item with:
        public id : fetchai/gym:0.19.0
        hash : QmVLvrU8w8nJB57ncPfoYwB5niA3RWeeKpqyRi3ug2hkY8
```
