#!/usr/bin/env bash
set -e

VERSION=$(git rev-parse --short HEAD)

# read -p 'Where to upload the image (prod, or sandbox)?: ' envvar
envvar=${1:-"sandbox"}
shopt -s nocasematch
case "$envvar" in
 "prod" ) 
   echo "Production config selected"
   REGISTRY="gcr.io/fetch-ai-images"
   DOCKERFILE="Dockerfile.dev"
   echo "Registry to upload is $REGISTRY"
   ;;
 "sandbox" ) 
   echo "sandbox config selected"
   REGISTRY="gcr.io/fetch-ai-sandbox"
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

docker build -t ${REGISTRY}/acn_node:${VERSION} -f ./scripts/acn/${DOCKERFILE} ./
docker push ${REGISTRY}/acn_node:${VERSION}
