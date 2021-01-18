## Scaffold generator

The scaffold generator builds out the directory structure required when adding new skills, protocols, contracts and connections to the AEA.

For example, create a new AEA project (add the author flag using your own author handle if this is your first project using the `aea` package).

``` bash
aea create my_aea --author "fetchai"
cd my_aea
```

Then, enter into your project directory and scaffold your project skill, protocol, or connection.


### Scaffold a skill

``` bash
aea scaffold skill my_skill
```


### Scaffold a protocol

``` bash
aea scaffold protocol my_protocol
```


### Scaffold a contract

``` bash
aea scaffold contract my_contract
```

### Scaffold a connection

``` bash
aea scaffold connection my_connection
```

After running the above commands, you are able to develop your own skill, protocol, contract and connection.

Once you have made changes to your scaffolded packages, make sure you update the fingerprint of the package:

``` bash
aea fingerprint [package_name] [public_id]
```

Then you are ready to run the AEA.

<br />