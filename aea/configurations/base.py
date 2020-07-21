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
import pprint
import re
from abc import ABC, abstractmethod
from collections import OrderedDict
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Collection,
    Dict,
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
from packaging.specifiers import SpecifierSet
from packaging.version import Version

import semver

import aea
from aea.helpers.ipfs.base import IPFSHashOnly

T = TypeVar("T")
DEFAULT_VERSION = "0.1.0"
DEFAULT_AEA_CONFIG_FILE = "aea-config.yaml"
DEFAULT_SKILL_CONFIG_FILE = "skill.yaml"
DEFAULT_CONNECTION_CONFIG_FILE = "connection.yaml"
DEFAULT_CONTRACT_CONFIG_FILE = "contract.yaml"
DEFAULT_PROTOCOL_CONFIG_FILE = "protocol.yaml"
DEFAULT_README_FILE = "README.md"
DEFAULT_REGISTRY_PATH = str(Path("./", "packages"))
DEFAULT_LICENSE = "Apache-2.0"

DEFAULT_FINGERPRINT_IGNORE_PATTERNS = [
    ".DS_Store",
    "*__pycache__/*",
    "*.pyc",
    "aea-config.yaml",
    "protocol.yaml",
    "connection.yaml",
    "skill.yaml",
    "contract.yaml",
]

# TODO implement a proper class to represent this type.
Dependency = dict
"""
A dependency is a dictionary with the following (optional) keys:
    - version: a version specifier(s) (e.g. '==0.1.0').
    - index: the PyPI index where to download the package from (default: https://pypi.org)
    - git: the URL to the Git repository (e.g. https://github.com/fetchai/agents-aea.git)
    - ref: either the branch name, the tag, the commit number or a Git reference (default: 'master'.)
If the 'git' field is set, the 'version' field will be ignored.
These fields will be forwarded to the 'pip' command.
"""

Dependencies = Dict[str, Dependency]
"""
A dictionary from package name to dependency data structure (see above).
The package name must satisfy [the constraints on Python packages names](https://www.python.org/dev/peps/pep-0426/#name).

The main advantage of having a dictionary is that we implicitly filter out dependency duplicates.
We cannot have two items with the same package name since the keys of a YAML object form a set.
"""

PackageVersion = Type[semver.VersionInfo]
PackageVersionLike = Union[str, semver.VersionInfo]


class PackageType(Enum):
    """Package types."""

    AGENT = "agent"
    PROTOCOL = "protocol"
    CONNECTION = "connection"
    CONTRACT = "contract"
    SKILL = "skill"

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
    elif item_type == PackageType.PROTOCOL:
        return DEFAULT_PROTOCOL_CONFIG_FILE
    elif item_type == PackageType.CONNECTION:
        return DEFAULT_CONNECTION_CONFIG_FILE
    elif item_type == PackageType.SKILL:
        return DEFAULT_SKILL_CONFIG_FILE
    elif item_type == PackageType.CONTRACT:
        return DEFAULT_CONTRACT_CONFIG_FILE
    else:
        raise ValueError(
            "Item type not valid: {}".format(str(item_type))
        )  # pragma: no cover


