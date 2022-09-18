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

"""Read to and write from file with envelopes."""

import codecs
import logging
from contextlib import contextmanager
from logging import Logger
from typing import Generator, IO, Optional, Union

from aea.configurations.base import PublicId
from aea.helpers import file_lock
from aea.helpers.base import exception_log_and_reraise
from aea.mail.base import Envelope


SEPARATOR = b","

_default_logger = logging.getLogger(__name__)


def _encode(e: Envelope, separator: bytes = SEPARATOR) -> bytes:
    result = b""
    result += e.to.encode("utf-8")
    result += separator
    result += e.sender.encode("utf-8")
    result += separator
    result += str(e.protocol_specification_id).encode("utf-8")
    result += separator
    result += e.message_bytes
    result += separator

    return result


def _decode(e: bytes, separator: bytes = SEPARATOR) -> Envelope:
    split = e.split(separator)

    if len(split) < 5 or split[-1] not in [b"", b"\n"]:
        raise ValueError(
            "Expected at least 5 values separated by commas and last value being empty or new line, got {}".format(
                len(split)
            )
        )

    to = split[0].decode("utf-8").strip().lstrip("\x00")
    sender = split[1].decode("utf-8").strip()
    protocol_specification_id = PublicId.from_str(split[2].decode("utf-8").strip())
    # protobuf messages cannot be delimited as they can contain an arbitrary byte sequence; however
    # we know everything remaining constitutes the protobuf message.
    message = SEPARATOR.join(split[3:-1])
    if b"\\x" in message:  # pragma: nocover
        # hack to account for manual usage of `echo`
        message = codecs.decode(message, "unicode-escape").encode("utf-8")

    return Envelope(
        to=to,
        sender=sender,
        protocol_specification_id=protocol_specification_id,
        message=message,
    )


@contextmanager
def lock_file(
    file_descriptor: IO[bytes], logger: Logger = _default_logger
) -> Generator:
    """Lock file in context manager.

    :param file_descriptor: file descriptor of file to lock.
    :param logger: the logger.
    :yield: generator
    """
    with exception_log_and_reraise(
        logger.error,
        f"Couldn't acquire lock for file {file_descriptor.name}: {{}}",
    ):
        file_lock.lock(file_descriptor, file_lock.LOCK_EX)

    try:
        yield
    finally:
        file_lock.unlock(file_descriptor)


def write_envelope(
    envelope: Envelope,
    file_pointer: IO[bytes],
    separator: bytes = SEPARATOR,
    logger: Logger = _default_logger,
) -> None:
    """Write envelope to file."""
    encoded_envelope = _encode(envelope, separator=separator)
    logger.debug("write {!r}: to {}".format(encoded_envelope, file_pointer.name))
    write_with_lock(file_pointer, encoded_envelope, logger)


def write_with_lock(
    file_pointer: IO[bytes], data: Union[bytes], logger: Logger = _default_logger
) -> None:
    """Write bytes to file protected with file lock."""
    with lock_file(file_pointer, logger):
        file_pointer.write(data)
        file_pointer.flush()


def envelope_from_bytes(
    bytes_: bytes, separator: bytes = SEPARATOR, logger: Logger = _default_logger
) -> Optional[Envelope]:
    """
    Decode bytes to get the envelope.

    :param bytes_: the encoded envelope
    :param separator: the separator used
    :param logger: the logger
    :return: Envelope
    """
    logger.debug("processing: {!r}".format(bytes_))
    envelope = None  # type: Optional[Envelope]
    try:
        envelope = _decode(bytes_, separator=separator)
    except ValueError as e:
        logger.error("Bad formatted input: {!r}. {}".format(bytes_, e))
    except Exception as e:  # pragma: nocover # pylint: disable=broad-except
        logger.exception("Error when processing a input. Message: {}".format(str(e)))
    return envelope
