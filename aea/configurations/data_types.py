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
"""Base config data types."""
import functools
import re
from abc import ABC, abstractmethod
from enum import Enum
from typing import (
    Any,
    Collection,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
    cast,
)

import semver
from packaging.specifiers import SpecifierSet

from aea.configurations.constants import (
    AGENT,
    CONNECTION,
    CONTRACT,
    DEFAULT_GIT_REF,
    PROTOCOL,
    SERVICE,
    SKILL,
)
from aea.exceptions import enforce
from aea.helpers.base import (
    IPFSHash,
    IPFSHashOrStr,
    IPFS_HASH_REGEX,
    RegexConstrainedString,
    SIMPLE_ID_REGEX,
    SimpleId,
    SimpleIdOrStr,
)


T = TypeVar("T")


VersionInfoClass = semver.VersionInfo
PackageVersionLike = Union[str, semver.VersionInfo]


class JSONSerializable(ABC):
    """Interface for JSON-serializable objects."""

    @property
    @abstractmethod
    def json(self) -> Dict:
        """Compute the JSON representation."""

    @classmethod
    def from_json(cls, obj: Dict) -> "JSONSerializable":
        """Build from a JSON object."""


@functools.total_ordering
class PackageVersion:
    """A package version."""

    _version: PackageVersionLike

    def __init__(self, version_like: PackageVersionLike) -> None:
        """
        Initialize a package version.

        :param version_like: a string, os a semver.VersionInfo object.
        """
        if isinstance(version_like, str) and version_like == "latest":
            self._version = version_like
        elif isinstance(version_like, str) and version_like == "any":
            self._version = version_like
        elif isinstance(version_like, str):
            self._version = VersionInfoClass.parse(version_like)
        elif isinstance(version_like, VersionInfoClass):
            self._version = version_like
        else:
            raise ValueError("Version type not valid.")

    @property
    def is_latest(self) -> bool:
        """Check whether the version is 'latest'."""
        return isinstance(self._version, str) and self._version == "latest"

    def __str__(self) -> str:
        """Get the string representation."""
        return str(self._version)

    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        return isinstance(other, PackageVersion) and self._version == other._version

    def __lt__(self, other: Any) -> bool:
        """Compare with another object."""
        enforce(
            isinstance(other, PackageVersion),
            f"Cannot compare {type(self)} with type {type(other)}.",
        )
        other = cast(PackageVersion, other)
        if self.is_latest or other.is_latest:
            return self.is_latest < other.is_latest
        return str(self) < str(other)


class PackageType(Enum):
    """Package types."""

    AGENT = AGENT
    PROTOCOL = PROTOCOL
    CONNECTION = CONNECTION
    CONTRACT = CONTRACT
    SKILL = SKILL
    SERVICE = SERVICE

    def to_plural(self) -> str:
        """
        Get the plural name.

        >>> PackageType.AGENT.to_plural()
        'agents'
        >>> PackageType.PROTOCOL.to_plural()
        'protocols'
        >>> PackageType.CONNECTION.to_plural()
        'connections'
        >>> PackageType.SKILL.to_plural()
        'skills'
        >>> PackageType.CONTRACT.to_plural()
        'contracts'

        :return: pluralised package type
        """
        return self.value + "s"

    def __str__(self) -> str:
        """Convert to string."""
        return str(self.value)


