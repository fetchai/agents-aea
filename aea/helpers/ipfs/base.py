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
import io
import re
from typing import Generator, Sized, cast

import base58

from aea.helpers.io import open_file
from aea.helpers.ipfs.utils import _protobuf_python_implementation


# https://github.com/multiformats/multicodec/blob/master/table.csv
SHA256_ID = "12"  # 0x12
LEN_SHA256 = "20"  # 0x20


with _protobuf_python_implementation():  # pylint: disable=import-outside-toplevel
    from aea.helpers.ipfs.pb import merkledag_pb2, unixfs_pb2
    from aea.helpers.ipfs.pb.merkledag_pb2 import PBNode


def _dos2unix(file_content: bytes) -> bytes:
    """
    Replace occurrences of Windows line terminator CR/LF with only LF.

    :param file_content: the content of the file.
    :return: the same content but with the line terminator
    """
    return re.sub(b"\r\n", b"\n", file_content, flags=re.M)


def _is_text(file_path: str) -> bool:
    """Check if a file can be read as text or not."""
    try:
        with open_file(file_path, "r") as f:
            f.read()
        return True
    except UnicodeDecodeError:
        return False


def _read(file_path: str) -> bytes:
    """Read a file, replacing Windows line endings if it is a text file."""
    is_text = _is_text(file_path)
    with open(file_path, "rb") as file:
        file_b = file.read()
        if is_text:
            file_b = _dos2unix(file_b)

    return file_b


def chunks(data: Sized, size: int) -> Generator:
    """Yield successivesize chunks from data."""
    for i in range(0, len(data), size):
        yield data[i : i + size]  # type: ignore


class IPFSHashOnly:
    """A helper class which allows construction of an IPFS hash without interacting with an IPFS daemon."""

    DEFAULT_CHUNK_SIZE = 262144
    # according to https://pkg.go.dev/github.com/ipfs/go-ipfs-chunker#pkg-constants

    def get(self, file_path: str) -> str:
        """
        Get the IPFS hash for a single file.

        :param file_path: the file path
        :return: the ipfs hash
        """
        file_b = _read(file_path)
        file_pb = self._pb_serialize_file(file_b)
        ipfs_hash = self._generate_multihash(file_pb)
        return ipfs_hash

    @classmethod
    def _make_unixfs_pb2(cls, data: bytes) -> bytes:
        if len(data) > cls.DEFAULT_CHUNK_SIZE:  # pragma: nocover
            raise ValueError("Data is too big! use chunks!")
        data_pb = unixfs_pb2.Data()  # type: ignore
        data_pb.Type = unixfs_pb2.Data.File  # type: ignore # pylint: disable=no-member
        data_pb.Data = data
        data_pb.filesize = len(data)
        serialized_data = data_pb.SerializeToString(deterministic=True)
        return serialized_data

    @classmethod
    def _pb_serialize_data(cls, data: bytes) -> bytes:
        outer_node = PBNode()  # type: ignore
        outer_node.Data = cls._make_unixfs_pb2(data)
        result = cls._serialize(outer_node)
        return result

    @classmethod
    def _pb_serialize_file(cls, data: bytes) -> bytes:
        """
        Serialize a bytes object representing a file.

        :param data: a bytes string representing a file
        :return: a bytes string representing a file in protobuf serialization
        """
        if len(data) > cls.DEFAULT_CHUNK_SIZE:
            outer_node = PBNode()  # type: ignore
            data_pb = unixfs_pb2.Data()  # type: ignore
            data_pb.Type = unixfs_pb2.Data.File  # type: ignore # pylint: disable=no-member
            data_pb.filesize = len(data)
            for chunk in chunks(data, cls.DEFAULT_CHUNK_SIZE):
                link = merkledag_pb2.PBLink()
                block = cls._pb_serialize_data(chunk)
                link.Hash = cls._generate_multihash_bytes(block)
                link.Tsize = len(block)
                link.Name = ""
                outer_node.Links.append(link)  # type: ignore # pylint: disable=no-member
                data_pb.blocksizes.append(len(chunk))  # type: ignore # pylint: disable=no-member
            outer_node.Data = data_pb.SerializeToString(deterministic=True)
            return cls._serialize(outer_node)
        return cls._pb_serialize_data(data)

    @staticmethod
    def _generate_multihash_bytes(pb_data: bytes) -> bytes:
        sha256_hash = hashlib.sha256(pb_data).hexdigest()
        multihash_hex = SHA256_ID + LEN_SHA256 + sha256_hash
        multihash_bytes = codecs.decode(str.encode(multihash_hex), "hex")
        return cast(bytes, multihash_bytes)

    @classmethod
    def _generate_multihash(cls, pb_data: bytes) -> str:
        """
        Generate an IPFS multihash.

        Uses the default IPFS hashing function: sha256

        :param pb_data: the data to be hashed
        :return: string representing the hash
        """
        multihash_bytes = cls._generate_multihash_bytes(pb_data)
        ipfs_hash = base58.b58encode(multihash_bytes)
        return str(ipfs_hash, "utf-8")

    @classmethod
    def _generate_hash(cls, data: bytes) -> str:
        """Generate hash for data."""
        pb_data = cls._pb_serialize_file(data)
        return cls._generate_multihash(pb_data)

    @classmethod
    def _serialize(cls, pb_node: PBNode) -> bytes:  # type: ignore
        """Serialize PBNode instance with fixed fields sequence."""
        f = io.BytesIO()
        for field_descriptor, field_value in reversed(pb_node.ListFields()):  # type: ignore
            field_descriptor._encoder(  # pylint: disable=protected-access
                f.write, field_value, True
            )
        return f.getvalue()
