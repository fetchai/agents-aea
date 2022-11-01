#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

"""Script to check that all internal doc links are valid."""
import re
import sys
import xml.etree.ElementTree as ET  # nosec
from pathlib import Path
from typing import Dict, List, Pattern, Set

import requests
import urllib3  # type: ignore
from requests.adapters import HTTPAdapter  # type: ignore
from requests.packages.urllib3.util.retry import (  # type: ignore # pylint: disable=import-error
    Retry,
)


LINK_PATTERN_MD = re.compile(r"\[([^]]+)]\(\s*([^]]+)\s*\)")
LINK_PATTERN = re.compile(r'(?<=<a href=")[^"]*')
IMAGE_PATTERN = re.compile(r'<img[^>]+src="([^">]+)"')
RELATIVE_PATH_STR = "../"
RELATIVE_PATH_STR_LEN = len(RELATIVE_PATH_STR)
INDEX_FILE_PATH = Path("docs/index.md")

# Special links that are allowed to respond with an error status
# Remove non-url-allowed characters like ` before adding them here
URL_SKIPS: List[str] = []

# Define here custom timeouts for some edge cases
CUSTOM_TIMEOUTS: Dict[str, int] = {}

DEFAULT_REQUEST_TIMEOUT = 5  # seconds

# Disable insecure request warning (expired SSL certificates)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure request retries
retry_strategy = Retry(
    total=3,  # number of retries
    status_forcelist=[404, 429, 500, 502, 503, 504],  # codes to retry on
)
# https://stackoverflow.com/questions/18466079/change-the-connection-pool-size-for-pythons-requests-module-when-in-threading
adapter = HTTPAdapter(
    max_retries=retry_strategy, pool_connections=100, pool_maxsize=100
)
session = requests.Session()
session.mount("https://", adapter)
session.mount("http://", adapter)


def is_url_reachable(url: str) -> bool:
    """
    Check if an url is reachable.

    :param url: the url to check
    :return: bool
    """
    if url.startswith("http://localhost") or url.startswith("http://127.0.0.1"):
        return True
    if url in URL_SKIPS:
        return True

    try:
        # Do not verify requests. Expired SSL certificates would make those links fail
        status_code = session.get(
            url,
            timeout=CUSTOM_TIMEOUTS.get(url, DEFAULT_REQUEST_TIMEOUT),
            verify=False,
        ).status_code
        if status_code not in (200, 403):
            return False
    except (
        requests.exceptions.RetryError,
        requests.exceptions.ConnectionError,
    ):
        return False

    return True


def check_header_in_file(header: str, file: Path) -> None:
    """
    Check if the string is present in the file.

    :param header: the header
    :param file: the file path
    """
    with open(file) as f:
        s = f.read()
        if header not in s:
            raise ValueError(
                "Header={} not found in file={}!".format(header, str(file))
            )


def validate_internal_url(file: Path, url: str, all_files: Set[Path]) -> None:
    """
    Validate whether the url is a valid path to a file in docs.

    :param file: the file path
    :param url: the url to check
    :param all_files: all the docs files.
    """
    is_index_file = file == INDEX_FILE_PATH

    if not url.startswith(RELATIVE_PATH_STR) and not is_index_file:
        raise ValueError("Invalid relative path={} in file={}!".format(url, str(file)))

    md_index = url.find(".md")
    if md_index != -1:
        raise ValueError(
            "Path={} contains invalid `.md` in file={}!".format(url, str(file))
        )

    hash_index = url.find("#")
    if hash_index == -1:
        n_url = url[RELATIVE_PATH_STR_LEN:] if not is_index_file else url
        n_url = n_url[:-1] if n_url[-1] == "/" else n_url
        path = Path("docs/{}.md".format(n_url))
        header = ""
    else:
        n_url = url[RELATIVE_PATH_STR_LEN:hash_index] if not is_index_file else url
        n_url = n_url[:-1] if n_url[-1] == "/" else n_url
        path = Path("docs/{}.md".format(n_url))
        header = url[hash_index:]

    if path not in all_files:
        raise ValueError(
            "Path={} found in file={} does not exist!".format(str(path), str(file))
        )

    if header != "":
        check_header_in_file(header, file)