class ComponentType(Enum):
    """Enum of component types supported."""

    PROTOCOL = PROTOCOL
    CONNECTION = CONNECTION
    SKILL = SKILL
    CONTRACT = CONTRACT

    def to_package_type(self) -> PackageType:
        """Get package type for component type."""
        return PackageType(self.value)

    @staticmethod
    def plurals() -> Collection[str]:  # pylint: disable=unsubscriptable-object
        """
        Get the collection of type names, plural.

        >>> ComponentType.plurals()
        ['protocols', 'connections', 'skills', 'contracts']

        :return: list of all pluralised component types
        """
        return list(map(lambda x: x.to_plural(), ComponentType))

    def to_plural(self) -> str:
        """
        Get the plural version of the component type.

        >>> ComponentType.PROTOCOL.to_plural()
        'protocols'
        >>> ComponentType.CONNECTION.to_plural()
        'connections'
        >>> ComponentType.SKILL.to_plural()
        'skills'
        >>> ComponentType.CONTRACT.to_plural()
        'contracts'

        :return: pluralised component type
        """
        return self.value + "s"

    def __str__(self) -> str:
        """Get the string representation."""
        return str(self.value)


PackageIdPrefix = Tuple[ComponentType, str, str]


class PublicId(JSONSerializable):
    """This class implement a public identifier.

    A public identifier is composed of three elements:
    - author
    - name
    - version

    The concatenation of those three elements gives the public identifier:

        author/name:version

    >>> public_id = PublicId("author", "my_package", "0.1.0")
    >>> assert public_id.author == "author"
    >>> assert public_id.name == "my_package"
    >>> assert public_id.version == "0.1.0"
    >>> another_public_id = PublicId("author", "my_package", "0.1.0")
    >>> assert hash(public_id) == hash(another_public_id)
    >>> assert public_id == another_public_id
    >>> latest_public_id = PublicId("author", "my_package", "latest")
    >>> latest_public_id
    <author/my_package:latest>
    >>> latest_public_id.package_version.is_latest
    True
    """

    __slots__ = ("_author", "_name", "_package_version", "_package_hash")

    AUTHOR_REGEX = SIMPLE_ID_REGEX
    IPFS_HASH_REGEX = IPFS_HASH_REGEX
    PACKAGE_NAME_REGEX = SIMPLE_ID_REGEX

    VERSION_NUMBER_PART_REGEX = r"(0|[1-9]\d*)"
    VERSION_REGEX = rf"(any|latest|({VERSION_NUMBER_PART_REGEX})\.({VERSION_NUMBER_PART_REGEX})\.({VERSION_NUMBER_PART_REGEX})(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?)"
    PUBLIC_ID_URI_REGEX = (
        rf"^({AUTHOR_REGEX})/({PACKAGE_NAME_REGEX})/({VERSION_REGEX})$"
    )
    PUBLIC_ID_REGEX = rf"^({AUTHOR_REGEX})/({PACKAGE_NAME_REGEX})(:{VERSION_REGEX})?(:{IPFS_HASH_REGEX})?$"

    ANY_VERSION = "any"
    LATEST_VERSION = "latest"

    def __init__(
        self,
        author: SimpleIdOrStr,
        name: SimpleIdOrStr,
        version: Optional[PackageVersionLike] = None,
        package_hash: Optional[IPFSHashOrStr] = None,
    ) -> None:
        """Initialize the public identifier."""
        self._author = SimpleId(author)
        self._name = SimpleId(name)
        self._package_version = (
            PackageVersion(version)
            if version is not None
            else PackageVersion(self.LATEST_VERSION)
        )
        self._package_hash = (
            IPFSHash(package_hash) if package_hash is not None else None
        )

    @property
    def author(self) -> str:
        """Get the author."""
        return str(self._author)

    @property
    def name(self) -> str:
        """Get the name."""
        return str(self._name)

    @property
    def version(self) -> str:
        """Get the version string."""
        return str(self._package_version)

    @property
    def package_version(self) -> PackageVersion:
        """Get the package version object."""
        return self._package_version

    @property
    def hash(
        self,
    ) -> str:
        """Returns the hash for the package."""
        if self._package_hash is None:
            raise ValueError("Package hash was not provided.")
        return str(self._package_hash)

    def same_prefix(self, other: "PublicId") -> bool:
        """Check if the other public id has the same author and name of this."""
        return self.name == other.name and self.author == other.author

    def to_any(self) -> "PublicId":
        """Return the same public id, but with any version."""
        return PublicId(self.author, self.name, self.ANY_VERSION)

    def to_latest(self) -> "PublicId":
        """Return the same public id, but with latest version."""
        return PublicId(self.author, self.name, self.LATEST_VERSION)

    @classmethod
    def is_valid_str(cls, public_id_string: str) -> bool:
        """
        Check if a string is a public id.

        :param public_id_string: the public id in string format.
        :return: bool indicating validity
        """
        match = re.match(cls.PUBLIC_ID_REGEX, public_id_string)
        return match is not None

    @classmethod
    def from_str(cls, public_id_string: str) -> "PublicId":
        """Initialize the public id from the string.

        >>> str(PublicId.from_str("author/package_name:0.1.0"))
        'author/package_name:0.1.0'

        >>> str(PublicId.from_str("author/package_name:0.1.0:QmYAXgX8ARiriupMQsbGXtKdDyGzWry1YV3sycKw1qqmgH"))
        'author/package_name:0.1.0:QmYAXgX8ARiriupMQsbGXtKdDyGzWry1YV3sycKw1qqmgH'

        A bad formatted input raises value error:
        >>> PublicId.from_str("bad/formatted:input")
        Traceback (most recent call last):
        ...
        ValueError: Input 'bad/formatted:input' is not well formatted.

        >>> PublicId.from_str("bad/formatted:0.1.0:Qmbadhash")
        Traceback (most recent call last):
        ...
        ValueError: Input 'bad/formatted:0.1.0:Qmbadhash' is not well formatted.

        :param public_id_string: the public id in string format.
        :return: the public id object.
        :raises ValueError: if the string in input is not well formatted.
        """
        match = re.match(cls.PUBLIC_ID_REGEX, public_id_string)
        if match is None:
            raise ValueError(
                "Input '{}' is not well formatted.".format(public_id_string)
            )

        username = match.group(1)
        package_name = match.group(2)
        version = match.group(3)
        if version is not None:
            version = version.replace(":", "")
        package_hash = match.group(13)
        if package_hash is not None:
            package_hash = package_hash.replace(":", "")

        return PublicId(username, package_name, version, package_hash)

    @classmethod
    def try_from_str(cls, public_id_string: str) -> Optional["PublicId"]:
        """
        Safely try to get public id from string.

        :param public_id_string: the public id in string format.
        :return: the public id object or None
        """
        result: Optional[PublicId] = None
        try:
            result = cls.from_str(public_id_string)
        except ValueError:
            pass
        return result

    @classmethod
    def from_uri_path(cls, public_id_uri_path: str) -> "PublicId":
        """
        Initialize the public id from the string.

        >>> str(PublicId.from_uri_path("author/package_name/0.1.0"))
        'author/package_name:0.1.0'

        A bad formatted input raises value error:
        >>> PublicId.from_uri_path("bad/formatted:input")
        Traceback (most recent call last):
        ...
        ValueError: Input 'bad/formatted:input' is not well formatted.

        :param public_id_uri_path: the public id in uri path string format.
        :return: the public id object.
        :raises ValueError: if the string in input is not well formatted.
        """
        if not re.match(cls.PUBLIC_ID_URI_REGEX, public_id_uri_path):
            raise ValueError(
                "Input '{}' is not well formatted.".format(public_id_uri_path)
            )
        username, package_name, version = re.findall(
            cls.PUBLIC_ID_URI_REGEX, public_id_uri_path
        )[0][:3]
        return PublicId(username, package_name, version)

    @property
    def to_uri_path(self) -> str:
        """
        Turn the public id into a uri path string.

        :return: uri path string
        """
        return "{author}/{name}/{version}".format(
            author=self.author, name=self.name, version=self.version
        )

    @property
    def json(self) -> Dict:
        """Compute the JSON representation."""
        data = {
            "author": self.author,
            "name": self.name,
            "version": self.version,
        }
        if self._package_hash is not None:
            data["package_hash"] = self.hash

        return data

    @classmethod
    def from_json(cls, obj: Dict) -> "PublicId":
        """Build from a JSON object."""
        return PublicId(
            obj["author"],
            obj["name"],
            obj.get("version", None),
            obj.get("package_hash", None),
        )

    def __hash__(self) -> int:
        """Get the hash."""
        return hash((self.author, self.name, self.version))

    def __repr__(self) -> str:
        """Get the representation."""
        return f"<{self}>"

    def __eq__(self, other: Any) -> bool:
        """Compare with another object."""
        return (
            isinstance(other, PublicId)
            and self.author == other.author
            and self.name == other.name
            and self.version == other.version
        )

    def __lt__(self, other: Any) -> bool:
        """
        Compare two public ids.

        >>> public_id_1 = PublicId("author_1", "name_1", "0.1.0")
        >>> public_id_2 = PublicId("author_1", "name_1", "0.1.1")
        >>> public_id_3 = PublicId("author_1", "name_2", "0.1.0")
        >>> public_id_1 > public_id_2
        False
        >>> public_id_1 < public_id_2
        True

        >>> public_id_1 < public_id_3
        Traceback (most recent call last):
        ...
        ValueError: The public IDs author_1/name_1:0.1.0 and author_1/name_2:0.1.0 cannot be compared. Their author or name attributes are different.

        :param other: the object to compate to
        :raises ValueError: if the public ids cannot be confirmed
        :return: whether or not the inequality is satisfied
        """
        if (
            isinstance(other, PublicId)
            and self.author == other.author
            and self.name == other.name
        ):
            return self.package_version < other.package_version
        raise ValueError(
            "The public IDs {} and {} cannot be compared. Their author or name attributes are different.".format(
                self, other
            )
        )

    def without_hash(
        self,
    ) -> "PublicId":
        """Returns a `PublicId` object with same parameters."""
        return PublicId(self.author, self.name, self.version)

    def with_hash(self, package_hash: str) -> "PublicId":
        """Returns a `PublicId` object with same parameters."""
        return PublicId(self.author, self.name, self.version, package_hash)

    def __str__(self) -> str:
        """Get the string representation."""
        if self._package_hash is None:
            return "{author}/{name}:{version}".format(
                author=self.author, name=self.name, version=self.version
            )

        return "{author}/{name}:{version}:{package_hash}".format(
            author=self.author,
            name=self.name,
            version=self.version,
            package_hash=self.hash,
        )


