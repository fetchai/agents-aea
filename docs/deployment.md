
The easiest way to run an AEA is using your development environment.

If you would like to run an AEA from a browser you can use <a href="https://colab.research.google.com" target="_blank">Google Colab</a>. <a href="https://gist.github.com/DavidMinarsch/2eeb1541508a61e828b497ab161e1834" target="_blank">This gist</a> can be opened in <a href="https://colab.research.google.com" target="_blank">Colab</a> and implements the <a href="../quickstart">quick start</a>.

For deployment, we recommend you use <a href="https://www.docker.com/" target="_blank">Docker</a>.

## Deployment using a Docker Image

First, we fetch a directory containing a Dockerfile and some dependencies:
``` bash
svn export https://github.com/fetchai/agents-aea/branches/main/deploy-image
cd deploy-image
```

Then follow the `README.md` contained in the folder.

## Deployment using Kubernetes

For an example of how to use <a href="https://kubernetes.io" target="_blank">Kubernetes</a> navigate to our <a href="https://github.com/fetchai/agents-aea/tree/main/examples/tac_deploy" target="_blank">TAC deployment example</a>.
