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
"""Run different checks on AEA packages."""

import dis
import importlib
import os
import pprint
import re
import sys
from abc import abstractmethod
from collections import defaultdict
from functools import partial, wraps
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Set, Tuple, Union

import click
import yaml
from pip._internal.commands.show import search_packages_info

from aea.cli.utils.context import Context
from aea.cli.utils.decorators import pass_ctx
from aea.configurations.base import PackageId, PackageType, PublicId
from aea.configurations.constants import (
    AGENTS,
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_CONNECTION_CONFIG_FILE,
    DEFAULT_CONTRACT_CONFIG_FILE,
    DEFAULT_PROTOCOL_CONFIG_FILE,
    DEFAULT_SKILL_CONFIG_FILE,
)


CONFIG_FILE_NAMES = [
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_SKILL_CONFIG_FILE,
    DEFAULT_CONNECTION_CONFIG_FILE,
    DEFAULT_CONTRACT_CONFIG_FILE,
    DEFAULT_PROTOCOL_CONFIG_FILE,
]  # type: List[str]

IGNORE_PACKAGES: Set[str] = {"pkg_resources"}
IGNORE_PACKAGE_SUBFOLDERS: Set[Path] = {Path("tests")}
DEP_NAME_RE = re.compile(r"(^[^=><\[]+)", re.I)  # type: ignore


class CustomException(Exception):
    """A custom exception class for this script."""

    @abstractmethod
    def print_error(self) -> None:
        """Print the error message."""


def list_decorator(fn: Callable) -> Callable:
    """Wraps generator to return list."""

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> List[Any]:
        return list(fn(*args, **kwargs))

    return wrapper


class PypiDependencyNotFound(CustomException):
    """Custom exception for Pypi dependency not found."""

    def print_error(self) -> None:
        """Print the error message."""
        return print(self.args[0])


class DependencyNotFound(CustomException):
    """Custom exception for dependencies not found."""

    def __init__(
        self,
        configuration_file: Path,
        expected_deps: Set[PackageId],
        missing_dependencies: Set[PackageId],
        *args: Any,
    ) -> None:
        """
        Initialize DependencyNotFound exception.

        :param configuration_file: path to the checked file.
        :param expected_deps: expected dependencies.
        :param missing_dependencies: missing dependencies.
        :param args: super class args.
        """
        super().__init__(*args)
        self.configuration_file = configuration_file
        self.expected_dependencies = expected_deps
        self.missing_dependencies = missing_dependencies

    def print_error(self) -> None:
        """Print the error message."""
        sorted_expected = list(map(str, sorted(self.expected_dependencies)))
        sorted_missing = list(map(str, sorted(self.missing_dependencies)))
        print("=" * 50)
        print(f"Package {self.configuration_file}:")
        print(f"Expected: {pprint.pformat(sorted_expected)}")
        print(f"Missing: {pprint.pformat(sorted_missing)}")
        print("=" * 50)


class EmptyPackageDescription(CustomException):
    """Custom exception for empty description field."""

    def __init__(
        self,
        configuration_file: Path,
        *args: Any,
    ) -> None:
        """
        Initialize EmptyPackageDescription exception.

        :param configuration_file: path to the checked file.
        :param args: super class args.
        """
        super().__init__(*args)
        self.configuration_file = configuration_file

    def print_error(self) -> None:
        """Print the error message."""
        print("=" * 50)
        print(f"Package '{self.configuration_file}' has empty description field.")
        print("=" * 50)


class UnexpectedAuthorError(CustomException):
    """Custom exception for unexpected author value."""

    def __init__(
        self,
        configuration_file: Path,
        expected_author: str,
        actual_author: str,
        *args: Any,
    ):
        """
        Initialize the exception.

        :param configuration_file: the file to the configuration that raised the error.
        :param expected_author: the expected author.
        :param actual_author: the actual author.
        :param args: other positional arguments.
        """
        super().__init__(*args)
        self.configuration_file = configuration_file
        self.expected_author = expected_author
        self.actual_author = actual_author

    def print_error(self) -> None:
        """Print the error message."""
        print("=" * 50)
        print(
            f"Package '{self.configuration_file}' has an unexpected author value: "
            f"expected {self.expected_author}, found '{self.actual_author}'."
        )
        print("=" * 50)


