# Relationship with the Twelve-Factor App methodology.

The [Twelve-Factor App](https://12factor.net/) is
a set of best practices to build modern
web applications, or *software-as-a-service*.

In this section, we will see how the AEA framework
facilitates the achievement of those
in the development, release and deployment 
phases of an AEA project. 

Note that an AEA instance, as a software agent,
can be seen as a more general case of a web app,
as it not only shows reactive behaviour,
but it is also *proactive*, depending
on the goals assigned to it.

## Codebase

> One codebase tracked in revision control, many deploys

Support: Excellent

The framework does not impose any particular requirement
or convention on the type of version control
software to be used to store an AEA project.

## Dependencies

> Explicitly declare and isolate dependencies

Support: Good

The framework allows an AEA project to explicitly declare
the AEA package dependencies, and the PyPI dependencies 
needed to proper working.

However, it does not provide built-in support
for checking platform-specific dependencies,
e.g. specific Python version, or needed system-wide available libraries.
Nevertheless, this can be indirectly achieved
by means of build scripts called on `aea build`,
which can do the checks manually according to the specific
requirements of the project.


## Config

> Store config in the environment

Support: Good

An AEA project can specify an environment configuration
file `.env`, stored in the project root,
that the framework will use to update 
environment variables before the execution of the AEA instance.

The CLI tool command `aea run` accepts the option `--env PATH`
to change the default configuration file.
However, the framework does not
automatically switch between, nor allows to add, 
different types of configuration files, one for each
deployment step (e.g. development, staging, production),
without using the `--env` option.

## Backing services

> Treat backing services as attached resources

TODO

## Build, release, run

> Strictly separate build and run stages

TODO

## Processes

> Execute the app as one or more stateless processes

TODO

## Port binding

> Export services via port binding

TODO

## Concurrency

> Scale out via the process model

TODO

## Disposability

> Maximize robustness with fast startup and graceful shutdown

TODO

## Dev/prod parity

> Keep development, staging, and production as similar as possible

TODO

## Logs

> Treat logs as event streams

TODO

## Admin processes

> Run admin/management tasks as one-off processes

TODO


## Summary 

TODO table with levels of support: Excellent, Good, Not supported