class ComponentType(Enum):
    """Enum of component types supported."""

    PROTOCOL = "protocol"
    CONNECTION = "connection"
    SKILL = "skill"
    CONTRACT = "contract"

    def to_configuration_type(self) -> PackageType:
        """Get package type for component type."""
        return PackageType(self.value)

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
            assert key not in result, "Key in results!"
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
        else:
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
    """

    AUTHOR_REGEX = r"[a-zA-Z_][a-zA-Z0-9_]*"
    PACKAGE_NAME_REGEX = r"[a-zA-Z_][a-zA-Z0-9_]*"
    VERSION_REGEX = r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?"
    PUBLIC_ID_REGEX = r"^({})/({}):({})$".format(
        AUTHOR_REGEX, PACKAGE_NAME_REGEX, VERSION_REGEX
    )
    PUBLIC_ID_URI_REGEX = r"^({})/({})/({})$".format(
        AUTHOR_REGEX, PACKAGE_NAME_REGEX, VERSION_REGEX
    )

    def __init__(self, author: str, name: str, version: PackageVersionLike):
        """Initialize the public identifier."""
        self._author = author
        self._name = name
        self._version, self._version_info = self._process_version(version)

    @staticmethod
    def _process_version(version_like: PackageVersionLike) -> Tuple[Any, Any]:
        if isinstance(version_like, str):
            return version_like, semver.VersionInfo.parse(version_like)
        elif isinstance(version_like, semver.VersionInfo):
            return str(version_like), version_like
        else:
            raise ValueError("Version type not valid.")

    @property
    def author(self) -> str:
        """Get the author."""
        return self._author

    @property
    def name(self) -> str:
        """Get the name."""
        return self._name

    @property
    def version(self) -> str:
        """Get the version."""
        return self._version

    @property
    def version_info(self) -> PackageVersion:
        """Get the package version."""
        return self._version_info

    @property
    def latest(self) -> str:
        """Get the public id in `latest` form."""
        return "{author}/{name}:*".format(author=self.author, name=self.name)

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
        if not re.match(cls.PUBLIC_ID_REGEX, public_id_string):
            raise ValueError(
                "Input '{}' is not well formatted.".format(public_id_string)
            )
        else:
            username, package_name, version = re.findall(
                cls.PUBLIC_ID_REGEX, public_id_string
            )[0][:3]
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
        else:
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
            return self.version_info < other.version_info
        else:
            raise ValueError(
                "The public IDs {} and {} cannot be compared. Their author or name attributes are different.".format(
                    self, other
                )
            )


class PackageId:
    """A package identifier."""

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

    def __hash__(self):
        """Get the hash."""
        return hash((self.package_type, self.public_id))

    def __str__(self):
        """Get the string representation."""
        return "({package_type}, {public_id})".format(
            package_type=self.package_type.value, public_id=self.public_id,
        )

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

    @property
    def prefix_import_path(self) -> str:
        """Get the prefix import path for this component."""
        return "packages.{}.{}.{}".format(
            self.public_id.author, self.component_type.to_plural(), self.public_id.name
        )


ProtocolId = PublicId
ContractId = PublicId
ConnectionId = PublicId
SkillId = PublicId


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

    def __init__(
        self,
        name: str,
        author: str,
        version: str = "",
        license_: str = "",
        aea_version: str = "",
        fingerprint: Optional[Dict[str, str]] = None,
        fingerprint_ignore_patterns: Optional[Sequence[str]] = None,
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
        """
        super().__init__()
        assert (
            name is not None and author is not None
        ), "Name and author must be set on the configuration!"
        self.name = name
        self.author = author
        self.version = version if version != "" else DEFAULT_VERSION
        self.license = license_ if license_ != "" else DEFAULT_LICENSE
        self.fingerprint = fingerprint if fingerprint is not None else {}
        self.fingerprint_ignore_patterns = (
            fingerprint_ignore_patterns
            if fingerprint_ignore_patterns is not None
            else []
        )
        self.aea_version = aea_version if aea_version != "" else aea.__version__
        self._aea_version_specifiers = self._parse_aea_version_specifier(aea_version)

        self._directory = None  # type: Optional[Path]

    @property
    def directory(self) -> Optional[Path]:
        """Get the path to the configuration file associated to this file, if any."""
        return self._directory

    @directory.setter
    def directory(self, directory: Path) -> None:
        """Set directory if not already set."""
        assert self._directory is None, "Directory already set"
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


