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
"""Key pieces of functionality for CLI GUI."""

import glob
import os
import subprocess  # nosec
import sys
import threading
from typing import Dict, List

from click import ClickException

import connexion

import flask

from aea.cli.add import add_item as cli_add_item
from aea.cli.create import create_aea as cli_create_aea
from aea.cli.delete import delete_aea as cli_delete_aea
from aea.cli.fetch import fetch_agent_locally as cli_fetch_agent_locally
from aea.cli.list import list_agent_items as cli_list_agent_items
from aea.cli.registry.fetch import fetch_agent as cli_fetch_agent
from aea.cli.remove import remove_item as cli_remove_item
from aea.cli.scaffold import scaffold_item as cli_scaffold_item
from aea.cli.search import (
    search_items as cli_search_items,
    setup_search_ctx as cli_setup_search_ctx,
)
from aea.cli.utils.config import try_to_load_agent_config
from aea.cli.utils.context import Context
from aea.cli.utils.formatting import sort_items
from aea.cli_gui.utils import (
    ProcessState,
    call_aea_async,
    get_process_status,
    is_agent_dir,
    read_error,
    read_tty,
    stop_agent_process,
    terminate_processes,
)
from aea.configurations.base import PublicId

elements = [
    ["local", "agent", "localAgents"],
    ["registered", "protocol", "registeredProtocols"],
    ["registered", "connection", "registeredConections"],
    ["registered", "skill", "registeredSkills"],
    ["local", "protocol", "localProtocols"],
    ["local", "connection", "localConnections"],
    ["local", "contract", "localContracts"],
    ["local", "skill", "localSkills"],
]


max_log_lines = 100


class AppContext:
    """Store useful global information about the app.

    Can't add it into the app object itself because mypy complains.
    """

    agent_processes: Dict[str, subprocess.Popen] = {}
    agent_tty: Dict[str, List[str]] = {}
    agent_error: Dict[str, List[str]] = {}

    ui_is_starting = False
    agents_dir = os.path.abspath(os.getcwd())
    module_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "../../")

    local = "--local" in sys.argv  # a hack to get "local" option from cli args


app_context = AppContext()


def get_agents() -> List[Dict]:
    """Return list of all local agents."""
    file_list = glob.glob(os.path.join(app_context.agents_dir, "*"))

    agent_list = []

    for path in file_list:
        if is_agent_dir(path):
            _head, tail = os.path.split(path)
            agent_list.append(
                {
                    "public_id": tail,  # it is not a public_id actually, just a folder name.
                    # the reason it's called here so is the view that is used to represent items with public_ids
                    # used also for agent displaying
                    # TODO: change it when we will have a separate view for an agent.
                    "description": "placeholder description",
                }
            )

    return agent_list


def get_registered_items(item_type: str):
    """Create a new AEA project."""
    # need to place ourselves one directory down so the cher can find the packages
    ctx = Context(cwd=app_context.agents_dir)
    try:
        cli_setup_search_ctx(ctx, local=app_context.local)
        result = cli_search_items(ctx, item_type, query="")
    except ClickException:
        return {"detail": "Failed to search items."}, 400  # 400 Bad request
    else:
        sorted_items = sort_items(result)
        return sorted_items, 200  # 200 (Success)


def search_registered_items(item_type: str, search_term: str):
    """Create a new AEA project."""
    # need to place ourselves one directory down so the searcher can find the packages
    ctx = Context(cwd=app_context.agents_dir)
    try:
        cli_setup_search_ctx(ctx, local=app_context.local)
        result = cli_search_items(ctx, item_type, query=search_term)
    except ClickException:
        return {"detail": "Failed to search items."}, 400  # 400 Bad request
    else:
        sorted_items = sort_items(result)
        response = {
            "search_result": sorted_items,
            "item_type": item_type,
            "search_term": search_term,
        }
        return response, 200  # 200 (Success)


def create_agent(agent_id: str):
    """Create a new AEA project."""
    ctx = Context(cwd=app_context.agents_dir)
    try:
        cli_create_aea(ctx, agent_id, local=app_context.local)
    except ClickException as e:
        return (
            {"detail": "Failed to create Agent. {}".format(str(e))},
            400,
        )  # 400 Bad request
    else:
        return agent_id, 201  # 201 (Created)


