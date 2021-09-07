#!/usr/bin/env python3
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
"""Check aea dependencies."""
import copy
import dis
import importlib
import re
import sys
from collections import defaultdict
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Set, Tuple, Union

from pip._internal.commands.show import search_packages_info  # type: ignore


AEA_ROOT_DIR = Path(__file__).parent.parent

sys.path.append(str(AEA_ROOT_DIR))

from aea.crypto.registries import (  # noqa # pylint: disable=wrong-import-position
    crypto_registry,
)


IGNORE: Set[str] = {"pkg_resources"}
DEP_NAME_RE = re.compile(r"(^[^=><\[]+)", re.I)  # type: ignore


def list_decorator(fn: Callable) -> Callable:
    """Wraps generator to return list."""

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> List[Any]:
        return list(fn(*args, **kwargs))

    return wrapper


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
        imports = [i for i in instructions if "IMPORT" in i.opname]

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
        root_path: Union[Path, str], pattern: str = "**/*.py"
    ) -> Generator:
        """List all python files in directory."""
        root_path = Path(root_path)
        for path in root_path.rglob(pattern):
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
            if "site-packages" not in Path(pyfile).parts:
                continue
            yield module_name, Path(pyfile)

    @classmethod
    @list_decorator
    def list_all_pyfiles_with_3rdpart_imports(
        cls, root_path: Union[str, Path], pattern: str = "**/*.py"
    ) -> Generator:
        """Get list of all python sources with 3rd party modules imported."""
        for pyfile in cls.list_all_pyfiles(root_path, pattern=pattern):
            mods = list(cls.get_third_part_imports_for_file(root_path / pyfile))
            if not mods:
                continue
            yield Path(pyfile), list(set(mods))


class CheckTool:
    """Tool to check imports in sources match dependencies in setup.py."""

    @classmethod
    def get_section_dependencies_from_setup(cls) -> Dict[str, Dict[str, List[Path]]]:
        """Get sections with dependencies with files lists."""
        spec = importlib.util.spec_from_file_location(
            "setup", str(AEA_ROOT_DIR / "setup.py")
        )
        setup = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = setup
        spec.loader.exec_module(setup)  # type: ignore

        sections_dependencies = copy.deepcopy(setup.all_extras)  # type: ignore
        sections_dependencies.pop("all")
        base = setup.base_deps  # type: ignore

        for crypto_id in crypto_registry.supported_ids:  # type: ignore
            if crypto_id == "fetchai":
                crypto_id = "fetch"
            if crypto_id in sections_dependencies:
                sections_dependencies.pop(crypto_id)
        sections_dependencies["base"] = base

        return cls.sections_dependencies_add_files(sections_dependencies)

    @staticmethod
    def sections_dependencies_add_files(
        sections_dependencies: Dict[str, List[str]]
    ) -> Dict[str, Dict[str, List[Path]]]:
        """Add packages file lists to dependencies in sections."""
        result: Dict[str, Dict[str, List[Path]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for section, deps in sections_dependencies.items():
            for dep in deps:
                dep = DependenciesTool.clean_dependency_name(dep)
                result[section][dep] = DependenciesTool.get_package_files(dep)
        return result

    @classmethod
    def run(cls) -> None:
        """Run dependency check."""
        print("Dependencies check report:")
        print("==========================")
        files_and_modules = ImportsTool.list_all_pyfiles_with_3rdpart_imports(
            AEA_ROOT_DIR, pattern="aea/**/*.py"
        )

        sections_dependencies = cls.get_section_dependencies_from_setup()
        sections_imports = cls.make_sections_with_3rdpart_imports(
            files_and_modules, set(sections_dependencies.keys())
        )
        missed_deps_for_imports, deps_not_imported_directly = cls.check_imports(
            sections_imports, sections_dependencies  # type: ignore
        )

        for section, unresolved_imports in missed_deps_for_imports.items():
            print(
                f"Section `{section}` unresolved imports: {', '.join(unresolved_imports)}"
            )

        if deps_not_imported_directly:
            if missed_deps_for_imports:
                print()
            print(
                f"Dependencies not imported in code directly: {', '.join(deps_not_imported_directly)}"
            )

        if missed_deps_for_imports or deps_not_imported_directly:
            sys.exit(1)
        else:
            print("All good!")

    @staticmethod
    def make_sections_with_3rdpart_imports(
        files_and_modules: List[Tuple[str, List[Tuple[str, Path]]]],
        section_names: Set[str],
    ) -> Dict[str, Set[Tuple[str, Path]]]:
        """Make sections with list of 3r part imports."""
        sections_imports: Dict[str, Set[Tuple[str, Path]]] = defaultdict(set)
        for pyfile, imports in files_and_modules:
            section_name = Path(pyfile).parts[1]

            if section_name not in section_names:
                section_name = "base"

            sections_imports[section_name].update(imports)

        return sections_imports

    @staticmethod
    def check_imports(
        sections_imports: Dict[str, Set[str]],
        sections_dependencies: Dict[str, Dict[str, List[str]]],
    ) -> Tuple[Dict[str, List[str]], List[str]]:
        """Find missing dependencies for imports and not imported dependencies."""

        def _find_dependency_for_module(
            dependencies: Dict[str, List[str]], pyfile: str
        ) -> Optional[str]:
            for package, files in dependencies.items():
                if pyfile in files:
                    return package
            return None

        sections_imports_packages: Dict[str, Dict[str, Optional[str]]] = defaultdict(
            dict
        )
        for section, modules in sections_imports.items():
            for module, pyfile in modules:
                package = _find_dependency_for_module(
                    sections_dependencies.get(section, {}), pyfile
                )
                if module not in IGNORE:
                    sections_imports_packages[section][module] = package

        all_dependencies_set = set(
            sum((list(i.keys()) for _, i in sections_dependencies.items()), [])
        )
        used_dependencies_set = set(
            sum(
                [
                    list(section.values())
                    for section in sections_imports_packages.values()
                ],
                [],
            )
        )
        deps_not_imported_directly: List[str] = list(
            all_dependencies_set - used_dependencies_set
        )
        missed_deps_for_imports: Dict[str, List[str]] = {
            section: [k for k, v in modules.items() if v is None]
            for section, modules in sections_imports_packages.items()
            if None in modules.values()
        }
        return missed_deps_for_imports, deps_not_imported_directly


if __name__ == "__main__":
    CheckTool.run()
