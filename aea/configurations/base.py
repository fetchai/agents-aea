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

"""Classes to handle AEA configurations."""
import functools
import pprint
import re
from abc import ABC, abstractmethod
from collections import OrderedDict
from copy import copy, deepcopy
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Collection,
    Dict,
    FrozenSet,
    Generic,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

import packaging
import semver
from packaging.specifiers import SpecifierSet
from packaging.version import Version
from urllib3.util import Url, parse_url

from aea.__version__ import __version__ as __aea_version__
from aea.configurations.constants import (
    AGENT,
    CONNECTION,
    CONNECTIONS,
    CONTRACT,
    CONTRACTS,
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_CONNECTION_CONFIG_FILE,
    DEFAULT_CONTRACT_CONFIG_FILE,
    DEFAULT_FINGERPRINT_IGNORE_PATTERNS,
    DEFAULT_GIT_REF,
    DEFAULT_LICENSE,
    DEFAULT_PROTOCOL_CONFIG_FILE,
    DEFAULT_REGISTRY_NAME,
    DEFAULT_SKILL_CONFIG_FILE,
    DEFAULT_VERSION,
    PACKAGE_PUBLIC_ID_VAR_NAME,
    PROTOCOL,
    PROTOCOLS,
    SKILL,
    SKILLS,
)
from aea.exceptions import enforce
from aea.helpers.base import (
    RegexConstrainedString,
    STRING_LENGTH_LIMIT,
    SimpleId,
    SimpleIdOrStr,
    load_module,
    recursive_update,
)
from aea.helpers.ipfs.base import IPFSHashOnly


T = TypeVar("T")


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

    def __init__(
        self,
        name: Union[PyPIPackageName, str],
        version: Union[str, SpecifierSet] = "",
        index: Optional[Union[str, Url]] = None,
        git: Optional[Union[str, Url]] = None,
        ref: Optional[Union[GitRef, str]] = None,
    ):
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
        self._index: Optional[Url] = self._parse_url(
            index
        ) if index is not None else None
        self._git: Optional[Url] = self._parse_url(git) if git is not None else None
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

    @staticmethod
    def _parse_url(url: Union[str, Url]) -> Url:
        """
        Parse an URL.

        :param url: the URL, in either string or an urllib3.Url instance.
        :return: the urllib3.Url instance.
        """
        return url if isinstance(url, Url) else parse_url(url)

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

    def __eq__(self, other):
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


def dependencies_from_json(obj: Dict[str, Dict]) -> Dependencies:
    """
    Parse a JSON object to get an instance of Dependencies.

    :param obj: a dictionary whose keys are package names and values are dictionary with package specifications.
    :return: a Dependencies object.
    """
    return {key: Dependency.from_json({key: value}) for key, value in obj.items()}


def dependencies_to_json(dependencies: Dependencies) -> Dict[str, Dict]:
    """
    Transform a Dependencies object into a JSON object.

    :param dependencies: an instance of "Dependencies" type.
    :return: a dictionary whose keys are package names and
             values are the JSON version of a Dependency object.
    """
    result = {}
    for key, value in dependencies.items():
        dep_to_json = value.to_json()
        package_name = list(dep_to_json.items())[0][0]
        enforce(
            key == package_name, f"Names of dependency differ: {key} != {package_name}"
        )
        result[key] = dep_to_json[key]
    return result


VersionInfoClass = semver.VersionInfo
PackageVersionLike = Union[str, semver.VersionInfo]