class PublicIdDefinitionError(CustomException):
    """Custom exception for error about PUBLIC_ID definitions in package Python modules."""

    def __init__(
        self,
        package_type: PackageType,
        public_id: PublicId,
        actual_nb_definitions: int,
        *args: Any,
    ) -> None:
        """Initialize the exception."""
        super().__init__(*args)
        self.package_type = package_type
        self.public_id = public_id
        self.actual_nb_definitions = actual_nb_definitions

    def print_error(self) -> None:
        """Print the error message."""
        print("=" * 50)
        print(
            f"expected unique definition of PUBLIC_ID for package {self.public_id} of type {self.package_type.value}; "
            f"found {self.actual_nb_definitions}"
        )
        print("=" * 50)


class WrongPublicIdError(CustomException):
    """Custom exception for error about wrong value of PUBLIC_ID."""

    def __init__(
        self,
        package_type: PackageType,
        public_id: PublicId,
        public_id_code: str,
        *args: Any,
    ) -> None:
        """Initialize the exception."""
        super().__init__(*args)
        self.package_type = package_type
        self.public_id = public_id
        self.public_id_code = public_id_code

    def print_error(self) -> None:
        """Print the error message."""
        print("=" * 50)
        print(
            f"expected {self.public_id} for package of type {self.package_type.value}; found '{self.public_id_code}'"
        )
        print("=" * 50)


def find_all_configuration_files(
    packages_dir: Path, vendor: Optional[str] = None
) -> List:
    """Find all configuration files."""
    config_files = [
        path
        for path in packages_dir.glob("*/*/*/*.yaml")
        if any([file in str(path) for file in CONFIG_FILE_NAMES])
        and (vendor is None or path.parent.parent.parent.name == vendor)
    ]
    return config_files


def get_public_id_from_yaml(configuration_file: Path) -> PublicId:
    """
    Get the public id from yaml.

    :param configuration_file: the path to the config yaml
    :return: public id
    """
    data = unified_yaml_load(configuration_file)
    author = data.get("author", None)
    if not author:
        raise KeyError(f"No author field in {str(configuration_file)}")
    # handle the case when it's a package or agent config file.
    try:
        name = data["name"] if "name" in data else data["agent_name"]
    except KeyError:
        click.echo(f"No name or agent_name field in {str(configuration_file)}")
        raise
    version = data.get("version", None)
    if not version:
        raise KeyError(f"No version field in {str(configuration_file)}")
    return PublicId(author, name, version)


def find_all_packages_ids(packages_dir: Path) -> Set[PackageId]:
    """Find all packages ids."""
    package_ids: Set[PackageId] = set()
    for configuration_file in find_all_configuration_files(packages_dir):
        package_type = PackageType(configuration_file.parts[-3][:-1])
        package_public_id = get_public_id_from_yaml(configuration_file)
        package_id = PackageId(package_type, package_public_id)
        package_ids.add(package_id)

    return package_ids


def unified_yaml_load(configuration_file: Path) -> Dict:
    """
    Load YAML file, unified (both single- and multi-paged).

    :param configuration_file: the configuration file path.
    :return: the data.
    """
    package_type = configuration_file.parent.parent.name
    with configuration_file.open() as fp:
        if package_type != AGENTS:
            return yaml.safe_load(fp)
        # when it is an agent configuration file,
        # we are interested only in the first page of the YAML,
        # because the dependencies are contained only there.
        data = yaml.safe_load_all(fp)
        return list(data)[0]


