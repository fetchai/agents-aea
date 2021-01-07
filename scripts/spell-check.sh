#!/bin/bash
# This script requires `mdspell`:
#
#    https://www.npmjs.com/package/markdown-spellcheck
#
# Run this script from the root directory.
# Usage:
#   ./scripts/spell-check.sh
#

MDSPELL_PATH="$(which mdspell)"
if [ -z "${MDSPELL_PATH}" ]; then
  echo "Cannot find executable 'mdspell'. Please install it to run this script: npm i markdown-spellcheck -g"
  exit 127
else
  echo "Found 'mdspell' executable at ${MDSPELL_PATH}"
  mdspell -n -a --en-gb '**/*.md' '!docker-images/*.md' '!docs/api/**/*.md'
fi
