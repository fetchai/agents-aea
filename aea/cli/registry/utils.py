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
"""Utils used for operating Registry with CLI."""
import os
import tarfile
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, cast

import click

from aea.cli.registry.settings import AUTH_TOKEN_KEY, REGISTRY_API_URL
from aea.cli.utils.config import get_or_create_cli_config
from aea.cli.utils.context import Context
from aea.cli.utils.loggers import logger
from aea.cli.utils.package_utils import find_item_locally
from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.configurations.constants import ITEM_TYPE_TO_PLURAL
from aea.helpers import http_requests as requests


FILE_DOWNLOAD_TIMEOUT = (
    180  # quite big number case possible slow channels and package can be quite big
)


def get_auth_token() -> str:
    """
    Get current auth token.

    :return: str auth token
    """
    config = get_or_create_cli_config()
    return config.get(AUTH_TOKEN_KEY, None)


def request_api(
    method: str,
    path: str,
    params: Optional[Dict] = None,
    data: Optional[Dict] = None,
    is_auth: bool = False,
    files: Optional[Dict] = None,
    handle_400: bool = True,
    return_code: bool = False,
) -> Union[JSONLike, Tuple[JSONLike, int]]:
    """
    Request Registry API.

    :param method: str request method ('GET, 'POST', 'PUT', etc.).
    :param path: str URL path.
    :param params: dict GET params.
    :param data: dict POST data.
    :param is_auth: bool is auth required (default False).
    :param files: optional dict {file_field_name: open(filepath, "rb")} (default None).
    :param handle_400: whether or not to handle 400 response
    :param return_code: whether or not to return return_code

    :return: dict response from Registry API or tuple (dict response, status code).
    """
    headers = {}
    if is_auth:
        token = get_auth_token()
        if token is None:
            raise click.ClickException(
                "Unable to read authentication config. "
                'Please sign in with "aea login" command.'
            )
        headers.update({"Authorization": "Token {}".format(token)})
    try:
        resp = _perform_registry_request(method, path, params, data, files, headers)
        resp_json = resp.json()
    except requests.exceptions.ConnectionError:
        raise click.ClickException("Registry server is not responding.")
    except requests.JSONDecodeError:
        resp_json = None

    if resp.status_code == 200:
        pass
    elif resp.status_code == 201:
        logger.debug("Successfully created!")
    elif resp.status_code == 403:
        raise click.ClickException(
            "You are not authenticated. " 'Please sign in with "aea login" command.'
        )
    elif resp.status_code == 500:
        raise click.ClickException(
            "Registry internal server error: {}".format(resp_json["detail"])
        )
    elif resp.status_code == 404:
        raise click.ClickException("Not found in Registry.")
    elif resp.status_code == 409:
        raise click.ClickException(
            "Conflict in Registry. {}".format(resp_json["detail"])
        )
    elif resp.status_code == 400:
        if handle_400:
            raise click.ClickException(resp_json)
    elif resp_json is None:
        raise click.ClickException(
            "Wrong server response. Status code: {}: Response text: {}".format(
                resp.status_code, resp.text
            )
        )
    else:
        raise click.ClickException(
            "Wrong server response. Status code: {}: Error detail: {}".format(
                resp.status_code, resp_json.get("detail", resp_json)
            )
        )

    if return_code:
        return resp_json, resp.status_code
    return resp_json


def _perform_registry_request(
    method: str,
    path: str,
    params: Optional[Dict] = None,
    data: Optional[Dict] = None,
    files: Optional[Dict] = None,
    headers: Optional[Dict] = None,
) -> requests.Response:
    """Perform HTTP request and resturn response object."""
    request_kwargs = dict(
        method=method,
        url="{}{}".format(REGISTRY_API_URL, path),
        params=params,
        files=files,
        data=data,
        headers=headers,
    )
    resp = requests.request(**request_kwargs)
    return resp


def download_file(url: str, cwd: str, timeout: float = FILE_DOWNLOAD_TIMEOUT) -> str:
    """
    Download file from URL and save it in CWD (current working directory).

    :param url: str url of the file to download.
    :param cwd: str path to current working directory.
    :param timeout: float. timeout to download a file

    :return: str path to downloaded file
    """
    local_filename = url.split("/")[-1]
    filepath = os.path.join(cwd, local_filename)
    # NOTE the stream=True parameter below
    response = requests.get(url, stream=True, timeout=timeout)
    if response.status_code == 200:
        with open(filepath, "wb") as f:
            f.write(response.raw.read())
    else:
        raise click.ClickException(
            "Wrong response from server when downloading package."
        )
    return filepath


def extract(source: str, target: str) -> None:
    """
    Extract tarball and remove source file.

    :param source: str path to a source tarball file.
    :param target: str path to target directory.
    """
    if source.endswith("tar.gz"):
        tar = tarfile.open(source, "r:gz")
        tar.extractall(path=target)
        tar.close()
    else:
        raise ValueError("Unknown file type: {}".format(source))

    os.remove(source)


