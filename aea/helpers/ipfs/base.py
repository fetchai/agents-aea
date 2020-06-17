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

"""This module contains helper methods and classes for the 'aea' package."""

import codecs
import hashlib
import re

import base58

from aea.helpers.ipfs.pb import merkledag_pb2
from aea.helpers.ipfs.pb import unixfs_pb2

# https://github.com/multiformats/multicodec/blob/master/table.csv
SHA256_ID = "12"  # 0x12
LEN_SHA256 = "20"  # 0x20


def _dos2unix(file_content: bytes) -> bytes:
    """
    Replace occurrences of Windows line terminator CR/LF with only LF.

    :param file_content: teh content of the file.
    :return the same content but with the line terminator
    """
    return re.sub(b"\r$", b"", file_content, flags=re.M)


class IPFSHashOnly:
    """A helper class which allows construction of an IPFS hash without interacting with an IPFS daemon."""

    def get(self, file_path: str) -> str:
        """
        Get the IPFS hash for a single file.

        :param file_path: the file path
        """
        with open(file_path, "rb") as file:
            file_b = _dos2unix(file.read())
        file_pb = self._pb_serialize_file(file_b)
        ipfs_hash = self._generate_multihash(file_pb)
        return ipfs_hash

    @staticmethod
    def _pb_serialize_file(data: bytes) -> bytes:
        """
        Serialize a bytes object representing a file.

        :param data: a bytes string representing a file
        :return: a bytes string representing a file in protobuf serialization
        """
        data_pb = unixfs_pb2.Data()  # type: ignore
        data_pb.Type = unixfs_pb2.Data.File  # type: ignore # pylint: disable=no-member
        data_pb.Data = data
        data_pb.filesize = len(data)

        serialized_data = data_pb.SerializeToString()

        outer_node = merkledag_pb2.PBNode()  # type: ignore
        outer_node.Data = serialized_data
        result = outer_node.SerializeToString()
        return result

    @staticmethod
    def _generate_multihash(pb_data: bytes) -> str:
        """
        Generate an IPFS multihash.

        Uses the default IPFS hashing function: sha256

        :param pb_data: the data to be hashed
        :return: string representing the hash
        """
        sha256_hash = hashlib.sha256(pb_data).hexdigest()
        multihash_hex = SHA256_ID + LEN_SHA256 + sha256_hash
        multihash_bytes = codecs.decode(str.encode(multihash_hex), "hex")
        ipfs_hash = base58.b58encode(multihash_bytes)
        return str(ipfs_hash, "utf-8")
