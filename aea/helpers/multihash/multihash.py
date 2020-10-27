# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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

"""Multihash class and utility functions"""

import base64
from collections import namedtuple

from aea.helpers.multihash.codecs import CodecReg
from aea.helpers.multihash.funcs import Func, FuncReg, _is_app_specific_func


def _do_digest(data, func):
    """Return the binary digest of `data` with the given `func`."""
    func = FuncReg.get(func)
    hash_ = FuncReg.hash_from_func(func)
    if not hash_:
        raise ValueError("no available hash function for hash", func)
    hash_.update(data)
    return bytes(hash_.digest())


class Multihash(namedtuple("Multihash", "func digest")):
    """
    A named tuple representing a multihash function and digest.

    The hash function is usually a `Func` member.

    >>> mh = Multihash(Func.sha1, b'BINARY_DIGEST')
    >>> mh == (Func.sha1, b'BINARY_DIGEST')
    True
    >>> mh == (mh.func, mh.digest)
    True

    However it can also be its integer value (the function code) or its string
    name (the function name, with either underscore or hyphen).

    >>> mhfc = Multihash(Func.sha1.value, mh.digest)
    >>> mhfc == mh
    True
    >>> mhfn = Multihash('sha2-256', b'...')
    >>> mhfn.func is Func.sha2_256
    True

    Application-specific codes (0x00-0x0f) are also accepted.  Other codes
    raise a `KeyError`.

    >>> mhfc = Multihash(0x01, b'...')
    >>> mhfc.func
    1
    >>> mhfc = Multihash(1234, b'...')
    Traceback (most recent call last):
        ...
    KeyError: ('unknown hash function', 1234)
    """

    __slots__ = ()

    def __new__(cls, func, digest_):
        """Create a new instance of Multihash."""
        try:
            func = FuncReg.get(func)
        except KeyError:
            if _is_app_specific_func(func):
                # Application-specific function codes
                # are allowed even if not registered.
                func = int(func)
            else:
                raise
        digest_ = bytes(digest_)
        return super(cls, Multihash).__new__(cls, func, digest_)

    @classmethod
    def from_hash(cls, hash_):
        """Create a `Multihash` from a hashlib-compatible `hash` object.

        >>> import hashlib
        >>> data = b'foo'
        >>> hash_ = hashlib.sha1(data)
        >>> digest_ = hash_.digest()
        >>> mh = Multihash.from_hash(hash_)
        >>> mh == (Func.sha1, digest_)
        True

        Application-specific hash functions are also supported (see
        `FuncReg`).

        If there is no matching multihash hash function for the given `hash`,
        a `ValueError` is raised.
        """
        try:
            func = FuncReg.func_from_hash(hash_)
        except KeyError as ke:
            raise ValueError("no matching multihash function", hash_.name) from ke
        digest_ = hash_.digest()
        return Multihash(func, digest_)

    def __str__(self):
        """Return a compact string representation of the multihash.

        The representation includes the name of the standard multihash
        function or the hexadecimal code of the application-specific one, and
        a Base64-encoded version of the raw digest.  This is *not* the
        complete multihash-encoded digest that can be obtained with
        `Multihash.encode()`.

        >>> mh = Multihash(Func.sha1, b'TEST')
        >>> print(mh)
        Multihash(sha1, b64:VEVTVA==)
        >>> mh = Multihash(0x01, b'TEST')
        >>> print(mh)
        Multihash(0x1, b64:VEVTVA==)
        """
        return "Multihash({func}, b64:{digest})".format(
            func=self.func.name if self.func in Func else hex(self.func),
            digest=base64.b64encode(self.digest).decode(),
        )

    def encode(self, encoding=None):
        r"""Encode into a multihash-encoded digest.

        If `encoding` is `None`, a binary digest is produced:

        >>> mh = Multihash(0x01, b'TEST')
        >>> mh.encode()
        b'\x01\x04TEST'

        If the name of an `encoding` is specified, it is used to encode the
        binary digest before returning it (see `CodecReg` for supported
        codecs).

        >>> mh.encode('base64')
        b'AQRURVNU'

        If the `encoding` is not available, a `KeyError` is raised.
        """
        try:
            fc = self.func.value
        except AttributeError:  # application-specific function code
            fc = self.func
        mhash = bytes([fc, len(self.digest)]) + self.digest
        if encoding:
            mhash = CodecReg.get_encoder(encoding)(mhash)
        return mhash

    def verify(self, data):
        r"""Does the given `data` hash to the digest in this `Multihash`?

        >>> import hashlib
        >>> data = b'foo'
        >>> hash = hashlib.sha1(data)
        >>> mh = Multihash.from_hash(hash)
        >>> mh.verify(data)
        True
        >>> mh.verify(b'foobar')
        False

        Application-specific hash functions are also supported (see
        `FuncReg`).
        """
        digest_ = _do_digest(data, self.func)
        return digest_[: len(self.digest)] == self.digest

    def truncate(self, length):
        """Return a new `Multihash` with a shorter digest `length`.

        If the given `length` is greater than the original, a `ValueError`
        is raised.

        >>> mh1 = Multihash(0x01, b'FOOBAR')
        >>> mh2 = mh1.truncate(3)
        >>> mh2 == (0x01, b'FOO')
        True
        >>> mh3 = mh1.truncate(10)
        Traceback (most recent call last):
            ...
        ValueError: cannot enlarge the original digest by 4 bytes
        """
        if length > len(self.digest):
            raise ValueError(
                "cannot enlarge the original digest by %d bytes"
                % (length - len(self.digest))
            )
        return self.__class__(self.func, self.digest[:length])


def digest(data, func):
    """Hash the given `data` into a new `Multihash`.

    The given hash function `func` is used to perform the hashing.  It must be
    a registered hash function (see `FuncReg`).

    >>> data_ = b'foo'
    >>> mh = digest(data_, Func.sha1)
    >>> mh.encode('base64')
    b'ERQL7se16j8P28ldDdR/PFvCddqKMw=='
    """
    digest_ = _do_digest(data, func)
    return Multihash(func, digest_)


def decode(mhash, encoding=None):
    r"""Decode a multihash-encoded digest into a `Multihash`.

    If `encoding` is `None`, a binary digest is assumed.

    >>> mhash = b'\x11\x0a\x0b\xee\xc7\xb5\xea?\x0f\xdb\xc9]'
    >>> mh = decode(mhash)
    >>> mh == (Func.sha1, mhash[2:])
    True

    If the name of an `encoding` is specified, it is used to decode the digest
    before parsing it (see `CodecReg` for supported codecs).

    >>> import base64
    >>> emhash = base64.b64encode(mhash)
    >>> emh = decode(emhash, 'base64')
    >>> emh == mh
    True

    If the `encoding` is not available, a `KeyError` is raised.  If the digest
    has an invalid format or contains invalid data, a `ValueError` is raised.
    """
    mhash = bytes(mhash)
    if encoding:
        mhash = CodecReg.get_decoder(encoding)(mhash)
    try:
        func = mhash[0]
        length = mhash[1]
        digest_ = mhash[2:]
    except IndexError as ie:
        raise ValueError("multihash is too short") from ie
    if length != len(digest_):
        raise ValueError("multihash length field does not match digest field length")
    return Multihash(func, digest_)
