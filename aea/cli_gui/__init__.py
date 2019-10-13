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

"""Main app for CLI GUI."""

import argparse
from enum import Enum
import glob
import os
import subprocess

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


class OEFProcessState(Enum):
    """The state of execution of the OEF Node."""

    NOT_STARTED = "Not started yet"
    RUNNING = "Running"
    STOPPING = "Stopping"
    FINISHED = "Finished"
    FAILED = "Failed"

oef_node_name = "aea_local_oef_node"

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



def start_oef_node(dummy):
    """Start an OEF node running."""
    flask.app.ui_is_starting = True

    old_cwd = os.getcwd()

    CUR_DIR = os.path.abspath(os.path.dirname(__file__))
    os.chdir(os.path.join(CUR_DIR, "../../"))

    kill_running_oef_nodes()


    param_list = [
        "python",
        "scripts/oef/launch.py",
        "--disable_stdin",
        "--name",
        oef_node_name,
        "-c",
        "./scripts/oef/launch_config.json"]

    flask.app.oef_process = subprocess.Popen(param_list)

    os.chdir(old_cwd)

    if flask.app.oef_process is not None:
        return "All fine {}".format(dummy), 200   # 200 (OK)
    else:
        return {"detail": "Failed to start OEF Node"}, 400  # 400 Bad request

def get_oef_node_status():
    """Get the status of the OEF Node."""
    return str(get_oef_process_status()), 200  # (OK)


def stop_oef_node():
    """Stop an OEF node running."""

    kill_running_oef_nodes()
    flask.app.oef_process = None
    return "All fine", 200  # 200 (OK)


def _call_aea(param_list, dir):
    old_cwd = os.getcwd()
    os.chdir(dir)
    ret = subprocess.call(param_list)
    os.chdir(old_cwd)
    return ret


def get_oef_process_status() -> OEFProcessState:
    """Return the state of the execution."""
    if flask.app.oef_process is None:
        return OEFProcessState.NOT_STARTED

    return_code = flask.app.oef_process.poll()
    if return_code is None:
        if flask.app.ui_is_starting:
            return OEFProcessState.RUNNING
        else:
            return OEFProcessState.STOPPING
    elif return_code == 0:
        return OEFProcessState.FINISHED
    elif return_code > 0:
        return OEFProcessState.FAILED
    else:
        raise ValueError("Unexpected return code.")

def kill_running_oef_nodes():
    print("In case there is an OEF node running already - kill it off!")
    subprocess.call(['docker', 'kill', oef_node_name])


def run():
    """Run the flask server."""
    kill_running_oef_nodes()
    CUR_DIR = os.path.abspath(os.path.dirname(__file__))
    app = connexion.FlaskApp(__name__, specification_dir=CUR_DIR)
    flask.app.oef_process = None
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
