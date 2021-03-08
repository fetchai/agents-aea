
The AEA framework takes every care to follow best practice around security.

The following advice will help you when writing your own code:

- Many potential common security vulnerabilities can be caught by static code analysis. We recommend you use `safety`, `pylint` and `bandit` to analyse your code.

- Don't use relative import paths, these can lead to malicious code being executed.

- Try to avoid using the `subprocess` module. If needed, make sure you sanitise commands passed to `subprocess`.

- Try to avoid using the `pickle` module. Pickle should never be used for agent-to-agent communication protocols.

