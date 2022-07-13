# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
import os
import re
from pathlib import Path
from typing import Any, Dict, Generator, Sized, Tuple, cast

import base58

from aea.helpers.cid import to_v1
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

    @classmethod
    def get(cls, file_path: str, wrap: bool = True, cid_v1: bool = True) -> str:
        """Get the IPFS hash."""
        if os.path.isdir(file_path):
            return cls.hash_directory(file_path, wrap=wrap, cid_v1=cid_v1)

        return cls.hash_file(file_path, wrap=wrap)

    @classmethod
    def hash_file(cls, file_path: str, wrap: bool = True, cid_v1: bool = True) -> str:
        """
        Get the IPFS hash for a single file.

        :param file_path: the file path
        :param wrap: whether to wrap the content in wrapper node or not
        :param cid_v1: whether to use CID v1 hashes
        :return: the ipfs hash
        """
        file_b = _read(file_path)
        file_pb, file_length = cls._pb_serialize_file(file_b)

        if wrap:
            link_hash = cls._generate_multihash_bytes(file_pb)
            link = cls.create_link(link_hash, file_length, Path(file_path).name)
            file_hash = cls.wrap_in_a_node(link)
        else:
            file_hash = cls._generate_multihash(file_pb)

        if cid_v1:
            return to_v1(file_hash)

        return file_hash

    @classmethod
    def hash_directory(
        cls, dir_path: str, wrap: bool = True, cid_v1: bool = True
    ) -> str:
        """
        Get the IPFS hash for a directory.

        :param dir_path: the directory path
        :param wrap: whether to wrap the content in wrapper node or not
        :param cid_v1: whether to use CID v1 hashes
        :return: the ipfs hash
        """

        path = Path(dir_path)
        hashed_dir = cls._hash_directory_recursively(path)

        if wrap:
            link = cls.create_link(
                cast(bytes, hashed_dir.get("hash_bytes")),
                len(cast(bytes, hashed_dir.get("serialization")))
                + cast(int, hashed_dir.get("content_size")),
                path.name,
            )
            dir_hash = cls.wrap_in_a_node(link)
        else:
            dir_hash = cast(str, hashed_dir.get("hash"))

        if cid_v1:
            return to_v1(dir_hash)

        return dir_hash

    @staticmethod
    def create_link(link_hash: bytes, tsize: int, name: str) -> Any:
        """Create PBLink object."""
        link = merkledag_pb2.PBLink()
        link.Hash = link_hash
        link.Tsize = tsize
        link.Name = name

        return link

    @classmethod
    def wrap_in_a_node(cls, link: Any) -> str:
        """Wrap content in a wrapper node."""
        wrapper_node = PBNode()
        wrapper_node.Links.append(link)  # type: ignore # pylint: disable=no-member

        wrapper_node_data = unixfs_pb2.Data()
        wrapper_node_data.Type = unixfs_pb2.Data.Directory  # type: ignore  # pylint: disable=no-member
        wrapper_node.Data = wrapper_node_data.SerializeToString(deterministic=True)  # type: ignore # pylint: disable=no-member

        wrapper_node_serialization = cls._serialize(wrapper_node)
        wrapper_node_hash_bytes = cls._generate_multihash_bytes(
            wrapper_node_serialization
        )

        return base58.b58encode(wrapper_node_hash_bytes).decode()

    @classmethod
    def _hash_directory_recursively(cls, root: Path) -> Dict:
        """Hash directories recursively, starting from provided root directory."""

        root_node = PBNode()
        content_size = 0

        for child_path in sorted(root.iterdir()):
            if child_path.is_dir():
                if child_path.name == "__pycache__":
                    continue
                metadata = cls._hash_directory_recursively(child_path)
                content_size_child = len(
                    cast(bytes, metadata.get("serialization"))
                ) + cast(int, metadata.get("content_size"))
                root_node.Links.append(  # type: ignore # pylint: disable=no-member
                    cls.create_link(
                        cast(bytes, metadata.get("hash_bytes")),
                        content_size_child,
                        child_path.name,
                    )
                )
                content_size += content_size_child

            else:
                if child_path.name.endswith(".pyc"):
                    continue
                data = _read(str(child_path))
                file_pb, file_length = cls._pb_serialize_file(data)
                child_hash = cls._generate_multihash_bytes(file_pb)
                content_size += file_length
                root_node.Links.append(  # type: ignore # pylint: disable=no-member
                    cls.create_link(child_hash, file_length, child_path.name)
                )

        root_node_data = unixfs_pb2.Data()
        root_node_data.Type = unixfs_pb2.Data.Directory  # type: ignore  # pylint: disable=no-member
        root_node.Data = root_node_data.SerializeToString(deterministic=True)  # type: ignore # pylint: disable=no-member

        root_node_serialization = cls._serialize(root_node)
        root_node_hash_bytes = cls._generate_multihash_bytes(root_node_serialization)
        root_node_hash = base58.b58encode(root_node_hash_bytes).decode()

        return {
            "serialization": root_node_serialization,
            "hash_bytes": root_node_hash_bytes,
            "hash": root_node_hash,
            "content_size": content_size,
        }

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
    def _serialize(cls, pb_node: PBNode) -> bytes:  # type: ignore
        """Serialize PBNode instance with fixed fields sequence."""
        f = io.BytesIO()
        for field_descriptor, field_value in reversed(pb_node.ListFields()):  # type: ignore
            field_descriptor._encoder(  # pylint: disable=protected-access
                f.write, field_value, True
            )
        return f.getvalue()

    @classmethod
    def _pb_serialize_file(cls, data: bytes) -> Tuple[bytes, int]:
        """
        Serialize a bytes object representing a file.

        :param data: a bytes string representing a file
        :return: a bytes string representing a file in protobuf serialization, content size
        """
        if len(data) > cls.DEFAULT_CHUNK_SIZE:
            content_size = 0
            outer_node = PBNode()  # type: ignore
            data_pb = unixfs_pb2.Data()  # type: ignore
            data_pb.Type = unixfs_pb2.Data.File  # type: ignore # pylint: disable=no-member
            data_pb.filesize = len(data)
            for chunk in chunks(data, cls.DEFAULT_CHUNK_SIZE):
                block = cls._pb_serialize_data(chunk)
                block_length = len(block)
                content_size += block_length
                outer_node.Links.append(  # type: ignore # pylint: disable=no-member
                    cls.create_link(
                        cls._generate_multihash_bytes(block), block_length, ""
                    )
                )
                data_pb.blocksizes.append(len(chunk))  # type: ignore # pylint: disable=no-member
            outer_node.Data = data_pb.SerializeToString(deterministic=True)
            file_pb = cls._serialize(outer_node)
            content_size += len(file_pb)
            return file_pb, content_size

        file_pb = cls._pb_serialize_data(data)
        return file_pb, len(file_pb)

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
        return ipfs_hash.decode()

    @classmethod
    def _generate_hash(cls, data: bytes) -> str:
        """Generate hash for data."""
        pb_data, _ = cls._pb_serialize_file(data)
        return cls._generate_multihash(pb_data)