class PackageId:
    """A package identifier."""

    PACKAGE_TYPE_REGEX = r"({}|{}|{}|{}|{}|{})".format(
        PackageType.AGENT,
        PackageType.PROTOCOL,
        PackageType.SKILL,
        PackageType.CONNECTION,
        PackageType.CONTRACT,
        PackageType.SERVICE,
    )
    PACKAGE_ID_URI_REGEX = r"{}/{}".format(
        PACKAGE_TYPE_REGEX, PublicId.PUBLIC_ID_URI_REGEX[1:-1]
    )

    __slots__ = ("_package_type", "_public_id")

    def __init__(
        self, package_type: Union[PackageType, str], public_id: PublicId
    ) -> None:
        """
        Initialize the package id.

        :param package_type: the package type.
        :param public_id: the public id.
        """
        self._package_type = PackageType(package_type)
        self._public_id = public_id

    @property
    def package_type(self) -> PackageType:
        """Get the package type."""
        return self._package_type

    @property
    def public_id(self) -> PublicId:
        """Get the public id."""
        return self._public_id

    @property
    def author(self) -> str:
        """Get the author of the package."""
        return self.public_id.author

    @property
    def name(self) -> str:
        """Get the name of the package."""
        return self.public_id.name

    @property
    def version(self) -> str:
        """Get the version of the package."""
        return self.public_id.version

    @property
    def package_hash(self) -> str:
        """Get the version of the package."""
        return self.public_id.hash

    @property
    def package_prefix(self) -> Tuple[PackageType, str, str]:
        """Get the package identifier without the version."""
        return self.package_type, self.author, self.name

    @classmethod
    def from_uri_path(cls, package_id_uri_path: str) -> "PackageId":
        """
        Initialize the package id from the string.

        >>> str(PackageId.from_uri_path("skill/author/package_name/0.1.0"))
        '(skill, author/package_name:0.1.0)'

        A bad formatted input raises value error:
        >>> PackageId.from_uri_path("very/bad/formatted:input")
        Traceback (most recent call last):
        ...
        ValueError: Input 'very/bad/formatted:input' is not well formatted.

        :param package_id_uri_path: the package id in uri path string format.
        :return: the package id object.
        :raises ValueError: if the string in input is not well formatted.
        """
        if not re.match(cls.PACKAGE_ID_URI_REGEX, package_id_uri_path):
            raise ValueError(
                "Input '{}' is not well formatted.".format(package_id_uri_path)
            )
        package_type_str, username, package_name, version = re.findall(
            cls.PACKAGE_ID_URI_REGEX, package_id_uri_path
        )[0][:4]
        package_type = PackageType(package_type_str)
        public_id = PublicId(username, package_name, version)
        return PackageId(package_type, public_id)

    @property
    def to_uri_path(self) -> str:
        """
        Turn the package id into a uri path string.

        :return: uri path string
        """
        return f"{str(self.package_type)}/{self.author}/{self.name}/{self.version}"

    def without_hash(
        self,
    ) -> "PackageId":
        """Returns PackageId object without hash"""
        return PackageId(self.package_type, self.public_id.without_hash())

    def with_hash(self, package_hash: str) -> "PackageId":
        """Returns PackageId object without hash"""
        return PackageId(
            self.package_type, self.public_id.with_hash(package_hash=package_hash)
        )

    def __hash__(self) -> int:
        """Get the hash."""
        return hash((self.package_type, self.public_id))

    def __str__(self) -> str:
        """Get the string representation."""
        return "({package_type}, {public_id})".format(
            package_type=self.package_type.value,
            public_id=self.public_id,
        )

    def __repr__(self) -> str:
        """Get the object representation in string."""
        return f"PackageId{self.__str__()}"

    def __eq__(self, other: Any) -> bool:
        """Compare with another object."""
        return (
            isinstance(other, PackageId)
            and self.package_type == other.package_type
            and self.public_id == other.public_id
        )

    def __lt__(self, other: Any) -> bool:
        """Compare two public ids."""
        return str(self) < str(other)


