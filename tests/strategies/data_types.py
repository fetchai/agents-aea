# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""Hypothesis strategies for data types."""

import collections
import re

import semver
from hypothesis import strategies as st
from packaging.specifiers import Specifier, SpecifierSet

from aea.configurations.data_types import (
    ComponentId,
    ComponentType,
    Dependency,
    GitRef,
    PackageId,
    PackageType,
    PackageVersion,
    PublicId,
    PyPIPackageName,
)
from aea.helpers.base import IPFSHash, SimpleId


positive_integer_strategy = st.integers(min_value=0)
user_string_pattern = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]{0,127}")
user_string_strategy = st.from_regex(user_string_pattern, fullmatch=True)
simple_id_strategy = st.from_regex(SimpleId.REGEX, fullmatch=True)
ipfs_hash_strategy = st.from_regex(IPFSHash.REGEX, fullmatch=True)
pypi_package_name_strategy = st.from_regex(PyPIPackageName.REGEX, fullmatch=True)
gitref_strategy = st.from_regex(GitRef.REGEX, fullmatch=True)
specifier_strategy = st.from_regex(Specifier._regex, fullmatch=True)


st.register_type_strategy(collections.UserString, user_string_strategy)
st.register_type_strategy(SimpleId, simple_id_strategy)
st.register_type_strategy(IPFSHash, ipfs_hash_strategy)
st.register_type_strategy(PyPIPackageName, pypi_package_name_strategy)
st.register_type_strategy(GitRef, gitref_strategy)
st.register_type_strategy(Specifier, specifier_strategy)


version_info_strategy = st.builds(
    lambda kwargs: semver.VersionInfo(**kwargs),
    st.fixed_dictionaries(
        dict(
            major=positive_integer_strategy,
            minor=positive_integer_strategy,
            patch=positive_integer_strategy,
        ),
    ),
)
st.register_type_strategy(semver.VersionInfo, version_info_strategy)


package_version_strategy = st.builds(
    lambda kwargs: PackageVersion(**kwargs),
    st.fixed_dictionaries(dict(version_like=version_info_strategy)),
)
st.register_type_strategy(PackageVersion, package_version_strategy)


s = st.fixed_dictionaries(
    dict(
        author=st.from_type(SimpleId),
        name=st.from_type(SimpleId),
        version=st.from_type(semver.VersionInfo),
        package_hash=st.from_type(IPFSHash),
    )
)
public_id_strategy = st.builds(lambda kwargs: PublicId(**kwargs), s)
st.register_type_strategy(PublicId, public_id_strategy)


s = st.fixed_dictionaries(
    dict(
        package_type=st.from_type(PackageType),
        public_id=st.from_type(PublicId),
    )
)
package_id_strategy = st.builds(lambda kwargs: PackageId(**kwargs), s)
st.register_type_strategy(PackageId, package_id_strategy)


s = st.fixed_dictionaries(
    dict(
        component_type=st.from_type(ComponentType),
        public_id=st.from_type(PublicId),
    )
)
component_id_strategy = st.builds(lambda kwargs: ComponentId(**kwargs), s)
st.register_type_strategy(ComponentId, component_id_strategy)


specifier_set_strategy = st.builds(
    lambda ss: ",".join(ss), st.lists(specifier_strategy)
)
s = st.fixed_dictionaries(dict(specifiers=specifier_set_strategy))
specifier_set_strategy = st.builds(lambda kwargs: SpecifierSet(**kwargs), s)
st.register_type_strategy(SpecifierSet, specifier_set_strategy)


s = st.fixed_dictionaries(
    dict(
        name=st.from_type(PyPIPackageName),
        version=st.from_type(SpecifierSet),
        index=st.text(),
        git=st.text(),
        ref=st.from_type(GitRef),
    )
)
dependency_strategy = st.builds(lambda kwargs: Dependency(**kwargs), s)
st.register_type_strategy(Dependency, dependency_strategy)


del s  # clean-up namespace