@functools.total_ordering
class PackageVersion:
    """A package version."""

    _version: PackageVersionLike

    def __init__(self, version_like: PackageVersionLike):
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

    def __eq__(self, other) -> bool:
        """Check equality."""
        return isinstance(other, PackageVersion) and self._version == other._version

    def __lt__(self, other):
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

        """
        return self.value + "s"

    def configuration_class(self) -> Type["PackageConfiguration"]:
        """Get the configuration class."""
        d: Dict[PackageType, Type["PackageConfiguration"]] = {
            PackageType.AGENT: AgentConfig,
            PackageType.PROTOCOL: ProtocolConfig,
            PackageType.CONNECTION: ConnectionConfig,
            PackageType.CONTRACT: ContractConfig,
            PackageType.SKILL: SkillConfig,
        }
        return d[self]

    def __str__(self):
        """Convert to string."""
        return str(self.value)


def _get_default_configuration_file_name_from_type(
    item_type: Union[str, PackageType]
) -> str:
    """Get the default configuration file name from item type."""
    item_type = PackageType(item_type)
    if item_type == PackageType.AGENT:
        return DEFAULT_AEA_CONFIG_FILE
    if item_type == PackageType.PROTOCOL:
        return DEFAULT_PROTOCOL_CONFIG_FILE
    if item_type == PackageType.CONNECTION:
        return DEFAULT_CONNECTION_CONFIG_FILE
    if item_type == PackageType.SKILL:
        return DEFAULT_SKILL_CONFIG_FILE
    if item_type == PackageType.CONTRACT:
        return DEFAULT_CONTRACT_CONFIG_FILE
    raise ValueError(  # pragma: no cover
        "Item type not valid: {}".format(str(item_type))
    )


class ComponentType(Enum):
    """Enum of component types supported."""

    PROTOCOL = PROTOCOL
    CONNECTION = CONNECTION
    SKILL = SKILL
    CONTRACT = CONTRACT

    def to_configuration_type(self) -> PackageType:
        """Get package type for component type."""
        return PackageType(self.value)

    @staticmethod
    def plurals() -> Collection[str]:
        """
        Get the collection of type names, plural.

        >>> ComponentType.plurals()
        ['protocols', 'connections', 'skills', 'contracts']
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
        """
        return self.value + "s"

    def __str__(self) -> str:
        """Get the string representation."""
        return str(self.value)


class ProtocolSpecificationParseError(Exception):
    """Exception for parsing a protocol specification file."""


class JSONSerializable(ABC):
    """Interface for JSON-serializable objects."""

    @property
    @abstractmethod
    def json(self) -> Dict:
        """Compute the JSON representation."""

    @classmethod
    def from_json(cls, obj: Dict):
        """Build from a JSON object."""


class Configuration(JSONSerializable, ABC):
    """Configuration class."""

    def __init__(self):
        """Initialize a configuration object."""
        # a list of keys that remembers the key order of the configuration file.
        # this is set by the configuration loader.
        self._key_order = []

    @classmethod
    def from_json(cls, obj: Dict) -> "Configuration":
        """Build from a JSON object."""

    @property
    def ordered_json(self) -> OrderedDict:
        """
        Reorder the dictionary according to a key ordering.

        This method takes all the keys in the key_order list and
        get the associated value in the dictionary (if present).
        For the remaining keys not considered in the order,
        it will use alphanumerical ordering.

        In particular, if key_order is an empty sequence, this reduces to
        alphanumerical sorting.

        It does not do side-effect.
        :return: the ordered dictionary.
        """
        data = self.json
        result = OrderedDict()  # type: OrderedDict

        # parse all the known keys. This might ignore some keys in the dictionary.
        seen_keys = set()
        for key in self._key_order:
            enforce(key not in result, "Key in results!")
            value = data.get(key)
            if value is not None:
                result[key] = value
                seen_keys.add(key)

        # Now process the keys in the dictionary that were not covered before.
        for key, value in data.items():
            if key not in seen_keys:
                result[key] = value
        return result


class CRUDCollection(Generic[T]):
    """Interface of a CRUD collection."""

    def __init__(self):
        """Instantiate a CRUD collection."""
        self._items_by_id = {}  # type: Dict[str, T]

    def create(self, item_id: str, item: T) -> None:
        """
        Add an item.

        :param item_id: the item id.
        :param item: the item to be added.
        :return: None
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
        :return: None
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

    AUTHOR_REGEX = fr"[a-zA-Z_][a-zA-Z0-9_]{{0,{STRING_LENGTH_LIMIT - 1}}}"
    PACKAGE_NAME_REGEX = fr"[a-zA-Z_][a-zA-Z0-9_]{{0,{STRING_LENGTH_LIMIT  - 1}}}"
    VERSION_NUMBER_PART_REGEX = r"(0|[1-9]\d*)"
    VERSION_REGEX = fr"(any|latest|({VERSION_NUMBER_PART_REGEX})\.({VERSION_NUMBER_PART_REGEX})\.({VERSION_NUMBER_PART_REGEX})(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?)"
    PUBLIC_ID_REGEX = fr"^({AUTHOR_REGEX})/({PACKAGE_NAME_REGEX})(:({VERSION_REGEX}))?$"
    PUBLIC_ID_URI_REGEX = (
        fr"^({AUTHOR_REGEX})/({PACKAGE_NAME_REGEX})/({VERSION_REGEX})$"
    )

    ANY_VERSION = "any"
    LATEST_VERSION = "latest"

    def __init__(
        self,
        author: SimpleIdOrStr,
        name: SimpleIdOrStr,
        version: Optional[PackageVersionLike] = None,
    ):
        """Initialize the public identifier."""
        self._author = SimpleId(author)
        self._name = SimpleId(name)
        self._package_version = (
            PackageVersion(version)
            if version is not None
            else PackageVersion(self.LATEST_VERSION)
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

    def to_any(self) -> "PublicId":
        """Return the same public id, but with any version."""
        return PublicId(self.author, self.name, self.ANY_VERSION)

    def same_prefix(self, other: "PublicId") -> bool:
        """Check if the other public id has the same author and name of this."""
        return self.name == other.name and self.author == other.author

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
        """
        Initialize the public id from the string.

        >>> str(PublicId.from_str("author/package_name:0.1.0"))
        'author/package_name:0.1.0'

        A bad formatted input raises value error:
        >>> PublicId.from_str("bad/formatted:input")
        Traceback (most recent call last):
        ...
        ValueError: Input 'bad/formatted:input' is not well formatted.

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
        version = match.group(3)[1:] if ":" in public_id_string else None
        return PublicId(username, package_name, version)

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
        return {"author": self.author, "name": self.name, "version": self.version}

    @classmethod
    def from_json(cls, obj: Dict):
        """Build from a JSON object."""
        return PublicId(obj["author"], obj["name"], obj["version"],)

    def __hash__(self):
        """Get the hash."""
        return hash((self.author, self.name, self.version))

    def __str__(self):
        """Get the string representation."""
        return "{author}/{name}:{version}".format(
            author=self.author, name=self.name, version=self.version
        )

    def __repr__(self):
        """Get the representation."""
        return f"<{self}>"

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, PublicId)
            and self.author == other.author
            and self.name == other.name
            and self.version == other.version
        )

    def __lt__(self, other):
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


class PackageId:
    """A package identifier."""

    PACKAGE_TYPE_REGEX = r"({}|{}|{}|{}|{})".format(
        PackageType.AGENT,
        PackageType.PROTOCOL,
        PackageType.SKILL,
        PackageType.CONNECTION,
        PackageType.CONTRACT,
    )
    PACKAGE_ID_URI_REGEX = r"{}/{}".format(
        PACKAGE_TYPE_REGEX, PublicId.PUBLIC_ID_URI_REGEX[1:-1]
    )

    def __init__(self, package_type: Union[PackageType, str], public_id: PublicId):
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
    def package_prefix(self) -> Tuple[PackageType, str, str]:
        """Get the package identifier without the version."""
        return self.package_type, self.author, self.name

    @classmethod
    def from_uri_path(cls, package_id_uri_path: str) -> "PackageId":
        """
        Initialize the public id from the string.

        >>> str(PackageId.from_uri_path("skill/author/package_name/0.1.0"))
        '(skill, author/package_name:0.1.0)'

        A bad formatted input raises value error:
        >>> PackageId.from_uri_path("very/bad/formatted:input")
        Traceback (most recent call last):
        ...
        ValueError: Input 'very/bad/formatted:input' is not well formatted.

        :param public_id_uri_path: the public id in uri path string format.
        :return: the public id object.
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

    def __hash__(self):
        """Get the hash."""
        return hash((self.package_type, self.public_id))

    def __str__(self):
        """Get the string representation."""
        return "({package_type}, {public_id})".format(
            package_type=self.package_type.value, public_id=self.public_id,
        )

    def __repr__(self):
        """Get the object representation in string."""
        return f"PackageId{self.__str__()}"

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, PackageId)
            and self.package_type == other.package_type
            and self.public_id == other.public_id
        )

    def __lt__(self, other):
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

    def __init__(self, component_type: Union[ComponentType, str], public_id: PublicId):
        """
        Initialize the component id.

        :param component_type: the component type.
        :param public_id: the public id.
        """
        component_type = ComponentType(component_type)
        super().__init__(component_type.to_configuration_type(), public_id)

    @property
    def component_type(self) -> ComponentType:
        """Get the component type."""
        return ComponentType(self.package_type.value)

    @property
    def component_prefix(self) -> Tuple[ComponentType, str, str]:
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


