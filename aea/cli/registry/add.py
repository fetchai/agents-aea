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
"""Registry utils used for CLI add command."""

import os
from pathlib import Path
from typing import cast

from aea.cli.registry.utils import download_file, extract, get_package_meta
from aea.cli.utils.loggers import logger
from aea.configurations.base import PublicId


def fetch_package(obj_type: str, public_id: PublicId, cwd: str, dest: str) -> Path:
    """
    Fetch a package (connection/contract/protocol/skill) from Registry.

    :param obj_type: str type of object you want to fetch:
        'connection', 'protocol', 'skill'
    :param public_id: str public ID of object.
    :param cwd: str path to current working directory.
    :param dest: destination where to save package.

    :return: package path
    """
    logger.debug(
        "Fetching {obj_type} {public_id} from Registry...".format(
            public_id=public_id, obj_type=obj_type
        )
    )

    logger.debug(
        "Downloading {obj_type} {public_id}...".format(
            public_id=public_id, obj_type=obj_type
        )
    )
    package_meta = get_package_meta(obj_type, public_id)
    file_url = cast(str, package_meta["file"])
    filepath = download_file(file_url, cwd)

    # next code line is needed because the items are stored in tarball packages as folders
    dest = os.path.split(dest)[0]
    logger.debug(
        "Extracting {obj_type} {public_id}...".format(
            public_id=public_id, obj_type=obj_type
        )
    )
    extract(filepath, dest)
    logger.debug(
        "Successfully fetched {obj_type} '{public_id}'.".format(
            public_id=public_id, obj_type=obj_type
        )
    )
    package_path = os.path.join(dest, public_id.name)
    return Path(package_path)
