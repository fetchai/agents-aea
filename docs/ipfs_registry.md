# IPFS Registry

## Extended PublicId

IPFS registry utilizes an updated version of the existing PublicId format. Previous PublicId followed `author/package:version` format as a package identifier. But the newer version also includes the IPFS hash for the package as a part of the identifier with `author/package:version:hash` format.

So to utilize the newer PublicId format we have a script which extends all available packages with the new PublicId format.

## Setup the AEA to use the IPFS registry

Initialize AEA cli tool with default registry set to remote and default remote registry set to ipfs.

`aea init --author author_name --remote --ipfs`

You can either set the multiaddr value for the IPFS node at the initialization or export it as an environment variable.

`aea init --author author_name --remote --ipfs --ipfs-node MULTIADDR`

Or

`export OPEN_AEA_IPFS_ADDR=MULTIADDR`

## Publish packages

To publish a package on the IPFS registry, first run `aea hash all` to update the dependencies with the latest IPFS hashes. Then push the relevant packages using

`aea push COMPONENT_TYPE COMPONENT_PATH`

For example, push the signing protocol using

`aea push protocol packages/open_aea/protocols/signing`

## Adding packages

Packages can be downloaded using both extended public ids and hashes

`aea add COMPONENT_TYPE PUBLIC_ID_OR_HASH`

Add the signing protocol using

`aea add protocol open_aea/signing:1.0.0:bafybeiambqptflge33eemdhis2whik67hjplfnqwieoa6wblzlaf7vuo44 --remote`

Or

`aea add protocol open_aea/signing:1.0.0:bafybeiambqptflge33eemdhis2whik67hjplfnqwieoa6wblzlaf7vuo44 --remote`

## Publishing agents

Navigate to the agent directory and publish the agent using

`aea publish`

## Fetching agents

Agents can be fetched from the IPFS registry in the same way as fetching packages by using extended public ids or plain IPFS hashes.

`aea fetch PUBLIC_ID_OR_HASH`

