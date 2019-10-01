## Scaffold generator

The scaffold generator builds out the entire directory structure required for creating a particular skill.

For example, create a new AEA project.

``` bash
aea create new_project
cd new_project
```

Then, cd into your project directory and scaffold your project skill, protocol, or connection.

You will see the directories filled out with the files required and the skill, protocol, or connection registered in the top level `aea-config.yaml`.


### Scaffold a skill

``` bash
aea scaffold skill new_skill
```


### Scaffold a protocol

``` bash
aea scaffold protocol new_protocol
```


### Scaffold a connection

``` bash
aea scaffold connection new_connection
```

After running the above commands, you will have the fully constructed file system required by the AEA.

<center>![The echo call and response log](assets/full-scaffold.png)</center>


<br />