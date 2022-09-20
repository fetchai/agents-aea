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

"""This module contains a checker for PyPI version consistency."""
import operator
from collections import defaultdict
from copy import deepcopy
from functools import reduce
from typing import Dict, List, Set, cast

from packaging.specifiers import Specifier, SpecifierSet
from packaging.version import InvalidVersion, Version

from aea.configurations.base import Dependencies, Dependency


def and_(s1: SpecifierSet, s2: SpecifierSet) -> SpecifierSet:
    """Do the and between two specifier sets."""
    return operator.and_(s1, s2)


def _handle_compatibility_operator(
    all_specifiers: List[Specifier],
    operator_to_specifiers: Dict[str, Set[Specifier]],
    specifier: Specifier,
) -> None:
    """
    Handle a specifier with operator '~='.

    Split specifier of the form "~=<major.minor>" in two specifiers:
    - >= <major.minor>
    - < <major+1>
    Also handle micro-numbers, i.e. "~=<major.minor.micro>"
    (see last examples of https://www.python.org/dev/peps/pep-0440/#compatible-release)

    :param all_specifiers: the list of all specifiers (to be populated).
    :param operator_to_specifiers: a mapping from operator to specifiers (to be populated).
    :param specifier: the specifier to process.
    """
    spec_version = Version(specifier.version)
    base_version = spec_version.base_version
    parts = base_version.split(".")
    index_to_update = -2
    if (
        spec_version.is_prerelease
        or spec_version.is_devrelease
        or spec_version.is_postrelease
    ):
        # if it is a pre-release, ignore the suffix.
        index_to_update += 1
        parts = parts[:-1]
    # bump second-to-last part
    parts[index_to_update] = str(int(parts[index_to_update]) + 1)
    upper_version = Version(".".join(parts))
    spec_1 = Specifier(">=" + str(spec_version))
    spec_2 = Specifier("<" + str(upper_version))
    all_specifiers.extend([spec_1, spec_2])
    operator_to_specifiers[spec_1.operator].add(spec_1)
    operator_to_specifiers[spec_2.operator].add(spec_2)


def is_satisfiable(specifier_set: SpecifierSet) -> bool:
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
    >>> is_satisfiable(s1)
    True

    The specifier set "==1.0, >1.1" is not satisfiable:

    >>> s1 = SpecifierSet("==1.0,>1.1")
    >>> is_satisfiable(s1)
    False

    For other details, please refer to PEP440:

        https://www.python.org/dev/peps/pep-0440

    :param specifier_set: the specifier set.
    :return: False if the constraints are surely non-satisfiable, True if we don't know.
    """
    # group single specifiers by operator
    all_specifiers: List[Specifier] = []
    operator_to_specifiers: Dict[str, Set[Specifier]] = defaultdict(set)
    # pre-processing
    for specifier in list(specifier_set):
        specifier = cast(Specifier, specifier)
        try:
            # if we can't parse the version number, ignore that specifier.
            # Even if it follows a legacy version format (e.g. "2.*")
            Version(specifier.version)
        except InvalidVersion:
            continue

        # handle specifiers with '~=' operators.
        if specifier.operator == "~=":
            _handle_compatibility_operator(
                all_specifiers, operator_to_specifiers, specifier
            )
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

    # group all the ">" or ">=" together. They are interpreted as conjunction.
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
    Check whether two specifiers of the following type are compatible.

    It is a helper method for the is_satisfiable function and checks:
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
    if version_greater_than == version_less_than:
        # check if one of them has NOT the equality
        one_of_them_is_a_strict_comparison = (
            greatest_greater_than.operator == ">"
        ) or (lowest_less_than.operator == "<")
        return not one_of_them_is_a_strict_comparison
    return True


def is_simple_dep(dep: Dependency) -> bool:
    """
    Check if it is a simple dependency.

    Namely, if it has no field specified, or only the 'version' field set.

    :param dep: the dependency
    :return: whether it is a simple dependency or not
    """
    return dep.index is None and dep.git is None


def to_set_specifier(dep: Dependency) -> SpecifierSet:
    """Get the set specifier. It assumes to be a simple dependency (see above)."""
    return SpecifierSet(dep.version)


def merge_dependencies(dep1: Dependencies, dep2: Dependencies) -> Dependencies:
    """
    Merge two groups of dependencies.

    If some of them are not "simple" (see above), and there is no risk
      of conflict because there is no other package with the same name,
      we leave them; otherwise we raise an error.

    :param dep1: the first operand
    :param dep2: the second operand.
    :return: the merged dependencies.
    """
    result: Dependencies
    result = deepcopy(dep1)

    for pkg_name, info in dep2.items():
        old_dep = result.get(pkg_name)
        old_dep_exists = old_dep is not None
        new_dep_is_simple = is_simple_dep(info)
        old_dep_is_simple = is_simple_dep(info) if old_dep_exists else False

        # if the new dependency already exists in the list, ignore
        if old_dep == info:
            continue
        # if one of the operands does not have a dependency,
        # we add it untouched to the final result and continue
        if not old_dep_exists:
            result[pkg_name] = info
            continue

        # in case a dependency exists in both operands and one of them is not simple:
        if (new_dep_is_simple and old_dep_exists and not old_dep_is_simple) or (
            not new_dep_is_simple and old_dep_exists
        ):
            # we raise error because we can't trivially merge the specifier sets (unless they are equal, see above)
            raise ValueError(
                f"cannot trivially merge these two PyPI dependencies:\n- {pkg_name}: {old_dep}\n- {pkg_name}: {info}"
            )

        # if we are here, it means both in the first and second operand
        # there are two 'simple' dependencies with the same name
        # therefore, we need to merge them
        new_specifier = SpecifierSet(info.version)
        old_specifier = (
            SpecifierSet(result[pkg_name].version)
            if pkg_name in result
            else SpecifierSet("")
        )
        combined_specifier = and_(new_specifier, old_specifier)
        new_info = Dependency(
            name=info.name,
            version=combined_specifier,
            index=info.index,
            git=info.git,
            ref=info.ref,
        )
        result[pkg_name] = new_info

    return result


def merge_dependencies_list(*deps: Dependencies) -> Dependencies:
    """
    Merge a list of dependencies.

    :param deps: the list of dependencies
    :return: the merged dependencies.
    """
    result: Dependencies = reduce(merge_dependencies, deps, {})
    return result
