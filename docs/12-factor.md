# Relationship with the Twelve-Factor App methodology.

The <a href="https://12factor.net/" target="_blank">Twelve-Factor App</a> is
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


## Configuration

> Store configuration in the environment

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

Support: Good

A persistent storage of an AEA can be seen 
as an attached resource in the 12-factor terminology. 
The default storage is SQLite, but the interface 
`AbstractStorageBacked` allows to implement
specific wrappers to other backing services,
without changing the AEA project code.
The support for integrating
different storage back-end implementations in an AEA project
by using a plug-in mechanism is currently missing. 

Moreover, new adapters to backing services
can be implemented as custom connections, which 
can connect to attached resources.
This does not usually requires a change
in the skill code, especially
in the case when a custom protocol
can abstract the details of the interaction with 
the specific resource.


## Build, release, run

> Strictly separate build and run stages

Support: Excellent

The phases of build, release and run
of an AEA project are neatly separated,
both for programmatic usage
and through the usage of the CLI tool,
as each of them corresponds to different subcommands.

## Processes

> Execute the app as one or more stateless processes

Support: Excellent

Whether the process is stateless depends on the specific AEA. 
No strict enforcement is applied by the framework.
Moreover, dialogue histories can be stored
with persistent storage, if enabled by the developer.

## Port binding

> Export services via port binding

Support: Excellent

An AEA project may not need to expose services via HTTP.
This property depends on the specific choices of
the project developer, and the framework does not 
impose any restriction.

One of the provided package, the "HTTP server" connection, 
relies on `aiohttp`, which makes the connection completely
self-contained—therefore, it satisfies the requirement. 

Another relevant example is the ACN node, which 
exposes its service to the Libp2p AEA connection

## Concurrency

> Scale out via the process model

Support: Not Supported

The framework does not easily allow to scale up an
AEA instance with multiple processes,
as it is bound to a process.
However, note that its attached services
can live in a different process, which could
give better scalability.

## Disposability

> Maximize robustness with fast startup and graceful shutdown

Support: Good

Disposability of an AEA instance
depends, in general, on the AEA itself;
whether the connections can be quickly 
connected and disconnected,
whether skills can be easily torn
down or not, whether other resources
can be detached successfully like 
the persistent storage,
just to name a few examples.

There has been put some effort into 
reducing startup time, and to ensure
that a graceful shut down can happen 
when the process receives a SIGTERM
under normal circumstances,
but robustness cannot be ensured for individual components,
as it depends on their implementation.

Additionally,
the framework does provide some features to 
control some aspects of AEA disposability,
e.g. the possibility to change
execution timeout for behaviours or handlers, 
implementation of an effective exception propagation
from a component code to the main agent loop.

## Dev/prod parity

> Keep development, staging, and production as similar as possible

Support: Good

This aspect mostly depends on the specific AEA project,
and the framework does not impose particular restrictions
on best deployment practices (e.g. continuous integration,
same backing services between development
and production stages). 

## Logs

> Treat logs as event streams

Support: Excellent

Thanks to the seamless integration with the 
Python standard library `logging`,
the developer or the deployer has great control
on the routing and filtering of log records.
The behaviour can be changed by providing
a proper configuration in the AEA project configuration file,
according to the standard library specification.
The framework facilitates this 
by creating ad-hoc logger names that can be used
for finer-grained routing or filtering;
for example, each AEA instance uses its own 
logging namespace to send logging events.
Integration with other log handlers
is delegated to extensions of the standard library,
hence not necessarily coupled with the AEA framework.

## Admin processes

> Run admin/management tasks as one-off processes

Support: Good

The CLI tool provides commands to
manage private keys and ledger related operations, and 
it is possible to extend it with a plugin to manage databases of AEA's persistent storage
for maintenance operations.

Moreover, the Python programming language
makes it easy to run one-off scripts or running a console
(also known as REPL) to do management tasks.
It follows that it is also easy to ensure
dependency isolation and same configurations
of the running AEA instance.