class ComponentConfiguration(PackageConfiguration, ABC):
    """Class to represent an agent component configuration."""

    def __init__(
        self,
        name: str,
        author: str,
        version: str = "",
        license_: str = "",
        aea_version: str = "",
        fingerprint: Optional[Dict[str, str]] = None,
        fingerprint_ignore_patterns: Optional[Sequence[str]] = None,
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
        )
        self._pypi_dependencies = dependencies if dependencies is not None else {}

    @property
    def pypi_dependencies(self) -> Dependencies:
        """Get PyPI dependencies."""
        return self._pypi_dependencies

    @property
    @abstractmethod
    def component_type(self) -> ComponentType:
        """Get the component type."""

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

    @staticmethod
    def load(
        component_type: ComponentType,
        directory: Path,
        skip_consistency_check: bool = False,
    ) -> "ComponentConfiguration":
        """
        Load configuration and check that it is consistent against the directory.

        :param component_type: the component type.
        :param directory: the root of the package
        :param skip_consistency_check: if True, the consistency check are skipped.
        :return: the configuration object.
        """
        configuration_object = ComponentConfiguration._load_configuration_object(
            component_type, directory
        )
        if not skip_consistency_check:
            configuration_object._check_configuration_consistency(  # pylint: disable=protected-access
                directory
            )
        return configuration_object

    @staticmethod
    def _load_configuration_object(
        component_type: ComponentType, directory: Path
    ) -> "ComponentConfiguration":
        """
        Load the configuration object, without consistency checks.

        :param component_type: the component type.
        :param directory: the directory of the configuration.
        :return: the configuration object.
        :raises FileNotFoundError: if the configuration file is not found.
        """
        from aea.configurations.loader import (  # pylint: disable=import-outside-toplevel
            ConfigLoader,
        )

        configuration_loader = ConfigLoader.from_configuration_type(
            component_type.to_configuration_type()
        )
        configuration_filename = (
            configuration_loader.configuration_class.default_configuration_filename
        )
        configuration_filepath = directory / configuration_filename
        try:
            fp = open(configuration_filepath)
            configuration_object = configuration_loader.load(fp)
        except FileNotFoundError:
            raise FileNotFoundError(
                "{} configuration not found: {}".format(
                    component_type.value.capitalize(), configuration_filepath
                )
            )
        return configuration_object

    def _check_configuration_consistency(self, directory: Path):
        """Check that the configuration file is consistent against a directory."""
        self.check_fingerprint(directory)
        self.check_aea_version()

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


class ConnectionConfig(ComponentConfiguration):
    """Handle connection configuration."""

    default_configuration_filename = DEFAULT_CONNECTION_CONFIG_FILE

    def __init__(
        self,
        name: str = "",
        author: str = "",
        version: str = "",
        license_: str = "",
        aea_version: str = "",
        fingerprint: Optional[Dict[str, str]] = None,
        fingerprint_ignore_patterns: Optional[Sequence[str]] = None,
        class_name: str = "",
        protocols: Optional[Set[PublicId]] = None,
        restricted_to_protocols: Optional[Set[PublicId]] = None,
        excluded_protocols: Optional[Set[PublicId]] = None,
        dependencies: Optional[Dependencies] = None,
        description: str = "",
        connection_id: Optional[PublicId] = None,
        **config,
    ):
        """Initialize a connection configuration object."""
        if connection_id is None:
            assert name != "", "Name or connection_id must be set."
            assert author != "", "Author or connection_id must be set."
            assert version != "", "Version or connection_id must be set."
        else:
            assert name in (
                "",
                connection_id.name,
            ), "Non matching name in ConnectionConfig name and public id."
            name = connection_id.name
            assert author in (
                "",
                connection_id.author,
            ), "Non matching author in ConnectionConfig author and public id."
            author = connection_id.author
            assert version in (
                "",
                connection_id.version,
            ), "Non matching version in ConnectionConfig version and public id."
            version = connection_id.version
        super().__init__(
            name,
            author,
            version,
            license_,
            aea_version,
            fingerprint,
            fingerprint_ignore_patterns,
            dependencies,
        )
        self.class_name = class_name
        self.protocols = protocols if protocols is not None else []
        self.restricted_to_protocols = (
            restricted_to_protocols if restricted_to_protocols is not None else set()
        )
        self.excluded_protocols = (
            excluded_protocols if excluded_protocols is not None else set()
        )
        self.dependencies = dependencies if dependencies is not None else {}
        self.description = description
        self.config = config

    @property
    def component_type(self) -> ComponentType:
        """Get the component type."""
        return ComponentType.CONNECTION

    @property
    def package_dependencies(self) -> Set[ComponentId]:
        """Get the connection dependencies."""
        return set(
            ComponentId(ComponentType.PROTOCOL, protocol_id)
            for protocol_id in self.protocols
        )

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        return OrderedDict(
            {
                "name": self.name,
                "author": self.author,
                "version": self.version,
                "description": self.description,
                "license": self.license,
                "aea_version": self.aea_version,
                "fingerprint": self.fingerprint,
                "fingerprint_ignore_patterns": self.fingerprint_ignore_patterns,
                "protocols": sorted(map(str, self.protocols)),
                "class_name": self.class_name,
                "config": self.config,
                "excluded_protocols": sorted(map(str, self.excluded_protocols)),
                "restricted_to_protocols": sorted(
                    map(str, self.restricted_to_protocols)
                ),
                "dependencies": self.dependencies,
            }
        )

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        restricted_to_protocols = obj.get("restricted_to_protocols", set())
        restricted_to_protocols = {
            PublicId.from_str(id_) for id_ in restricted_to_protocols
        }
        excluded_protocols = obj.get("excluded_protocols", set())
        excluded_protocols = {PublicId.from_str(id_) for id_ in excluded_protocols}
        dependencies = obj.get("dependencies", {})
        protocols = {PublicId.from_str(id_) for id_ in obj.get("protocols", set())}
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
            class_name=cast(str, obj.get("class_name")),
            protocols=cast(Set[PublicId], protocols),
            restricted_to_protocols=cast(Set[PublicId], restricted_to_protocols),
            excluded_protocols=cast(Set[PublicId], excluded_protocols),
            dependencies=cast(Dependencies, dependencies),
            description=cast(str, obj.get("description", "")),
            **cast(dict, obj.get("config")),
        )


