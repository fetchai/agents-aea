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
import io
import logging
import os
import subprocess  # nosec
import sys
import threading
import time
from enum import Enum
from typing import Dict, List

import connexion

import flask

from aea.configurations.base import PublicId

elements = [
    ["local", "agent", "localAgents"],
    ["registered", "protocol", "registeredProtocols"],
    ["registered", "connection", "registeredConections"],
    ["registered", "skill", "registeredSkills"],
    ["local", "protocol", "localProtocols"],
    ["local", "connection", "localConnections"],
    ["local", "skill", "localSkills"],
]

DEFAULT_AUTHOR = "default_author"


class ProcessState(Enum):
    """The state of execution of the OEF Node."""

    NOT_STARTED = "Not started yet"
    RUNNING = "Running"
    STOPPING = "Stopping"
    FINISHED = "Finished"
    FAILED = "Failed"


oef_node_name = "aea_local_oef_node"
max_log_lines = 100
lock = threading.Lock()


class AppContext:
    """Store useful global information about the app.

    Can't add it into the app object itself because mypy complains.
    """

    oef_process = None
    agent_processes: Dict[str, subprocess.Popen] = {}
    agent_tty: Dict[str, List[str]] = {}
    agent_error: Dict[str, List[str]] = {}
    oef_tty: List[str] = []
    oef_error: List[str] = []

    ui_is_starting = False
    agents_dir = os.path.abspath(os.getcwd())
    module_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "../../")


app_context = AppContext()


def is_agent_dir(dir_name: str) -> bool:
    """Return true if this directory contains an AEA project (an agent)."""
    if not os.path.isdir(dir_name):
        return False
    else:
        return os.path.isfile(os.path.join(dir_name, "aea-config.yaml"))


def get_agents() -> List[Dict]:
    """Return list of all local agents."""
    file_list = glob.glob(os.path.join(app_context.agents_dir, "*"))

    agent_list = []

    for path in file_list:
        if is_agent_dir(path):
            _head, tail = os.path.split(path)
            agent_list.append({"id": tail, "description": "placeholder description"})

    return agent_list


def _sync_extract_items_from_tty(pid: subprocess.Popen):
    item_ids = []
    item_descs = []
    output = []
    err = ""
    for line in io.TextIOWrapper(pid.stdout, encoding="utf-8"):
        if line[:11] == "Public ID: ":
            item_ids.append(line[11:-1])

        if line[:13] == "Description: ":
            item_descs.append(line[13:-1])

    assert len(item_ids) == len(item_descs)

    for i in range(0, len(item_ids)):
        output.append({"id": item_ids[i], "description": item_descs[i]})

    for line in io.TextIOWrapper(pid.stderr, encoding="utf-8"):
        err += line + "\n"

    while pid.poll() is None:
        time.sleep(0.1)  # pragma: no cover

    if pid.poll() == 0:
        return output, 200  # 200 (Success)
    else:
        return {"detail": err}, 400  # 400 Bad request


def get_registered_items(item_type: str):
    """Create a new AEA project."""
    # need to place ourselves one directory down so the searcher can find the packages
    pid = _call_aea_async(
        [sys.executable, "-m", "aea.cli", "search", item_type + "s"],
        app_context.agents_dir,
    )
    return _sync_extract_items_from_tty(pid)


def search_registered_items(item_type: str, search_term: str):
    """Create a new AEA project."""
    # need to place ourselves one directory down so the searcher can find the packages
    pid = _call_aea_async(
        ["aea", "search", item_type + "s", "--query", search_term],
        os.path.join(app_context.agents_dir, "aea"),
    )
    ret = _sync_extract_items_from_tty(pid)
    search_result, status = ret
    response = {
        "search_result": search_result,
        "item_type": item_type,
        "search_term": search_term,
    }
    return response, status


def create_agent(agent_id: str):
    """Create a new AEA project."""
    if (
        _call_aea(
            [
                sys.executable,
                "-m",
                "aea.cli",
                "create",
                agent_id,
                "--author",
                DEFAULT_AUTHOR,
            ],
            app_context.agents_dir,
        )
        == 0
    ):
        return agent_id, 201  # 201 (Created)
    else:
        return (
            {
                "detail": "Failed to create Agent {} - a folder of this name may exist already".format(
                    agent_id
                )
            },
            400,
        )  # 400 Bad request


