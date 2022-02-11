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
"""Helper functions related to YAML loading/dumping."""
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Sequence, TextIO

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

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the AEAYamlLoader.

        It adds a YAML Loader constructor to use 'OderedDict' to load the files.

        :param args: the positional arguments.
        :param kwargs: the keyword arguments.
        """
        super().__init__(*args, **kwargs)
        _AEAYamlLoader.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, self._construct_mapping
        )

    @staticmethod
    def _construct_mapping(loader: "_AEAYamlLoader", node: MappingNode) -> OrderedDict:
        """Construct a YAML mapping with OrderedDict."""
        object_pairs_hook = OrderedDict
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))


class _AEAYamlDumper(yaml.SafeDumper):
    """
    Custom yaml.SafeDumper for the AEA framework.

    It extends the default SafeDumper so to dump
    YAML configurations while *following the order of the fields*.

    This class is for internal usage only; please use
    the public functions of the module 'yaml_dump' and 'yaml_dump_all'.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the AEAYamlDumper.

        It adds a YAML Dumper representer to use 'OderedDict' to dump the files.

        :param args: the positional arguments.
        :param kwargs: the keyword arguments.
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
    result = yaml.load(stream, Loader=_AEAYamlLoader)  # nosec
    return result if result is not None else {}


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
    """
    yaml.dump(data, stream=stream, Dumper=_AEAYamlDumper)  # nosec


def yaml_dump_all(data: Sequence[Dict], stream: Optional[TextIO] = None) -> None:
    """
    Dump YAML data to a yaml file in an ordered way.

    :param data: the data to write.
    :param stream: (optional) the file to write on.
    """
    yaml.dump_all(data, stream=stream, Dumper=_AEAYamlDumper)  # nosec