class PackageConfiguration(Configuration, ABC):
    """
    This class represent a package configuration.

    A package can be one of:
    - agents
    - protocols
    - connections
    - skills
    - contracts
    """

    default_configuration_filename: str
    package_type: PackageType
    FIELDS_ALLOWED_TO_UPDATE: FrozenSet[str] = frozenset()

    def __init__(
        self,
        name: SimpleIdOrStr,
        author: SimpleIdOrStr,
        version: str = "",
        license_: str = "",
        aea_version: str = "",
        fingerprint: Optional[Dict[str, str]] = None,
        fingerprint_ignore_patterns: Optional[Sequence[str]] = None,
        build_entrypoint: Optional[str] = None,
    ):
        """
        Initialize a package configuration.

        :param name: the name of the package.
        :param author: the author of the package.
        :param version: the version of the package (SemVer format).
        :param license_: the license.
        :param aea_version: either a fixed version, or a set of specifiers
           describing the AEA versions allowed.
           (default: empty string - no constraint).
           The fixed version is interpreted with the specifier '=='.
        :param fingerprint: the fingerprint.
        :param fingerprint_ignore_patterns: a list of file patterns to ignore files to fingerprint.
        :param build_entrypoint: path to a script to execute at build time.
        """
        super().__init__()
        if name is None or author is None:  # pragma: nocover
            raise ValueError("Name and author must be set on the configuration!")
        self._name = SimpleId(name)
        self._author = SimpleId(author)
        self.version = version if version != "" else DEFAULT_VERSION
        self.license = license_ if license_ != "" else DEFAULT_LICENSE
        self.fingerprint = fingerprint if fingerprint is not None else {}
        self.fingerprint_ignore_patterns = (
            fingerprint_ignore_patterns
            if fingerprint_ignore_patterns is not None
            else []
        )
        self.build_entrypoint = build_entrypoint
        self.aea_version = aea_version if aea_version != "" else __aea_version__
        self._aea_version_specifiers = self._parse_aea_version_specifier(aea_version)

        self._directory = None  # type: Optional[Path]

    @property
    def name(self) -> str:
        """Get the name."""
        return str(self._name)

    @name.setter
    def name(self, value: SimpleIdOrStr):
        """Set the name."""
        self._name = SimpleId(value)

    @property
    def author(self) -> str:
        """Get the author."""
        return str(self._author)

    @author.setter
    def author(self, value: SimpleIdOrStr):
        """Set the author."""
        self._author = SimpleId(value)

    @property
    def directory(self) -> Optional[Path]:
        """Get the path to the configuration file associated to this file, if any."""
        return self._directory

    @directory.setter
    def directory(self, directory: Path) -> None:
        """Set directory if not already set."""
        if self._directory is not None:  # pragma: nocover
            raise ValueError("Directory already set")
        self._directory = directory

    @staticmethod
    def _parse_aea_version_specifier(aea_version_specifiers: str) -> SpecifierSet:
        try:
            Version(aea_version_specifiers)
            return SpecifierSet("==" + aea_version_specifiers)
        except packaging.version.InvalidVersion:
            pass
        return SpecifierSet(aea_version_specifiers)

    @property
    def aea_version_specifiers(self) -> SpecifierSet:
        """Get the AEA version set specifier."""
        return self._aea_version_specifiers

    @property
    def public_id(self) -> PublicId:
        """Get the public id."""
        return PublicId(self.author, self.name, self.version)

    @property
    def package_dependencies(self) -> Set[ComponentId]:
        """Get the package dependencies."""
        return set()

    def update(self, data: Dict) -> None:
        """
        Update configuration with other data.

        :param data: the data to replace.
        :return: None
        """


class ComponentConfiguration(PackageConfiguration, ABC):
    """Class to represent an agent component configuration."""

    package_type: PackageType

    def __init__(
        self,
        name: SimpleIdOrStr,
        author: SimpleIdOrStr,
        version: str = "",
        license_: str = "",
        aea_version: str = "",
        fingerprint: Optional[Dict[str, str]] = None,
        fingerprint_ignore_patterns: Optional[Sequence[str]] = None,
        build_entrypoint: Optional[str] = None,
        build_directory: Optional[str] = None,
        dependencies: Optional[Dependencies] = None,
    ):
        """Set component configuration."""
        super().__init__(
            name,
            author,
            version,
            license_,
            aea_version,
            fingerprint,
            fingerprint_ignore_patterns,
            build_entrypoint,
        )
        self.pypi_dependencies: Dependencies = dependencies if dependencies is not None else {}
        self._build_directory = build_directory

    @property
    def build_directory(self) -> Optional[str]:
        """Get the component type."""
        return self._build_directory

    @build_directory.setter
    def build_directory(self, value: Optional[str]) -> None:
        """Get the component type."""
        self._build_directory = value

    @property
    def component_type(self) -> ComponentType:
        """Get the component type."""
        return ComponentType(self.package_type.value)

    @property
    def component_id(self) -> ComponentId:
        """Get the component id."""
        return ComponentId(self.component_type, self.public_id)

    @property
    def prefix_import_path(self) -> str:
        """Get the prefix import path for this component."""
        return "packages.{}.{}.{}".format(
            self.public_id.author, self.component_type.to_plural(), self.public_id.name
        )

    @property
    def is_abstract_component(self) -> bool:
        """Check whether the component is abstract."""
        return False

    def _check_configuration_consistency(self, directory: Path):
        """Check that the configuration file is consistent against a directory."""
        self.check_fingerprint(directory)
        self.check_aea_version()
        self.check_public_id_consistency(directory)

    def check_fingerprint(self, directory: Path) -> None:
        """
        Check that the fingerprint are correct against a directory path.

        :raises ValueError if:
            - the argument is not a valid package directory
            - the fingerprints do not match.
        """
        if not directory.exists() or not directory.is_dir():
            raise ValueError("Directory {} is not valid.".format(directory))
        _compare_fingerprints(
            self, directory, False, self.component_type.to_configuration_type()
        )

    def check_aea_version(self):
        """
        Check that the AEA version matches the specifier set.

        :raises ValueError if the version of the aea framework falls within a specifier.
        """
        _check_aea_version(self)

    def check_public_id_consistency(self, directory: Path) -> None:
        """
        Check that the public ids in the init file match the config.

        :raises ValueError if:
            - the argument is not a valid package directory
            - the public ids do not match.
        """
        if not directory.exists() or not directory.is_dir():
            raise ValueError("Directory {} is not valid.".format(directory))
        _compare_public_ids(self, directory)


