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

"""Codec registry"""

import base64

# Import codecs mentioned in the multihash spec.
import binascii
from collections import namedtuple


# Try to import external codecs mentioned in the multihash spec.
try:
    import base58
except ImportError:
    base58 = None  # type: ignore


class _CodecRegMeta(type):
    def __contains__(cls, encoding):
        """Return whether `encoding` is a registered codec.

        >>> CodecReg.reset()
        >>> 'base64' in CodecReg
        True
        """
        return encoding in cls._codecs

    def __iter__(cls):
        """Iterate over registered codec names.

        >>> CodecReg.reset()
        >>> {'hex', 'base32', 'base64'}.issubset(CodecReg)
        True
        """
        return iter(cls._codecs)


class CodecReg(metaclass=_CodecRegMeta):
    """Registry of supported codecs."""

    # Common codec data.
    _common_codec_data = [  # (name, encode, decode)
        ("hex", binascii.b2a_hex, binascii.a2b_hex),
        ("base32", base64.b32encode, base64.b32decode),
        ("base64", base64.b64encode, base64.b64decode),
    ]
    if base58:
        _common_codec_data.append(
            ("base58", lambda s: bytes(base58.b58encode(s), "ascii"), base58.b58decode)  # type: ignore
        )

    # Codec data: encoding and decoding functions (both from bytes to bytes).
    _codec = namedtuple("codec", "encode decode")

    @classmethod
    def reset(cls):
        """Reset the registry to the standard codecs."""
        cls._codecs = {}
        c = cls._codec
        for (name, encode, decode) in cls._common_codec_data:
            cls._codecs[name] = c(encode, decode)

    @classmethod
    def register(cls, name, encode, decode):
        """Add a codec to the registry.

        Registers a codec with the given `name` (a string) to be used with the
        given `encode` and `decode` functions, which take a `bytes` object and
        return another one.  An existing codec is replaced.

        >>> import binascii
        >>> CodecReg.register('uu', binascii.b2a_uu, binascii.a2b_uu)
        >>> CodecReg.get_decoder('uu') is binascii.a2b_uu
        True
        >>> CodecReg.reset()
        >>> 'uu' in CodecReg
        False
        """
        cls._codecs[name] = cls._codec(encode, decode)

    @classmethod
    def unregister(cls, name):
        """Remove a codec from the registry.

        Unregisters the codec with the given `name` (a string).  If the codec
        is not registered, a `KeyError` is raised.

        >>> import binascii
        >>> CodecReg.register('uu', binascii.b2a_uu, binascii.a2b_uu)
        >>> 'uu' in CodecReg
        True
        >>> CodecReg.unregister('uu')
        >>> 'uu' in CodecReg
        False
        """
        del cls._codecs[name]

    @classmethod
    def get_encoder(cls, encoding):
        r"""Return an encoder for the given `encoding`.

        The encoder gets a `bytes` object as argument and returns another
        encoded `bytes` object.  If the `encoding` is not registered, a
        `KeyError` is raised.

        >>> encode = CodecReg.get_encoder('hex')
        >>> encode(b'FOO\x00')
        b'464f4f00'
        """
        return cls._codecs[encoding].encode

    @classmethod
    def get_decoder(cls, encoding):
        r"""Return a decoder for the given `encoding`.

        The decoder gets a `bytes` object as argument and returns another
        decoded `bytes` object.  If the `encoding` is not registered, a
        `KeyError` is raised.

        >>> decode = CodecReg.get_decoder('hex')
        >>> decode(b'464f4f00')
        b'FOO\x00'
        """
        return cls._codecs[encoding].decode


# Initialize the codec registry.
CodecReg.reset()
