``` bash
svn export https://github.com/fetchai/agents-aea/branches/master/deploy-image
cd deploy-image
rm -rf scripts
svn export https://github.com/fetchai/docker-images/branches/master/scripts
cd ..
```
``` bash
./deploy-image/scripts/docker-build-img.sh -t aea-deploy:latest --
```
``` bash
docker run -it aea-deploy:latest
```
