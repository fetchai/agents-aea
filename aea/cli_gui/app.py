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


def is_agent_dir(dir_name):
    if not os.path.isdir(dir_name):
        return False
    else:
        return os.path.isfile(os.path.join(dir_name, "aea-config.yaml"))


def get_agents():
    agent_dir = os.path.join(os.getcwd(), args.agent_dir)

    # Get a list of all the directories paths that ends with .txt from in specified directory
    file_list = glob.glob(os.path.join(agent_dir, '*'))

    agent_list = []


    # Iterate over the list of filepaths & test if they are aea project directories
    for path in file_list:
        if is_agent_dir(path):
            head, tail = os.path.split(path)
            agent_list.append({"agentId": tail, "description": "placeholder description"})

    return agent_list


def create_agent(agent_id):
    old_cwd = os.getcwd()
    os.chdir(args.agent_dir)
    ret = subprocess.call(["aea", "create", agent_id])
    print("creating agent: {}".format(os.path.join(os.getcwd(), agent_id)))
    os.chdir(old_cwd)

    if ret == 0:
        return agent_id, 201  # 201 (Created)
    else:
        return {"detail": "Failed to create Agent {} - a folder of this name may exist already".format(agent_id)}, 400  # 400 Bad request



def delete_agent(agent_id):
    old_cwd = os.getcwd()
    os.chdir(args.agent_dir)
    ret = subprocess.call(["aea", "delete", agent_id])
    print("ret ={} ".format(ret))
    os.chdir(old_cwd)
    if ret == 0:
        return 'Agent {} deleted'.format(agent_id),   200  # 200 (OK)
    else:
        return {"detail": "Failed to delete Agent {} - it ay not exist".format(agent_id)}, 400  # 400 Bad request





app = connexion.FlaskApp(__name__, specification_dir='./')
app.add_api('swagger.yaml')


@app.route('/')
def home():
    """ This function just responds to the browser ULR:  localhost:5000/ """
    return flask.render_template('home.html')



@app.route('/favicon.ico')
def favicon():
    return flask.send_from_directory(
        os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


# If we're running in stand alone mode, run the application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
