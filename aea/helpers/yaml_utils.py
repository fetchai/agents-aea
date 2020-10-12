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
from collections import OrderedDict
from typing import Any, Callable, Dict, List, TextIO

import yaml


def _ordered_loading(fun: Callable):
    # for pydocstyle
    def ordered_load(stream: TextIO):
        object_pairs_hook = OrderedDict

        class OrderedLoader(yaml.SafeLoader):
            """A wrapper for safe yaml loader."""

            pass

        def construct_mapping(loader, node):
            loader.flatten_mapping(node)
            return object_pairs_hook(loader.construct_pairs(node))

        OrderedLoader.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping
        )
        return fun(stream, Loader=OrderedLoader)  # nosec

    return ordered_load


def _ordered_dumping(fun: Callable):
    # for pydocstyle
    def ordered_dump(data, stream=None, **kwds):
        class OrderedDumper(yaml.SafeDumper):
            """A wrapper for safe yaml loader."""

            pass

        def _dict_representer(dumper, data):
            return dumper.represent_mapping(
                yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, data.items()
            )

        OrderedDumper.add_representer(OrderedDict, _dict_representer)
        return fun(data, stream, Dumper=OrderedDumper, **kwds)  # nosec

    return ordered_dump


@_ordered_loading
def yaml_load(*args, **kwargs) -> Dict[str, Any]:
    """
    Load a yaml from a file pointer in an ordered way.

    :return: the yaml
    """
    return yaml.load(*args, **kwargs)  # nosec


@_ordered_loading
def yaml_load_all(*args, **kwargs) -> List[Dict[str, Any]]:
    """
    Load a multi-paged yaml from a file pointer in an ordered way.

    :return: the yaml
    """
    return list(yaml.load_all(*args, **kwargs))  # nosec


@_ordered_dumping
def yaml_dump(*args, **kwargs) -> None:
    """
    Dump multi-paged yaml data to a yaml file in an ordered way.

    :return None
    """
    yaml.dump(*args, **kwargs)  # nosec


@_ordered_dumping
def yaml_dump_all(*args, **kwargs) -> None:
    """
    Dump multi-paged yaml data to a yaml file in an ordered way.

    :return None
    """
    yaml.dump_all(*args, **kwargs)  # nosec
