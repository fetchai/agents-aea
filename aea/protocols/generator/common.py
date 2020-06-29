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
"""This module contains utility code for generator modules."""

import os
import re
import shutil
import subprocess  # nosec
import sys
from typing import Tuple

from aea.configurations.base import ProtocolSpecification
from aea.configurations.loader import ConfigLoader

SPECIFICATION_PRIMITIVE_TYPES = ["pt:bytes", "pt:int", "pt:float", "pt:bool", "pt:str"]


def _get_sub_types_of_compositional_types(compositional_type: str) -> tuple:
    """
    Extract the sub-types of compositional types.

    This method handles both specification types (e.g. pt:set[], pt:dict[]) as well as python types (e.g. FrozenSet[], Union[]).

    :param compositional_type: the compositional type string whose sub-types are to be extracted.
    :return: tuple containing all extracted sub-types.
    """
    sub_types_list = list()
    if compositional_type.startswith("Optional") or compositional_type.startswith(
        "pt:optional"
    ):
        sub_type1 = compositional_type[
            compositional_type.index("[") + 1 : compositional_type.rindex("]")
        ].strip()
        sub_types_list.append(sub_type1)
    if (
        compositional_type.startswith("FrozenSet")
        or compositional_type.startswith("pt:set")
        or compositional_type.startswith("pt:list")
    ):
        sub_type1 = compositional_type[
            compositional_type.index("[") + 1 : compositional_type.rindex("]")
        ].strip()
        sub_types_list.append(sub_type1)
    if compositional_type.startswith("Tuple"):
        sub_type1 = compositional_type[
            compositional_type.index("[") + 1 : compositional_type.rindex("]")
        ].strip()
        sub_type1 = sub_type1[:-5]
        sub_types_list.append(sub_type1)
    if compositional_type.startswith("Dict") or compositional_type.startswith(
        "pt:dict"
    ):
        sub_type1 = compositional_type[
            compositional_type.index("[") + 1 : compositional_type.index(",")
        ].strip()
        sub_type2 = compositional_type[
            compositional_type.index(",") + 1 : compositional_type.rindex("]")
        ].strip()
        sub_types_list.extend([sub_type1, sub_type2])
    if compositional_type.startswith("Union") or compositional_type.startswith(
        "pt:union"
    ):
        inside_union = compositional_type[
            compositional_type.index("[") + 1 : compositional_type.rindex("]")
        ].strip()
        while inside_union != "":
            if inside_union.startswith("Dict") or inside_union.startswith("pt:dict"):
                sub_type = inside_union[: inside_union.index("]") + 1].strip()
                rest_of_inside_union = inside_union[
                    inside_union.index("]") + 1 :
                ].strip()
                if rest_of_inside_union.find(",") == -1:
                    # it is the last sub-type
                    inside_union = rest_of_inside_union.strip()
                else:
                    # it is not the last sub-type
                    inside_union = rest_of_inside_union[
                        rest_of_inside_union.index(",") + 1 :
                    ].strip()
            elif inside_union.startswith("Tuple"):
                sub_type = inside_union[: inside_union.index("]") + 1].strip()
                rest_of_inside_union = inside_union[
                    inside_union.index("]") + 1 :
                ].strip()
                if rest_of_inside_union.find(",") == -1:
                    # it is the last sub-type
                    inside_union = rest_of_inside_union.strip()
                else:
                    # it is not the last sub-type
                    inside_union = rest_of_inside_union[
                        rest_of_inside_union.index(",") + 1 :
                    ].strip()
            else:
                if inside_union.find(",") == -1:
                    # it is the last sub-type
                    sub_type = inside_union.strip()
                    inside_union = ""
                else:
                    # it is not the last sub-type
                    sub_type = inside_union[: inside_union.index(",")].strip()
                    inside_union = inside_union[inside_union.index(",") + 1 :].strip()
            sub_types_list.append(sub_type)
    return tuple(sub_types_list)


def is_installed(programme: str) -> bool:
    """
    Check whether a programme is installed on the system.

    :param programme: the name of the programme.
    :return: True if installed, False otherwise
    """
    res = shutil.which(programme)
    if res is None:
        return False
    else:
        return True


def check_prerequisites() -> None:
    """
    Check whether a programme is installed on the system.

    :return: None
    """
    # check protocol buffer compiler is installed
    if not is_installed("black"):
        raise FileNotFoundError(
            "Cannot find black code formatter! To install, please follow this link: https://black.readthedocs.io/en/stable/installation_and_usage.html"
        )

    # check black code formatter is installed
    if not is_installed("protoc"):
        raise FileNotFoundError(
            "Cannot find protocol buffer compiler! To install, please follow this link: https://developers.google.com/protocol-buffers/"
        )


def load_protocol_specification(specification_path: str) -> ProtocolSpecification:
    """
    Load a protocol specification.

    :param specification_path: path to the protocol specification yaml file.
    :return: A ProtocolSpecification object
    """
    config_loader = ConfigLoader(
        "protocol-specification_schema.json", ProtocolSpecification
    )
    protocol_spec = config_loader.load_protocol_specification(open(specification_path))
    return protocol_spec


def _create_protocol_file(
    path_to_protocol_package: str, file_name: str, file_content: str
) -> None:
    """
    Create a file in the generated protocol package.

    :param path_to_protocol_package: path to the file
    :param file_name: the name of the file
    :param file_content: the content of the file

    :return: None
    """
    pathname = os.path.join(path_to_protocol_package, file_name)

    with open(pathname, "w") as file:
        file.write(file_content)


def try_run_black_formatting(path_to_protocol_package: str) -> None:
    """
    Run Black code formatting via subprocess.

    :param path_to_protocol_package: a path where formatting should be applied.
    :return: None
    """
    try:
        subprocess.run(  # nosec
            [sys.executable, "-m", "black", path_to_protocol_package, "--quiet"],
            check=True,
        )
    except Exception:
        raise


def try_run_protoc(path_to_generated_protocol_package, name) -> None:
    """
    Run 'protoc' protocol buffer compiler via subprocess.

    :param path_to_generated_protocol_package: path to the protocol buffer schema file.
    :param name: name of the protocol buffer schema file.

    :return: A completed process object.
    """
    try:
        # command: "protoc -I={} --python_out={} {}/{}.proto"
        subprocess.run(  # nosec
            [
                "protoc",
                "-I={}".format(path_to_generated_protocol_package),
                "--python_out={}".format(path_to_generated_protocol_package),
                "{}/{}.proto".format(path_to_generated_protocol_package, name),
            ],
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=True,
            env=os.environ.copy(),
        )
    except Exception:
        raise


def check_protobuf_using_protoc(
    path_to_generated_protocol_package, name
) -> Tuple[bool, str]:
    """
    Check whether a protocol buffer schema file is valid.

    Validation is via trying to compile the schema file. If successfully compiled it is valid, otherwise invalid.
    If valid, return True and a 'protobuf file is valid' message, otherwise return False and the error thrown by the compiler.

    :param path_to_generated_protocol_package: path to the protocol buffer schema file.
    :param name: name of the protocol buffer schema file.

    :return: Boolean result and an accompanying message
    """
    try:
        try_run_protoc(path_to_generated_protocol_package, name)
        os.remove(os.path.join(path_to_generated_protocol_package, name + "_pb2.py"))
        return True, "protobuf file is valid"
    except subprocess.CalledProcessError as e:
        pattern = name + ".proto:[0-9]+:[0-9]+: "
        error_message = re.sub(pattern, "", e.stderr[:-1])
        return False, error_message
    except Exception:
        raise
