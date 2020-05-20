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

"""This module contains a checker for PyPI version consistency."""
import operator
from collections import defaultdict
from typing import Dict, Set, cast

from packaging.specifiers import Specifier, SpecifierSet
from packaging.version import InvalidVersion, Version


def and_(s1: SpecifierSet, s2: SpecifierSet):
    """Do the and between two specifier sets."""
    return operator.and_(s1, s2)


def _is_satisfiable(specifier_set: SpecifierSet) -> bool:
    """
    Check if the specifier set is satisfiable.

    Satisfiable means that there exists a version number
    that satisfies all the constraints. It is worth
    noticing that it doesn't mean that that version
    number with that package actually exists.

    >>> from packaging.specifiers import SpecifierSet

    The specifier set ">0.9, ==1.0" is satisfiable:
    the version number "1.0" satisfies the constraints

    >>> s1 = SpecifierSet(">0.9,==1.0")
    >>> "1.0" in s1
    True
    >>> _is_satisfiable(s1)
    True

    The specifier set "==1.0, >1.1" is not satisfiable:

    >>> s1 = SpecifierSet("==1.0,>1.1")
    >>> _is_satisfiable(s1)
    False

    Other examples:

    >>> _is_satisfiable(SpecifierSet("<=1.0,>1.1, >0.9"))
    False
    >>> _is_satisfiable(SpecifierSet("==1.0,!=1.0"))
    False
    >>> _is_satisfiable(SpecifierSet("!=0.9,!=1.0"))
    True
    >>> _is_satisfiable(SpecifierSet("<=1.0,>=1.0"))
    True
    >>> _is_satisfiable(SpecifierSet("<=1.0,>1.0"))
    False
    >>> _is_satisfiable(SpecifierSet("<1.0,<=1.0,>1.0"))
    False
    >>> _is_satisfiable(SpecifierSet(">1.0,>=1.0,<1.0"))
    False
    >>> _is_satisfiable(SpecifierSet("~=1.1,==2.0"))  # fails because of major number 2
    False
    >>> _is_satisfiable(SpecifierSet("~=1.1,==1.0"))  # fails because minor is 0
    False
    >>> _is_satisfiable(SpecifierSet("~=1.1,<=1.1"))  # satisfiable: "1.1"
    True
    >>> _is_satisfiable(SpecifierSet("~=1.1,<1.1"))
    False
    >>> _is_satisfiable(SpecifierSet("~=1.0,<1.0"))
    False
    >>> _is_satisfiable(SpecifierSet("~=1.1,==1.2"))
    True
    >>> _is_satisfiable(SpecifierSet("~=1.1,>1.2"))
    True

    We ignore legacy versions:

    >>> _is_satisfiable(SpecifierSet("==1.0,==1.*"))
    True

    For other details, please refer to PEP440:

        https://www.python.org/dev/peps/pep-0440

    :param specifier_set: the specifier set.
    :return: False if the constraints are surely non-satisfiable, True if we don't know.
    """
    # group single specifiers by operator
    all_specifiers = []
    operator_to_specifiers: Dict[str, Set[Specifier]] = defaultdict(lambda: set())
    # pre-processing
    for specifier in list(specifier_set):
        specifier = cast(Specifier, specifier)
        try:
            # if we can't parse the version number, ignore that specifier.
            # Even if it follows a legacy version format (e.g. "2.*")
            Version(specifier.version)
        except InvalidVersion:
            continue

        # split specifier "~=<major.minor>" in two specifiers:
        # - >= <major.minor>
        # - < <major+1>
        # TODO this is not the full story. we should check the version number
        #   up to the last zero, which might be the micro number.
        #   e.g. see last examples of https://www.python.org/dev/peps/pep-0440/#compatible-release
        if specifier.operator == "~=":
            spec_version = Version(specifier.version)
            upper_major_version = Version(str(spec_version.major + 1))
            spec_1 = Specifier(">=" + str(spec_version))
            spec_2 = Specifier("<" + str(upper_major_version))
            all_specifiers.extend([spec_1, spec_2])
            operator_to_specifiers[spec_1.operator].add(spec_1)
            operator_to_specifiers[spec_2.operator].add(spec_2)
        else:
            all_specifiers.append(specifier)
            operator_to_specifiers[specifier.operator].add(specifier)

    # end of pre-processing. Start evaluation
    # if there are two different "==" specifier, return False
    if len(operator_to_specifiers["=="]) >= 2:
        return False

    if len(operator_to_specifiers["=="]) == 1:
        eq_specifier = operator_to_specifiers["=="].pop()
        eq_version = eq_specifier.version
        # notice: we implicitly handle the "!=" constraints.
        return eq_version in specifier_set

    # group all the "<" or "<=" together. They are interpreted as conjunction.
    # simplify: the spec with the lowest version number is the strictest constraint
    less_than_strict_specs = operator_to_specifiers["<"]
    less_than_equal_specs = operator_to_specifiers["<="]
    less_than_specs = set.union(less_than_equal_specs, less_than_strict_specs)
    # sort less-than constraints in the following way: ["<1.0", "<=1.0", "<2.0", "<=2.0"]
    # the first element is the strictest constraint.
    sorted_less_than_specs = sorted(
        less_than_specs, key=lambda x: (Version(x.version), len(x.operator))
    )
    lowest_less_than = (
        sorted_less_than_specs[0] if len(sorted_less_than_specs) > 0 else None
    )

    # group all the ">" or ">=" together
    # simplify: the spec with the greatest version number is the strictest constraint
    greater_than_strict_specs = operator_to_specifiers[">"]
    greater_than_equal_specs = operator_to_specifiers[">="]
    greater_than_specs = set.union(greater_than_strict_specs, greater_than_equal_specs)
    # sort greater-than constraints in the following way: [">=1.0", ">1.0", ">=2.0", ">2.0"]
    # the last element is the strictest constraint.
    sorted_greater_than_specs = sorted(
        greater_than_specs, key=lambda x: (Version(x.version), -len(x.operator))
    )
    greatest_greater_than = (
        sorted_greater_than_specs[-1] if len(sorted_greater_than_specs) > 0 else None
    )

    # if there exist two range constraints, check satisfiability.
    # otherwise, we can't say much.
    if lowest_less_than is not None and greatest_greater_than is not None:
        return _handle_range_constraints(lowest_less_than, greatest_greater_than)

    return True


