An agent that is generated from the AEA framework is a modular system with different skills, connections, and protocols.
When we create a new agent with the command `aea create my_aea` we create the file structure that looks like the following :
- connections
- protocols
- skills
- vendor
- aea-config.yaml

The `vendor` folder contains the packages from the registry which have been developed by other authors or ourselves and are namespaced by author name. 
The packages we developed as part of the given AEA project are in the respective connections, protocols, and skills folders.

To use a package, the `public_id` for the package must be listed in the `aea-config.yaml` file.
```yaml
connections:
- fetchai/stub:0.1.0
```
The above shows a part of the `aea-config.yaml`. If you see the connections, you will see that we follow a pattern of `author/name_package:version` to identify each package. The author that we are using is the author of the package and not 
the author that shows the `aea-config.yaml` file. This indicates, that we are using a package that is made by Fetch.ai and is located inside the `vendor/fetchai/connections` folder.

The way we import packages inside the agent is in the form of `packages.author.package_type.package_name.module_name`. So for the above example, 
the import path is `packages.fetchai.connections.stub.module_name`. 

The framework loads the modules from the local agent project and adds them to Python's sys.modules under the respective path.

## Create a package

If you want to create a package, you can use `aea scaffold connection/skill/protocol name` and this will create the package
and put it inside the respective folder based on the command for example if we `scaffold` skill with the name `my_skill`
it will be located inside the folder skills in the root directory of the agent (`my_aea/skills/my_skill`). On the other hand,
if you use a package from the registry or the packages folder that comes along with the AEA framework, you will be able to locate
the package under the folder `vendor`. To sum up, the packages you have developed in the context of the given AEA project should be in the root folders and all the other packages under
the `vendor` folder.

## Difference of vendor and own packages

The main difference of the packages that are located under the `vendor` folder and your own is that these packages are located under the vendor folder based on the author. For example, all the packages that we are using are under the folder `vendor/fetchai`
Your packages exist in the root directory of your `aea`.


## Name and author

When you create a package, you must change the author name in the package to match your author handle. You can find these inside
the `.yaml` file of your newly created package.