class ComponentId(PackageId):
    """
    Class to represent a component identifier.

    A component id is a package id, but excludes the case when the package is an agent.
    >>> pacakge_id = PackageId(PackageType.PROTOCOL, PublicId("author", "name", "0.1.0"))
    >>> component_id = ComponentId(ComponentType.PROTOCOL, PublicId("author", "name", "0.1.0"))
    >>> pacakge_id == component_id
    True

    >>> component_id2 = ComponentId(ComponentType.PROTOCOL, PublicId("author", "name", "0.1.1"))
    >>> pacakge_id == component_id2
    False
    """

    def __init__(
        self, component_type: Union[ComponentType, str], public_id: PublicId
    ) -> None:
        """
        Initialize the component id.

        :param component_type: the component type.
        :param public_id: the public id.
        """
        component_type = ComponentType(component_type)
        super().__init__(component_type.to_package_type(), public_id)

    @property
    def component_type(self) -> ComponentType:
        """Get the component type."""
        return ComponentType(self.package_type.value)

    @property
    def component_prefix(self) -> PackageIdPrefix:
        """Get the component identifier without the version."""
        package_prefix = super().package_prefix
        package_type, author, name = package_prefix
        return ComponentType(package_type.value), author, name

    def same_prefix(self, other: "ComponentId") -> bool:
        """Check if the other component id has the same type, author and name of this."""
        return (
            self.component_type == other.component_type
            and self.public_id.same_prefix(other.public_id)
        )

    @property
    def prefix_import_path(self) -> str:
        """Get the prefix import path for this component."""
        return "packages.{}.{}.{}".format(
            self.public_id.author, self.component_type.to_plural(), self.public_id.name
        )

    @property
    def json(self) -> Dict:
        """Get the JSON representation."""
        return dict(**self.public_id.json, type=str(self.component_type))

    @classmethod
    def from_json(cls, json_data: Dict) -> "ComponentId":
        """Create  component id from json data."""
        return cls(
            component_type=json_data["type"],
            public_id=PublicId.from_json(json_data),
        )

    def without_hash(
        self,
    ) -> "ComponentId":
        """Returns PackageId object without hash"""
        return ComponentId(self.component_type, self.public_id.without_hash())