def _handle_range_constraints(
    lowest_less_than: Specifier, greatest_greater_than: Specifier
) -> bool:
    """
    Helper method for the _is_satisfiable function.

    It checks whether two specifiers of the following type are compatible:
    - "<=<some-version-number>"
    - ">=<some-version-number>"

    The equality might be optional.

    The pseudo-code is the following:
    - is the version number of the lower-than constraint smaller than the one of
      the greater-than constraint? E.g. we are in cases like "<=1.0" and ">1.1".
      -  If yes, then the constraints are unsatisfiable.
      -  Otherwise, they are satisfiable.
    - are the version numbers the same? E.g. "<=1.0,>=1.0"
      - If yes, if at least one of them is a strict comparison, then return False, otherwise True.
    - otherwise, return True.

    :param lowest_less_than: the less-than constraint.
    :param greatest_greater_than: the greater than constraint.
    :return: False if we are sure the two constraints are not satisfiable, True if we don't know.
    """
    version_less_than = Version(lowest_less_than.version)
    version_greater_than = Version(greatest_greater_than.version)
    if version_less_than < version_greater_than:
        return False
    elif version_greater_than == version_less_than:
        # check if one of them has NOT the equality
        one_of_them_is_a_strict_comparison = (
            greatest_greater_than.operator == ">"
        ) or (lowest_less_than.operator == "<")
        return not one_of_them_is_a_strict_comparison
    else:
        return True


class PyPIChecker:
    """
    Find out if PyPI version specifiers are unsatisfiable.

    Its usage is incremental: you keep an instance of the
    checker and you populate with new constraints.
    """

    def __init__(self):
        """Initialize the checker."""
        # mapping from package name to specifier set.
        self._pypi_dependencies = {}  # type: Dict[str, SpecifierSet]

    def add(self, package_name: str, specifier_set: SpecifierSet):
        """
        Add a specifier set for a package in the checker.

        :param package_name: the package name
        :param specifier_set: the set of specifiers.
        :return: None
        :raises ValueError: if the set of specifier plus the one already present
            is surely unsatisfiable.
        """
        specifier = self._merge_with_existing_specifier_set_if_any(
            package_name, specifier_set
        )

        try:
            result = _is_satisfiable(specifier)
        except Exception:
            # we ignore possible errors. There might be some corner cases that make
            # our checks to raise exception, e.g. requirements like git+https://...
            result = True

        if result is False:
            raise ValueError(
                "Specifier set {} for package {} not satisfiable.".format(
                    specifier_set, package_name
                )
            )
        self._pypi_dependencies[package_name] = specifier_set

    def _add_or_merge_with_existing_specifier_set(
        self, package_name: str, specifier_set: SpecifierSet
    ) -> None:
        """
        Add a new package/specifier set pair, or, if one already exists, merge
        the new specifier with the old one.

        :param package_name: the package name
        :param specifier_set: the specifier set
        :return: None
        """
        if package_name in self._pypi_dependencies:
            previous_spec = self._pypi_dependencies[package_name]
            new_spec = operator.and_(previous_spec, specifier_set)
            self._pypi_dependencies[package_name] = new_spec
        else:
            self._pypi_dependencies[package_name] = specifier_set

    def _merge_with_existing_specifier_set_if_any(
        self, package_name: str, new_specifier_set: SpecifierSet
    ) -> SpecifierSet:
        """
        If a package name is already registered, take the associated specifier set
        and merge with the new one.
        Otherwise, return the new one.

        :param package_name: the package name
        :param new_specifier_set: the new specifier set.
        :return: the merged specifier set, or only the new one.
        """
        if package_name in self._pypi_dependencies:
            old_set = self._pypi_dependencies[package_name]
            return and_(old_set, new_specifier_set)
        else:
            return new_specifier_set