def _rm_tarfiles() -> None:
    cwd = os.getcwd()
    for filename in os.listdir(cwd):
        if filename.endswith(".tar.gz"):
            filepath = os.path.join(cwd, filename)
            os.remove(filepath)


def clean_tarfiles(func: Callable) -> Callable:
    """Decorate func to clean tarfiles after executing."""

    def wrapper(*args: Any, **kwargs: Any) -> Callable:
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            _rm_tarfiles()
            raise e
        else:
            _rm_tarfiles()
            return result

    return wrapper


def check_is_author_logged_in(author_name: str) -> None:
    """
    Check if current user's name equals to item's author.

    :param author_name: str item author username.

    :raise ClickException: if username and author's name are not equal.
    """
    resp = cast(JSONLike, request_api("GET", "/rest-auth/user/", is_auth=True))
    if not author_name == resp["username"]:
        raise click.ClickException(
            "Author username is not equal to current logged in username "
            "(logged in: {}, author: {}). Please logout and then login correctly.".format(
                resp["username"], author_name
            )
        )


def is_auth_token_present() -> bool:
    """
    Check if any user is currently logged in.

    :return: bool is logged in.
    """
    return get_auth_token() is not None


def get_package_meta(
    obj_type: str, public_id: PublicId, aea_version: Optional[str] = None
) -> JSONLike:
    """
    Get package meta data from remote registry.

    Optionally filter by AEA version.

    :param obj_type: str. component type
    :param public_id: component public id
    :param aea_version: the AEA version (e.g. "0.1.0") or None.

    :return: dict with package details
    """
    params = dict(aea_version=aea_version) if aea_version else None
    api_path = f"/{obj_type}s/{public_id.author}/{public_id.name}/{public_id.version}"
    resp = cast(JSONLike, request_api("GET", api_path, params=params))
    return resp


def get_latest_public_id_mixed(
    ctx: Context,
    item_type: str,
    item_public_id: PublicId,
    aea_version: Optional[str] = None,
) -> PublicId:
    """
    Get latest public id of the message, mixed mode.

    That is, give priority to local registry, and fall back to remote registry
    in case of failure.

    :param ctx: the CLI context.
    :param item_type: the item type.
    :param item_public_id: the item public id.
    :param aea_version: the AEA version constraint, or None
    :return: the path to the found package.
    """
    try:
        _, item_config = find_item_locally(ctx, item_type, item_public_id)
        latest_item_public_id = item_config.public_id
    except click.ClickException:
        logger.debug(
            "Get latest public id from local registry failed, trying remote registry..."
        )
        # the following might raise exception, but we don't catch it this time
        package_meta = get_package_meta(
            item_type, item_public_id, aea_version=aea_version
        )
        latest_item_public_id = PublicId.from_str(cast(str, package_meta["public_id"]))
    return latest_item_public_id


def get_latest_version_available_in_registry(
    ctx: Context,
    item_type: str,
    item_public_id: PublicId,
    aea_version: Optional[str] = None,
) -> PublicId:
    """
    Get latest available package version public id.

    Optionally consider AEA version through the `aea_version` parameter.

    :param ctx: Context object.
    :param item_type: the item type.
    :param item_public_id: the item public id.
    :param aea_version: the AEA version (e.g. "0.1.0") or None.
    :return: the latest public id.
    """
    is_local = ctx.config.get("is_local")
    is_mixed = ctx.config.get("is_mixed")
    try:
        if is_mixed:
            latest_item_public_id = get_latest_public_id_mixed(
                ctx, item_type, item_public_id, aea_version
            )
        elif is_local:
            _, item_config = find_item_locally(ctx, item_type, item_public_id)
            latest_item_public_id = item_config.public_id
        else:
            package_meta = get_package_meta(item_type, item_public_id, aea_version)
            latest_item_public_id = PublicId.from_str(
                cast(str, package_meta["public_id"])
            )
    except Exception:  # pylint: disable=broad-except
        raise click.ClickException(
            f"Package {item_public_id} details can not be fetched from the registry!"
        )

    return latest_item_public_id


def list_missing_packages(
    packages: List[Tuple[str, PublicId]]
) -> List[Tuple[str, PublicId]]:
    """Get list of packages not currently present in registry."""
    result: List[Tuple[str, PublicId]] = []

    for package_type, package_id in packages:
        api_path = f"/{ITEM_TYPE_TO_PLURAL[package_type]}/{package_id.author}/{package_id.name}/{package_id.version}"
        resp = _perform_registry_request("GET", api_path)
        if resp.status_code == 404:
            result.append((package_type, package_id))
        elif resp.status_code == 200:
            pass
        else:  # pragma: nocover
            raise ValueError("Error on registry request")
    return result
