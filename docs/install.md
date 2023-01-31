# Installation

!!! Info "Platforms"
    The AEA framework can be used on `Windows`, `Ubuntu/Debian` and `MacOS`.

## System Requirements

1. <a name="python"></a>You need <a href="https://www.python.org/downloads/" target="_blank">Python 3.8, 3.9 or 3.10</a> on your system.
2. GCC installation is also required:
 
    === "Ubuntu"
        ``` bash
        apt-get install gcc
        ```
    === "MacOS X (with <a href="https://brew.sh" target="_blank">Homebrew</a>)"
        ``` bash
        brew install gcc
        ```
    === "Windows (with <a href="https://chocolatey.org/" target="_blank">choco</a>)"
        ``` bash
        choco install mingw
        ```

??? tip "Tips"

    - **Ubuntu/Debian**: install Python headers, depending on the Python version you have installed on your machine. For example for Python 3.8: 

        ``` bash
        sudo apt-get install python3.8-dev
        ```

    - **Windows**: install <a href="https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2019" target="_blank">tools for Visual Studio</a>.

### Alternatively: Use Docker

We also provide a Docker image with all the needed dependencies.

[//]: # (To use the image, you will first have to pull it, then run it with your current local directory mounted as a docker volume. This allows you to keep your agents local while working on them from within the docker container.)

1. Pull the image:

    ``` bash
    docker pull fetchai/aea-user:latest
    ```

2. Run the image with your current local directory mounted as a docker volume. This allows you to keep your agents local while working on them from within the docker container:

    === "Linux and MacOs"
        ``` bash
        docker run -it -v $(pwd):/agents --workdir=/agents fetchai/aea-user:latest
        ```
    === "Windows"
        ``` powershell
        docker run -it -v %cd%:/agents --workdir=/agents fetchai/aea-user:latest
        ```

Once successfully logged into the docker container, you can follow the rest of the guide the same way as if not using docker.

## For Agent Development

### Preliminaries

1. Create a new working directory. Let's call it `my_aea_projects`. This is where you will create your agent projects.

2. Inside `my_aea_projects`, add an empty directory called `packages`. This is a local registry for your agents' components.

You should now have the following directory structure:

```bash
my_aea_projects
└── packages
```

!!! tip "Alternatively, clone a template repo:"
    Instead of the above, you can clone the template repo as described in `Approach 1` in the <a href="../development-setup#approach-1">development setup</a> guide.

#### Virtual Environment

Unless you are using the docker image, we highly recommend using a virtual environment so that your setup is isolated from the rest of your system. This prevents clashes and ensures consistency across dependencies.

You can use any common virtual environment manager for Python, such as [`pipenv`](https://pypi.org/project/pipenv/) and [`poetry`](https://python-poetry.org/docs/#installation). If you do not have either, install one.

Once installed, create a new virtual environment in the `my_aea_projects` directory and enter it:

=== "pipenv"
    Use any <a href="#system-requirements">Python version supported</a> in the command:
    ``` bash
    pipenv --python 3.9 && pipenv shell
    ```
=== "poetry"
    ``` bash
    poetry init -n && poetry shell
    ```

### Installation

The latest version of the Python implementation of the AEA Framework is:

<a href="https://pypi.org/project/aea/" target="_blank"><img alt="PyPI" src="https://img.shields.io/pypi/v/aea"></a>

!!! info "Note"
    If you are upgrading your AEA project from a previous version of the AEA framework, make sure you check out <a href="../upgrading/">the upgrading notes</a>.

#### Using pip

Install the AEA framework using pip:

=== "bash/windows"
    ``` bash
    pip install aea[all]
    ```
=== "zsh"
    ``` zsh
    pip install 'aea[all]'
    ```

??? tip "Troubleshooting"
    To ensure no cache is used, add `--force --no-cache-dir` to the installation command.

#### Using pipx

Install the AEA framework using pipx:

``` bash
pipx install aea[all]
```

## For Contributing to the AEA Framework

To contribute to the development of the framework or related tools (e.g. ACN), please refer to the <a href="https://github.com/fetchai/agents-aea/blob/main/CONTRIBUTING.md">Contribution</a> and <a href="https://github.com/fetchai/agents-aea/blob/main/DEVELOPING.md">Development</a> guides in our GitHub repository.

## Other Tools You Might Need

Depending on what you want to do, you might need extra tools on your system:

- To use the Agent Communication Network (ACN) for peer-to-peer communication between agents (e.g. using the `fetchai/p2p_libp2p` connection) you will need <a href="https://go.dev/doc/install" target="_blank"> Golang 1.14.2 or higher</a>.
- The framework uses <a href="https://protobuf.dev" target="_blank">Google Protocol Buffers</a> for message serialization. If you want to develop protocols, install the protobuf compiler on your system. The version you install must match the `protobuf` library installed with the project (see <a href="https://github.com/fetchai/agents-aea/blob/main/pyproject.toml" target="_blank">pyproject.toml</a>).
- To update fingerprint hashes of packages, you will need the <a href="https://docs.ipfs.tech/install" target="_blank">IPFS daemon</a>.
