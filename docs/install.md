# Installation and setup

## System Requirements

!!! Info "System requirements"
    The AEA framework can be used on `Windows`, `Ubuntu/Debian` and `MacOS`.
    
    You need <a href="https://www.python.org/downloads/" target="_blank">Python 3.8, 3.9 or 3.10</a> on your system.

GCC installation is required:

- Ubuntu: `apt-get install gcc`
- MacOS X (with home brew): `brew install gcc`
- Windows (with <a href="https://chocolatey.org/" target="_blank">`choco`</a>
 installed): `choco install mingw`

### Option 1: Manual System Preparation

Install a compatible Python version on your system.

??? note "Manual approach:"

    The following hints can help:
    
    - Ubuntu/Debian systems only: install Python headers, depending on the Python version you have installed on your machine. E.g. for Python 3.8: 

        ``` bash
        sudo apt-get install python3.8-dev
        ```

    - Windows users: install <a href="https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2019" target="_blank">tools for Visual Studio</a>.

### Option 2: Using Docker

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

Create a new working directory. Let's call it `my_aea_projects`. This is where you will create your agent projects.

Inside `my_aea_projects`, add an empty directory called `packages`. This is a local registry for your agents' components.

You should now have the following directory structure:

```bash
my_aea_projects
└── packages
```

Instead of the above, you can clone the template repo as described in `Approach 1` in the <a href="../development-setup#approach-1">development setup</a> guide.

### Virtual Environment

Unless you are using the docker image, we highly recommend using a virtual environment so that your setup is isolated from the rest of your system. This prevents clashes and ensures consistency across dependencies.

You can use any common virtual environment manager for Python, such as [`pipenv`](https://pypi.org/project/pipenv/) and [`poetry`](https://python-poetry.org/docs/#installation). If you do not have either, install one.

Once installed, create a new virtual environment in the `my_aea_projects` directory and enter it:

=== "pipenv"
    (you can use Python version `3.8`, `3.9`, or `3.10` in the command):
    ``` bash
    pipenv --python 3.9 && pipenv shell
    ```
=== "poetry"
    ``` bash
    poetry init -n && poetry shell
    ```

## Installation

!!! info
    Skip this step if you used the 'install script' above: <a href="../quickstart#option-2-using-an-automated-install-script">Option 2 </a>.

Install the AEA framework:

=== "bash/windows"
    ``` bash
    pip install aea[all]
    ```
=== "zsh"
    ``` zsh
    pip install 'aea[all]'
    ```

If installation fail, it might be a dependency issue. Make sure you have followed all the relevant steps under `System Requirements`.

## Other tools you might need

Depending on what you want to do, you might need extra tools on your system:

- To use the Agent Communication Network (ACN) for peer-to-peer communication between agents (e.g. using the `fetchai/p2p_libp2p` connection) you will need to [install Golang 1.14.2 or higher](https://go.dev/doc/install).
- The framework uses [Google Protocol Buffers](https://protobuf.dev) for message serialization. If you want to develop protocols, install the protobuf compiler on your system. The version you install must match the protobuf library installed with the project (see pyproject.toml).
- To update fingerprint hashes of packages, you will need the IPFS daemon.

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
