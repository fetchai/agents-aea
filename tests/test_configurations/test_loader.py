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

"""This module contains the tests for the aea.configurations.loader module."""
import os
from pathlib import Path
from unittest import mock

import pytest

from aea.configurations.base import PackageType
from aea.configurations.loader import ConfigLoader, make_jsonschema_base_uri
from aea.protocols.generator.common import load_protocol_specification

from tests.conftest import protocol_specification_files


@pytest.mark.parametrize("system", ["nt", "posix"])
def test_windows_uri_path(system):
    """Test windows uri path."""
    dir = Path("aea", "configurations").absolute()
    with mock.patch.object(os, "name", system):
        output = make_jsonschema_base_uri(dir)

    if system == "nt":
        assert output == f"file:///{'/'.join(dir.parts)}/"
    else:
        assert output == f"file:/{'/'.join(dir.parts)}/"


def test_config_loader_get_required_fields():
    """Test required fields of ConfigLoader."""
    config_loader = ConfigLoader.from_configuration_type(PackageType.PROTOCOL)
    config_loader.required_fields


@pytest.mark.parametrize("spec_file_path", protocol_specification_files)
def test_load_protocol_specification(spec_file_path):
    """Test for the utility function 'load_protocol_specification'"""
    load_protocol_specification(spec_file_path)
