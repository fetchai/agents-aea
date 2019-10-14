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

import argparse
from enum import Enum
import glob
import io
import os
import subprocess
import threading

import connexion
import flask
import yaml


parser = argparse.ArgumentParser(description='Launch the AEA CLI GUI')
parser.add_argument(
    '-ad',
    '--agent_dir',
    default='./',
    help='Location of script and package files and where agents will be created (default: ./)'
)
args = None  # pragma: no cover


elements = [['local', 'agent', 'localAgents'],
            ['registered', 'protocol', 'registeredProtocols'],
            ['registered', 'connection', 'registeredConections'],
            ['registered', 'skill', 'registeredSkills'],
            ['local', 'protocol', 'localProtocols'],
            ['local', 'connection', 'localConnections'],
            ['local', 'skill', 'localSkills']]


class ProcessState(Enum):
    """The state of execution of the OEF Node."""

    NOT_STARTED = "Not started yet"
    RUNNING = "Running"
    STOPPING = "Stopping"
    FINISHED = "Finished"
    FAILED = "Failed"


oef_node_name = "aea_local_oef_node"
max_log_lines = 100


def read_description(dir_name, yaml_name):
    """Return true if this directory contains an items in an AEA project i.e.  protocol, skill or connection."""
    assert os.path.isdir(dir_name)
    file_path = os.path.join(dir_name, yaml_name + ".yaml")
    assert os.path.isfile(file_path)
    with open(file_path, 'r') as stream:
        try:
            yaml_data = yaml.safe_load(stream)
            if "description" in yaml_data:
                return yaml_data["description"]
        except yaml.YAMLError as exc:
            print(exc)
    return "Placeholder description"


def is_agent_dir(dir_name):
    """Return trye if this directory contains an AEA project (an agent)."""
    if not os.path.isdir(dir_name):
        return False
    else:
        return os.path.isfile(os.path.join(dir_name, "aea-config.yaml"))


def is_item_dir(dir_name, item_type):
    """Return true if this directory contains an items in an AEA project i.e.  protocol, skill or connection."""
    if not os.path.isdir(dir_name):
        return False
    else:
        return os.path.isfile(os.path.join(dir_name, item_type + ".yaml"))


def get_agents():
    """Return list of all local agents."""
    agent_dir = os.path.join(os.getcwd(), args.agent_dir)

    file_list = glob.glob(os.path.join(agent_dir, '*'))

    agent_list = []

    for path in file_list:
        if is_agent_dir(path):
            head, tail = os.path.split(path)
            agent_list.append({"id": tail, "description": "placeholder description"})

    return agent_list


def get_registered_items(item_type):
    """Return list of all protocols, connections or skills in the registry."""
    agent_dir = os.path.join(os.getcwd(), args.agent_dir)
    item_dir = os.path.join(agent_dir, "packages/" + item_type + "s")

    file_list = glob.glob(os.path.join(item_dir, '*'))

    items_list = []

    for path in file_list:
        if is_item_dir(path, item_type):
            head, tail = os.path.split(path)
            desc = read_description(path, item_type)
            items_list.append({"id": tail, "description": desc})

    return items_list


def create_agent(agent_id):
    """Create a new AEA project."""
    if _call_aea(["aea", "create", agent_id], args.agent_dir) == 0:
        return agent_id, 201  # 201 (Created)
    else:
        return {"detail": "Failed to create Agent {} - a folder of this name may exist already".format(agent_id)}, 400  # 400 Bad request


def delete_agent(agent_id):
    """Delete an existing AEA project."""
    if _call_aea(["aea", "delete", agent_id], args.agent_dir) == 0:
        return 'Agent {} deleted'.format(agent_id), 200   # 200 (OK)
    else:
        return {"detail": "Failed to delete Agent {} - it ay not exist".format(agent_id)}, 400   # 400 Bad request


def add_item(agent_id, item_type, item_id):
    """Add a protocol, skill or connection to the register to a local agent."""
    agent_dir = os.path.join(args.agent_dir, agent_id)
    if _call_aea(["aea", "add", item_type, item_id], agent_dir) == 0:
        return agent_id, 201  # 200 (OK)
    else:
        return {"detail": "Failed to add protocol {} to agent {}".format(item_id, agent_id)}, 400  # 400 Bad request


def remove_local_item(agent_id, item_type, item_id):
    """Remove a protocol, skill or connection from a local agent."""
    agent_dir = os.path.join(args.agent_dir, agent_id)
    if _call_aea(["aea", "remove", item_type, item_id], agent_dir) == 0:
        return agent_id, 201  # 200 (OK)
    else:
        return {"detail": "Failed to remove {} {} from agent {}".format(item_type, item_id, agent_id)}, 400  # 400 Bad request