def delete_agent(agent_id: str):
    """Delete an existing AEA project."""
    if (
        _call_aea(
            [sys.executable, "-m", "aea.cli", "delete", agent_id],
            app_context.agents_dir,
        )
        == 0
    ):
        return "Agent {} deleted".format(agent_id), 200  # 200 (OK)
    else:
        return (
            {"detail": "Failed to delete Agent {} - it may not exist".format(agent_id)},
            400,
        )  # 400 Bad request


def add_item(agent_id: str, item_type: str, item_id: str):
    """Add a protocol, skill or connection to the register to a local agent."""
    agent_dir = os.path.join(app_context.agents_dir, agent_id)
    if (
        _call_aea(
            [sys.executable, "-m", "aea.cli", "add", item_type, item_id], agent_dir
        )
        == 0
    ):
        return agent_id, 201  # 200 (OK)
    else:
        return (
            {
                "detail": "Failed to add {} {} to agent {}".format(
                    item_type, item_id, agent_id
                )
            },
            400,
        )  # 400 Bad request


def remove_local_item(agent_id: str, item_type: str, item_id: str):
    """Remove a protocol, skill or connection from a local agent."""
    agent_dir = os.path.join(app_context.agents_dir, agent_id)
    if (
        _call_aea(
            [sys.executable, "-m", "aea.cli", "remove", item_type, item_id], agent_dir
        )
        == 0
    ):
        return agent_id, 201  # 200 (OK)
    else:
        return (
            {
                "detail": "Failed to remove {} {} from agent {}".format(
                    item_type, item_id, agent_id
                )
            },
            400,
        )  # 400 Bad request


def get_local_items(agent_id: str, item_type: str):
    """Return a list of protocols, skills or connections supported by a local agent."""
    if agent_id == "NONE":
        return [], 200  # 200 (Success)

    # need to place ourselves one directory down so the searcher can find the packages
    pid = _call_aea_async(
        [sys.executable, "-m", "aea.cli", "list", item_type + "s"],
        os.path.join(app_context.agents_dir, agent_id),
    )
    return _sync_extract_items_from_tty(pid)


def scaffold_item(agent_id: str, item_type: str, item_id: str):
    """Scaffold a moslty empty item on an agent (either protocol, skill or connection)."""
    agent_dir = os.path.join(app_context.agents_dir, agent_id)
    if (
        _call_aea(
            [sys.executable, "-m", "aea.cli", "scaffold", item_type, item_id], agent_dir
        )
        == 0
    ):
        return agent_id, 201  # 200 (OK)
    else:
        return (
            {
                "detail": "Failed to scaffold a new {} in to agent {}".format(
                    item_type, agent_id
                )
            },
            400,
        )  # 400 Bad request


def _call_aea(param_list: List[str], dir_arg: str) -> int:
    with lock:
        old_cwd = os.getcwd()
        os.chdir(dir_arg)
        ret = subprocess.call(param_list)  # nosec
        os.chdir(old_cwd)
    return ret


def _call_aea_async(param_list: List[str], dir_arg: str) -> subprocess.Popen:
    # Should lock here to prevent multiple calls coming in at once and changing the current working directory weirdly
    with lock:
        old_cwd = os.getcwd()

        os.chdir(dir_arg)
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        ret = subprocess.Popen(  # nosec
            param_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env
        )
        os.chdir(old_cwd)
    return ret


def start_oef_node():
    """Start an OEF node running."""
    _kill_running_oef_nodes()

    param_list = [
        sys.executable,
        "./scripts/oef/launch.py",
        "--disable_stdin",
        "--name",
        oef_node_name,
        "-c",
        "./scripts/oef/launch_config.json",
    ]

    app_context.oef_process = _call_aea_async(param_list, app_context.agents_dir)

    if app_context.oef_process is not None:
        app_context.oef_tty = []
        app_context.oef_error = []

        tty_read_thread = threading.Thread(
            target=_read_tty, args=(app_context.oef_process, app_context.oef_tty)
        )
        tty_read_thread.start()

        error_read_thread = threading.Thread(
            target=_read_error, args=(app_context.oef_process, app_context.oef_error)
        )
        error_read_thread.start()

        return "OEF Node started", 200  # 200 (OK)
    else:
        return {"detail": "Failed to start OEF Node"}, 400  # 400 Bad request


