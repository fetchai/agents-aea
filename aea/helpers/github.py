#!/usr/bin/env python3
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

"""Fetch folders from Github URLs. Borrows from https://github.com/sdushantha/gitdir/blob/master/gitdir/gitdir.py"""

import json
import logging
import os
import re
import urllib.request
from typing import Optional, Tuple


_default_logger = logging.getLogger(__name__)


def _create_url(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    From the given url, produce a URL that is compatible with Github's REST API. Can handle blob or tree paths.

    :param url: the url to download from.
    :return: tuple of api url and download urls
    """
    repo_only_url = re.compile(
        r"https:\/\/github\.com\/[a-z\d](?:[a-z\d]|-(?=[a-z\d])){0,38}\/[a-zA-Z0-9-]+/?$"
    )
    re_branch = re.compile("/(tree|blob)/(.+?)/")

    # Check if the given url is a url to a GitHub repo. If it is, tell the
    # user to use 'git clone' to download it
    if re.match(repo_only_url, url):
        _default_logger.warning(
            "The given URL is a complete repository. Use 'git clone' to download the repository."
        )
        return None, None

    # extract the branch name from the given url (e.g master)
    branch = re_branch.search(url)
    if branch is None:
        _default_logger.warning("Cannot extract branch from URL.")
        return None, None
    download_dirs = url[branch.end() :]
    api_url = (
        url[: branch.start()].replace("github.com", "api.github.com/repos", 1)
        + "/contents/"
        + download_dirs
        + "?ref="
        + branch.group(2)
    )
    return api_url, download_dirs


def download(repo_url: str, flatten: bool = False, output_dir: str = "./") -> int:
    """
    Downloads the files and directories in repo_url.

    If flatten is specified, the contents of any and all
    sub-directories will be pulled upwards into the root folder.

    :param repo_url: the repo url
    :param flatten: whether to flatten the folder
    :param output_dir: the output directory
    :return: count of files downloaded
    """
    # generate the url which returns the JSON data
    api_url, download_dirs = _create_url(repo_url)
    if api_url is None or download_dirs is None:
        return 0

    # To handle file names.
    if not flatten:
        if len(download_dirs.split(".")) == 0:
            dir_out = os.path.join(output_dir, download_dirs)
        else:
            dir_out = os.path.join(output_dir, "/".join(download_dirs.split("/")[:-1]))
    else:
        dir_out = output_dir

    try:
        opener = urllib.request.build_opener()
        opener.addheaders = [("User-agent", "Mozilla/5.0")]
        urllib.request.install_opener(opener)
        response = urllib.request.urlretrieve(api_url)  # nosec
    except KeyboardInterrupt:
        _default_logger.warning("Got interrupted")
        return 0

    if not flatten:
        # make a directory with the name which is taken from
        # the actual repo
        os.makedirs(dir_out, exist_ok=True)

    # total files count
    total_files = 0

    with open(response[0], "r") as f:
        data = json.load(f)
        # getting the total number of files so that we
        # can use it for the output information later
        total_files += len(data)

        # If the data is a file, download it as one.
        if isinstance(data, dict) and data["type"] == "file":
            try:
                # download the file
                opener = urllib.request.build_opener()
                opener.addheaders = [("User-agent", "Mozilla/5.0")]
                urllib.request.install_opener(opener)
                urllib.request.urlretrieve(  # nosec
                    data["download_url"], os.path.join(dir_out, data["name"])
                )
                _default_logger.info("Downloaded: {}".format(data["name"]))

                return total_files
            except KeyboardInterrupt:
                _default_logger.warning("Got interrupted")
                return total_files

        for file in data:
            file_url = file["download_url"]
            file_name = file["name"]

            if flatten:
                path = os.path.basename(file["path"])
            else:
                path = file["path"]
            dirname = os.path.dirname(path)

            if dirname != "":
                os.makedirs(os.path.dirname(path), exist_ok=True)
            else:
                pass

            if file_url is not None:
                try:
                    opener = urllib.request.build_opener()
                    opener.addheaders = [("User-agent", "Mozilla/5.0")]
                    urllib.request.install_opener(opener)
                    # download the file
                    urllib.request.urlretrieve(file_url, path)  # nosec
                    _default_logger.info("Downloaded: {}".format(file_name))

                except KeyboardInterrupt:
                    _default_logger.warning("Got interrupted")
                    return total_files

            else:
                download(file["html_url"], flatten, dir_out)

    return total_files