def get_local_items(agent_id, item_type):
    """Return a list of protocols, skills or connections supported by a local agent."""
    items_dir = os.path.join(os.path.join(args.agent_dir, agent_id), item_type + "s")

    file_list = glob.glob(os.path.join(items_dir, '*'))

    items_list = []

    for path in file_list:
        if is_item_dir(path, item_type):
            head, tail = os.path.split(path)
            desc = read_description(path, item_type)
            items_list.append({"id": tail, "description": desc})

    return items_list


def scaffold_item(agent_id, item_type, item_id):
    """Scaffold a moslty empty item on an agent (either protocol, skill or connection)."""
    agent_dir = os.path.join(args.agent_dir, agent_id)
    if _call_aea(["aea", "scaffold", item_type, item_id], agent_dir) == 0:
        return agent_id, 201  # 200 (OK)
    else:
        return {"detail": "Failed to scaffold a new {} in to agent {}".format(item_type, agent_id)}, 400  # 400 Bad request


def _call_aea(param_list, dir):
    old_cwd = os.getcwd()
    os.chdir(dir)
    ret = subprocess.call(param_list)
    os.chdir(old_cwd)
    return ret


def _call_aea_async(param_list, dir):
    old_cwd = os.getcwd()
    os.chdir(dir)
    ret = subprocess.Popen(param_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    os.chdir(old_cwd)
    return ret


def start_oef_node(dummy):
    """Start an OEF node running."""
    _kill_running_oef_nodes()

    CUR_DIR = os.path.abspath(os.path.dirname(__file__))

    param_list = [
        "python",
        "scripts/oef/launch.py",
        "--disable_stdin",
        "--name",
        oef_node_name,
        "-c",
        "./scripts/oef/launch_config.json"]

    flask.app.oef_process = _call_aea_async(param_list, os.path.join(CUR_DIR, "../../"))

    if flask.app.oef_process is not None:
        flask.app.oef_tty = []
        flask.app.oef_error = []

        tty_read_thread = threading.Thread(target=_read_tty, args=(flask.app.oef_process, flask.app.oef_tty))
        tty_read_thread.start()

        error_read_thread = threading.Thread(target=_read_error, args=(flask.app.oef_process, flask.app.oef_error))
        error_read_thread.start()

        return "All fine {}".format(dummy), 200   # 200 (OK)
    else:
        return {"detail": "Failed to start OEF Node"}, 400  # 400 Bad request


def get_oef_node_status():
    """Get the status of the OEF Node."""
    tty_str = ""
    error_str = ""
    status_str = str(ProcessState.NOT_STARTED).replace('ProcessState.', '')

    if flask.app.oef_process is not None:
        status_str = str(get_process_status(flask.app.oef_process)).replace('ProcessState.', '')

        total_num_lines = len(flask.app.oef_tty)
        for i in range(max(0, total_num_lines - max_log_lines), total_num_lines):
            tty_str += flask.app.oef_tty[i]

        tty_str = tty_str.replace("\n", "<br>")

        total_num_lines = len(flask.app.oef_error)
        for i in range(max(0, total_num_lines - max_log_lines), total_num_lines):
            error_str += flask.app.oef_error[i]

        error_str = error_str.replace("\n", "<br>")

    return {"status": status_str, "tty": tty_str, "error": error_str}, 200  # (OK)


def stop_oef_node():
    """Stop an OEF node running."""
    _kill_running_oef_nodes()
    flask.app.oef_process = None
    return "All fine", 200  # 200 (OK)


def start_agent(agent_id):
    """Start a local agent running."""
    # Test if it is already running in some form
    if agent_id in flask.app.agent_processes:
        if get_process_status(flask.app.agent_processes[agent_id]) != ProcessState.RUNNING:
            if flask.app.agent_processes[agent_id] is not None:
                flask.app.agent_processes[agent_id].terminate()
                flask.app.agent_processes[agent_id].wait()
            del flask.app.agent_processes[agent_id]
            del flask.app.agent_tty[agent_id]
            del flask.app.agent_erroe[agent_id]
        else:
            return {"detail": "Agent {} is already running".format(agent_id)}, 400  # 400 Bad request

    agent_dir = os.path.join(args.agent_dir, agent_id)
    agent_process = _call_aea_async(["aea", "run"], agent_dir)
    if agent_process is None:
        return {"detail": "Failed to run agent {}".format(agent_id)}, 400  # 400 Bad request
    else:
        flask.app.agent_processes[agent_id] = agent_process
        flask.app.agent_tty[agent_id] = []
        flask.app.agent_error[agent_id] = []

        tty_read_thread = threading.Thread(target=_read_tty, args=(flask.app.agent_processes[agent_id], flask.app.agent_tty[agent_id]))
        tty_read_thread.start()

        error_read_thread = threading.Thread(target=_read_error, args=(flask.app.agent_processes[agent_id], flask.app.agent_error[agent_id]))
        error_read_thread.start()

    return agent_id, 201  # 200 (OK)


def _read_tty(process, str_list):
    for line in io.TextIOWrapper(process.stdout, encoding="utf-8"):
        # print(line)
        str_list.append(line)

    str_list.append("process terminated\n")


def _read_error(process, str_list):
    for line in io.TextIOWrapper(process.stderr, encoding="utf-8"):
        # print("Error:" + line)
        str_list.append(line)

    str_list.append("process terminated\n")


def get_agent_status(agent_id):
    """Get the status of the running agent Node."""
    status_str = str(ProcessState.NOT_STARTED).replace('ProcessState.', '')
    tty_str = ""
    error_str = ""

    if agent_id in flask.app.agent_processes and flask.app.agent_processes[agent_id] is not None:

        status_str = str(get_process_status(flask.app.agent_processes[agent_id])).replace('ProcessState.', '')

    if agent_id in flask.app.agent_tty:
        total_num_lines = len(flask.app.agent_tty[agent_id])
        for i in range(max(0, total_num_lines - max_log_lines), total_num_lines):
            tty_str += flask.app.agent_tty[agent_id][i]

    else:
        tty_str = ""

    tty_str = tty_str.replace("\n", "<br>")

    if agent_id in flask.app.agent_error:
        total_num_lines = len(flask.app.agent_error[agent_id])
        for i in range(max(0, total_num_lines - max_log_lines), total_num_lines):
            error_str += flask.app.agent_error[agent_id][i]

    else:
        error_str = ""

    error_str = error_str.replace("\n", "<br>")

    return {"status": status_str, "tty": tty_str, "error": error_str}, 200  # (OK)


def stop_agent(agent_id):
    """Stop agent running."""
    # Test if we have the process id
    if agent_id not in flask.app.agent_processes:
        return {"detail": "Agent {} is not running".format(agent_id)}, 400  # 400 Bad request

    flask.app.agent_processes[agent_id].terminate()
    flask.app.agent_processes[agent_id].wait()
    del flask.app.agent_processes[agent_id]

    return "stop_agent: All fine {}".format(agent_id), 200  # 200 (OK)


def get_process_status(process_id) -> ProcessState:
    """Return the state of the execution."""
    if process_id is None:
        return ProcessState.NOT_STARTED

    return_code = process_id.poll()
    if return_code is None:
        return ProcessState.RUNNING
    elif return_code <= 0:
        return ProcessState.FINISHED
    elif return_code > 0:
        return ProcessState.FAILED
    else:
        raise ValueError("Unexpected return code.")


def _kill_running_oef_nodes():
    print("Kill off any existing OEF nodes which are running...")
    subprocess.call(['docker', 'kill', oef_node_name])


def run():
    """Run the flask server."""
    _kill_running_oef_nodes()
    CUR_DIR = os.path.abspath(os.path.dirname(__file__))
    app = connexion.FlaskApp(__name__, specification_dir=CUR_DIR)
    flask.app.oef_process = None
    flask.app.agent_processes = {}
    flask.app.agent_tty = {}
    flask.app.agent_error = {}
    flask.app.ui_is_starting = False

    app.add_api('aea_cli_rest.yaml')

    @app.route('/')
    def home():
        """Respond to browser URL:  localhost:5000/ ."""
        return flask.render_template('home.html', len=len(elements), htmlElements=elements)

    @app.route('/static/js/home.js')
    def homejs():
        """Serve the home.js file (as it needs templating)."""
        return flask.render_template('home.js', len=len(elements), htmlElements=elements)

    @app.route('/favicon.ico')
    def favicon():
        """Return an icon to be displayed in the browser."""
        return flask.send_from_directory(
            os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

    app.run(host='127.0.0.1', port=8080, debug=True)


# If we're running in stand alone mode, run the application
if __name__ == '__main__':
    args = parser.parse_args()  # pragma: no cover
    run()

else:
    args, _ = parser.parse_known_args()