def delete_agent(agent_id: str):
    """Delete an existing AEA project."""
    ctx = Context(cwd=app_context.agents_dir)
    try:
        cli_delete_aea(ctx, agent_id)
    except ClickException:
        return (
            {"detail": "Failed to delete Agent {} - it may not exist".format(agent_id)},
            400,
        )  # 400 Bad request
    else:
        return "Agent {} deleted".format(agent_id), 200  # 200 (OK)


def add_item(agent_id: str, item_type: str, item_id: str):
    """Add a protocol, skill or connection to the register to a local agent."""
    ctx = Context(cwd=os.path.join(app_context.agents_dir, agent_id))
    ctx.set_config("is_local", app_context.local)
    try:
        try_to_load_agent_config(ctx)
        cli_add_item(ctx, item_type, PublicId.from_str(item_id))
    except ClickException as e:
        return (
            {
                "detail": "Failed to add {} {} to agent {}. {}".format(
                    item_type, item_id, agent_id, str(e)
                )
            },
            400,
        )  # 400 Bad request
    else:
        return agent_id, 201  # 200 (OK)


def fetch_agent(agent_id: str):
    """Fetch an agent."""
    ctx = Context(cwd=app_context.agents_dir)
    fetch_agent = cli_fetch_agent_locally if app_context.local else cli_fetch_agent
    try:
        agent_public_id = PublicId.from_str(agent_id)
        fetch_agent(ctx, agent_public_id)
    except ClickException as e:
        return (
            {"detail": "Failed to fetch an agent {}. {}".format(agent_id, str(e))},
            400,
        )  # 400 Bad request
    else:
        return agent_public_id.name, 201  # 200 (OK)


def remove_local_item(agent_id: str, item_type: str, item_id: str):
    """Remove a protocol, skill or connection from a local agent."""
    agent_dir = os.path.join(app_context.agents_dir, agent_id)
    ctx = Context(cwd=agent_dir)
    try:
        try_to_load_agent_config(ctx)
        cli_remove_item(ctx, item_type, PublicId.from_str(item_id))
    except ClickException:
        return (
            {
                "detail": "Failed to remove {} {} from agent {}".format(
                    item_type, item_id, agent_id
                )
            },
            400,
        )  # 400 Bad request
    else:
        return agent_id, 201  # 200 (OK)


def get_local_items(agent_id: str, item_type: str):

    """Return a list of protocols, skills or connections supported by a local agent."""
    if agent_id == "NONE":
        return [], 200  # 200 (Success)

    # need to place ourselves one directory down so the searcher can find the packages
    ctx = Context(cwd=os.path.join(app_context.agents_dir, agent_id))
    try:
        try_to_load_agent_config(ctx)
        result = cli_list_agent_items(ctx, item_type)
    except ClickException:
        return {"detail": "Failed to list agent items."}, 400  # 400 Bad request
    else:
        sorted_items = sort_items(result)
        return sorted_items, 200  # 200 (Success)


def scaffold_item(agent_id: str, item_type: str, item_id: str):
    """Scaffold a moslty empty item on an agent (either protocol, skill or connection)."""
    agent_dir = os.path.join(app_context.agents_dir, agent_id)
    ctx = Context(cwd=agent_dir)
    try:
        try_to_load_agent_config(ctx)
        cli_scaffold_item(ctx, item_type, item_id)
    except ClickException:
        return (
            {
                "detail": "Failed to scaffold a new {} in to agent {}".format(
                    item_type, agent_id
                )
            },
            400,
        )  # 400 Bad request
    else:
        return agent_id, 201  # 200 (OK)