def check_dependencies(
    configuration_file: Path, all_packages_ids: Set[PackageId]
) -> None:
    """
    Check dependencies of configuration file.

    :param configuration_file: path to a package configuration file.
    :param all_packages_ids: all the package ids.
    """
    data = unified_yaml_load(configuration_file)

    def _add_package_type(package_type: PackageType, public_id_str: str) -> PackageId:
        return PackageId(package_type, PublicId.from_str(public_id_str))

    def _get_package_ids(
        package_type: PackageType, public_ids: Set[PublicId]
    ) -> Set[PackageId]:
        return set(map(partial(_add_package_type, package_type), public_ids))

    dependencies: Set[PackageId] = set.union(
        *[
            _get_package_ids(package_type, data.get(package_type.to_plural(), set()))
            for package_type in list(PackageType)
        ]
    )

    diff = dependencies.difference(all_packages_ids)
    if len(diff) > 0:
        raise DependencyNotFound(configuration_file, dependencies, diff)


def check_description(configuration_file: Path) -> None:
    """Check description field of a package is non-empty."""
    yaml_object = unified_yaml_load(configuration_file)
    description = yaml_object.get("description")
    if description == "":
        raise EmptyPackageDescription(configuration_file)


def check_author(configuration_file: Path, expected_author: str) -> None:
    """Check the author matches a certain desired value."""
    yaml_object = unified_yaml_load(configuration_file)
    actual_author = yaml_object.get("author", "")
    if actual_author != expected_author:
        raise UnexpectedAuthorError(configuration_file, expected_author, actual_author)


def check_public_id(configuration_file: Path) -> None:
    """Check the public_id in the code and configuration match."""
    expected_public_id = get_public_id_from_yaml(configuration_file)
    # remove last 's' character (as package type is plural in packages directory)
    package_type_str = configuration_file.parent.parent.name[:-1]
    package_type = PackageType(package_type_str)
    if package_type == PackageType.CONNECTION:
        module_name_to_load = Path("connection.py")
    elif package_type == PackageType.SKILL:
        module_name_to_load = Path("__init__.py")
    else:
        # no check to do.
        return
    module_path_to_load = configuration_file.parent / module_name_to_load
    content = module_path_to_load.read_text()

    # check number of definitions of PUBLIC_ID. Required exactly one match.
    assignments_to_public_id = re.findall("^PUBLIC_ID = (.*)", content, re.MULTILINE)
    if len(assignments_to_public_id) != 1:
        raise PublicIdDefinitionError(
            package_type, expected_public_id, len(assignments_to_public_id)
        )

    # check first pattern of public id: PublicId.from_str(...)
    matches = re.findall(
        r"^PUBLIC_ID = PublicId.from_str\( *(\"(.*)\"|'(.*)') *\)$",
        content,
        re.MULTILINE,
    )
    if len(matches) == 1:
        # process the result
        _, match1, match2 = matches[0]
        match = match1 if match1 != "" else match2
        if str(expected_public_id) != match:
            raise WrongPublicIdError(package_type, expected_public_id, match)
        return

    # check second pattern of public id: PublicId('...', '...', '...')
    matches = re.findall(
        r"^PUBLIC_ID = PublicId\( *['\"](.*)['\"] *, *['\"](.*)['\"] *, *['\"](.*)['\"] *\)$",
        content,
        re.MULTILINE,
    )
    if len(matches) == 1:
        # process the result
        author, name, version = matches[0]
        actual_public_id_str = f"{author}/{name}:{version}"
        if str(expected_public_id) != actual_public_id_str:
            raise WrongPublicIdError(
                package_type, expected_public_id, actual_public_id_str
            )
        return

    public_id_code = matches[0]
    if str(expected_public_id) not in public_id_code:
        raise WrongPublicIdError(package_type, expected_public_id, public_id_code)


