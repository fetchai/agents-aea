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

"""Enumeration of standard multihash functions, and function registry"""

# Import standard hashlib-compatible modules.
import hashlib
from collections import namedtuple
from enum import Enum
from numbers import Integral

# Try to import known optional hashlib-compatible modules.
from aea.exceptions import enforce


try:
    import sha3  # type: ignore
except ImportError:
    sha3 = None
try:
    import pyblake2 as blake2  # type: ignore
except ImportError:
    blake2 = None


def _is_app_specific_func(code):
    """Is the given hash function integer `code` application-specific?"""
    return isinstance(code, Integral) and (0x00 <= code <= 0x0F)


class Func(Enum):
    """
    An enumeration of hash functions supported by multihash.

    The name of each member has its hyphens replaced by underscores.
    The value of each member corresponds to its integer code.

    >>> Func.sha2_512.value == 0x13
    True
    """

    sha1 = 0x11
    sha2_256 = 0x12
    sha2_512 = 0x13
    # See jbenet/multihash#11 for new SHA-3 function names and codes.
    sha3_512 = 0x14
    sha3 = sha3_512  # deprecated, for backwards compatibility
    sha3_384 = 0x15
    sha3_256 = 0x16
    sha3_224 = 0x17
    shake_128 = 0x18
    shake_256 = 0x19
    blake2b = 0x40
    blake2s = 0x41


class _FuncRegMeta(type):
    def __contains__(cls, func):
        """Return whether `func` is a registered function.

        >>> FuncReg.reset()
        >>> Func.sha2_256 in FuncReg
        True
        """
        return func in cls._func_hash

    def __iter__(cls):
        """Iterate over registered functions.

        Standard multihash functions are represented as members of `Func`,
        while application-specific functions are integers.

        >>> FuncReg.reset()
        >>> set(FuncReg) == set(Func)
        True
        """
        return iter(cls._func_hash)