def get_oef_node_status():
    """Get the status of the OEF Node."""
    tty_str = ""
    error_str = ""
    status_str = str(ProcessState.NOT_STARTED).replace("ProcessState.", "")

    if app_context.oef_process is not None:
        status_str = str(get_process_status(app_context.oef_process)).replace(
            "ProcessState.", ""
        )

        total_num_lines = len(app_context.oef_tty)
        for i in range(max(0, total_num_lines - max_log_lines), total_num_lines):
            tty_str += app_context.oef_tty[i]

        tty_str = tty_str.replace("\n", "<br>")

        total_num_lines = len(app_context.oef_error)
        for i in range(max(0, total_num_lines - max_log_lines), total_num_lines):
            error_str += app_context.oef_error[i]

        error_str = error_str.replace("\n", "<br>")

    return {"status": status_str, "tty": tty_str, "error": error_str}, 200  # (OK)


def stop_oef_node():
    """Stop an OEF node running."""
    _kill_running_oef_nodes()
    app_context.oef_process = None
    return "All fine", 200  # 200 (OK)


def start_agent(agent_id: str, connection_id: PublicId):
    """Start a local agent running."""
    # Test if it is already running in some form
    if agent_id in app_context.agent_processes:
        if (
            get_process_status(app_context.agent_processes[agent_id])
            != ProcessState.RUNNING
        ):
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
            if element["id"] == connection_id:
                has_named_connection = True
        if has_named_connection:
            agent_process = _call_aea_async(
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
        agent_process = _call_aea_async(
            [sys.executable, "-m", "aea.cli", "run"], agent_dir
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
            target=_read_tty,
            args=(
                app_context.agent_processes[agent_id],
                app_context.agent_tty[agent_id],
            ),
        )
        tty_read_thread.start()

        error_read_thread = threading.Thread(
            target=_read_error,
            args=(
                app_context.agent_processes[agent_id],
                app_context.agent_error[agent_id],
            ),
        )
        error_read_thread.start()

    return agent_id, 201  # 200 (OK)


def _read_tty(pid: subprocess.Popen, str_list: List[str]):
    for line in io.TextIOWrapper(pid.stdout, encoding="utf-8"):
        out = line.replace("\n", "")
        logging.info("stdout: {}".format(out))
        str_list.append(line)

    str_list.append("process terminated\n")


def _read_error(pid: subprocess.Popen, str_list: List[str]):
    for line in io.TextIOWrapper(pid.stderr, encoding="utf-8"):
        out = line.replace("\n", "")
        logging.error("stderr: {}".format(out))
        str_list.append(line)

    str_list.append("process terminated\n")


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
    return _stop_agent(agent_id)


def _stop_agent(agent_id: str):
    # Test if we have the process id
    if agent_id not in app_context.agent_processes:
        return (
            {"detail": "Agent {} is not running".format(agent_id)},
            400,
        )  # 400 Bad request

    app_context.agent_processes[agent_id].terminate()
    app_context.agent_processes[agent_id].wait()
    del app_context.agent_processes[agent_id]

    return "stop_agent: All fine {}".format(agent_id), 200  # 200 (OK)


def get_process_status(process_id: subprocess.Popen) -> ProcessState:
    """Return the state of the execution."""
    assert process_id is not None

    return_code = process_id.poll()
    if return_code is None:
        return ProcessState.RUNNING
    elif return_code <= 0:
        return ProcessState.FINISHED
    else:
        return ProcessState.FAILED


def _kill_running_oef_nodes():
    logging.info("Kill off any existing OEF nodes which are running...")
    subprocess.call(["docker", "kill", oef_node_name])  # nosec


def create_app():
    """Run the flask server."""
    CUR_DIR = os.path.abspath(os.path.dirname(__file__))
    app = connexion.FlaskApp(__name__, specification_dir=CUR_DIR)
    global app_context
    app_context = AppContext()

    app_context.oef_process = None
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
    def home():
        """Respond to browser URL:  localhost:5000/."""
        return flask.render_template(
            "home.html", len=len(elements), htmlElements=elements
        )

    @app.route("/static/js/home.js")
    def homejs():
        """Serve the home.js file (as it needs templating)."""
        return flask.render_template(
            "home.js", len=len(elements), htmlElements=elements
        )

    @app.route("/favicon.ico")
    def favicon():
        """Return an icon to be displayed in the browser."""
        return flask.send_from_directory(
            os.path.join(app.root_path, "static"),
            "favicon.ico",
            mimetype="image/vnd.microsoft.icon",
        )

    return app


def run(port: int, host: str = "127.0.0.1"):
    """Run the GUI."""
    _kill_running_oef_nodes()

    app = create_app()
    app.run(host=host, port=port, debug=False)

    return app


def run_test():
    """Run the gui in the form where we can run tests against it."""
    app = create_app()
    return app.app.test_client()