class DependenciesTool:
    """Tool to work with setup.py dependencies."""

    @staticmethod
    def get_package_files(package_name: str) -> List[Path]:
        """Get package files list."""
        packages_info = list(search_packages_info([package_name]))
        if len(packages_info) == 0:
            raise Exception(f"package {package_name} not found")
        if isinstance(packages_info[0], dict):
            files = packages_info[0]["files"]
            location = packages_info[0]["location"]
        else:
            files = packages_info[0].files  # type: ignore
            location = packages_info[0].location  # type: ignore
        return [Path(location) / i for i in files]  # type: ignore

    @staticmethod
    def clean_dependency_name(dependecy_specification: str) -> str:
        """Get dependency name from dependency specification."""
        match = DEP_NAME_RE.match(dependecy_specification)
        if not match:
            raise ValueError(f"Bad dependency specification: {dependecy_specification}")
        return match.groups()[0]


class ImportsTool:
    """Tool to work with 3rd part imports in source code."""

    @staticmethod
    def get_imports_for_file(pyfile: Union[str, Path]) -> List[str]:
        """Get all imported modules for python source file."""
        with open(pyfile, "r") as f:
            statements = f.read()
        instructions = dis.get_instructions(statements)  # type: ignore
        imports = []
        is_try_except_block = False
        for im in instructions:
            if "SETUP_FINALLY" in im.opname:
                is_try_except_block = True

            if "POP_EXCEPT" in im.opname:
                is_try_except_block = False

            if is_try_except_block:
                continue

            if "IMPORT" in im.opname:
                imports.append(im)

        grouped: Dict[str, List[str]] = defaultdict(list)
        for instr in imports:
            grouped[instr.opname].append(instr.argval)

        return grouped["IMPORT_NAME"]

    @staticmethod
    def get_module_file(module_name: str) -> str:
        """Get module source file name."""
        try:
            mod = importlib.import_module(module_name)
            return getattr(mod, "__file__", "")
        except (AttributeError, ModuleNotFoundError):
            return ""

    @staticmethod
    @list_decorator
    def list_all_pyfiles(
        root_path: Union[Path, str],
        pattern: str = "**/*.py",
        ignores: Optional[Set[Path]] = None,
    ) -> Generator:
        """List all python files in directory."""
        ignores = ignores or set()
        root_path = Path(root_path)
        for path in root_path.glob(pattern):
            # check if path is a subpath of an ignore path
            relative_path = path.relative_to(root_path)
            if any(os.path.commonprefix([relative_path, p]) != "" for p in ignores):
                continue
            yield path.relative_to(root_path)

    @classmethod
    @list_decorator
    def get_third_part_imports_for_file(cls, pyfile: str) -> Generator:
        """Get list of third part modules imported for source file."""
        imports = cls.get_imports_for_file(pyfile)
        for module_name in imports:
            pyfile = cls.get_module_file(module_name)
            if not pyfile:
                continue
            if "site-packages" not in Path(pyfile).parts or "aea" in Path(pyfile).parts:
                continue
            yield module_name, Path(pyfile)

    @classmethod
    @list_decorator
    def list_all_pyfiles_with_third_party_imports(
        cls, root_path: Union[str, Path], pattern: str = "**/*.py"
    ) -> Generator:
        """Get list of all python sources with 3rd party modules imported."""
        for pyfile in cls.list_all_pyfiles(
            root_path, pattern=pattern, ignores=IGNORE_PACKAGE_SUBFOLDERS
        ):
            mods = list(cls.get_third_part_imports_for_file(root_path / pyfile))
            if not mods:
                continue
            yield Path(pyfile), list(set(mods))