class FuncReg(metaclass=_FuncRegMeta):
    """Registry of supported hash functions."""

    # Standard hash function data.
    _std_func_data = [  # (func, hash name, hash new)
        (Func.sha1, "sha1", hashlib.sha1),
        (Func.sha2_256, "sha256", hashlib.sha256),
        (Func.sha2_512, "sha512", hashlib.sha512),
        (Func.sha3_512, "sha3_512", sha3.sha3_512 if sha3 else None),
        (Func.sha3_384, "sha3_384", sha3.sha3_384 if sha3 else None),
        (Func.sha3_256, "sha3_256", sha3.sha3_256 if sha3 else None),
        (Func.sha3_224, "sha3_224", sha3.sha3_224 if sha3 else None),
        (Func.shake_128, "shake_128", None),
        (Func.shake_256, "shake_256", None),
        (Func.blake2b, "blake2b", blake2.blake2b if blake2 else None),
        (Func.blake2s, "blake2s", blake2.blake2s if blake2 else None),
    ]

    # Hashlib compatibility data for a hash: hash name (e.g. ``sha256`` for
    # SHA-256, ``sha2-256`` in multihash), and the corresponding constructor.
    _hash = namedtuple("hash", "name new")

    @classmethod
    def reset(cls):
        """Reset the registry to the standard multihash functions."""
        # Maps function names (hyphens or underscores) to registered functions.
        cls._func_from_name = {}

        # Maps hashlib names to registered functions.
        cls._func_from_hash = {}

        # Hashlib compatibility data by function.
        cls._func_hash = {}

        register = cls._do_register
        for (func, hash_name, hash_new) in cls._std_func_data:
            register(func, func.name, hash_name, hash_new)
        enforce(set(cls._func_hash) == set(Func), "Hash sets must match.")

    @classmethod
    def get(cls, func_hint):
        """Return a registered hash function matching the given hint.

        The hint may be a `Func` member, a function name (with hyphens or
        underscores), or its code.  A `Func` member is returned for standard
        multihash functions and an integer code for application-specific ones.
        If no matching function is registered, a `KeyError` is raised.

        >>> fm = FuncReg.get(Func.sha2_256)
        >>> fnu = FuncReg.get('sha2_256')
        >>> fnh = FuncReg.get('sha2-256')
        >>> fc = FuncReg.get(0x12)
        >>> fm == fnu == fnh == fc
        True
        """
        # Different possibilities of `func_hint`, most to least probable.
        try:  # `Func` member (or its value)
            return Func(func_hint)
        except ValueError:
            pass
        if func_hint in cls._func_from_name:  # `Func` member name, extended
            return cls._func_from_name[func_hint]
        if func_hint in cls._func_hash:  # registered app-specific code
            return func_hint
        raise KeyError("unknown hash function", func_hint)

    @classmethod
    def _do_register(cls, code, name, hash_name=None, hash_new=None):
        """Add hash function data to the registry without checks."""
        cls._func_from_name[name.replace("-", "_")] = code
        cls._func_from_name[name.replace("_", "-")] = code
        if hash_name:
            cls._func_from_hash[hash_name] = code
        cls._func_hash[code] = cls._hash(hash_name, hash_new)

    @classmethod
    def register(cls, code, name, hash_name=None, hash_new=None):
        """Add an application-specific function to the registry.

        Registers a function with the given `code` (an integer) and `name` (a
        string, which is added both with only hyphens and only underscores),
        as well as an optional `hash_name` and `hash_new` constructor for
        hashlib compatibility.  If the application-specific function is
        already registered, the related data is replaced.  Registering a
        function with a `code` not in the application-specific range
        (0x00-0xff) or with names already registered for a different function
        raises a `ValueError`.

        >>> import hashlib
        >>> FuncReg.register(0x05, 'md-5', 'md5', hashlib.md5)
        >>> FuncReg.get('md-5') == FuncReg.get('md_5') == 0x05
        True
        >>> hashobj = FuncReg.hash_from_func(0x05)
        >>> hashobj.name == 'md5'
        True
        >>> FuncReg.func_from_hash(hashobj) == 0x05
        True
        >>> FuncReg.reset()
        >>> 0x05 in FuncReg
        False
        """
        if not _is_app_specific_func(code):
            raise ValueError("only application-specific functions can be registered")
        # Check already registered name in different mappings.
        name_mapping_data = [  # (mapping, name in mapping, error if existing)
            (
                cls._func_from_name,
                name,
                "function name is already registered for a different function",
            ),
            (
                cls._func_from_hash,
                hash_name,
                "hashlib name is already registered for a different function",
            ),
        ]
        for (mapping, nameinmap, errmsg) in name_mapping_data:
            existing_func = mapping.get(nameinmap, code)
            if existing_func != code:
                raise ValueError(errmsg, existing_func)
        # Unregister if existing to ensure no orphan entries.
        if code in cls._func_hash:
            cls.unregister(code)
        # Proceed to registration.
        cls._do_register(code, name, hash_name, hash_new)

    @classmethod
    def unregister(cls, code):
        """Remove an application-specific function from the registry.

        Unregisters the function with the given `code` (an integer).  If the
        function is not registered, a `KeyError` is raised.  Unregistering a
        function with a `code` not in the application-specific range
        (0x00-0xff) raises a `ValueError`.

        >>> import hashlib
        >>> FuncReg.register(0x05, 'md-5', 'md5', hashlib.md5)
        >>> FuncReg.get('md-5')
        5
        >>> FuncReg.unregister(0x05)
        >>> FuncReg.get('md-5')
        Traceback (most recent call last):
            ...
        KeyError: ('unknown hash function', 'md-5')
        """
        if code in Func:
            raise ValueError("only application-specific functions can be unregistered")
        # Remove mapping to function by name.
        func_names = {n for (n, f) in cls._func_from_name.items() if f == code}
        for func_name in func_names:
            del cls._func_from_name[func_name]
        # Remove hashlib data and mapping to hash.
        hash_ = cls._func_hash.pop(code)
        if hash_.name:
            del cls._func_from_hash[hash_.name]

    @classmethod
    def func_from_hash(cls, hash_):
        """Return the multihash `Func` for the hashlib-compatible `hash` object.

        If no `Func` is registered for the given hash, a `KeyError` is raised.

        >>> import hashlib
        >>> h = hashlib.sha256()
        >>> f = FuncReg.func_from_hash(h)
        >>> f is Func.sha2_256
        True
        """
        return cls._func_from_hash[hash_.name]

    @classmethod
    def hash_from_func(cls, func):
        """Return a hashlib-compatible object for the multihash `func`.

        If the `func` is registered but no hashlib-compatible constructor is
        available for it, `None` is returned.  If the `func` is not
        registered, a `KeyError` is raised.

        >>> h = FuncReg.hash_from_func(Func.sha2_256)
        >>> h.name
        'sha256'
        """
        new = cls._func_hash[func].new
        return new() if new else None


# Initialize the function hash registry.
FuncReg.reset()