class ConnectionConfig(ComponentConfiguration):
    """Handle connection configuration."""

    default_configuration_filename = DEFAULT_CONNECTION_CONFIG_FILE
    package_type = PackageType.CONNECTION

    FIELDS_ALLOWED_TO_UPDATE: FrozenSet[str] = frozenset(["config", "is_abstract"])

    def __init__(
        self,
        name: SimpleIdOrStr = "",
        author: SimpleIdOrStr = "",
        version: str = "",
        license_: str = "",
        aea_version: str = "",
        fingerprint: Optional[Dict[str, str]] = None,
        fingerprint_ignore_patterns: Optional[Sequence[str]] = None,
        build_entrypoint: Optional[str] = None,
        build_directory: Optional[str] = None,
        class_name: str = "",
        protocols: Optional[Set[PublicId]] = None,
        connections: Optional[Set[PublicId]] = None,
        restricted_to_protocols: Optional[Set[PublicId]] = None,
        excluded_protocols: Optional[Set[PublicId]] = None,
        dependencies: Optional[Dependencies] = None,
        description: str = "",
        connection_id: Optional[PublicId] = None,
        is_abstract: bool = False,
        **config,
    ):
        """Initialize a connection configuration object."""
        if connection_id is None:
            enforce(name != "", "Name or connection_id must be set.")
            enforce(author != "", "Author or connection_id must be set.")
            enforce(version != "", "Version or connection_id must be set.")
        else:
            enforce(
                name in ("", connection_id.name,),
                "Non matching name in ConnectionConfig name and public id.",
            )
            name = connection_id.name
            enforce(
                author in ("", connection_id.author,),
                "Non matching author in ConnectionConfig author and public id.",
            )
            author = connection_id.author
            enforce(
                version in ("", connection_id.version,),
                "Non matching version in ConnectionConfig version and public id.",
            )
            version = connection_id.version
        super().__init__(
            name,
            author,
            version,
            license_,
            aea_version,
            fingerprint,
            fingerprint_ignore_patterns,
            build_entrypoint,
            build_directory,
            dependencies,
        )
        self.class_name = class_name
        self.protocols = protocols if protocols is not None else set()
        self.connections = connections if connections is not None else set()
        self.restricted_to_protocols = (
            restricted_to_protocols if restricted_to_protocols is not None else set()
        )
        self.excluded_protocols = (
            excluded_protocols if excluded_protocols is not None else set()
        )
        self.dependencies = dependencies if dependencies is not None else {}
        self.description = description
        self.config = config if len(config) > 0 else {}
        self.is_abstract = is_abstract

    @property
    def package_dependencies(self) -> Set[ComponentId]:
        """Get the connection dependencies."""
        return {
            ComponentId(ComponentType.PROTOCOL, protocol_id)
            for protocol_id in self.protocols
        }.union(
            {
                ComponentId(ComponentType.CONNECTION, connection_id)
                for connection_id in self.connections
            }
        )

    @property
    def is_abstract_component(self) -> bool:
        """Check whether the component is abstract."""
        return self.is_abstract

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        result = OrderedDict(
            {
                "name": self.name,
                "author": self.author,
                "version": self.version,
                "type": self.component_type.value,
                "description": self.description,
                "license": self.license,
                "aea_version": self.aea_version,
                "fingerprint": self.fingerprint,
                "fingerprint_ignore_patterns": self.fingerprint_ignore_patterns,
                PROTOCOLS: sorted(map(str, self.protocols)),
                CONNECTIONS: sorted(map(str, self.connections)),
                "class_name": self.class_name,
                "config": self.config,
                "excluded_protocols": sorted(map(str, self.excluded_protocols)),
                "restricted_to_protocols": sorted(
                    map(str, self.restricted_to_protocols)
                ),
                "dependencies": dependencies_to_json(self.dependencies),
                "is_abstract": self.is_abstract,
            }
        )
        if self.build_entrypoint:
            result["build_entrypoint"] = self.build_entrypoint
        if self.build_directory:
            result["build_directory"] = self.build_directory
        return result

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        restricted_to_protocols = obj.get("restricted_to_protocols", set())
        restricted_to_protocols = {
            PublicId.from_str(id_) for id_ in restricted_to_protocols
        }
        excluded_protocols = obj.get("excluded_protocols", set())
        excluded_protocols = {PublicId.from_str(id_) for id_ in excluded_protocols}
        dependencies = dependencies_from_json(obj.get("dependencies", {}))
        protocols = {PublicId.from_str(id_) for id_ in obj.get(PROTOCOLS, set())}
        connections = {PublicId.from_str(id_) for id_ in obj.get(CONNECTIONS, set())}
        return ConnectionConfig(
            name=cast(str, obj.get("name")),
            author=cast(str, obj.get("author")),
            version=cast(str, obj.get("version")),
            license_=cast(str, obj.get("license")),
            aea_version=cast(str, obj.get("aea_version", "")),
            fingerprint=cast(Dict[str, str], obj.get("fingerprint")),
            fingerprint_ignore_patterns=cast(
                Sequence[str], obj.get("fingerprint_ignore_patterns")
            ),
            build_entrypoint=cast(Optional[str], obj.get("build_entrypoint")),
            build_directory=cast(Optional[str], obj.get("build_directory")),
            class_name=cast(str, obj.get("class_name")),
            protocols=cast(Set[PublicId], protocols),
            connections=cast(Set[PublicId], connections),
            restricted_to_protocols=cast(Set[PublicId], restricted_to_protocols),
            excluded_protocols=cast(Set[PublicId], excluded_protocols),
            dependencies=cast(Dependencies, dependencies),
            description=cast(str, obj.get("description", "")),
            is_abstract=obj.get("is_abstract", False),
            **cast(dict, obj.get("config", {})),
        )

    def update(self, data: Dict) -> None:
        """
        Update configuration with other data.

        This method does side-effect on the configuration object.

        :param data: the data to populate or replace.
        :return: None
        """
        new_config = data.get("config", {})
        recursive_update(self.config, new_config)
        self.is_abstract = data.get("is_abstract", self.is_abstract)


class ProtocolConfig(ComponentConfiguration):
    """Handle protocol configuration."""

    default_configuration_filename = DEFAULT_PROTOCOL_CONFIG_FILE
    package_type = PackageType.PROTOCOL

    FIELDS_ALLOWED_TO_UPDATE: FrozenSet[str] = frozenset()

    def __init__(
        self,
        name: SimpleIdOrStr,
        author: SimpleIdOrStr,
        version: str = "",
        license_: str = "",
        fingerprint: Optional[Dict[str, str]] = None,
        fingerprint_ignore_patterns: Optional[Sequence[str]] = None,
        build_entrypoint: Optional[str] = None,
        build_directory: Optional[str] = None,
        aea_version: str = "",
        dependencies: Optional[Dependencies] = None,
        description: str = "",
    ):
        """Initialize a connection configuration object."""
        super().__init__(
            name,
            author,
            version,
            license_,
            aea_version,
            fingerprint,
            fingerprint_ignore_patterns,
            build_entrypoint,
            build_directory,
            dependencies,
        )
        self.dependencies = dependencies if dependencies is not None else {}
        self.description = description

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        result = OrderedDict(
            {
                "name": self.name,
                "author": self.author,
                "version": self.version,
                "type": self.component_type.value,
                "description": self.description,
                "license": self.license,
                "aea_version": self.aea_version,
                "fingerprint": self.fingerprint,
                "fingerprint_ignore_patterns": self.fingerprint_ignore_patterns,
                "dependencies": dependencies_to_json(self.dependencies),
            }
        )
        if self.build_entrypoint:
            result["build_entrypoint"] = self.build_entrypoint
        if self.build_directory:
            result["build_directory"] = self.build_directory
        return result

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        dependencies = dependencies_from_json(obj.get("dependencies", {}))
        return ProtocolConfig(
            name=cast(str, obj.get("name")),
            author=cast(str, obj.get("author")),
            version=cast(str, obj.get("version")),
            license_=cast(str, obj.get("license")),
            aea_version=cast(str, obj.get("aea_version", "")),
            fingerprint=cast(Dict[str, str], obj.get("fingerprint")),
            fingerprint_ignore_patterns=cast(
                Sequence[str], obj.get("fingerprint_ignore_patterns")
            ),
            build_entrypoint=cast(Optional[str], obj.get("build_entrypoint")),
            build_directory=cast(Optional[str], obj.get("build_directory")),
            dependencies=dependencies,
            description=cast(str, obj.get("description", "")),
        )


class SkillComponentConfiguration:
    """This class represent a skill component configuration."""

    def __init__(self, class_name: str, **args):
        """
        Initialize a skill component configuration.

        :param skill_component_type: the skill component type.
        :param class_name: the class name of the component.
        :param args: keyword arguments.
        """
        self.class_name = class_name
        self.args = args

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        return {"class_name": self.class_name, "args": self.args}

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        class_name = cast(str, obj.get("class_name"))
        return SkillComponentConfiguration(class_name=class_name, **obj.get("args", {}))


