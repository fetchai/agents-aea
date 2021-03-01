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
"""Mail module common classes."""

from typing import Any, Optional
from urllib.parse import urlparse

from aea.configurations.base import PublicId


class URI:
    """URI following RFC3986."""

    __slots__ = ("_uri_raw",)

    def __init__(self, uri_raw: str) -> None:
        """
        Initialize the URI.

        Must follow: https://tools.ietf.org/html/rfc3986.html

        :param uri_raw: the raw form uri
        :raises ValueError: if uri_raw is not RFC3986 compliant
        """
        self._uri_raw = uri_raw

    @property
    def scheme(self) -> str:
        """Get the scheme."""
        parsed = urlparse(self._uri_raw)
        return parsed.scheme

    @property
    def netloc(self) -> str:
        """Get the netloc."""
        parsed = urlparse(self._uri_raw)
        return parsed.netloc

    @property
    def path(self) -> str:
        """Get the path."""
        parsed = urlparse(self._uri_raw)
        return parsed.path

    @property
    def params(self) -> str:
        """Get the params."""
        parsed = urlparse(self._uri_raw)
        return parsed.params

    @property
    def query(self) -> str:
        """Get the query."""
        parsed = urlparse(self._uri_raw)
        return parsed.query

    @property
    def fragment(self) -> str:
        """Get the fragment."""
        parsed = urlparse(self._uri_raw)
        return parsed.fragment

    @property
    def username(self) -> Optional[str]:
        """Get the username."""
        parsed = urlparse(self._uri_raw)
        return parsed.username

    @property
    def password(self) -> Optional[str]:
        """Get the password."""
        parsed = urlparse(self._uri_raw)
        return parsed.password

    @property
    def host(self) -> Optional[str]:
        """Get the host."""
        parsed = urlparse(self._uri_raw)
        return parsed.hostname

    @property
    def port(self) -> Optional[int]:
        """Get the port."""
        parsed = urlparse(self._uri_raw)
        return parsed.port

    def __str__(self) -> str:
        """Get string representation."""
        return self._uri_raw

    def __eq__(self, other: Any) -> bool:
        """Compare with another object."""
        return isinstance(other, URI) and str(self) == str(other)


class EnvelopeContext:
    """Contains context information of an envelope."""

    __slots__ = ("_connection_id", "_uri")

    def __init__(
        self, connection_id: Optional[PublicId] = None, uri: Optional[URI] = None,
    ) -> None:
        """
        Initialize the envelope context.

        :param connection_id: the connection id used for routing the outgoing envelope in the multiplexer.
        :param uri: the URI sent with the envelope.
        """
        self._connection_id = connection_id
        self._uri = uri

    @property
    def uri(self) -> Optional[URI]:
        """Get the URI."""
        return self._uri

    @property
    def connection_id(self) -> Optional[PublicId]:
        """Get the connection id to route the envelope."""
        return self._connection_id

    @connection_id.setter
    def connection_id(self, connection_id: PublicId) -> None:
        """Set the 'via' connection id."""
        if self._connection_id is not None:
            raise ValueError("connection_id already set!")  # pragma: nocover
        self._connection_id = connection_id

    def __str__(self) -> str:
        """Get the string representation."""
        return f"EnvelopeContext(connection_id={self.connection_id}, uri={self.uri})"

    def __eq__(self, other: Any) -> bool:
        """Compare with another object."""
        return (
            isinstance(other, EnvelopeContext)
            and self.connection_id == other.connection_id
            and self.uri == other.uri
        )

    def copy_without_uri(self) -> "EnvelopeContext":
        """Get a copy without the uri."""
        return EnvelopeContext(connection_id=self.connection_id)
