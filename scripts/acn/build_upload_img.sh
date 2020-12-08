
#!/usr/bin/env bash
VERSION=$(git describe --always --dirty=-WIP)

#Check For WIP
if [[ $VERSION == *-WIP ]];
then 
  echo "WIP detected - please commit changes"
  exit 1
fi

# read -p 'Where to upload the image (prod, or colearn)?: ' envvar
envvar="colearn"
shopt -s nocasematch
case "$envvar" in
 "prod" ) 
   echo "Production config selected"
   REGISTRY="gcr.io/fetch-ai-images"
   DOCKERFILE="Dockerfile.dev"
   echo "Registry to upload is $REGISTRY"
   ;;
 "colearn" ) 
   echo "colearn config selected"
   REGISTRY="gcr.io/fetch-ai-colearn"
   DOCKERFILE="Dockerfile.dev"
   echo "Registry to upload is $REGISTRY"
   ;;
 *) 
   echo "Wrong env selected. Try again" 
   echo "Exiting with exit code 1"
   exit 1
   ;;
esac

sleep 2

docker build -t ${REGISTRY}/acn_node:${VERSION} -f ${DOCKERFILE} ../../
docker push ${REGISTRY}/acn_node:${VERSION}