class ProtocolConfig(ComponentConfiguration):
    """Handle protocol configuration."""

    default_configuration_filename = DEFAULT_PROTOCOL_CONFIG_FILE

    def __init__(
        self,
        name: str,
        author: str,
        version: str = "",
        license_: str = "",
        fingerprint: Optional[Dict[str, str]] = None,
        fingerprint_ignore_patterns: Optional[Sequence[str]] = None,
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
            dependencies,
        )
        self.dependencies = dependencies if dependencies is not None else {}
        self.description = description

    @property
    def component_type(self) -> ComponentType:
        """Get the component type."""
        return ComponentType.PROTOCOL

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        return OrderedDict(
            {
                "name": self.name,
                "author": self.author,
                "version": self.version,
                "description": self.description,
                "license": self.license,
                "aea_version": self.aea_version,
                "fingerprint": self.fingerprint,
                "fingerprint_ignore_patterns": self.fingerprint_ignore_patterns,
                "dependencies": self.dependencies,
            }
        )

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        dependencies = cast(Dependencies, obj.get("dependencies", {}))
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

    def __init__(
        self,
        name: str,
        author: str,
        version: str = "",
        license_: str = "",
        aea_version: str = "",
        fingerprint: Optional[Dict[str, str]] = None,
        fingerprint_ignore_patterns: Optional[Sequence[str]] = None,
        protocols: List[PublicId] = None,
        contracts: List[PublicId] = None,
        skills: List[PublicId] = None,
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
            dependencies,
        )
        self.protocols: List[PublicId] = (protocols if protocols is not None else [])
        self.contracts: List[PublicId] = (contracts if contracts is not None else [])
        self.skills: List[PublicId] = (skills if skills is not None else [])
        self.dependencies = dependencies if dependencies is not None else {}
        self.description = description
        self.handlers = CRUDCollection[SkillComponentConfiguration]()
        self.behaviours = CRUDCollection[SkillComponentConfiguration]()
        self.models = CRUDCollection[SkillComponentConfiguration]()

        self.is_abstract = is_abstract

    @property
    def component_type(self) -> ComponentType:
        """Get the component type."""
        return ComponentType.SKILL

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
                "description": self.description,
                "license": self.license,
                "aea_version": self.aea_version,
                "fingerprint": self.fingerprint,
                "fingerprint_ignore_patterns": self.fingerprint_ignore_patterns,
                "contracts": sorted(map(str, self.contracts)),
                "protocols": sorted(map(str, self.protocols)),
                "skills": sorted(map(str, self.skills)),
                "behaviours": {key: b.json for key, b in self.behaviours.read_all()},
                "handlers": {key: h.json for key, h in self.handlers.read_all()},
                "models": {key: m.json for key, m in self.models.read_all()},
                "dependencies": self.dependencies,
                "is_abstract": self.is_abstract,
            }
        )
        if result["is_abstract"] is False:
            result.pop("is_abstract")

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
        protocols = cast(
            List[PublicId],
            [PublicId.from_str(id_) for id_ in obj.get("protocols", [])],
        )
        contracts = cast(
            List[PublicId],
            [PublicId.from_str(id_) for id_ in obj.get("contracts", [])],
        )
        skills = cast(
            List[PublicId], [PublicId.from_str(id_) for id_ in obj.get("skills", [])],
        )
        dependencies = cast(Dependencies, obj.get("dependencies", {}))
        description = cast(str, obj.get("description", ""))
        skill_config = SkillConfig(
            name=name,
            author=author,
            version=version,
            license_=license_,
            aea_version=aea_version_specifiers,
            fingerprint=fingerprint,
            fingerprint_ignore_patterns=fingerprint_ignore_patterns,
            protocols=protocols,
            contracts=contracts,
            skills=skills,
            dependencies=dependencies,
            description=description,
            is_abstract=obj.get("is_abstract", False),
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


class AgentConfig(PackageConfiguration):
    """Class to represent the agent configuration file."""

    default_configuration_filename = DEFAULT_AEA_CONFIG_FILE

    def __init__(
        self,
        agent_name: str,
        author: str,
        version: str = "",
        license_: str = "",
        aea_version: str = "",
        fingerprint: Optional[Dict[str, str]] = None,
        fingerprint_ignore_patterns: Optional[Sequence[str]] = None,
        registry_path: str = DEFAULT_REGISTRY_PATH,
        description: str = "",
        logging_config: Optional[Dict] = None,
        timeout: Optional[float] = None,
        execution_timeout: Optional[float] = None,
        max_reactions: Optional[int] = None,
        decision_maker_handler: Optional[Dict] = None,
        skill_exception_policy: Optional[str] = None,
        default_routing: Optional[Dict] = None,
        loop_mode: Optional[str] = None,
        runtime_mode: Optional[str] = None,
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
        )
        self.agent_name = agent_name
        self.registry_path = registry_path
        self.description = description
        self.private_key_paths = CRUDCollection[str]()
        self.connection_private_key_paths = CRUDCollection[str]()

        self.logging_config = logging_config if logging_config is not None else {}
        self._default_ledger = None  # type: Optional[str]
        self._default_connection = None  # type: Optional[PublicId]
        self.connections = set()  # type: Set[PublicId]
        self.contracts = set()  # type: Set[PublicId]
        self.protocols = set()  # type: Set[PublicId]
        self.skills = set()  # type: Set[PublicId]

        if self.logging_config == {}:
            self.logging_config["version"] = 1
            self.logging_config["disable_existing_loggers"] = False

        self.timeout: Optional[float] = timeout
        self.execution_timeout: Optional[float] = execution_timeout
        self.max_reactions: Optional[int] = max_reactions
        self.skill_exception_policy: Optional[str] = skill_exception_policy

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

    @property
    def default_connection(self) -> str:
        """Get the default connection."""
        assert self._default_connection is not None, "Default connection not set yet."
        return str(self._default_connection)

    @default_connection.setter
    def default_connection(self, connection_id: Optional[Union[str, PublicId]]):
        """
        Set the default connection.

        :param connection_id: the name of the default connection.
        :return: None
        """
        if connection_id is None:
            self._default_connection = None
        elif isinstance(connection_id, str):
            self._default_connection = PublicId.from_str(connection_id)
        else:
            self._default_connection = connection_id

    @property
    def default_ledger(self) -> str:
        """Get the default ledger."""
        assert self._default_ledger is not None, "Default ledger not set yet."
        return self._default_ledger

    @default_ledger.setter
    def default_ledger(self, ledger_id: str):
        """
        Set the default ledger.

        :param ledger_id: the id of the default ledger.
        :return: None
        """
        self._default_ledger = ledger_id

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        config = OrderedDict(
            {
                "agent_name": self.agent_name,
                "author": self.author,
                "version": self.version,
                "description": self.description,
                "license": self.license,
                "aea_version": self.aea_version,
                "fingerprint": self.fingerprint,
                "fingerprint_ignore_patterns": self.fingerprint_ignore_patterns,
                "connections": sorted(map(str, self.connections)),
                "contracts": sorted(map(str, self.contracts)),
                "protocols": sorted(map(str, self.protocols)),
                "skills": sorted(map(str, self.skills)),
                "default_connection": self.default_connection,
                "default_ledger": self.default_ledger,
                "logging_config": self.logging_config,
                "private_key_paths": self.private_key_paths_dict,
                "registry_path": self.registry_path,
            }
        )  # type: Dict[str, Any]

        if len(self.connection_private_key_paths_dict) > 0:
            config[
                "connection_private_key_paths"
            ] = self.connection_private_key_paths_dict

        if self.timeout is not None:
            config["timeout"] = self.timeout
        if self.execution_timeout is not None:
            config["execution_timeout"] = self.execution_timeout
        if self.max_reactions is not None:
            config["max_reactions"] = self.max_reactions
        if self.decision_maker_handler != {}:
            config["decision_maker_handler"] = self.decision_maker_handler
        if self.skill_exception_policy is not None:
            config["skill_exception_policy"] = self.skill_exception_policy
        if self.default_routing != {}:
            config["default_routing"] = {
                str(key): str(value) for key, value in self.default_routing.items()
            }
        if self.loop_mode is not None:
            config["loop_mode"] = self.loop_mode

        if self.runtime_mode is not None:
            config["runtime_mode"] = self.runtime_mode

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
            logging_config=cast(Dict, obj.get("logging_config", {})),
            timeout=cast(float, obj.get("timeout")),
            execution_timeout=cast(float, obj.get("execution_timeout")),
            max_reactions=cast(int, obj.get("max_reactions")),
            decision_maker_handler=cast(Dict, obj.get("decision_maker_handler", {})),
            skill_exception_policy=cast(str, obj.get("skill_exception_policy")),
            default_routing=cast(Dict, obj.get("default_routing", {})),
            loop_mode=cast(str, obj.get("loop_mode")),
            runtime_mode=cast(str, obj.get("runtime_mode")),
        )

        for crypto_id, path in obj.get("private_key_paths", {}).items():
            agent_config.private_key_paths.create(crypto_id, path)

        for crypto_id, path in obj.get("connection_private_key_paths", {}).items():
            agent_config.connection_private_key_paths.create(crypto_id, path)

        # parse connection public ids
        connections = set(
            map(
                lambda x: PublicId.from_str(x),  # pylint: disable=unnecessary-lambda
                obj.get("connections", []),
            )
        )
        agent_config.connections = cast(Set[PublicId], connections)

        # parse contracts public ids
        contracts = set(
            map(
                lambda x: PublicId.from_str(x),  # pylint: disable=unnecessary-lambda
                obj.get("contracts", []),
            )
        )
        agent_config.contracts = cast(Set[PublicId], contracts)

        # parse protocol public ids
        protocols = set(
            map(
                lambda x: PublicId.from_str(x),  # pylint: disable=unnecessary-lambda
                obj.get("protocols", []),
            )
        )
        agent_config.protocols = cast(Set[PublicId], protocols)

        # parse skills public ids
        skills = set(
            map(
                lambda x: PublicId.from_str(x),  # pylint: disable=unnecessary-lambda
                obj.get("skills", []),
            )
        )
        agent_config.skills = cast(Set[PublicId], skills)

        # set default connection
        default_connection_name = obj.get("default_connection", None)
        agent_config.default_connection = default_connection_name
        default_ledger_id = obj.get("default_ledger", None)
        agent_config.default_ledger = default_ledger_id

        return agent_config


