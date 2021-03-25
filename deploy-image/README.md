# Docker Deployment image

All the commands must be executed from the parent directory, if not stated otherwise.

## Creating your own image

### Modify scripts

The example uses the `fetchai/my_first_aea` project. You will likely want to modify it to one of your own agents or an agent from the AEA registry.


First, review the `build.sh` script to make sure you are fetching the correct agent and do all the necessary setup.

Second, review the `entrypoint.sh` script to make sure you supply the agent with the right amount of private keys. In the example one key-pair each for the agent and connections is used, you might need more than that depending on your agent.

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

## Build and Publish example

**Only required for repo maintainers**

### Build

We recommend using the following command for building:

    ./deploy-image/scripts/docker-build-img.sh -t fetchai/aea-deploy:latest --

The images will be automatically tagged with `fetchai/aea-deploy:latest` and `fetchai/aea-deploy:<latest-version-number>` (as specified in `docker-env.sh`).

### Publish

Simply us `docker push fetchai/aea-deploy:latest` and `fetchai/aea-deploy:<latest-version-number>` to push the images.

### Pull

Docker images for all releases are available on Docker hub. Simply use `docker pull fetchai/aea-deploy:latest` to get the latest image.