class PyPIPackageName(RegexConstrainedString):
    """A PyPI Package name."""

    REGEX = re.compile(r"^([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9._-]*[A-Za-z0-9])$")


class GitRef(RegexConstrainedString):
    """
    A Git reference.

    It can be a branch name, a commit hash or a tag.
    """

    REGEX = re.compile(r"^[A-Za-z0-9/.\-_]+$")


class Dependency:
    """
    This class represents a PyPI dependency.

    It contains the following information:
    - version: a version specifier(s) (e.g. '==0.1.0').
    - index: the PyPI index where to download the package from (default: https://pypi.org)
    - git: the URL to the Git repository (e.g. https://github.com/fetchai/agents-aea.git)
    - ref: either the branch name, the tag, the commit number or a Git reference (default: 'master'.)

    If the 'git' field is set, the 'version' field will be ignored.
    These fields will be forwarded to the 'pip' command.
    """

    __slots__ = ("_name", "_version", "_index", "_git", "_ref")

    def __init__(
        self,
        name: Union[PyPIPackageName, str],
        version: Union[str, SpecifierSet] = "",
        index: Optional[str] = None,
        git: Optional[str] = None,
        ref: Optional[Union[GitRef, str]] = None,
    ) -> None:
        """
        Initialize a PyPI dependency.

        :param name: the package name.
        :param version: the specifier set object
        :param index: the URL to the PyPI server.
        :param git: the URL to a git repository.
        :param ref: the Git reference (branch/commit/tag).
        """
        self._name: PyPIPackageName = PyPIPackageName(name)
        self._version: SpecifierSet = self._parse_version(version)
        self._index: Optional[str] = index
        self._git: Optional[str] = git
        self._ref: Optional[GitRef] = GitRef(ref) if ref is not None else None

    @property
    def name(self) -> str:
        """Get the name."""
        return str(self._name)

    @property
    def version(self) -> str:
        """Get the version."""
        return str(self._version)

    @property
    def index(self) -> Optional[str]:
        """Get the index."""
        return str(self._index) if self._index else None

    @property
    def git(self) -> Optional[str]:
        """Get the git."""
        return str(self._git) if self._git else None

    @property
    def ref(self) -> Optional[str]:
        """Get the ref."""
        return str(self._ref) if self._ref else None

    @staticmethod
    def _parse_version(version: Union[str, SpecifierSet]) -> SpecifierSet:
        """
        Parse a version specifier set.

        :param version: the version, a string or a SpecifierSet instance.
        :return: the SpecifierSet instance.
        """
        return version if isinstance(version, SpecifierSet) else SpecifierSet(version)

    @classmethod
    def from_json(cls, obj: Dict[str, Dict[str, str]]) -> "Dependency":
        """Parse a dependency object from a dictionary."""
        if len(obj) != 1:
            raise ValueError(f"Only one key allowed, found {set(obj.keys())}")
        name, attributes = list(obj.items())[0]
        allowed_keys = {"version", "index", "git", "ref"}
        not_allowed_keys = set(attributes.keys()).difference(allowed_keys)
        if len(not_allowed_keys) > 0:
            raise ValueError(f"Not allowed keys: {not_allowed_keys}")

        version = attributes.get("version", "")
        index = attributes.get("index", None)
        git = attributes.get("git", None)
        ref = attributes.get("ref", None)

        return Dependency(name=name, version=version, index=index, git=git, ref=ref)

    def to_json(self) -> Dict[str, Dict[str, str]]:
        """Transform the object to JSON."""
        result = {}
        if self.version != "":
            result["version"] = self.version
        if self.index is not None:
            result["index"] = self.index
        if self.git is not None:
            result["git"] = cast(str, self.git)
        if self.ref is not None:
            result["ref"] = cast(str, self.ref)
        return {self.name: result}

    def get_pip_install_args(self) -> List[str]:
        """Get 'pip install' arguments."""
        name = self.name
        index = self.index
        git_url = self.git
        revision = self.ref if self.ref is not None else DEFAULT_GIT_REF
        version_constraint = str(self.version)
        command: List[str] = []
        if index is not None:
            command += ["-i", index]
        if git_url is not None:
            command += ["git+" + git_url + "@" + revision + "#egg=" + name]
        else:
            command += [name + version_constraint]
        return command

    def __str__(self) -> str:
        """Get the string representation."""
        return f"{self.__class__.__name__}(name='{self.name}', version='{self.version}', index='{self.index}', git='{self.git}', ref='{self.ref}')"

    def __eq__(self, other: Any) -> bool:
        """Compare with another object."""
        return (
            isinstance(other, Dependency)
            and self._name == other._name
            and self._version == other._version
            and self._index == other._index
            and self._git == other._git
            and self._ref == other._ref
        )