class SkillConfig(ComponentConfiguration):
    """Class to represent a skill configuration file."""

    default_configuration_filename = DEFAULT_SKILL_CONFIG_FILE
    package_type = PackageType.SKILL

    FIELDS_ALLOWED_TO_UPDATE: FrozenSet[str] = frozenset(
        ["behaviours", "handlers", "models", "is_abstract"]
    )
    FIELDS_WITH_NESTED_FIELDS: FrozenSet[str] = frozenset(
        ["behaviours", "handlers", "models"]
    )
    NESTED_FIELDS_ALLOWED_TO_UPDATE: FrozenSet[str] = frozenset(["args"])

    def __init__(
        self,
        name: SimpleIdOrStr,
        author: SimpleIdOrStr,
        version: str = "",
        license_: str = "",
        aea_version: str = "",
        fingerprint: Optional[Dict[str, str]] = None,
        fingerprint_ignore_patterns: Optional[Sequence[str]] = None,
        build_entrypoint: Optional[str] = None,
        build_directory: Optional[str] = None,
        connections: Optional[Set[PublicId]] = None,
        protocols: Optional[Set[PublicId]] = None,
        contracts: Optional[Set[PublicId]] = None,
        skills: Optional[Set[PublicId]] = None,
        dependencies: Optional[Dependencies] = None,
        description: str = "",
        is_abstract: bool = False,
    ):
        """Initialize a skill configuration."""
        super().__init__(
            name,
            author,
            version,
            license_,
            aea_version,
            fingerprint,
            fingerprint_ignore_patterns,
            build_entrypoint,
            build_directory,
            dependencies,
        )
        self.connections = connections if connections is not None else set()
        self.protocols = protocols if protocols is not None else set()
        self.contracts = contracts if contracts is not None else set()
        self.skills = skills if skills is not None else set()
        self.dependencies = dependencies if dependencies is not None else {}
        self.description = description
        self.handlers: CRUDCollection[SkillComponentConfiguration] = CRUDCollection()
        self.behaviours: CRUDCollection[SkillComponentConfiguration] = CRUDCollection()
        self.models: CRUDCollection[SkillComponentConfiguration] = CRUDCollection()

        self.is_abstract = is_abstract

    @property
    def package_dependencies(self) -> Set[ComponentId]:
        """Get the skill dependencies."""
        return (
            {
                ComponentId(ComponentType.PROTOCOL, protocol_id)
                for protocol_id in self.protocols
            }
            .union(
                {
                    ComponentId(ComponentType.CONTRACT, contract_id)
                    for contract_id in self.contracts
                }
            )
            .union(
                {ComponentId(ComponentType.SKILL, skill_id) for skill_id in self.skills}
            )
            .union(
                {
                    ComponentId(ComponentType.CONNECTION, connection_id)
                    for connection_id in self.connections
                }
            )
        )

    @property
    def is_abstract_component(self) -> bool:
        """Check whether the component is abstract."""
        return self.is_abstract

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        result = OrderedDict(
            {
                "name": self.name,
                "author": self.author,
                "version": self.version,
                "type": self.component_type.value,
                "description": self.description,
                "license": self.license,
                "aea_version": self.aea_version,
                "fingerprint": self.fingerprint,
                "fingerprint_ignore_patterns": self.fingerprint_ignore_patterns,
                CONNECTIONS: sorted(map(str, self.connections)),
                CONTRACTS: sorted(map(str, self.contracts)),
                PROTOCOLS: sorted(map(str, self.protocols)),
                SKILLS: sorted(map(str, self.skills)),
                "behaviours": {key: b.json for key, b in self.behaviours.read_all()},
                "handlers": {key: h.json for key, h in self.handlers.read_all()},
                "models": {key: m.json for key, m in self.models.read_all()},
                "dependencies": dependencies_to_json(self.dependencies),
                "is_abstract": self.is_abstract,
            }
        )
        if self.build_entrypoint:
            result["build_entrypoint"] = self.build_entrypoint
        if self.build_directory:
            result["build_directory"] = self.build_directory
        return result

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        name = cast(str, obj.get("name"))
        author = cast(str, obj.get("author"))
        version = cast(str, obj.get("version"))
        license_ = cast(str, obj.get("license"))
        aea_version_specifiers = cast(str, obj.get("aea_version", ""))
        fingerprint = cast(Dict[str, str], obj.get("fingerprint"))
        fingerprint_ignore_patterns = cast(
            Sequence[str], obj.get("fingerprint_ignore_patterns")
        )
        build_entrypoint = cast(Optional[str], obj.get("build_entrypoint"))
        connections = {PublicId.from_str(id_) for id_ in obj.get(CONNECTIONS, set())}
        protocols = {PublicId.from_str(id_) for id_ in obj.get(PROTOCOLS, set())}
        contracts = {PublicId.from_str(id_) for id_ in obj.get(CONTRACTS, set())}
        skills = {PublicId.from_str(id_) for id_ in obj.get(SKILLS, set())}
        dependencies = dependencies_from_json(obj.get("dependencies", {}))
        description = cast(str, obj.get("description", ""))
        skill_config = SkillConfig(
            name=name,
            author=author,
            version=version,
            license_=license_,
            aea_version=aea_version_specifiers,
            fingerprint=fingerprint,
            fingerprint_ignore_patterns=fingerprint_ignore_patterns,
            build_entrypoint=build_entrypoint,
            connections=connections,
            protocols=protocols,
            contracts=contracts,
            skills=skills,
            dependencies=dependencies,
            description=description,
            is_abstract=obj.get("is_abstract", False),
            build_directory=cast(Optional[str], obj.get("build_directory")),
        )

        for behaviour_id, behaviour_data in obj.get("behaviours", {}).items():
            behaviour_config = SkillComponentConfiguration.from_json(behaviour_data)
            skill_config.behaviours.create(behaviour_id, behaviour_config)

        for handler_id, handler_data in obj.get("handlers", {}).items():
            handler_config = SkillComponentConfiguration.from_json(handler_data)
            skill_config.handlers.create(handler_id, handler_config)

        for model_id, model_data in obj.get("models", {}).items():
            model_config = SkillComponentConfiguration.from_json(model_data)
            skill_config.models.create(model_id, model_config)

        return skill_config

    def update(self, data: Dict) -> None:
        """
        Update configuration with other data.

        :param data: the data to replace.
        :return: None
        """

        def _update_skill_component_config(type_plural: str, data: Dict):
            """
            Update skill component configurations with new data.

            Also check that there are not undeclared components.
            """
            registry: CRUDCollection[SkillComponentConfiguration] = getattr(
                self, type_plural
            )
            new_component_config = data.get(type_plural, {})
            all_component_names = dict(registry.read_all())

            new_skill_component_names = set(new_component_config.keys()).difference(
                set(all_component_names.keys())
            )
            if len(new_skill_component_names) > 0:
                raise ValueError(
                    f"The custom configuration for skill {self.public_id} includes new {type_plural}: {new_skill_component_names}. This is not allowed."
                )

            for component_name, component_data in data.get(type_plural, {}).items():
                component_config = cast(
                    SkillComponentConfiguration, registry.read(component_name)
                )
                component_data_keys = set(component_data.keys())
                unallowed_keys = component_data_keys.difference(
                    SkillConfig.NESTED_FIELDS_ALLOWED_TO_UPDATE
                )
                if len(unallowed_keys) > 0:
                    raise ValueError(
                        f"These fields of skill component configuration '{component_name}' of skill '{self.public_id}' are not allowed to change: {unallowed_keys}."
                    )
                recursive_update(component_config.args, component_data.get("args", {}))

        _update_skill_component_config("behaviours", data)
        _update_skill_component_config("handlers", data)
        _update_skill_component_config("models", data)
        self.is_abstract = data.get("is_abstract", self.is_abstract)