class SpeechActContentConfig(Configuration):
    """Handle a speech_act content configuration."""

    def __init__(self, **args):
        """Initialize a speech_act content configuration."""
        super().__init__()
        self.args = args  # type: Dict[str, str]
        self._check_consistency()

    def _check_consistency(self):
        """Check consistency of the args."""
        for content_name, content_type in self.args.items():
            if not isinstance(content_name, str) or not isinstance(content_type, str):
                raise ProtocolSpecificationParseError(
                    "Contents' names and types must be string."
                )
            # Check each content definition key/value (i.e. content name/type) is not empty
            if content_name == "" or content_type == "":
                raise ProtocolSpecificationParseError(
                    "Contents' names and types cannot be empty."
                )

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
        name: str,
        author: str,
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
        return OrderedDict(
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
        protocol_specification._check_consistency()  # pylint: disable=protected-access
        return protocol_specification

    def _check_consistency(self):
        """Validate the correctness of the speech_acts."""
        if len(self.speech_acts.read_all()) == 0:
            raise ProtocolSpecificationParseError(
                "There should be at least one performative defined in the speech_acts."
            )
        content_dict = {}
        for performative, speech_act_content_config in self.speech_acts.read_all():
            if not isinstance(performative, str):
                raise ProtocolSpecificationParseError(
                    "A 'performative' is not specified as a string."
                )
            if performative == "":
                raise ProtocolSpecificationParseError(
                    "A 'performative' cannot be an empty string."
                )
            for content_name, content_type in speech_act_content_config.args.items():
                if content_name in content_dict.keys():
                    if content_type != content_dict[content_name]:  # pragma: no cover
                        raise ProtocolSpecificationParseError(
                            "The content '{}' appears more than once with different types in speech_acts.".format(
                                content_name
                            )
                        )
                content_dict[content_name] = content_type


class ContractConfig(ComponentConfiguration):
    """Handle contract configuration."""

    default_configuration_filename = DEFAULT_CONTRACT_CONFIG_FILE

    def __init__(
        self,
        name: str,
        author: str,
        version: str = "",
        license_: str = "",
        aea_version: str = "",
        fingerprint: Optional[Dict[str, str]] = None,
        fingerprint_ignore_patterns: Optional[Sequence[str]] = None,
        dependencies: Optional[Dependencies] = None,
        description: str = "",
        path_to_contract_interface: str = "",
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
            dependencies,
        )
        self.dependencies = dependencies if dependencies is not None else {}
        self.description = description
        self.path_to_contract_interface = path_to_contract_interface
        self.class_name = class_name

    @property
    def component_type(self) -> ComponentType:
        """Get the component type."""
        return ComponentType.CONTRACT

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        return OrderedDict(
            {
                "name": self.name,
                "author": self.author,
                "version": self.version,
                "description": self.description,
                "license": self.license,
                "aea_version": self.aea_version,
                "fingerprint": self.fingerprint,
                "fingerprint_ignore_patterns": self.fingerprint_ignore_patterns,
                "class_name": self.class_name,
                "path_to_contract_interface": self.path_to_contract_interface,
                "dependencies": self.dependencies,
            }
        )

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        dependencies = cast(Dependencies, obj.get("dependencies", {}))
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
            dependencies=dependencies,
            description=cast(str, obj.get("description", "")),
            path_to_contract_interface=cast(
                str, obj.get("path_to_contract_interface", "")
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
        assert key not in fingerprints, "Key in fingerprints!"  # nosec
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
        else:
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
    current_aea_version = Version(aea.__version__)
    version_specifiers = package_configuration.aea_version_specifiers
    if current_aea_version not in version_specifiers:
        raise ValueError(
            "The CLI version is {}, but package {} requires version {}".format(
                current_aea_version,
                package_configuration.public_id,
                package_configuration.aea_version_specifiers,
            )
        )