def start_agent(agent_id: str, connection_id: PublicId):
    """Start a local agent running."""
    # Test if it is already running in some form
    if agent_id in app_context.agent_processes:
        if (
            get_process_status(app_context.agent_processes[agent_id])
            != ProcessState.RUNNING
        ):  # pragma: no cover
            if app_context.agent_processes[agent_id] is not None:
                app_context.agent_processes[agent_id].terminate()
                app_context.agent_processes[agent_id].wait()
            del app_context.agent_processes[agent_id]
            del app_context.agent_tty[agent_id]
            del app_context.agent_error[agent_id]
        else:
            return (
                {"detail": "Agent {} is already running".format(agent_id)},
                400,
            )  # 400 Bad request

    agent_dir = os.path.join(app_context.agents_dir, agent_id)

    if connection_id is not None and connection_id != "":
        connections = get_local_items(agent_id, "connection")[0]
        has_named_connection = False
        for element in connections:
            if element["public_id"] == connection_id:
                has_named_connection = True
        if has_named_connection:
            agent_process = call_aea_async(
                [
                    sys.executable,
                    "-m",
                    "aea.cli",
                    "run",
                    "--connections",
                    str(connection_id),
                ],
                agent_dir,
            )
        else:
            return (
                {
                    "detail": "Trying to run agent {} with non-existent connection: {}".format(
                        agent_id, connection_id
                    )
                },
                400,
            )  # 400 Bad request
    else:
        agent_process = call_aea_async(
            [sys.executable, "-m", "aea.cli", "run", "--install-deps"], agent_dir
        )

    if agent_process is None:
        return (
            {"detail": "Failed to run agent {}".format(agent_id)},
            400,
        )  # 400 Bad request
    else:
        app_context.agent_processes[agent_id] = agent_process
        app_context.agent_tty[agent_id] = []
        app_context.agent_error[agent_id] = []

        tty_read_thread = threading.Thread(
            target=read_tty,
            args=(
                app_context.agent_processes[agent_id],
                app_context.agent_tty[agent_id],
            ),
        )
        tty_read_thread.start()

        error_read_thread = threading.Thread(
            target=read_error,
            args=(
                app_context.agent_processes[agent_id],
                app_context.agent_error[agent_id],
            ),
        )
        error_read_thread.start()

    return agent_id, 201  # 200 (OK)


def get_agent_status(agent_id: str):
    """Get the status of the running agent Node."""
    status_str = str(ProcessState.NOT_STARTED).replace("ProcessState.", "")
    tty_str = ""
    error_str = ""

    # agent_id will not be in lists if we haven't run it yet
    if (
        agent_id in app_context.agent_processes
        and app_context.agent_processes[agent_id] is not None
    ):
        status_str = str(
            get_process_status(app_context.agent_processes[agent_id])
        ).replace("ProcessState.", "")

    if agent_id in app_context.agent_tty:
        total_num_lines = len(app_context.agent_tty[agent_id])
        for i in range(max(0, total_num_lines - max_log_lines), total_num_lines):
            tty_str += app_context.agent_tty[agent_id][i]

    else:
        tty_str = ""

    tty_str = tty_str.replace("\n", "<br>")

    if agent_id in app_context.agent_error:
        total_num_lines = len(app_context.agent_error[agent_id])
        for i in range(max(0, total_num_lines - max_log_lines), total_num_lines):
            error_str += app_context.agent_error[agent_id][i]

    else:
        error_str = ""

    error_str = error_str.replace("\n", "<br>")

    return {"status": status_str, "tty": tty_str, "error": error_str}, 200  # (OK)


def stop_agent(agent_id: str):
    """Stop agent running."""
    # pass to private function to make it easier to mock
    return stop_agent_process(agent_id, app_context)


def create_app():
    """Run the flask server."""
    CUR_DIR = os.path.abspath(os.path.dirname(__file__))
    app = connexion.FlaskApp(__name__, specification_dir=CUR_DIR)
    global app_context  # pylint: disable=global-statement
    app_context = AppContext()

    app_context.agent_processes = {}
    app_context.agent_tty = {}
    app_context.agent_error = {}
    app_context.ui_is_starting = False
    app_context.agents_dir = os.path.abspath(os.getcwd())
    app_context.module_dir = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "../../"
    )

    app.add_api("aea_cli_rest.yaml")

    @app.route("/")
    def home():  # pylint: disable=unused-variable
        """Respond to browser URL:  localhost:5000/."""
        return flask.render_template(
            "home.html", len=len(elements), htmlElements=elements
        )

    @app.route("/static/js/home.js")
    def homejs():  # pylint: disable=unused-variable
        """Serve the home.js file (as it needs templating)."""
        return flask.render_template(
            "home.js", len=len(elements), htmlElements=elements
        )

    @app.route("/favicon.ico")
    def favicon():  # pylint: disable=unused-variable
        """Return an icon to be displayed in the browser."""
        return flask.send_from_directory(
            os.path.join(app.root_path, "static"),
            "favicon.ico",
            mimetype="image/vnd.microsoft.icon",
        )

    return app


def run(port: int, host: str = "127.0.0.1"):
    """Run the GUI."""

    app = create_app()
    try:
        app.run(host=host, port=port, debug=False)
    finally:
        terminate_processes()

    return app


def run_test():
    """Run the gui in the form where we can run tests against it."""
    app = create_app()
    return app.app.test_client()