class AgentConfig(PackageConfiguration):
    """Class to represent the agent configuration file."""

    default_configuration_filename = DEFAULT_AEA_CONFIG_FILE
    package_type = PackageType.AGENT

    FIELDS_ALLOWED_TO_UPDATE: FrozenSet[str] = frozenset(
        [
            "description",
            "registry_path",
            "logging_config",
            "private_key_paths",
            "connection_private_key_paths",
            "loop_mode",
            "runtime_mode",
            "execution_timeout",
            "timeout",
            "period",
            "max_reactions",
            "skill_exception_policy",
            "connection_exception_policy",
            "default_connection",
            "default_ledger",
            "default_routing",
            "storage_uri",
        ]
    )

    def __init__(
        self,
        agent_name: SimpleIdOrStr,
        author: SimpleIdOrStr,
        version: str = "",
        license_: str = "",
        aea_version: str = "",
        fingerprint: Optional[Dict[str, str]] = None,
        fingerprint_ignore_patterns: Optional[Sequence[str]] = None,
        build_entrypoint: Optional[str] = None,
        registry_path: str = DEFAULT_REGISTRY_NAME,
        description: str = "",
        logging_config: Optional[Dict] = None,
        period: Optional[float] = None,
        execution_timeout: Optional[float] = None,
        max_reactions: Optional[int] = None,
        error_handler: Optional[Dict] = None,
        decision_maker_handler: Optional[Dict] = None,
        skill_exception_policy: Optional[str] = None,
        connection_exception_policy: Optional[str] = None,
        default_ledger: Optional[str] = None,
        currency_denominations: Optional[Dict[str, str]] = None,
        default_connection: Optional[str] = None,
        default_routing: Optional[Dict[str, str]] = None,
        loop_mode: Optional[str] = None,
        runtime_mode: Optional[str] = None,
        storage_uri: Optional[str] = None,
        component_configurations: Optional[Dict[ComponentId, Dict]] = None,
    ):
        """Instantiate the agent configuration object."""
        super().__init__(
            agent_name,
            author,
            version,
            license_,
            aea_version,
            fingerprint,
            fingerprint_ignore_patterns,
            build_entrypoint,
        )
        self.agent_name = self.name
        self.registry_path = registry_path
        self.description = description
        self.private_key_paths = CRUDCollection[str]()
        self.connection_private_key_paths = CRUDCollection[str]()

        self.logging_config = logging_config if logging_config is not None else {}
        self.default_ledger = default_ledger
        self.currency_denominations = (
            currency_denominations if currency_denominations is not None else {}
        )
        self.default_connection = (
            PublicId.from_str(default_connection)
            if default_connection is not None
            else None
        )
        self.connections = set()  # type: Set[PublicId]
        self.contracts = set()  # type: Set[PublicId]
        self.protocols = set()  # type: Set[PublicId]
        self.skills = set()  # type: Set[PublicId]

        if self.logging_config == {}:
            self.logging_config["version"] = 1
            self.logging_config["disable_existing_loggers"] = False

        self.period: Optional[float] = period
        self.execution_timeout: Optional[float] = execution_timeout
        self.max_reactions: Optional[int] = max_reactions

        self.skill_exception_policy: Optional[str] = skill_exception_policy
        self.connection_exception_policy: Optional[str] = connection_exception_policy

        self.error_handler = error_handler if error_handler is not None else {}
        self.decision_maker_handler = (
            decision_maker_handler if decision_maker_handler is not None else {}
        )

        self.default_routing = (
            {
                PublicId.from_str(key): PublicId.from_str(value)
                for key, value in default_routing.items()
            }
            if default_routing is not None
            else {}
        )  # type: Dict[PublicId, PublicId]
        self.loop_mode = loop_mode
        self.runtime_mode = runtime_mode
        self.storage_uri = storage_uri
        # this attribute will be set through the setter below
        self._component_configurations: Dict[ComponentId, Dict] = {}
        self.component_configurations = (
            component_configurations if component_configurations is not None else {}
        )

    @property
    def component_configurations(self) -> Dict[ComponentId, Dict]:
        """Get the custom component configurations."""
        return self._component_configurations

    @component_configurations.setter
    def component_configurations(self, d: Dict[ComponentId, Dict]) -> None:
        """Set the component configurations."""
        package_type_to_set = {
            PackageType.PROTOCOL: self.protocols,
            PackageType.CONNECTION: self.connections,
            PackageType.CONTRACT: self.contracts,
            PackageType.SKILL: self.skills,
        }
        for component_id, component_configuration in d.items():
            enforce(
                component_id.public_id
                in package_type_to_set[component_id.package_type],
                f"Component {component_id} not declared in the agent configuration.",
            )
            from aea.configurations.loader import (  # pylint: disable=import-outside-toplevel,cyclic-import
                ConfigLoader,
            )

            ConfigLoader.validate_component_configuration(
                component_id, component_configuration
            )
        self._component_configurations = d

    @property
    def package_dependencies(self) -> Set[ComponentId]:
        """Get the package dependencies."""
        protocols = set(
            ComponentId(ComponentType.PROTOCOL, public_id)
            for public_id in self.protocols
        )
        connections = set(
            ComponentId(ComponentType.CONNECTION, public_id)
            for public_id in self.connections
        )
        skills = set(
            ComponentId(ComponentType.SKILL, public_id) for public_id in self.skills
        )

        contracts = set(
            ComponentId(ComponentType.CONTRACT, public_id)
            for public_id in self.contracts
        )

        return set.union(protocols, contracts, connections, skills)

    @property
    def private_key_paths_dict(self) -> Dict[str, str]:
        """Get dictionary version of private key paths."""
        return {  # pylint: disable=unnecessary-comprehension
            key: path for key, path in self.private_key_paths.read_all()
        }

    @property
    def connection_private_key_paths_dict(self) -> Dict[str, str]:
        """Get dictionary version of connection private key paths."""
        return {  # pylint: disable=unnecessary-comprehension
            key: path for key, path in self.connection_private_key_paths.read_all()
        }

    def component_configurations_json(self) -> List[OrderedDict]:
        """Get the component configurations in JSON format."""
        result: List[OrderedDict] = []
        for component_id, config in self.component_configurations.items():
            result.append(
                OrderedDict(
                    public_id=str(component_id.public_id),
                    type=str(component_id.component_type),
                    **config,
                )
            )
        return result

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        config = OrderedDict(
            {
                "agent_name": self.agent_name,
                "author": self.author,
                "version": self.version,
                "license": self.license,
                "description": self.description,
                "aea_version": self.aea_version,
                "fingerprint": self.fingerprint,
                "fingerprint_ignore_patterns": self.fingerprint_ignore_patterns,
                CONNECTIONS: sorted(map(str, self.connections)),
                CONTRACTS: sorted(map(str, self.contracts)),
                PROTOCOLS: sorted(map(str, self.protocols)),
                SKILLS: sorted(map(str, self.skills)),
                "default_connection": str(self.default_connection)
                if self.default_connection is not None
                else None,
                "default_ledger": self.default_ledger,
                "default_routing": {
                    str(key): str(value) for key, value in self.default_routing.items()
                },
                "connection_private_key_paths": self.connection_private_key_paths_dict,
                "private_key_paths": self.private_key_paths_dict,
                "logging_config": self.logging_config,
                "registry_path": self.registry_path,
                "component_configurations": self.component_configurations_json(),
            }
        )  # type: Dict[str, Any]

        if self.build_entrypoint:
            config["build_entrypoint"] = self.build_entrypoint

        # framework optional configs are only printed if defined.
        if self.period is not None:
            config["period"] = self.period
        if self.execution_timeout is not None:
            config["execution_timeout"] = self.execution_timeout
        if self.max_reactions is not None:
            config["max_reactions"] = self.max_reactions
        if self.error_handler != {}:
            config["error_handler"] = self.error_handler
        if self.decision_maker_handler != {}:
            config["decision_maker_handler"] = self.decision_maker_handler
        if self.skill_exception_policy is not None:
            config["skill_exception_policy"] = self.skill_exception_policy
        if self.connection_exception_policy is not None:
            config["connection_exception_policy"] = self.connection_exception_policy
        if self.loop_mode is not None:
            config["loop_mode"] = self.loop_mode
        if self.runtime_mode is not None:
            config["runtime_mode"] = self.runtime_mode
        if self.storage_uri is not None:
            config["storage_uri"] = self.storage_uri
        if self.currency_denominations != {}:
            config["currency_denominations"] = self.currency_denominations

        return config

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        agent_config = AgentConfig(
            agent_name=cast(str, obj.get("agent_name")),
            author=cast(str, obj.get("author")),
            version=cast(str, obj.get("version")),
            license_=cast(str, obj.get("license")),
            aea_version=cast(str, obj.get("aea_version", "")),
            registry_path=cast(str, obj.get("registry_path")),
            description=cast(str, obj.get("description", "")),
            fingerprint=cast(Dict[str, str], obj.get("fingerprint", {})),
            fingerprint_ignore_patterns=cast(
                Sequence[str], obj.get("fingerprint_ignore_patterns")
            ),
            build_entrypoint=cast(Optional[str], obj.get("build_entrypoint")),
            logging_config=cast(Dict, obj.get("logging_config", {})),
            period=cast(float, obj.get("period")),
            execution_timeout=cast(float, obj.get("execution_timeout")),
            max_reactions=cast(int, obj.get("max_reactions")),
            error_handler=cast(Dict, obj.get("error_handler", {})),
            decision_maker_handler=cast(Dict, obj.get("decision_maker_handler", {})),
            skill_exception_policy=cast(str, obj.get("skill_exception_policy")),
            connection_exception_policy=cast(
                str, obj.get("connection_exception_policy")
            ),
            default_ledger=cast(str, obj.get("default_ledger")),
            currency_denominations=cast(Dict, obj.get("currency_denominations", {})),
            default_connection=cast(str, obj.get("default_connection")),
            default_routing=cast(Dict, obj.get("default_routing", {})),
            loop_mode=cast(str, obj.get("loop_mode")),
            runtime_mode=cast(str, obj.get("runtime_mode")),
            storage_uri=cast(str, obj.get("storage_uri")),
            component_configurations=None,
        )

        #  parse private keys
        for crypto_id, path in obj.get("private_key_paths", {}).items():
            agent_config.private_key_paths.create(crypto_id, path)

        for crypto_id, path in obj.get("connection_private_key_paths", {}).items():
            agent_config.connection_private_key_paths.create(crypto_id, path)

        # parse connection public ids
        agent_config.connections = set(
            map(PublicId.from_str, obj.get(CONNECTIONS, []),)
        )

        # parse contracts public ids
        agent_config.contracts = set(map(PublicId.from_str, obj.get(CONTRACTS, []),))

        # parse protocol public ids
        agent_config.protocols = set(map(PublicId.from_str, obj.get(PROTOCOLS, []),))

        # parse skills public ids
        agent_config.skills = set(map(PublicId.from_str, obj.get(SKILLS, []),))

        # parse component configurations
        component_configurations = {}
        for config in obj.get("component_configurations", []):
            tmp = deepcopy(config)
            public_id = PublicId.from_str(tmp.pop("public_id"))
            type_ = tmp.pop("type")
            component_id = ComponentId(ComponentType(type_), public_id)
            component_configurations[component_id] = tmp
        agent_config.component_configurations = component_configurations

        return agent_config

    def update(self, data: Dict) -> None:
        """
        Update configuration with other data.

        To update the component parts, populate the field "component_configurations" as a
        mapping from ComponentId to configurations.

        :param data: the data to replace.
        :return: None
        """
        data = copy(data)
        # update component parts
        new_component_configurations: Dict = data.pop("component_configurations", {})
        result: Dict[ComponentId, Dict] = copy(self.component_configurations)
        for component_id, obj in new_component_configurations.items():
            if component_id not in result:
                result[component_id] = obj
            else:
                recursive_update(result[component_id], obj)
        self.component_configurations = result

        # update other fields
        for item_id, value in data.get("private_key_paths", {}).items():
            self.private_key_paths.update(item_id, value)

        for item_id, value in data.get("connection_private_key_paths", {}).items():
            self.connection_private_key_paths.update(item_id, value)

        self.logging_config = data.get("logging_config", self.logging_config)
        self.registry_path = data.get("registry_path", self.registry_path)


