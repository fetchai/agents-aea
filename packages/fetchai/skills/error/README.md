# Error

## Description

The error skill is used to handle incoming envelops that cannot be properly handled by the framework.

It handles the following cases:

- AEA receives an envelope referencing an unsupported protocol,
- AEA experiences a decoding error when reading an envelope,
- AEA receives an envelope referencing a protocol for which no skill is active.


## Handlers

* `error_handler`: handles `default` messages for problematic envelopes/messages.
