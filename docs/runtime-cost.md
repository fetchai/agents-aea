
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

```bash
docker build . -t valory/open-aea-user:<tag> --file ./develop-image/Dockerfile_local
```

It's time to build the image for the agent or service, that will build on top of the open-aea one. First, enable profiling by adding the corresponding flag in your start script. The run line should look like this:

```bash
aea run --aev --profiling 15  # This runs profiling every 15 seconds
```

Now build the image. If you have local changes to open-aea, you'll need to comment out any lines corresponding to the installation of open-aea and its plugins in your Dockerfile to avoid the pypi versions being used instead of the local ones:

```bash
docker build . -t <agent_image>:<tag> --file ./Dockerfile --no-cache
```

Please double-check your tags to be sure that you are using the correct images with local modifications. Once the build has finished, run a Hardhat node before using it:

```bash
docker run -p 8545:8545 -it valory/consensus-algorithms-hardhat:0.1.0
```

Run the deployment. You can check the logs using ```docker logs <container> -f``` or even copy them from the container like this:

```bash
sudo cp $(docker inspect --format='{{.LogPath}}' <container>) /tmp/docker_log && sudo chown <user> /tmp/docker_log
```

If you used the profiling flag, the logs will contain information about the memory used and object count for certain predefined classes. You can even plot that information using the script in open-aea's repository at `scripts/profile-log-parser.py`.

If you need further information, just log it directly if all you need is insight about the code execution or modify `open-aea/aea/helpers/profiling.py` if your code needs to run with the profiling. After this, some updates to the plot script `open-aea/scripts/profile-log-parser.py` should be enough to account for the new data.