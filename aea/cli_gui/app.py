import argparse
import glob
import os
import subprocess


import connexion
import flask

parser = argparse.ArgumentParser(description='Launch the AEA CLI GUI')
parser.add_argument(
    '-ad',
    '--agent_dir',
    default='./',
    help='Location of script and package files and where agents will be created (default: my_agents)'
)

args = parser.parse_args()


elements = [['local', 'agent', 'localAgents'],
            ['registered', 'protocol', 'registeredProtocols'],
            ['registered', 'connection', 'registeredConections'],
            ['registered', 'skill', 'registeredSkills'],
            ['local', 'protocol', 'localProtocols']]

def is_agent_dir(dir_name):
    if not os.path.isdir(dir_name):
        return False
    else:
        return os.path.isfile(os.path.join(dir_name, "aea-config.yaml"))


def is_protocol_dir(dir_name):
    if not os.path.isdir(dir_name):
        return False
    else:
        return os.path.isfile(os.path.join(dir_name, "protocol.yaml"))

def is_connection_dir(dir_name):
    if not os.path.isdir(dir_name):
        return False
    else:
        return os.path.isfile(os.path.join(dir_name, "connection.yaml"))

def is_skill_dir(dir_name):
    if not os.path.isdir(dir_name):
        return False
    else:
        return os.path.isfile(os.path.join(dir_name, "skill.yaml"))

def get_agents():
    agent_dir = os.path.join(os.getcwd(), args.agent_dir)

    # Get a list of all the directories paths that ends with .txt from in specified directory
    file_list = glob.glob(os.path.join(agent_dir, '*'))

    agent_list = []

    for path in file_list:
        if is_agent_dir(path):
            head, tail = os.path.split(path)
            agent_list.append({"id": tail, "description": "placeholder description"})

    return agent_list


def get_registered_protocols():
    agent_dir = os.path.join(os.getcwd(), args.agent_dir)
    protocols_dir = os.path.join(agent_dir, "packages/protocols")

    # Get a list of all the directories paths that ends with .txt from in specified directory
    file_list = glob.glob(os.path.join(protocols_dir, '*'))

    items_list = []

    for path in file_list:
        if is_protocol_dir(path):
            head, tail = os.path.split(path)
            items_list.append({"id": tail, "description": "placeholder description"})

    return items_list

def get_registered_connections():
    agent_dir = os.path.join(os.getcwd(), args.agent_dir)
    connections_dir = os.path.join(agent_dir, "packages/connections")

    # Get a list of all the directories paths that ends with .txt from in specified directory
    file_list = glob.glob(os.path.join(connections_dir, '*'))

    items_list = []

    for path in file_list:
        if is_connection_dir(path):
            head, tail = os.path.split(path)
            items_list.append({"id": tail, "description": "placeholder description"})

    return items_list

def get_registered_skills():
    agent_dir = os.path.join(os.getcwd(), args.agent_dir)
    skills_dir = os.path.join(agent_dir, "packages/skills")

    # Get a list of all the directories paths that ends with .txt from in specified directory
    file_list = glob.glob(os.path.join(skills_dir, '*'))

    items_list = []

    for path in file_list:
        if is_skill_dir(path):
            head, tail = os.path.split(path)
            items_list.append({"id": tail, "description": "placeholder description"})

    return items_list

def call_aea(param_list, dir):
    old_cwd = os.getcwd()
    os.chdir(dir)
    ret = subprocess.call(param_list)
    os.chdir(old_cwd)
    return ret

def create_agent(agent_id):
    if call_aea(["aea", "create", agent_id], args.agent_dir) == 0:
        return agent_id, 201  # 201 (Created)
    else:
        return {"detail": "Failed to create Agent {} - a folder of this name may exist already".format(agent_id)}, 400  # 400 Bad request



def delete_agent(agent_id):
    if call_aea(["aea", "delete", agent_id], args.agent_dir) == 0:
        return 'Agent {} deleted'.format(agent_id),   200  # 200 (OK)
    else:
        return {"detail": "Failed to delete Agent {} - it ay not exist".format(agent_id)}, 400  # 400 Bad request


def fetch_item(agent_id, item_type, item_id):
    dir = os.path.join( args.agent_dir, agent_id)
    if call_aea(["aea", "add", item_type, item_id], dir) == 0:
        return agent_id,   201  # 200 (OK)
    else:
        return {"detail": "Failed to add protocol {} to agent {}".format(item_id, agent_id)}, 400  # 400 Bad request



def get_local_items(agent_id, item_type):
    dir = os.path.join(os.path.join( args.agent_dir, agent_id), item_type+"s")

    # Get a list of all the directories paths that ends with .txt from in specified directory
    file_list = glob.glob(os.path.join(dir, '*'))

    items_list = []

    for path in file_list:
        if is_protocol_dir(path):
            head, tail = os.path.split(path)
            items_list.append({"id": tail, "description": "placeholder description"})

    return items_list


app = connexion.FlaskApp(__name__, specification_dir='./')
app.add_api('swagger.yaml')


@app.route('/')
def home():
    """ This function just responds to the browser ULR:  localhost:5000/ """
    return flask.render_template('home.html', len=len(elements), htmlElements=elements)

@app.route('/static/js/home.js')
def homejs():
    """ This function just responds to the browser ULR:  localhost:5000/ """
    return flask.render_template('home.js', len=len(elements), htmlElements=elements)

@app.route('/favicon.ico')
def favicon():
    return flask.send_from_directory(
        os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


# If we're running in stand alone mode, run the application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
