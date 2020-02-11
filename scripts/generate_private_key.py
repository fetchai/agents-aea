#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""
Generate a private key to be used for the Trading Agent Competition.

It prints the key in PEM format to the specified file.
"""

import argparse

from aea.crypto.fetchai import FetchAICrypto

parser = argparse.ArgumentParser("generate_private_key", description=__doc__)
parser.add_argument("out_file", type=str, help="Where to save the private key.")

if __name__ == "__main__":
    args = parser.parse_args()

    crypto = FetchAICrypto()
    file = open(args.out_file, "wb")
    crypto.dump(file)
