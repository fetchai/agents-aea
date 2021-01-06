
We can run an AEA in multiple modes thanks to the configurable design of the framework.

The AEA contains two runnable parts, the `AgentLoop`, which operates the skills, and the Multiplexer, which operates the connections. The `AgentLoop` can be configured to run in `async` or `sync` mode. The `Multiplexer` by default runs in `async` mode. The AEA itself, can be configured to run in `async` mode, if both the `Multiplexer` and `AgentLoop` have the same mode, or in `threaded` mode. The latter ensures that `AgentLoop` and `Multiplexer` are run in separate threads.
