

An AEA <a href="../package-imports">consists of packages </a>. When developing, it helps to be able to save packages in a local package registry, rather than pushing them to <a href="https://aea-registry.fetch.ai" target="_blank">remote registry</a>. This guide helps you set up a local package registry and configure the working directory for development.

There are two ways to write code for an AEA:

1. independent of a concrete AEA project, write individual packages

2. from within an AEA project, write packages for that AEA

## Approach 1

To prepare a directory (henceforth working directory) for development with the AEA framework you can take a few steps:

- Either, manually:

	- Ensure you start with an empty working directory to avoid any unnecessary side effects.

	- In your working directory, create an empty folder called `packages`. This folder will act as the local registry for packages.

	- In your working directory, create a `.env` file with the constant `PYTHONPATH=$PYTHONPATH:path_to_packages_dir` where `path_to_packages_dir` is the path to the packages folder in your working directory.

- Or, automated:

	- Fork our <a href="https://github.com/fetchai/agents-template" target="_blank">template repo</a> for AEA development. Then clone it to your machine.

- Depending on your editor, you might take further steps:

	- VS Code: The Python Extension in VS Code can be configured to include additional paths in the Python path. The extension has a setting for `python.envFile` which specifies the path to a file containing environment variable definitions. The default is set to `"python.envFile": "${workspaceFolder}/.env"`. Provide the path to the `.env` file in the above settings. In the `.env` file, add the `PYTHONPATH` constant defined above. Then close VS Code and re-open it for the settings to take effect.

After developing a package, you can add it to an AEA project in the working directory (e.g. `aea create AGENT_NAME && cd AGENT_NAME && aea add --local PACKAGE_TYPE PUBLIC_ID` will create a new AEA project `AGENT_NAME` and add the package of type `PACKAGE_TYPE` with public id `PUBLIC_ID` to it.)

## Approach 2

It is also possible to develop directly in an AEA project:

- Prepare a directory (henceforth working directory) for development.

- Create a new project `aea create AGENT_NAME && cd AGENT_NAME`

- Scaffold a new package `aea scaffold --with-symlinks PACKAGE_TYPE PACKAGE_NAME`. This will create the package scaffold under the directory `{PACKAGE_TYPE}s` and create symlinks to ensure package import paths line up with the folder structure. The symlinks are not needed to run the AEA. They are purely for your IDE.

- In your working directory, create a `.env` file with the constant `PYTHONPATH=$PYTHONPATH:path_to_project_dir` where `path_to_project_dir` is the path to the AEA project contained in your working directory.

- Depending on your editor, you might take further steps:

	- VS Code: The Python Extension in VS Code can be configured to include additional paths in the Python path. The extension has a setting for `python.envFile` which specifies the path to a file containing environment variable definitions. The default is set to `"python.envFile": "${workspaceFolder}/.env"`. Provide the path to the `.env` file in the above settings. In the `.env` file, add the `PYTHONPATH` constant defined above. Then close VS Code and re-open it for the settings to take effect.

## General advice

This advice partially overlaps with the previous two sections:

- When developing a specific AEA, it might be helpful to publish/push or fetch/add from local registry. From your working directory/AEA project, simply execute the usual AEA CLI commands. The CLI will first search in the `packages` directory, then in the remote AEA registry. You can explicitly point to local registry by providing flag `--local` or `--remote` to only point to remote registry (see <a href="../cli-commands">here</a> for more details on CLI commands).

- When working on an AEA, it may help to provide a symbolic link to the packages directory, so that the import paths are detected by your editor. Simply create an empty file with `touch packages` in your AEA project, then create a symbolic link to the `packages` directory with `ln -s ../packages packages`.

- Alternatively, it can help to provide symbolic links within an AEA to align import paths with folder structure. Simply create an empty file with `touch packages` in your AEA project, then create a symbolic link to `ln -s vendor packages`.
