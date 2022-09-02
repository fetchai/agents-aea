# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
from abc import ABC
from collections import OrderedDict
from copy import copy, deepcopy
from operator import attrgetter
from pathlib import Path
from typing import (
    Any,
    Collection,
    Dict,
    FrozenSet,
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

from aea.__version__ import __version__ as __aea_version__
from aea.configurations.constants import (
    CONNECTIONS,
    CONTRACTS,
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_CONNECTION_CONFIG_FILE,
    DEFAULT_CONTRACT_CONFIG_FILE,
    DEFAULT_FINGERPRINT_IGNORE_PATTERNS,
    DEFAULT_LICENSE,
    DEFAULT_LOGGING_CONFIG,
    DEFAULT_PROTOCOL_CONFIG_FILE,
    DEFAULT_SERVICE_CONFIG_FILE,
    DEFAULT_SKILL_CONFIG_FILE,
    DEFAULT_VERSION,
    PACKAGE_PUBLIC_ID_VAR_NAME,
    PROTOCOLS,
    SKILLS,
)
from aea.configurations.data_types import (
    CRUDCollection,
    ComponentId,
    ComponentType,
    Dependencies,
    Dependency,
    JSONSerializable,
    PackageId,
    PackageType,
    PackageVersion,
    PublicId,
)
from aea.configurations.validation import ConfigValidator, validate_data_with_pattern
from aea.exceptions import enforce
from aea.helpers.base import (
    CertRequest,
    SimpleId,
    SimpleIdOrStr,
    load_module,
    perform_dict_override,
    recursive_update,
)
from aea.helpers.ipfs.base import IPFSHashOnly


# for tests
_ = [PackageId, PackageVersion]


T = TypeVar("T")


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
    if item_type == PackageType.SERVICE:
        return DEFAULT_SERVICE_CONFIG_FILE
    raise ValueError(  # pragma: no cover
        "Item type not valid: {}".format(str(item_type))
    )


class ProtocolSpecificationParseError(Exception):
    """Exception for parsing a protocol specification file."""


class Configuration(JSONSerializable, ABC):
    """Configuration class."""

    __slots__ = ("_key_order",)

    def __init__(self) -> None:
        """Initialize a configuration object."""
        # a list of keys that remembers the key order of the configuration file.
        # this is set by the configuration loader.
        self._key_order: List[str] = []

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

    __slots__ = (
        "_name",
        "_author",
        "version",
        "license",
        "fingerprint",
        "fingerprint_ignore_patterns",
        "build_entrypoint",
        "_aea_version",
        "_aea_version_specifiers",
        "_directory",
    )

    default_configuration_filename: str
    package_type: PackageType

    FIELDS_ALLOWED_TO_UPDATE: FrozenSet[str] = frozenset(["build_directory"])
    FIELDS_WITH_NESTED_FIELDS: FrozenSet[str] = frozenset()
    NESTED_FIELDS_ALLOWED_TO_UPDATE: FrozenSet[str] = frozenset()

    schema: str
    CHECK_EXCLUDES: List[Tuple[str]] = []

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
    ) -> None:
        """
        Initialize a package configuration.

        :param name: the name of the package.
        :param author: the author of the package.
        :param version: the version of the package (SemVer format).
        :param license_: the license.
        :param aea_version: either a fixed version, or a set of specifiers describing the AEA versions allowed. (default: empty string - no constraint). The fixed version is interpreted with the specifier '=='.
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
        self._aea_version = aea_version if aea_version != "" else __aea_version__
        self._aea_version_specifiers = self.parse_aea_version_specifier(aea_version)

        self._directory = None  # type: Optional[Path]

    @property
    def name(self) -> str:
        """Get the name."""
        return str(self._name)

    @name.setter
    def name(self, value: SimpleIdOrStr) -> None:
        """Set the name."""
        self._name = SimpleId(value)

    @property
    def author(self) -> str:
        """Get the author."""
        return str(self._author)

    @author.setter
    def author(self, value: SimpleIdOrStr) -> None:
        """Set the author."""
        self._author = SimpleId(value)

    @property
    def aea_version(self) -> str:
        """Get the 'aea_version' attribute."""
        return self._aea_version

    @aea_version.setter
    def aea_version(self, new_aea_version: str) -> None:
        """Set the 'aea_version' attribute."""
        self._aea_version_specifiers = self.parse_aea_version_specifier(new_aea_version)
        self._aea_version = new_aea_version

    def check_aea_version(self) -> None:
        """
        Check that the AEA version matches the specifier set.

        :raises ValueError if the version of the aea framework falls within a specifier.
        """
        _check_aea_version(self)

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

    @property
    def package_id(self) -> PackageId:
        """Get package id."""
        return PackageId(package_type=self.package_type, public_id=self.public_id)

    @staticmethod
    def parse_aea_version_specifier(aea_version_specifiers: str) -> SpecifierSet:
        """
        Parse an 'aea_version' field.

        If 'aea_version' is a version, then output the specifier set "==${version}"
        Else, interpret it as specifier set.

        :param aea_version_specifiers: the AEA version, or a specifier set.
        :return: A specifier set object.
        """
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

    def update(self, data: Dict, env_vars_friendly: bool = False) -> None:
        """
        Update configuration with other data.

        :param data: the data to replace.
        :param env_vars_friendly: whether or not it is env vars friendly.
        """
        if not data:  # do nothing if nothing to update
            return

        self.check_overrides_valid(data, env_vars_friendly=env_vars_friendly)
        self._create_or_update_from_json(
            obj=self.make_resulting_config_data(data), instance=self
        )

    @classmethod
    def validate_config_data(
        cls, json_data: Dict, env_vars_friendly: bool = False
    ) -> None:
        """Perform config validation."""
        ConfigValidator(cls.schema, env_vars_friendly=env_vars_friendly).validate(
            json_data
        )

    @classmethod
    def from_json(cls, obj: Dict) -> "PackageConfiguration":
        """Initialize from a JSON object."""
        return cls._create_or_update_from_json(obj=obj, instance=None)

    @classmethod
    def _create_or_update_from_json(
        cls, obj: Dict, instance: Any = None
    ) -> "PackageConfiguration":
        """Create new config object or updates existing one from json data."""
        raise NotImplementedError  # pragma: nocover

    def make_resulting_config_data(self, overrides: Dict) -> Dict:
        """
        Make config data with overrides applied.

        Does not update config, just creates json representation.

        :param overrides: the overrides
        :return: config with overrides applied
        """
        current_config = self.json
        recursive_update(current_config, overrides, allow_new_values=True)
        return current_config

    def check_overrides_valid(
        self, overrides: Dict, env_vars_friendly: bool = False
    ) -> None:
        """Check overrides is correct, return list of errors if present."""
        # check for permitted overrides
        self._check_overrides_corresponds_to_overridable(
            overrides, env_vars_friendly=env_vars_friendly
        )
        # check resulting config with applied overrides passes validation

        result_config = self.make_resulting_config_data(overrides)
        self.validate_config_data(result_config, env_vars_friendly=env_vars_friendly)

    def _check_overrides_corresponds_to_overridable(
        self, overrides: Dict, env_vars_friendly: bool = False
    ) -> None:
        """Check overrides is correct, return list of errors if present."""
        errors_list = validate_data_with_pattern(
            overrides,
            self.get_overridable(),
            excludes=self.CHECK_EXCLUDES,
            skip_env_vars=env_vars_friendly,
        )
        if errors_list:
            raise ValueError(errors_list[0])

    def get_overridable(self) -> dict:
        """Get dictionary of values that can be updated for this config."""
        return {k: self.json.get(k) for k in self.FIELDS_ALLOWED_TO_UPDATE}

    @classmethod
    def _apply_params_to_instance(
        cls, params: dict, instance: Optional["PackageConfiguration"]
    ) -> "PackageConfiguration":
        """Constructs or update instance with params provided."""
        directory = (
            instance.directory if instance and hasattr(instance, "directory") else None
        )

        if instance is None:
            instance = cls(**params)
        else:
            instance.__init__(**params)  # type: ignore

        if directory and not instance.directory:
            instance.directory = directory

        return instance


class ComponentConfiguration(PackageConfiguration, ABC):
    """Class to represent an agent component configuration."""

    package_type: PackageType

    __slots__ = ("pypi_dependencies", "_build_directory")

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
    ) -> None:
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
        self.pypi_dependencies: Dependencies = (
            dependencies if dependencies is not None else {}
        )
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

    def _check_configuration_consistency(self, directory: Path) -> None:
        """Check that the configuration file is consistent against a directory."""
        self.check_fingerprint(directory)
        self.check_aea_version()
        self.check_public_id_consistency(directory)

    def check_fingerprint(self, directory: Path) -> None:
        """
        Check that the fingerprint are correct against a directory path.

        :param directory: the directory path.
        :raises ValueError: if
            - the argument is not a valid package directory
            - the fingerprints do not match.
        """
        if not directory.exists() or not directory.is_dir():
            raise ValueError("Directory {} is not valid.".format(directory))
        _compare_fingerprints(
            self, directory, False, self.component_type.to_package_type()
        )

    def check_public_id_consistency(self, directory: Path) -> None:
        """
        Check that the public ids in the init file match the config.

        :param directory: the directory path.
        :raises ValueError: if
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
    schema = "connection-config_schema.json"

    FIELDS_ALLOWED_TO_UPDATE: FrozenSet[str] = frozenset(
        ["config", "cert_requests", "is_abstract", "build_directory"]
    )
    FIELDS_WITH_NESTED_FIELDS: FrozenSet[str] = frozenset(["config"])

    __slots__ = (
        "class_name",
        "protocols",
        "connections",
        "restricted_to_protocols",
        "excluded_protocols",
        "dependencies",
        "description",
        "config",
        "is_abstract",
        "cert_requests",
    )

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
        cert_requests: Optional[List[CertRequest]] = None,
        **config: Any,
    ) -> None:
        """Initialize a connection configuration object."""
        if connection_id is None:
            enforce(name != "", "Name or connection_id must be set.")
            enforce(author != "", "Author or connection_id must be set.")
            enforce(version != "", "Version or connection_id must be set.")
        else:
            enforce(
                name
                in (
                    "",
                    connection_id.name,
                ),
                "Non matching name in ConnectionConfig name and public id.",
            )
            name = connection_id.name
            enforce(
                author
                in (
                    "",
                    connection_id.author,
                ),
                "Non matching author in ConnectionConfig author and public id.",
            )
            author = connection_id.author
            enforce(
                version
                in (
                    "",
                    connection_id.version,
                ),
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
        self.cert_requests = cert_requests

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

        if self.cert_requests is not None:
            result["cert_requests"] = list(map(attrgetter("json"), self.cert_requests))
        if self.build_entrypoint:
            result["build_entrypoint"] = self.build_entrypoint
        if self.build_directory:
            result["build_directory"] = self.build_directory
        return result

    @classmethod
    def _create_or_update_from_json(
        cls, obj: Dict, instance: Optional["ConnectionConfig"] = None
    ) -> "ConnectionConfig":
        """Create new config object or updates existing one from json data."""
        obj = {**(instance.json if instance else {}), **copy(obj)}
        restricted_to_protocols = obj.get("restricted_to_protocols", set())
        restricted_to_protocols = {
            PublicId.from_str(id_) for id_ in restricted_to_protocols
        }
        excluded_protocols = obj.get("excluded_protocols", set())
        excluded_protocols = {PublicId.from_str(id_) for id_ in excluded_protocols}
        dependencies = dependencies_from_json(obj.get("dependencies", {}))
        protocols = {PublicId.from_str(id_) for id_ in obj.get(PROTOCOLS, set())}
        connections = {PublicId.from_str(id_) for id_ in obj.get(CONNECTIONS, set())}
        cert_requests = (
            [
                # notice: yaml.load resolves datetime strings to datetime.datetime objects
                CertRequest.from_json(cert_request_json)
                for cert_request_json in obj["cert_requests"]
            ]
            if "cert_requests" in obj
            else None
        )

        params = dict(
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
            cert_requests=cert_requests,
            **cast(dict, obj.get("config", {})),
        )

        instance = cast(
            ConnectionConfig, cls._apply_params_to_instance(params, instance)
        )

        return instance


class ProtocolConfig(ComponentConfiguration):
    """Handle protocol configuration."""

    default_configuration_filename = DEFAULT_PROTOCOL_CONFIG_FILE
    package_type = PackageType.PROTOCOL
    schema = "protocol-config_schema.json"
    FIELDS_ALLOWED_TO_UPDATE: FrozenSet[str] = frozenset()

    __slots__ = (
        "dependencies",
        "description",
        "protocol_specification_id",
    )

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
        protocol_specification_id: Optional[str] = None,
    ) -> None:
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
        if protocol_specification_id is None:
            raise ValueError(  # pragma: nocover
                "protocol_specification_id not provided!"
            )
        self.protocol_specification_id = PublicId.from_str(
            str(protocol_specification_id)
        )

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        result = OrderedDict(
            {
                "name": self.name,
                "author": self.author,
                "version": self.version,
                "protocol_specification_id": str(self.protocol_specification_id),
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
    def _create_or_update_from_json(
        cls, obj: Dict, instance: Optional["ProtocolConfig"] = None
    ) -> "ProtocolConfig":
        """Initialize from a JSON object."""
        obj = {**(instance.json if instance else {}), **copy(obj)}
        dependencies = dependencies_from_json(obj.get("dependencies", {}))
        params = dict(
            name=cast(str, obj.get("name")),
            author=cast(str, obj.get("author")),
            protocol_specification_id=cast(str, obj.get("protocol_specification_id")),
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
        instance = cast(ProtocolConfig, cls._apply_params_to_instance(params, instance))

        return instance


class SkillComponentConfiguration:
    """This class represent a skill component configuration."""

    __slots__ = ("class_name", "file_path", "args")

    def __init__(
        self, class_name: str, file_path: Optional[str] = None, **args: Any
    ) -> None:
        """
        Initialize a skill component configuration.

        :param class_name: the class name of the component.
        :param file_path: the file path.
        :param args: keyword arguments.
        """
        self.class_name = class_name
        self.file_path: Optional[Path] = Path(file_path) if file_path else None
        self.args = args

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        result = {"class_name": self.class_name, "args": self.args}
        if self.file_path is not None:
            result["file_path"] = str(self.file_path.as_posix())
        return result

    @classmethod
    def from_json(cls, obj: Dict) -> "SkillComponentConfiguration":
        """Initialize from a JSON object."""
        return cls._create_or_update_from_json(obj, instance=None)

    @classmethod
    def _create_or_update_from_json(
        cls, obj: Dict, instance: Optional["SkillComponentConfiguration"] = None
    ) -> "SkillComponentConfiguration":
        """Initialize from a JSON object."""
        obj = {**(instance.json if instance else {}), **copy(obj)}
        class_name = cast(str, obj.get("class_name"))
        file_path = cast(Optional[str], obj.get("file_path"))
        params = dict(class_name=class_name, file_path=file_path, **obj.get("args", {}))

        instance = cast(
            SkillComponentConfiguration, cls._apply_params_to_instance(params, instance)
        )

        return instance

    @classmethod
    def _apply_params_to_instance(
        cls, params: dict, instance: Optional["SkillComponentConfiguration"]
    ) -> "SkillComponentConfiguration":
        """Constructs or update instance with params provided."""
        if instance is None:
            instance = cls(**params)
        else:  # pragma: nocover
            instance.__init__(**params)  # type: ignore
        return instance


class SkillConfig(ComponentConfiguration):
    """Class to represent a skill configuration file."""

    default_configuration_filename = DEFAULT_SKILL_CONFIG_FILE
    package_type = PackageType.SKILL
    schema = "skill-config_schema.json"
    abstract_field_name = "is_abstract"

    FIELDS_ALLOWED_TO_UPDATE: FrozenSet[str] = frozenset(
        ["behaviours", "handlers", "models", "is_abstract", "build_directory"]
    )
    FIELDS_WITH_NESTED_FIELDS: FrozenSet[str] = frozenset(
        ["behaviours", "handlers", "models"]
    )
    NESTED_FIELDS_ALLOWED_TO_UPDATE: FrozenSet[str] = frozenset(["args"])

    __slots__ = (
        "connections",
        "protocols",
        "contracts",
        "skills",
        "dependencies",
        "description",
        "handlers",
        "behaviours",
        "models",
        "is_abstract",
    )

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
    ) -> None:
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
        return self.is_abstract  # pragma: nocover

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
    def _create_or_update_from_json(
        cls, obj: Dict, instance: Optional["SkillConfig"] = None
    ) -> "SkillConfig":
        """Initialize from a JSON object."""
        obj = {**(instance.json if instance else {}), **copy(obj)}
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
        params = dict(
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
            build_directory=obj.get("build_directory"),
        )

        instance = cast(SkillConfig, cls._apply_params_to_instance(params, instance))

        for behaviour_id, behaviour_data in obj.get("behaviours", {}).items():
            behaviour_config = SkillComponentConfiguration.from_json(behaviour_data)
            instance.behaviours.create(behaviour_id, behaviour_config)

        for handler_id, handler_data in obj.get("handlers", {}).items():
            handler_config = SkillComponentConfiguration.from_json(handler_data)
            instance.handlers.create(handler_id, handler_config)

        for model_id, model_data in obj.get("models", {}).items():
            model_config = SkillComponentConfiguration.from_json(model_data)
            instance.models.create(model_id, model_config)

        return instance

    def get_overridable(self) -> dict:
        """Get overridable configuration data."""
        result = {}
        current_config_data = self.json
        if self.abstract_field_name in current_config_data:
            result[self.abstract_field_name] = current_config_data[
                self.abstract_field_name
            ]

        for field in self.FIELDS_WITH_NESTED_FIELDS:
            if not current_config_data.get(field, {}):
                continue
            result[field] = {}
            for name in current_config_data[field].keys():
                result[field][name] = {}
                for nested_field in self.NESTED_FIELDS_ALLOWED_TO_UPDATE:
                    result[field][name][nested_field] = current_config_data[field][
                        name
                    ][nested_field]
        return result


class AgentConfig(PackageConfiguration):
    """Class to represent the agent configuration file."""

    default_configuration_filename = DEFAULT_AEA_CONFIG_FILE
    package_type = PackageType.AGENT
    schema = "aea-config_schema.json"

    FIELDS_ALLOWED_TO_UPDATE: FrozenSet[str] = frozenset(
        [
            "description",
            "logging_config",
            "private_key_paths",
            "connection_private_key_paths",
            "loop_mode",
            "runtime_mode",
            "task_manager_mode",
            "execution_timeout",
            "timeout",
            "period",
            "max_reactions",
            "skill_exception_policy",
            "connection_exception_policy",
            "default_connection",
            "default_ledger",
            "required_ledgers",
            "default_routing",
            "storage_uri",
        ]
    )
    FIELDS_WITH_NESTED_FIELDS: FrozenSet[str] = frozenset(["logging_config"])
    CHECK_EXCLUDES = [
        ("private_key_paths",),
        ("connection_private_key_paths",),
        ("error_handler",),
        ("decision_maker_handler",),
        ("default_routing",),
        ("dependencies",),
        ("logging_config",),
    ]

    __slots__ = (
        "agent_name",
        "description",
        "private_key_paths",
        "connection_private_key_paths",
        "logging_config",
        "default_ledger",
        "required_ledgers",
        "currency_denominations",
        "default_connection",
        "connections",
        "protocols",
        "skills",
        "contracts",
        "period",
        "execution_timeout",
        "max_reactions",
        "skill_exception_policy",
        "connection_exception_policy",
        "error_handler",
        "decision_maker_handler",
        "default_routing",
        "loop_mode",
        "runtime_mode",
        "storage_uri",
        "data_dir",
        "_component_configurations",
        "dependencies",
    )

    def __init__(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        agent_name: SimpleIdOrStr,
        author: SimpleIdOrStr,
        version: str = "",
        license_: str = "",
        aea_version: str = "",
        fingerprint: Optional[Dict[str, str]] = None,
        fingerprint_ignore_patterns: Optional[Sequence[str]] = None,
        build_entrypoint: Optional[str] = None,
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
        required_ledgers: Optional[List[str]] = None,
        currency_denominations: Optional[Dict[str, str]] = None,
        default_connection: Optional[str] = None,
        default_routing: Optional[Dict[str, str]] = None,
        loop_mode: Optional[str] = None,
        runtime_mode: Optional[str] = None,
        task_manager_mode: Optional[str] = None,
        storage_uri: Optional[str] = None,
        data_dir: Optional[str] = None,
        component_configurations: Optional[Dict[ComponentId, Dict]] = None,
        dependencies: Optional[Dependencies] = None,
    ) -> None:
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
        self.description = description
        self.private_key_paths = CRUDCollection[str]()
        self.connection_private_key_paths = CRUDCollection[str]()

        self.logging_config = logging_config or DEFAULT_LOGGING_CONFIG
        self.default_ledger = (
            str(SimpleId(default_ledger)) if default_ledger is not None else None
        )
        self.required_ledgers = (
            [str(SimpleId(ledger)) for ledger in required_ledgers]
            if required_ledgers is not None
            else None
        )
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
        self.task_manager_mode = task_manager_mode
        self.storage_uri = storage_uri
        self.data_dir = data_dir
        # this attribute will be set through the setter below
        self._component_configurations: Dict[ComponentId, Dict] = {}
        self.component_configurations = (
            component_configurations if component_configurations is not None else {}
        )
        self.dependencies = dependencies or {}

    @property
    def component_configurations(self) -> Dict[ComponentId, Dict]:
        """Get the custom component configurations."""
        return self._component_configurations

    @component_configurations.setter
    def component_configurations(self, d: Dict[ComponentId, Dict]) -> None:
        """Set the component configurations."""
        package_type_to_set = {
            PackageType.PROTOCOL: {epid.without_hash() for epid in self.protocols},
            PackageType.CONNECTION: {epid.without_hash() for epid in self.connections},
            PackageType.CONTRACT: {epid.without_hash() for epid in self.contracts},
            PackageType.SKILL: {epid.without_hash() for epid in self.skills},
        }
        for component_id, component_configuration in d.items():
            enforce(
                component_id.public_id.without_hash()
                in package_type_to_set[component_id.package_type],
                f"Component {component_id} not declared in the agent configuration.",
            )
            ConfigValidator.validate_component_configuration(
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
                "required_ledgers": self.required_ledgers or [],
                "default_routing": {
                    str(key): str(value) for key, value in self.default_routing.items()
                },
                "connection_private_key_paths": self.connection_private_key_paths_dict,
                "private_key_paths": self.private_key_paths_dict,
                "logging_config": self.logging_config,
                "component_configurations": self.component_configurations_json(),
                "dependencies": dependencies_to_json(self.dependencies),
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
        if self.task_manager_mode is not None:
            config["task_manager_mode"] = self.task_manager_mode
        if self.storage_uri is not None:
            config["storage_uri"] = self.storage_uri
        if self.data_dir is not None:
            config["data_dir"] = self.data_dir
        if self.currency_denominations != {}:
            config["currency_denominations"] = self.currency_denominations

        return config

    @classmethod
    def _create_or_update_from_json(
        cls, obj: Dict, instance: Optional[Any] = None
    ) -> "AgentConfig":
        """Create new config object or updates existing one from json data."""
        obj = {**(instance.json if instance else {}), **copy(obj)}
        params = dict(
            agent_name=cast(str, obj.get("agent_name")),
            author=cast(str, obj.get("author")),
            version=cast(str, obj.get("version")),
            license_=cast(str, obj.get("license")),
            aea_version=cast(str, obj.get("aea_version", "")),
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
            required_ledgers=cast(Optional[List[str]], obj.get("required_ledgers")),
            currency_denominations=cast(Dict, obj.get("currency_denominations", {})),
            default_connection=cast(str, obj.get("default_connection")),
            default_routing=cast(Dict, obj.get("default_routing", {})),
            loop_mode=cast(str, obj.get("loop_mode")),
            runtime_mode=cast(str, obj.get("runtime_mode")),
            task_manager_mode=cast(str, obj.get("task_manager_mode")),
            storage_uri=cast(str, obj.get("storage_uri")),
            data_dir=cast(str, obj.get("data_dir")),
            component_configurations=None,
            dependencies=cast(
                Dependencies, dependencies_from_json(obj.get("dependencies", {}))
            ),
        )
        instance = cast(AgentConfig, cls._apply_params_to_instance(params, instance))

        agent_config = instance

        # Parse private keys
        for crypto_id, path in obj.get("private_key_paths", {}).items():
            agent_config.private_key_paths.create(crypto_id, path)

        for crypto_id, path in obj.get("connection_private_key_paths", {}).items():
            agent_config.connection_private_key_paths.create(crypto_id, path)

        # parse connection public ids
        agent_config.connections = set(
            map(
                PublicId.from_str,
                obj.get(CONNECTIONS, []),
            )
        )

        # parse contracts public ids
        agent_config.contracts = set(
            map(
                PublicId.from_str,
                obj.get(CONTRACTS, []),
            )
        )

        # parse protocol public ids
        agent_config.protocols = set(
            map(
                PublicId.from_str,
                obj.get(PROTOCOLS, []),
            )
        )

        # parse skills public ids
        agent_config.skills = set(
            map(
                PublicId.from_str,
                obj.get(SKILLS, []),
            )
        )

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

    @property
    def all_components_id(self) -> List[ComponentId]:
        """Get list of the all components for this agent config."""
        component_type_to_set = {
            ComponentType.PROTOCOL: self.protocols,
            ComponentType.CONNECTION: self.connections,
            ComponentType.CONTRACT: self.contracts,
            ComponentType.SKILL: self.skills,
        }
        result = []
        for component_type, public_ids in component_type_to_set.items():
            for public_id in public_ids:
                result.append(ComponentId(component_type, public_id))

        return result

    def update(  # pylint: disable=arguments-differ
        self,
        data: Dict,
        env_vars_friendly: bool = False,
        dict_overrides: Optional[Dict] = None,
    ) -> None:
        """
        Update configuration with other data.

        To update the component parts, populate the field "component_configurations" as a
        mapping from ComponentId to configurations.

        :param data: the data to replace.
        :param env_vars_friendly: whether or not it is env vars friendly.
        :param dict_overrides: A dictionary containing mapping for Component ID -> List of paths
        """
        data = copy(data)
        # update component parts
        new_component_configurations: Dict = data.pop("component_configurations", {})
        updated_component_configurations: Dict[ComponentId, Dict] = copy(
            self.component_configurations
        )
        for component_id, obj in new_component_configurations.items():
            if component_id not in updated_component_configurations:
                updated_component_configurations[component_id] = obj

            else:
                recursive_update(
                    updated_component_configurations[component_id],
                    obj,
                    allow_new_values=True,
                )

            if dict_overrides is not None and component_id in dict_overrides:
                perform_dict_override(
                    component_id,
                    dict_overrides,
                    updated_component_configurations,
                    new_component_configurations,
                )

        self.check_overrides_valid(data, env_vars_friendly=env_vars_friendly)
        super().update(data, env_vars_friendly=env_vars_friendly)
        self.validate_config_data(self.json, env_vars_friendly=env_vars_friendly)
        self.component_configurations = updated_component_configurations


class SpeechActContentConfig(Configuration):
    """Handle a speech_act content configuration."""

    __slots__ = ("args",)

    def __init__(self, **args: Any) -> None:
        """Initialize a speech_act content configuration."""
        super().__init__()
        self.args = args  # type: Dict[str, str]

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        return self.args

    @classmethod
    def from_json(cls, obj: Dict) -> "SpeechActContentConfig":
        """Initialize from a JSON object."""
        return SpeechActContentConfig(**obj)


class ProtocolSpecification(ProtocolConfig):
    """Handle protocol specification."""

    __slots__ = ("speech_acts", "_protobuf_snippets", "_dialogue_config")

    def __init__(
        self,
        name: SimpleIdOrStr,
        author: SimpleIdOrStr,
        version: str = "",
        license_: str = "",
        aea_version: str = "",
        description: str = "",
        protocol_specification_id: Optional[str] = None,
    ) -> None:
        """Initialize a protocol specification configuration object."""
        super().__init__(
            name,
            author,
            version,
            license_,
            aea_version=aea_version,
            description=description,
            protocol_specification_id=protocol_specification_id,
        )
        self.speech_acts = CRUDCollection[SpeechActContentConfig]()
        self._protobuf_snippets = {}  # type: Dict
        self._dialogue_config = {}  # type: Dict

    @property
    def protobuf_snippets(self) -> Dict:
        """Get the protobuf snippets."""
        return self._protobuf_snippets

    @protobuf_snippets.setter
    def protobuf_snippets(self, protobuf_snippets: Dict) -> None:
        """Set the protobuf snippets."""
        self._protobuf_snippets = protobuf_snippets

    @property
    def dialogue_config(self) -> Dict:
        """Get the dialogue config."""
        return self._dialogue_config

    @dialogue_config.setter
    def dialogue_config(self, dialogue_config: Dict) -> None:
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
                "protocol_specification_id": str(self.protocol_specification_id),
                "speech_acts": {
                    key: speech_act.json
                    for key, speech_act in self.speech_acts.read_all()
                },
            }
        )
        return result

    @classmethod
    def _create_or_update_from_json(  # type: ignore
        cls, obj: Dict, instance: Optional["ProtocolSpecification"] = None
    ) -> "ProtocolSpecification":
        """Initialize from a JSON object."""
        obj = {**(instance.json if instance else {}), **copy(obj)}
        params = dict(
            name=cast(str, obj.get("name")),
            author=cast(str, obj.get("author")),
            protocol_specification_id=cast(str, obj.get("protocol_specification_id")),
            version=cast(str, obj.get("version")),
            license_=cast(str, obj.get("license")),
            aea_version=cast(str, obj.get("aea_version", "")),
            description=cast(str, obj.get("description", "")),
        )

        instance = cast(
            ProtocolSpecification, cls._apply_params_to_instance(params, instance)
        )

        protocol_specification = instance
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
    schema = "contract-config_schema.json"

    FIELDS_ALLOWED_TO_UPDATE: FrozenSet[str] = frozenset(["build_directory"])

    __slots__ = (
        "dependencies",
        "description",
        "contract_interface_paths",
        "class_name",
        "contracts",
    )

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
        contracts: Optional[Set[PublicId]] = None,
    ) -> None:
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
        self.contracts = contracts or set()

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
                CONTRACTS: sorted(map(str, self.contracts)),
            }
        )
        if self.build_entrypoint:
            result["build_entrypoint"] = self.build_entrypoint
        if self.build_directory:
            result["build_directory"] = self.build_directory
        return result

    @classmethod
    def _create_or_update_from_json(
        cls, obj: Dict, instance: Optional["ContractConfig"] = None
    ) -> "ContractConfig":
        """Initialize from a JSON object."""
        obj = {**(instance.json if instance else {}), **copy(obj)}
        dependencies = cast(
            Dependencies, dependencies_from_json(obj.get("dependencies", {}))
        )
        contracts = {PublicId.from_str(id_) for id_ in obj.get(CONTRACTS, set())}
        params = dict(
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
            contracts=contracts,
        )
        instance = cast(ContractConfig, cls._apply_params_to_instance(params, instance))

        return instance

    @property
    def package_dependencies(self) -> Set[ComponentId]:
        """Get the contract dependencies."""
        return {
            ComponentId(ComponentType.CONTRACT, contract_id)
            for contract_id in self.contracts
        }


