# Setting up

Once you successfully <a href="../install">install the AEA framework</a>, you can set it up for agent development.

## Specify Author Handle

You need an author handle before being able to develop agents or agent components. This handle is used in the `author` field of any agent or component you create.

AEAs and their components can be developed by anyone and pushed to the <a href="https://aea-registry.fetch.ai" target="_blank">AEA registry</a> for others to use. To publish packages to the registry, you also need to register your author handle.

### Pick Author Handle and Register

If you are intending to use the registry:

``` bash
aea init --register
```

This will let you pick a new author handle and register it at the same time.

### Pick Author Handle Only

If you are unsure whether you will need a registry account, or intending not to use it, simply pick a new author handle:

``` bash
aea init
```

### Register Author Handle

To register an already created author handle with the AEA registry:

``` bash
aea register
```

!!! info "Note"
    The author handle is your unique author (or developer) name in the AEA ecosystem.
