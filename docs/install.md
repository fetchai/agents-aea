# Installation and setup

If you want to create Autonomous Economic Agents (AEAs) that can act independently of constant user input and autonomously execute actions to achieve their objective, you can use the AEA framework.

<iframe width="560" height="315" src="https://www.youtube.com/embed/mwkAUh-_uxA" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

This example will take you through a simple AEA to familiarise you with the basics of the framework.

## System Requirements

The AEA framework can be used on `Windows`, `Ubuntu/Debian` and `MacOS`.

You need <a href="https://www.python.org/downloads/" target="_blank">Python 3.6</a> or higher as well as <a href="https://go.dev/dl/" target="_blank">Go 1.14.2</a> or higher installed.

GCC installation is required:

- Ubuntu: `apt-get install gcc`
- Windows (with <a href="https://chocolatey.org/" target="_blank">`choco`</a>
 installed): `choco install mingw`
- MacOS X (with home brew): `brew install gcc`

### Option 1: Manual System Preparation

Install a compatible Python and Go version on your system (see <a href="https://realpython.com/installing-python/" target="_blank">this external resource</a> for a comprehensive guide).

??? note "Manual approach:"

    The following hints can help:
    
    - To install Go, follow the official guide, depending on your platform <a href="https://go.dev/doc/install" target="_blank">here</a>
    - Python is already included by default on many Linux distributions (e.g. Ubuntu), as well as MacOS. To check you have the right version, open a terminal and run:

        ``` bash
        python3 --version
        ```

    - To install Python on Windows machines, you can download a specific release <a href="https://www.python.org/downloads/" target="_blank">here</a>.
    - Ubuntu/Debian systems only: install Python headers, depending on the Python version you have installed on your machine. E.g. for Python 3.7: 

        ``` bash
        sudo apt-get install python3.7-dev
        ```

    - Windows users: install <a href="https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2019" target="_blank">tools for Visual Studio</a>.

### Option 2: Using an 'Automated Install' Script

We provide a script to automatically install all framework dependencies and the framework itself. This means that if you follow this option, you can skip the <a href="../quickstart#installation">installation step</a> that comes later on this page.

??? note "The 'Automated install' script approach:"
    On macOS or Ubuntu run the following commands to download and install:

    ``` bash
    curl https://raw.githubusercontent.com/fetchai/agents-aea/main/scripts/install.sh --output install.sh
    chmod +x install.sh
    ./install.sh
    ```

    On Windows: download <a href="https://raw.githubusercontent.com/fetchai/agents-aea/main/scripts/install.ps1" target="_blank">https://raw.githubusercontent.com/fetchai/agents-aea/main/scripts/install.ps1</a>, then run <code>install.ps1</code> with the PowerShell terminal.

### Option 3: Using Docker

​
We also provide a Docker image with all the needed dependencies.

??? note "Docker approach:"
    To use the image, you will first have to pull it, then run it with your current local directory mounted as a docker volume. This allows you to keep your agents local while working on them from within the docker container.

    To pull:

    ``` bash
    docker pull fetchai/aea-user:latest
    ```
    
    To run the image on Linux and MacOs:

    ``` bash
    docker run -it -v $(pwd):/agents --workdir=/agents fetchai/aea-user:latest 
    ```

    And on Windows:

    ``` bash
    docker run -it -v %cd%:/agents --workdir=/agents fetchai/aea-user:latest 
    ```
    
    Once successfully logged into the docker container, 
    you can follow the rest of the guide the same way as if not using docker.

## Preliminaries

Ensure, you are in a clean working directory:

- either you create it manually `mkdir my_aea_projects/ && cd my_aea_projects/`, then add an empty directory called `packages` with the following command `mkdir packages/`,

- or you clone the template repo as described in `Approach 1` in the <a href="../development-setup#approach-1">development setup</a> guide.

At this point, when typing `ls` you should see a single folder called `packages` in your working environment. This will act as your local registry for AEA components.

Unless you are using the docker image, we highly recommend using a virtual environment to ensure consistency across dependencies.

Check that you have <a href="https://github.com/pypa/pipenv" target="_blank">`pipenv`</a>.

``` bash
which pipenv
```

If you don't have it, install it. Instructions are <a href="https://pypi.org/project/pipenv/" target="_blank">here</a>.

Once installed, create a new environment and open it (here we use Python 3.7 but the AEA framework supports any Python >= 3.6).

``` bash
touch Pipfile && pipenv --python 3.7 && pipenv shell
```

## Installation

The following installs the entire AEA package which also includes a <a href="../cli-commands">command-line interface (CLI)</a>. (You can skip this step if you used the 'install script' above: <a href="../quickstart#option-2-using-an-automated-install-script">Option 2 </a>.)

``` bash
pip install aea[all]
```

If you are using `zsh` rather than `bash` type

``` zsh
pip install 'aea[all]'
```

If the installation steps fail, it might be a dependency issue. Make sure you have followed all the relevant system specific steps above under `System Requirements`.

## Setup Author Name

You can set up your author name using the `init` command:

``` bash
aea init
```

## Register as an AEA Author (optional)

AEAs are composed of components. AEAs and AEA components can be developed by anyone and pushed to the <a href="https://aea-registry.fetch.ai" target="_blank">AEA registry</a> for others to use. To publish packages to the registry, we need to register an author name:

``` bash
aea register
```

This is your unique author (or developer) name in the AEA ecosystem.

You should see a similar output (with your input instead of the sample username and email):

``` bash
Do you have a Registry account? [y/N]: n
Create a new account on the Registry now:
Username: fetchai
Email: hello@fetch.ai
Password:
Please make sure that passwords are equal.
Confirm password:
    _     _____     _
   / \   | ____|   / \
  / _ \  |  _|    / _ \
 / ___ \ | |___  / ___ \
/_/   \_\|_____|/_/   \_\

v1.2.5

AEA configurations successfully initialized: {'author': 'fetchai'}
```

!!! note
    If you would rather not create an account on the registry at this point, then run `aea init --local` instead.
