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

"""Helper functions related to YAML loading/dumping."""
import os
import re
from collections import OrderedDict
from typing import Any, Dict, List, Match, Optional, Sequence, TextIO, cast

import yaml
from yaml import MappingNode


class _AEAYamlLoader(yaml.SafeLoader):
    """
    Custom yaml.SafeLoader for the AEA framework.

    It extends the default SafeLoader in two ways:
    - loads YAML configurations while *remembering the order of the fields*;
    - resolves the environment variables at loading time.

    This class is for internal usage only; please use
    the public functions of the module 'yaml_load' and 'yaml_load_all'.
    """

    envvar_matcher = re.compile(r"\${([^}^{]+)\}")
    envvar_key = "!envvar"

    def __init__(self, *args, **kwargs):
        """
        Initialize the AEAYamlLoader.

        It adds a YAML Loader constructor to use 'OderedDict' to load the files.
        """
        super().__init__(*args, **kwargs)
        _AEAYamlLoader.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, self._construct_mapping
        )
        _AEAYamlLoader.add_constructor(self.envvar_key, self._envvar_constructor)
        self._add_implicit_resolver_if_not_present_already()

    def _add_implicit_resolver_if_not_present_already(self) -> None:
        """Add implicit resolver for environment variables, if not present already."""
        if self.envvar_key not in dict(self.yaml_implicit_resolvers.get(None, [])):
            _AEAYamlLoader.add_implicit_resolver(
                self.envvar_key, self.envvar_matcher, None
            )

    @staticmethod
    def _construct_mapping(loader: "_AEAYamlLoader", node: MappingNode):
        """Construct a YAML mapping with OrderedDict."""
        object_pairs_hook = OrderedDict
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))

    @staticmethod
    def _envvar_constructor(_loader: "_AEAYamlLoader", node: MappingNode) -> str:
        """Extract the matched value, expand env variable, and replace the match."""
        node_value = node.value
        match = _AEAYamlLoader.envvar_matcher.match(node_value)
        match = cast(Match[str], match)
        env_var = match.group()[2:-1]

        # check for defaults
        var_split = env_var.split(":")
        if len(var_split) == 2:
            var_name, default_value = var_split
        elif len(var_split) == 1:
            var_name, default_value = var_split[0], ""
        else:
            raise ValueError(f"Cannot resolve environment variable '{env_var}'.")
        var_name = var_name.strip()
        default_value = default_value.strip()
        var_value = os.getenv(var_name, default_value)
        return var_value + node_value[match.end() :]


class _AEAYamlDumper(yaml.SafeDumper):
    """
    Custom yaml.SafeDumper for the AEA framework.

    It extends the default SafeDumper so to dump
    YAML configurations while *following the order of the fields*.

    This class is for internal usage only; please use
    the public functions of the module 'yaml_dump' and 'yaml_dump_all'.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the AEAYamlDumper.

        It adds a YAML Dumper representer to use 'OderedDict' to dump the files.
        """
        super().__init__(*args, **kwargs)
        _AEAYamlDumper.add_representer(OrderedDict, self._dict_representer)

    @staticmethod
    def _dict_representer(dumper: "_AEAYamlDumper", data: OrderedDict) -> MappingNode:
        """Use a custom representer."""
        return dumper.represent_mapping(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, data.items()
        )


def yaml_load(stream: TextIO) -> Dict[str, Any]:
    """
    Load a yaml from a file pointer in an ordered way.

    :param stream: file pointer to the input file.
    :return: the dictionary object with the YAML file content.
    """
    return yaml.load(stream, Loader=_AEAYamlLoader)  # nosec


def yaml_load_all(stream: TextIO) -> List[Dict[str, Any]]:
    """
    Load a multi-paged yaml from a file pointer in an ordered way.

    :param stream: file pointer to the input file.
    :return: the list of dictionary objects with the (multi-paged) YAML file content.
    """
    return list(yaml.load_all(stream, Loader=_AEAYamlLoader))  # nosec


def yaml_dump(data: Dict, stream: Optional[TextIO] = None) -> None:
    """
    Dump YAML data to a yaml file in an ordered way.

    :param data: the data to write.
    :param stream: (optional) the file to write on.
    :return: None
    """
    yaml.dump(data, stream=stream, Dumper=_AEAYamlDumper)  # nosec


def yaml_dump_all(data: Sequence[Dict], stream: Optional[TextIO] = None) -> None:
    """
    Dump YAML data to a yaml file in an ordered way.

    :param data: the data to write.
    :param stream: (optional) the file to write on.
    :return: None
    """
    yaml.dump_all(data, stream=stream, Dumper=_AEAYamlDumper)  # nosec
