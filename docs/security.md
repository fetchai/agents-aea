
The AEA framework takes every care to follow best practice around security.

The following advice will help you when writing your own code:

- Many potential common security vulnerabilities can be caught by static code analysis. We recommend you use `safety`, `pylint` and `bandit` to analyse your code.

- Don't use relative import paths, these can lead to malicious code being executed.

- Try to avoid using the `subprocess` module. If needed, make sure you sanitise commands passed to `subprocess`.

- Try to avoid using the `pickle` module. Pickle should never be used for agent-to-agent communication protocols.

- By design, the framework prevents skill code from accessing private keys directly, as they are not reachable from the skill execution context through attribute getters. However, if the flag `-p` or the option `--password` are not used when generating private keys for an AEA project via the aea CLI tool, the private keys will be stored in plaintext. This allows the skills to access them via interaction with the OS file system. We recommend to always specify a password to encrypt private keys by using the flag argument.