class SpeechActContentConfig(Configuration):
    """Handle a speech_act content configuration."""

    def __init__(self, **args):
        """Initialize a speech_act content configuration."""
        super().__init__()
        self.args = args  # type: Dict[str, str]

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        return self.args

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        return SpeechActContentConfig(**obj)


class ProtocolSpecification(ProtocolConfig):
    """Handle protocol specification."""

    def __init__(
        self,
        name: SimpleIdOrStr,
        author: SimpleIdOrStr,
        version: str = "",
        license_: str = "",
        aea_version: str = "",
        description: str = "",
    ):
        """Initialize a protocol specification configuration object."""
        super().__init__(
            name,
            author,
            version,
            license_,
            aea_version=aea_version,
            description=description,
        )
        self.speech_acts = CRUDCollection[SpeechActContentConfig]()
        self._protobuf_snippets = {}  # type: Dict
        self._dialogue_config = {}  # type: Dict

    @property
    def protobuf_snippets(self) -> Dict:
        """Get the protobuf snippets."""
        return self._protobuf_snippets

    @protobuf_snippets.setter
    def protobuf_snippets(self, protobuf_snippets: Dict):
        """Set the protobuf snippets."""
        self._protobuf_snippets = protobuf_snippets

    @property
    def dialogue_config(self) -> Dict:
        """Get the dialogue config."""
        return self._dialogue_config

    @dialogue_config.setter
    def dialogue_config(self, dialogue_config: Dict):
        """Set the dialogue config."""
        self._dialogue_config = dialogue_config

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        result: Dict[str, Any] = OrderedDict(
            {
                "name": self.name,
                "author": self.author,
                "version": self.version,
                "description": self.description,
                "license": self.license,
                "aea_version": self.aea_version,
                "speech_acts": {
                    key: speech_act.json
                    for key, speech_act in self.speech_acts.read_all()
                },
            }
        )
        return result

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        protocol_specification = ProtocolSpecification(
            name=cast(str, obj.get("name")),
            author=cast(str, obj.get("author")),
            version=cast(str, obj.get("version")),
            license_=cast(str, obj.get("license")),
            aea_version=cast(str, obj.get("aea_version", "")),
            description=cast(str, obj.get("description", "")),
        )
        for speech_act, speech_act_content in obj.get("speech_acts", {}).items():
            speech_act_content_config = SpeechActContentConfig.from_json(
                speech_act_content
            )
            protocol_specification.speech_acts.create(
                speech_act, speech_act_content_config
            )
        return protocol_specification


