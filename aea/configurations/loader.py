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

"""Implementation of the parser for configuration file."""

import inspect
import json
import os
import re
from pathlib import Path
from typing import TextIO, Type, TypeVar, Generic

import jsonschema
import python_jsonschema_objects as pjs
import yaml
from jsonschema import Draft7Validator

_CUR_DIR = os.path.dirname(inspect.getfile(inspect.currentframe()))  # type: ignore
_SCHEMAS_DIR = os.path.join(_CUR_DIR, "schemas")

definitions = json.load(open(str(Path(_SCHEMAS_DIR, "definitions.json"))))
store = {
    "definitions.json": definitions
}

T = TypeVar('T')


class ConfigLoader(Generic[T]):
    """This class implement parsing, serialization and validation functionalities for the 'aea' configuration files."""

    def __init__(self, schema_filename: str, configuration_type: Type[T]):
        """Initialize the parser for configuration files."""
        self.schema = json.load(open(os.path.join(_SCHEMAS_DIR, schema_filename)))
        self.resolver = jsonschema.RefResolver("SkillConfigurationSchema", self.schema, store=store)
        self.validator = Draft7Validator(self.schema, resolver=self.resolver)
        self.configuration_type = configuration_type  # type: Type[T]

        self.builder = pjs.ObjectBuilder(self.schema, resolver=self.resolver)
        self.ns = self.builder.build_classes()
        # get the class of the 'root' schema
        # the name of the class should contain 'ConfigurationSchema' -> see the "$id" field in the schemas
        config_class_names = list(filter(
            lambda x: re.match("|".join(["{}ConfigurationSchema".format(s)
                                         for s in ["Protocol", "Connection", "Skill", "Agent"]]),
                               x),
            dir(self.ns)))
        assert len(config_class_names) == 1
        self.config_class = getattr(self.ns, config_class_names[0])  # type: Type

    def load(self, fp: TextIO) -> T:
        """
        Load an agent configuration file.

        :param fp: the file pointer to the configuration file
        :return: the configuration object.
        :raises
        """
        configuration_file_json = yaml.safe_load(fp)
        self.validator.validate(instance=configuration_file_json)

        configuration_obj = self.config_class(**configuration_file_json)

        # just compatibility with the Configuration abs class.
        configuration_obj.__dict__["json"] = configuration_obj.for_json()

        return configuration_obj

    def dump(self, configuration: T, fp: TextIO) -> None:
        """Dump a configuration.

        :param configuration: the configuration to be dumped.
        :param fp: the file pointer to the configuration file
        :return: None
        """
        result = configuration.for_json()
        self.validator.validate(instance=result)
        yaml.safe_dump(result, fp)
