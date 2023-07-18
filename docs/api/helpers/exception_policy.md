<a id="aea.helpers.exception_policy"></a>

# aea.helpers.exception`_`policy

This module contains enum of AEA exception policies.

<a id="aea.helpers.exception_policy.ExceptionPolicyEnum"></a>

## ExceptionPolicyEnum Objects

```python
class ExceptionPolicyEnum(Enum)
```

AEA Exception policies.

<a id="aea.helpers.exception_policy.ExceptionPolicyEnum.propagate"></a>

#### propagate

just bubble up exception raised. run loop interrupted.

<a id="aea.helpers.exception_policy.ExceptionPolicyEnum.stop_and_exit"></a>

#### stop`_`and`_`exit

log exception and stop agent with raising AEAException to show it was terminated

