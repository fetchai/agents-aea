# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2020 fetchai
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

"""This module contains class representations corresponding to every custom type in the protocol specification."""


class RawTransaction:
    """This class represents an instance of RawTransaction."""

    def __init__(self):
        """Initialise an instance of RawTransaction."""
        raise NotImplementedError

    @staticmethod
    def encode(
        raw_transaction_protobuf_object, raw_transaction_object: "RawTransaction"
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the raw_transaction_protobuf_object argument must be matched with the instance of this class in the 'raw_transaction_object' argument.

        :param raw_transaction_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param raw_transaction_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        raise NotImplementedError

    @classmethod
    def decode(cls, raw_transaction_protobuf_object) -> "RawTransaction":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the protocol buffer object in the 'raw_transaction_protobuf_object' argument.

        :param raw_transaction_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'raw_transaction_protobuf_object' argument.
        """
        raise NotImplementedError

    def __eq__(self, other):
        raise NotImplementedError


class SignedTransaction:
    """This class represents an instance of SignedTransaction."""

    def __init__(self):
        """Initialise an instance of SignedTransaction."""
        raise NotImplementedError

    @staticmethod
    def encode(
        signed_transaction_protobuf_object,
        signed_transaction_object: "SignedTransaction",
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the signed_transaction_protobuf_object argument must be matched with the instance of this class in the 'signed_transaction_object' argument.

        :param signed_transaction_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param signed_transaction_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        raise NotImplementedError

    @classmethod
    def decode(cls, signed_transaction_protobuf_object) -> "SignedTransaction":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the protocol buffer object in the 'signed_transaction_protobuf_object' argument.

        :param signed_transaction_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'signed_transaction_protobuf_object' argument.
        """
        raise NotImplementedError

    def __eq__(self, other):
        raise NotImplementedError


class State:
    """This class represents an instance of State."""

    def __init__(self):
        """Initialise an instance of State."""
        raise NotImplementedError

    @staticmethod
    def encode(state_protobuf_object, state_object: "State") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the state_protobuf_object argument must be matched with the instance of this class in the 'state_object' argument.

        :param state_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param state_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        raise NotImplementedError

    @classmethod
    def decode(cls, state_protobuf_object) -> "State":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the protocol buffer object in the 'state_protobuf_object' argument.

        :param state_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'state_protobuf_object' argument.
        """
        raise NotImplementedError

    def __eq__(self, other):
        raise NotImplementedError


class Terms:
    """This class represents an instance of Terms."""

    def __init__(self):
        """Initialise an instance of Terms."""
        raise NotImplementedError

    @staticmethod
    def encode(terms_protobuf_object, terms_object: "Terms") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the terms_protobuf_object argument must be matched with the instance of this class in the 'terms_object' argument.

        :param terms_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param terms_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        raise NotImplementedError

    @classmethod
    def decode(cls, terms_protobuf_object) -> "Terms":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the protocol buffer object in the 'terms_protobuf_object' argument.

        :param terms_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'terms_protobuf_object' argument.
        """
        raise NotImplementedError

    def __eq__(self, other):
        raise NotImplementedError


class TransactionReceipt:
    """This class represents an instance of TransactionReceipt."""

    def __init__(self):
        """Initialise an instance of TransactionReceipt."""
        raise NotImplementedError

    @staticmethod
    def encode(
        transaction_receipt_protobuf_object,
        transaction_receipt_object: "TransactionReceipt",
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the transaction_receipt_protobuf_object argument must be matched with the instance of this class in the 'transaction_receipt_object' argument.

        :param transaction_receipt_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param transaction_receipt_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        raise NotImplementedError

    @classmethod
    def decode(cls, transaction_receipt_protobuf_object) -> "TransactionReceipt":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the protocol buffer object in the 'transaction_receipt_protobuf_object' argument.

        :param transaction_receipt_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'transaction_receipt_protobuf_object' argument.
        """
        raise NotImplementedError

    def __eq__(self, other):
        raise NotImplementedError
