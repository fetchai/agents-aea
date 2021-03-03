# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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
"""This module contains the tests for the yaml utils module."""
import io
import random
import string
from collections import OrderedDict

from aea.helpers.yaml_utils import (
    _AEAYamlLoader,
    yaml_dump,
    yaml_dump_all,
    yaml_load,
    yaml_load_all,
)


def test_yaml_dump_load():
    """Test yaml dump/load works."""
    data = OrderedDict({"a": 12, "b": None})
    stream = io.StringIO()
    yaml_dump(data, stream)
    stream.seek(0)
    loaded_data = yaml_load(stream)
    assert loaded_data == data


def test_yaml_dump_all_load_all():
    """Test yaml_dump_all and yaml_load_all."""
    f = io.StringIO()
    data = [{"a": "12"}, {"b": "13"}]
    yaml_dump_all(data, f)

    f.seek(0)
    assert yaml_load_all(f) == data


def test_instantiate_loader_twice():
    """Test that instantiating the AEA YAML loader twice doesn't add twice implicit resolvers."""
    loader = _AEAYamlLoader(io.StringIO())
    old_length = len(loader.yaml_implicit_resolvers)
    loader = _AEAYamlLoader(io.StringIO())
    assert len(loader.yaml_implicit_resolvers) == old_length


def _generate_random_string(n: int = 100):
    return "".join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(n)  # nosec
    )