class PyPIDependenciesCheckTool:
    """Tool to check imports in sources match dependencies in package configuration file."""

    def __init__(self, configuration_file: Path) -> None:
        """Init the checker for PyPI dependencies."""
        self.configuration_file = configuration_file
        self.config = unified_yaml_load(configuration_file)

    @staticmethod
    def make_third_party_imports(
        files_and_modules: List[Tuple[str, List[Tuple[str, Path]]]],
    ) -> Dict[str, Path]:
        """Make list of third party imports."""
        third_party_imports: Dict[str, Path] = {}
        for _pyfile, name_modules_pairs in files_and_modules:
            for package_name, modules in name_modules_pairs:
                third_party_imports[package_name] = modules

        return third_party_imports

    def get_dependencies(self) -> Dict[str, List[Path]]:
        """Get sections with dependencies with files lists."""
        dependencies = self.config.get("dependencies", set())
        result: Dict[str, List[Path]] = defaultdict(list)
        for dep in dependencies:
            dep = DependenciesTool.clean_dependency_name(dep)
            result[dep] = DependenciesTool.get_package_files(dep)
        return result

    def run(self) -> None:
        """Run dependency check."""
        files_and_modules = ImportsTool.list_all_pyfiles_with_third_party_imports(
            self.configuration_file.parent
        )
        package_dependencies = self.get_dependencies()
        third_party_imports = self.make_third_party_imports(files_and_modules)
        missed_deps_for_imports, deps_not_imported_directly = self.check_imports(
            third_party_imports, package_dependencies
        )

        if missed_deps_for_imports:
            raise PypiDependencyNotFound(
                f"unresolved imports: {', '.join(missed_deps_for_imports)}"
            )

        if deps_not_imported_directly:
            raise PypiDependencyNotFound(
                f"Dependencies not imported in code directly: {', '.join(deps_not_imported_directly)}"
            )

    @staticmethod
    def check_imports(
        third_party_imports: Dict[str, Path],
        pypi_dependencies: Dict[str, List[Path]],
    ) -> Tuple[Set[str], Set[str]]:
        """Find missing dependencies for imports and not imported dependencies."""

        def _find_dependency_for_module(
            dependencies: Dict[str, List[Path]], pyfile: Path
        ) -> Optional[str]:
            for package, files in dependencies.items():
                if pyfile in files:
                    return package
            return None

        imports_packages: Dict[str, Optional[str]] = {}
        for module, pyfile in third_party_imports.items():
            package_or_none = _find_dependency_for_module(pypi_dependencies, pyfile)
            if module not in IGNORE_PACKAGES:
                imports_packages[module] = package_or_none

        all_dependencies_set = set(third_party_imports.keys())
        used_dependencies_set = {
            k for k, v in imports_packages.items() if v is not None
        }
        deps_not_imported_directly: Set[str] = (
            all_dependencies_set - used_dependencies_set
        )
        missed_deps_for_imports: Set[str] = {
            k for k, v in imports_packages.items() if v is None
        }
        return missed_deps_for_imports, deps_not_imported_directly


def check_pypi_dependencies(configuration_file: Path) -> None:
    """Check PyPI dependencies of the AEA package."""
    PyPIDependenciesCheckTool(configuration_file).run()


@click.command(name="check-packages")
@click.option("--vendor", type=str, default=None, required=False)
@pass_ctx
def check_packages(ctx: Context, vendor: Optional[str]) -> None:
    """
    Run different checks on AEA packages.

    Namely:
    - Check that every package has existing dependencies
    - Check that every package has non-empty description

    :param ctx: AEA cli context.
    :param vendor: filter by author name
    """
    packages_dir = Path(ctx.registry_path).absolute()
    all_packages_ids_ = find_all_packages_ids(packages_dir)
    failed: bool = False

    for file in find_all_configuration_files(packages_dir, vendor=vendor):
        try:
            expected_author = file.parent.parent.parent.name
            click.echo("Processing " + str(file))
            check_author(file, expected_author)
            check_dependencies(file, all_packages_ids_)
            check_description(file)
            check_public_id(file)
            check_pypi_dependencies(file)
        except CustomException as exception:
            exception.print_error()
            failed = True

    if failed:
        click.echo("Failed!")
        sys.exit(1)
    else:
        click.echo("OK!")
        sys.exit(0)
