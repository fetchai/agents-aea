
## Measuring runtime cost

It is important to emphasise the fact that the AEA is a framework, so ultimately its running cost will highly depend on the number and type of components which are being run as part of a given AEA. The other cost factor is determined by the cost of running the core framework itself and how fast and efficient the framework is in interconnecting the components.

These observations can provide guidance on what to report as part of the cost of running an AEA.

Here is a list of suggestion on how to measure the cost of running an AEA:
- the cost of running the framework itself: by running a minimal agent with an idle loop (the default one) with no connections, skills or protocols and measuring memory usage and CPU consumption as a baseline.
- the cost of interconnecting components: by running an a agent with a basic skill (e.g. `fetchai/echo`) and measuring memory usage and CPU consumption relative to number of messages exchanged as well as bandwidth.
- the cost of basic components: dialogues memory relative to number of messages, SOEF connection baseline memory usage, P2P connection baseline memory usage, smart contract baseline memory usage

The `aea run --profiling SECONDS` command can be used to report measures in all of the above scenarios.

## Running and profiling a locally modified framework instance

In order to run a locally modified version of the framework, you will need to build the container using the `Dockerfile_local` in `develop_image/` and tag it. From the open-aea root, run:

```docker build . -t valory/open-aea-user:0.1.0 --file ./develop-image/Dockerfile_local```

Now let's run some agents from the consensus-alorithms's repository, for example price_estimation, an oracle that aggregates bitcoin prices from different sources. This repository can also have some local modifications.

Enable profiling by adding the corresponding flag in ```deployments/Dockerfiles/open-aea/start.sh```. Last line should look like this:

```aea run --aev --profiling 15 # This runs profiling every 15 seconds```

Also, double check that you are not broadcasting data to the server by setting ```broadcast_to_server: false``` in ```deployments/deployment_specifications/price_estimation_hardhat.yaml```. In this file you can also configure the number of agents that you would like to run in the test.

Build the image from the consensus-algorithms repository's root:

```cd /deployments/Dockerfiles/open_aea && docker build . -t valory/consensus-algorithms-open-aea:dev --file ./Dockerfile_local --no-cache```

Please double-check your tags to be sure that you are using the correct images with local modifications.

Now, run a hardhate node:

```docker run -p 8545:8545 -it valory/consensus-algorithms-hardhat:0.1.0```

And build and run the deployment, also from the repository's root:

```export VERSION=dev && python deployments/click_create.py build-deployment --valory-app oracle_hardhat --deployment-type docker-compose --configure-tendermint && cd deployments/build && docker-compose up --force-recreate```

The example should be running now. You can check the logs using ```docker logs abci0 -f``` or even copy them from the container like this:

```sudo cp $(docker inspect --format='{{.LogPath}}' abci0) /tmp/docker_log && sudo chown <user> /tmp/docker_log```

If you used the profiling flag, the logs will contain information about the memory used and object count for certain predefined classes. You can even plot that information using the script in open-aea's repository at ```scripts/profile-log-parser.py```.

If you need further information, just log it directly if all you need is insight about the code execution or modify ```open-aea/aea/helpers/profiling.py``` if your code needs to run with the profiling. After this, some updates to the plot script ```open-aea/scripts/profile-log-parser.py``` should be enough to account for the new data.