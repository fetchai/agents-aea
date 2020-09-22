
The easiest way to run an AEA is using your development environment.

If you would like to run an AEA from a browser you can use <a href="https://colab.research.google.com" target="_blank">Google Colab</a>. <a href="https://gist.github.com/DavidMinarsch/2eeb1541508a61e828b497ab161e1834" target="_blank">This gist</a> can be opened in <a href="https://colab.research.google.com" target="_blank">Colab</a> and implements the <a href="../quickstart">quickstart</a>.

For deployment, we recommend you use <a href="https://www.docker.com/" target="_blank">Docker</a>.

## Building a Docker Image

First, we fetch a directory containing a Dockerfile and some dependencies:
``` bash
svn export https://github.com/fetchai/agents-aea/branches/master/deploy-image
cd deploy-image
rm -rf scripts
svn export https://github.com/fetchai/docker-images/branches/master/scripts
cd ..
```

Next, we build the image:
``` bash
./deploy-image/scripts/docker-build-img.sh -t aea-deploy:latest --
```

## Running a Docker Image

Finally, we run it:
``` bash
docker run -it aea-deploy:latest
```

This will run the `fetchai/my_first_aea:0.12.0` demo project. You can edit `entrypoint.sh` to run whatever project you would like.

## Deployment

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>This section is incomplete and will soon be updated.
</p>
</div>