"""The following functions are called from aea.cli.utils."""


def _compute_fingerprint(  # pylint: disable=unsubscriptable-object
    package_directory: Path,
    ignore_patterns: Optional[Collection[str]] = None,
    is_recursive: bool = True,
    ignore_directories: Optional[Collection[str]] = None,
) -> Dict[str, str]:
    ignore_patterns = ignore_patterns if ignore_patterns is not None else []
    ignore_directories = ignore_directories if ignore_directories is not None else []
    ignore_patterns = set(ignore_patterns).union(DEFAULT_FINGERPRINT_IGNORE_PATTERNS)
    hasher = IPFSHashOnly()
    fingerprints = {}  # type: Dict[str, str]
    # find all valid files of the package
    all_files = [
        x
        for x in package_directory.glob("**/*" if is_recursive else "*")
        if x.is_file()
        and not any(x.match(pattern) for pattern in ignore_patterns)
        and not (x.parts[0] in ignore_directories)
    ]

    for file in all_files:
        file_hash = hasher.get(str(file), wrap=False)
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
    is_recursive: bool = True,
) -> None:
    """
    Check fingerprints of a package directory against the fingerprints declared in the configuration file.

    :param package_configuration: the package configuration object.
    :param package_directory: the directory of the package.
    :param is_vendor: whether the package is vendorized or not.
    :param item_type: the type of the item.
    :param is_recursive: look up sub directories for files to fingerprint

    :raises ValueError: if the fingerprints do not match.
    """
    expected_fingerprints = package_configuration.fingerprint
    ignore_patterns = package_configuration.fingerprint_ignore_patterns
    actual_fingerprints = _compute_fingerprint(
        package_directory, ignore_patterns, is_recursive=is_recursive
    )
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
        if item_type == PackageType.AGENT:
            raise ValueError(
                (
                    "Fingerprints for package {} do not match:\nExpected: {}\nActual: {}\n"
                    "Please fingerprint the package before continuing: 'aea fingerprint'"
                ).format(
                    package_directory,
                    pprint.pformat(expected_fingerprints),
                    pprint.pformat(actual_fingerprints),
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


class AEAVersionError(ValueError):
    """Special Exception for version error."""

    def __init__(
        self, package_id: PublicId, aea_version_specifiers: SpecifierSet
    ) -> None:
        """Init exception."""
        self.package_id = package_id
        self.aea_version_specifiers = aea_version_specifiers
        self.current_aea_version = Version(__aea_version__)
        super().__init__(
            f"The CLI version is {self.current_aea_version}, but package {self.package_id} requires version {self.aea_version_specifiers}"
        )


def _check_aea_version(package_configuration: PackageConfiguration) -> None:
    """Check the package configuration version against the version of the framework."""
    current_aea_version = Version(__aea_version__)
    version_specifiers = package_configuration.aea_version_specifiers
    if current_aea_version not in version_specifiers:
        raise AEAVersionError(
            package_configuration.public_id,
            package_configuration.aea_version_specifiers,
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


PACKAGE_TYPE_TO_CONFIG_CLASS: Dict[PackageType, Type[PackageConfiguration]] = {
    PackageType.AGENT: AgentConfig,
    PackageType.PROTOCOL: ProtocolConfig,
    PackageType.CONNECTION: ConnectionConfig,
    PackageType.SKILL: SkillConfig,
    PackageType.CONTRACT: ContractConfig,
}