Dependencies = Dict[str, Dependency]
"""
A dictionary from package name to dependency data structure (see above).
The package name must satisfy  <a href="https://www.python.org/dev/peps/pep-0426/#name">the constraints on Python packages names</a>.

The main advantage of having a dictionary is that we implicitly filter out dependency duplicates.
We cannot have two items with the same package name since the keys of a YAML object form a set.
"""


class CRUDCollection(Generic[T]):
    """Interface of a CRUD collection."""

    __slots__ = ("_items_by_id",)

    def __init__(self) -> None:
        """Instantiate a CRUD collection."""
        self._items_by_id = {}  # type: Dict[str, T]

    def create(self, item_id: str, item: T) -> None:
        """
        Add an item.

        :param item_id: the item id.
        :param item: the item to be added.
        :raises ValueError: if the item with the same id is already in the collection.
        """
        if item_id in self._items_by_id:
            raise ValueError("Item with name {} already present!".format(item_id))
        self._items_by_id[item_id] = item

    def read(self, item_id: str) -> Optional[T]:
        """
        Get an item by its name.

        :param item_id: the item id.
        :return: the associated item, or None if the item id is not present.
        """
        return self._items_by_id.get(item_id, None)

    def update(self, item_id: str, item: T) -> None:
        """
        Update an existing item.

        :param item_id: the item id.
        :param item: the item to be added.
        """
        self._items_by_id[item_id] = item

    def delete(self, item_id: str) -> None:
        """Delete an item."""
        if item_id in self._items_by_id.keys():
            del self._items_by_id[item_id]

    def read_all(self) -> List[Tuple[str, T]]:
        """Read all the items."""
        return [  # pylint: disable=unnecessary-comprehension
            (k, v) for k, v in self._items_by_id.items()
        ]

    def keys(self) -> Set[str]:
        """Get the set of keys."""
        return set(self._items_by_id.keys())
