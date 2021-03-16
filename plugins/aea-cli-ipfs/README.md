# AEA CLI IPFS Plug-in

IPFS command to publish and download directories.

## Installation and usage

Make sure you have `aea` installed.

Then, install the plug-in:
``` bash
pip install aea-cli-ipfs
```

Now you should be able to run `aea ipfs`.

``` bash
Usage: aea ipfs [OPTIONS] COMMAND [ARGS]...

  IPFS Commands

Options:
  --help  Show this message and exit.

Commands:
  add       Add directory to ipfs, if not directory specified the current...
  download  Download directory by it's hash, if not target directory...
  remove    Remove a directory from ipfs by it's hash.



Usage: aea ipfs add [OPTIONS] [DIR_PATH]

  Add directory to ipfs, if not directory specified the current one will be
  added.

Options:
  -p, --publish
  --help         Show this message and exit.



Usage: aea ipfs remove [OPTIONS] hash_id

  Remove a directory from ipfs by it's hash.

Options:
  --help  Show this message and exit.



Usage: aea ipfs download [OPTIONS] hash_id [TARGET_DIR]

  Download directory by it's hash, if not target directory specified will
  use current one.

Options:
  --help  Show this message and exit.

```
