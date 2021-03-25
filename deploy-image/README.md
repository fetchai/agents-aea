# Docker Deployment image

This guide explains how to prepare an image with your AEA for deployment.

## Creating your own image

### Modify scripts

The example uses the `fetchai/my_first_aea` project. You will likely want to modify it to one of your own agents or an agent from the AEA registry.

First, review the `build.sh` script to make sure you are fetching the correct agent and do all the necessary setup. Here you can modify the agent you want to use. Note, when fetching from local, make sure your local packages are in the (currently empty) `packages` folder.

Second, review the `entrypoint.sh` script to make sure you supply the agent with the right amount of private keys. In the example one key-pair each for the agent and connection is used, you might need more than that depending on your agent (see `required_ledgers` of your agent).

Importantly, do not add any private keys during the build step!

Third, create a local `.env` file with the relevant environment variables:
```
export AGENT_PRIV_KEY=
export P2P_PRIV_KEY=
```

### Build the image

``` bash
docker build -t my_first_aea -f Dockerfile .

```

## Run

``` bash
docker run my_first_aea --env-file .env
```
