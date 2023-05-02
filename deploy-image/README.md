# Docker Deployment image

This guide explains how to prepare a Docker image containing your AEA for deployment.

## Creating your own image

The example uses the `fetchai/my_first_aea` project. You will likely want to modify it to one of your own agents or an agent from the AEA registry.

### Fetch the example directory

Install subversion, then download the example directory to your local working directory

``` bash
svn checkout https://github.com/valory-xyz/open-aea/tags/v1.33.0/packages packages
```

### Modify scripts

First, review the `build.sh` script to make sure you are fetching the correct agent and do all the necessary setup. Here you can modify the agent you want to use. Note, when fetching from local, make sure your local packages are in the (currently empty) `packages` folder.

Second, review the `entrypoint.sh` script to make sure you supply the agent with the right amount of private keys. In the example one key-pair each for the agent and connection is used, you might need more than that depending on your agent (see `required_ledgers` of your agent).

Importantly, do not add any private keys during the build step!

Third, create a local `.env` file with the relevant environment variables:
```
AGENT_PRIV_KEY=hex_key_here
CONNECTION_PRIV_KEY=hex_key_here
```

Finally, if required, modify the `Dockerfile` to expose any ports needed by the AEA. (The default example does not require this.)


### Build the image

``` bash
docker build -t my_first_aea -f Dockerfile .
```

## Run

``` bash
docker run --env-file .env -t my_first_aea
```

To stop, use `docker ps` to find the container id and then `docker stop CONTAINER_ID` to stop the container.

## Advanced usage and comments

- The above approach implies that key files remain in the container. To avoid this, a static volume can be mounted with the key files in it (https://docs.docker.com/get-started/06_bind_mounts/).

