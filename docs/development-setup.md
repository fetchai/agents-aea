

An AEA <a href="../package-imports">consists of many packages </a>. When developing, it helps to be able to save packages in a local package registry, rather than pushing them to <a href="https://aea-registry.fetch.ai" target="_blank">remote registry</a>. This guide helps setting up a local package registry and configuring the working directory for development.

## Development setup

To prepare a directory (henceforth working directory) for development with the AEA framework you can take a few steps:

- Either, manually:

	- Ensure you start with an empty working directory to avoid any unnecessary side-effects.

	- In your working directory, create an empty folder called `packages`. This folder will act as the local registry for packages.

	- In your working directory, create a `.env` file with the constant `PYTHONPATH=$PYTHONPATH:path_to_packages_dir` where `path_to_packages_dir` is the path to the packages folder in your working directory.

- Or, automated:

	- Fork our <a href="https://github.com/fetchai/agents-template" target="_blank">template repo</a> for AEA development. Then clone it to your machine.

- Depending on your editor, you might take further steps:

	- VS Code: The Python Extension in VS Code can be configured to include additional paths in the Python path. The extension has a setting for `python.envFile` which specifies the path to a file containing environment variable definitions. The default is set to `"python.envFile": "${workspaceFolder}/.env"`. Provide the path to the `.env` file in the above settings. In the `.env` file, add the `PYTHONPATH` constant defined above. Then close VS Code and re-open it for the settings to take effect.

## Developing an AEA

- When developing a specific AEA, it might be helpful to publish/push or fetch/add from local registry. From your working directory, simply execute the usual AEA CLI commands. The CLI will first search in the `packages` directory, then in the remote AEA registry. You can explicitly point to local registry by providing flag `--local` (see <a href="../cli-commands">here</a>) or `--remote` to only point to remote registry.

- When working on an AEA it can help to provide a symbolic link to the packages directory, so that the import paths are detected by your editor. Simply create an empty file with `touch packages` in your AEA project, then create a symbolic link to the `packages` directory with `ln -s ../packages packages`.