class ContractConfig(ComponentConfiguration):
    """Handle contract configuration."""

    default_configuration_filename = DEFAULT_CONTRACT_CONFIG_FILE
    package_type = PackageType.CONTRACT

    FIELDS_ALLOWED_TO_UPDATE: FrozenSet[str] = frozenset([])

    def __init__(
        self,
        name: SimpleIdOrStr,
        author: SimpleIdOrStr,
        version: str = "",
        license_: str = "",
        aea_version: str = "",
        fingerprint: Optional[Dict[str, str]] = None,
        fingerprint_ignore_patterns: Optional[Sequence[str]] = None,
        build_entrypoint: Optional[str] = None,
        build_directory: Optional[str] = None,
        dependencies: Optional[Dependencies] = None,
        description: str = "",
        contract_interface_paths: Optional[Dict[str, str]] = None,
        class_name: str = "",
    ):
        """Initialize a protocol configuration object."""
        super().__init__(
            name,
            author,
            version,
            license_,
            aea_version,
            fingerprint,
            fingerprint_ignore_patterns,
            build_entrypoint,
            build_directory,
            dependencies,
        )
        self.dependencies = dependencies if dependencies is not None else {}
        self.description = description
        self.contract_interface_paths = (
            contract_interface_paths if contract_interface_paths is not None else {}
        )
        self.class_name = class_name

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        result = OrderedDict(
            {
                "name": self.name,
                "author": self.author,
                "version": self.version,
                "type": self.component_type.value,
                "description": self.description,
                "license": self.license,
                "aea_version": self.aea_version,
                "fingerprint": self.fingerprint,
                "fingerprint_ignore_patterns": self.fingerprint_ignore_patterns,
                "class_name": self.class_name,
                "contract_interface_paths": self.contract_interface_paths,
                "dependencies": dependencies_to_json(self.dependencies),
            }
        )
        if self.build_entrypoint:
            result["build_entrypoint"] = self.build_entrypoint
        if self.build_directory:
            result["build_directory"] = self.build_directory
        return result

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        dependencies = cast(
            Dependencies, dependencies_from_json(obj.get("dependencies", {}))
        )
        return ContractConfig(
            name=cast(str, obj.get("name")),
            author=cast(str, obj.get("author")),
            version=cast(str, obj.get("version")),
            license_=cast(str, obj.get("license")),
            aea_version=cast(str, obj.get("aea_version", "")),
            fingerprint=cast(Dict[str, str], obj.get("fingerprint", {})),
            fingerprint_ignore_patterns=cast(
                Sequence[str], obj.get("fingerprint_ignore_patterns")
            ),
            build_entrypoint=cast(Optional[str], obj.get("build_entrypoint")),
            build_directory=cast(Optional[str], obj.get("build_directory")),
            dependencies=dependencies,
            description=cast(str, obj.get("description", "")),
            contract_interface_paths=cast(
                Dict[str, str], obj.get("contract_interface_paths", {})
            ),
            class_name=obj.get("class_name", ""),
        )


"""The following functions are called from aea.cli.utils."""


def _compute_fingerprint(
    package_directory: Path, ignore_patterns: Optional[Collection[str]] = None
) -> Dict[str, str]:
    ignore_patterns = ignore_patterns if ignore_patterns is not None else []
    ignore_patterns = set(ignore_patterns).union(DEFAULT_FINGERPRINT_IGNORE_PATTERNS)
    hasher = IPFSHashOnly()
    fingerprints = {}  # type: Dict[str, str]
    # find all valid files of the package
    all_files = [
        x
        for x in package_directory.glob("**/*")
        if x.is_file()
        and (
            x.match("*.py") or not any(x.match(pattern) for pattern in ignore_patterns)
        )
    ]

    for file in all_files:
        file_hash = hasher.get(str(file))
        key = str(file.relative_to(package_directory))
        enforce(key not in fingerprints, "Key in fingerprints!")  # nosec
        # use '/' as path separator
        normalized_path = Path(key).as_posix()
        fingerprints[normalized_path] = file_hash

    return fingerprints


def _compare_fingerprints(
    package_configuration: PackageConfiguration,
    package_directory: Path,
    is_vendor: bool,
    item_type: PackageType,
):
    """
    Check fingerprints of a package directory against the fingerprints declared in the configuration file.

    :param package_configuration: the package configuration object.
    :param package_directory: the directory of the package.
    :param is_vendor: whether the package is vendorized or not.
    :param item_type: the type of the item.
    :return: None
    :raises ValueError: if the fingerprints do not match.
    """
    expected_fingerprints = package_configuration.fingerprint
    ignore_patterns = package_configuration.fingerprint_ignore_patterns
    actual_fingerprints = _compute_fingerprint(package_directory, ignore_patterns)
    if expected_fingerprints != actual_fingerprints:
        if is_vendor:
            raise ValueError(
                (
                    "Fingerprints for package {} do not match:\nExpected: {}\nActual: {}\n"
                    "Vendorized projects should not be tampered with, please revert any changes to {} {}"
                ).format(
                    package_directory,
                    pprint.pformat(expected_fingerprints),
                    pprint.pformat(actual_fingerprints),
                    str(item_type),
                    package_configuration.public_id,
                )
            )
        raise ValueError(
            (
                "Fingerprints for package {} do not match:\nExpected: {}\nActual: {}\n"
                "Please fingerprint the package before continuing: 'aea fingerprint {} {}'"
            ).format(
                package_directory,
                pprint.pformat(expected_fingerprints),
                pprint.pformat(actual_fingerprints),
                str(item_type),
                package_configuration.public_id,
            )
        )


def _check_aea_version(package_configuration: PackageConfiguration):
    """Check the package configuration version against the version of the framework."""
    current_aea_version = Version(__aea_version__)
    version_specifiers = package_configuration.aea_version_specifiers
    if current_aea_version not in version_specifiers:
        raise ValueError(
            "The CLI version is {}, but package {} requires version {}".format(
                current_aea_version,
                package_configuration.public_id,
                package_configuration.aea_version_specifiers,
            )
        )


def _compare_public_ids(
    component_configuration: ComponentConfiguration, package_directory: Path
) -> None:
    """Compare the public ids in config and init file."""
    if component_configuration.package_type != PackageType.SKILL:
        return
    filename = "__init__.py"
    public_id_in_init = _get_public_id_from_file(
        component_configuration, package_directory, filename
    )
    if (
        public_id_in_init is not None
        and public_id_in_init != component_configuration.public_id
    ):
        raise ValueError(  # pragma: nocover
            f"The public id specified in {filename} for package {package_directory} does not match the one specific in {component_configuration.package_type.value}.yaml"
        )


def _get_public_id_from_file(
    component_configuration: ComponentConfiguration,
    package_directory: Path,
    filename: str,
) -> Optional[PublicId]:
    """
    Get the public id from an init if present.

    :param component_configuration: the component configuration.
    :param package_directory: the path to the package directory.
    :param filename: the file
    :return: the public id, if found.
    """
    path_to_file = Path(package_directory, filename)
    module = load_module(component_configuration.prefix_import_path, path_to_file)
    package_public_id = getattr(module, PACKAGE_PUBLIC_ID_VAR_NAME, None)
    return package_public_id