def _checks_all_html(file: Path, regex: Pattern = LINK_PATTERN_MD) -> None:
    """
    Checks a file for matches to a pattern.

    :param file: the file path
    :param regex: the regex to check for in the file.
    """
    matches = regex.finditer(file.read_text())
    for _ in matches:
        raise ValueError("Markdown link found in file={}!".format(str(file)))


def is_external_url(url: str) -> bool:
    """
    Check if an URL is an external URL.

    :param url: the URL
    :return: true if it is external, false otherwise.
    """
    return url.startswith("https://") or url.startswith("http://")


def validate_external_url(url: str, file: Path) -> None:
    """
    Validate external URL.

    :param url: the URL.
    :param file: the file where the URL is found.
    """
    if not is_url_reachable(url):
        raise ValueError("Could not reach url={} in file={}!".format(url, str(file)))


def _checks_link(
    file: Path, all_files: Set[Path], regex: Pattern = LINK_PATTERN
) -> None:
    """
    Checks a file for matches to a pattern.

    :param file: the file path
    :param all_files: all the doc file paths
    :param regex: the regex to check for in the file.
    """
    matches = regex.finditer(file.read_text())
    for match in matches:
        result = match.group()
        if is_external_url(result):
            validate_external_url(result, file)
        else:
            validate_internal_url(file, result, all_files)


def _checks_image(file: Path, regex: Pattern = IMAGE_PATTERN) -> None:
    """
    Checks a file for matches to a pattern.

    :param file: the file path
    :param regex: the regex to check for in the file.
    """
    if file == Path("docs/version.md"):
        return
    matches = regex.finditer(file.read_text())
    for match in matches:
        result = match.group(1)

        png_index = result.find(".png")
        jpg_index = result.find(".jpg")
        svg_index = result.find(".svg")
        if png_index != -1 or jpg_index != -1 or svg_index != -1:
            img_path = Path("docs/{}".format(result[RELATIVE_PATH_STR_LEN:]))
            if not img_path.exists():
                raise ValueError(
                    "Image path={} in file={} not found!".format(img_path, str(file))
                )
            return
        if result.startswith("https") or result.startswith("http"):
            if not is_url_reachable(result):
                raise ValueError(
                    "Could not reach url={} in file={}!".format(result, str(file))
                )
        raise ValueError("Image path={} in file={} not `.png` or `.jpg` or `.svg`!")


def _checks_target_blank(file: Path) -> None:
    """
    Check target blank.

    :param file: the file.
    """
    matches = re.finditer("<a.*?>(.+?)</a>", file.read_text())
    for match in matches:
        tag = ET.fromstring(match.group())  # nosec
        href = tag.attrib.get("href")
        target = tag.attrib.get("target")
        if href is not None and is_external_url(href) and target != "_blank":
            raise ValueError(
                f"Anchor tag with href={href} and target={target} in file {str(file)} is not valid."
            )


def check_file(file: Path, all_files: Set[Path]) -> None:
    """
    Check the links in the file.

    :param file: the file path
    :param all_files: all the doc file paths
    """
    _checks_all_html(file)
    _checks_link(file, all_files)
    _checks_target_blank(file)
    _checks_image(file)


def get_all_docs_files() -> Set[Path]:
    """
    Get all file paths to docs or api docs.

    :return: list of all paths
    """
    all_files = Path("docs").glob("**/*.md")
    return set(all_files)


if __name__ == "__main__":
    all_docs_files = get_all_docs_files()
    docs_files = Path("docs").glob("*.md")

    try:
        for file_ in docs_files:
            print("Processing " + str(file_))
            check_file(file_, all_docs_files)
    except Exception as exc:  # pylint: disable=broad-except
        print(exc)
        sys.exit(1)

    print("Done!")
    sys.exit(0)
