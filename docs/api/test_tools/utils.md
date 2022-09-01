<a id="aea.test_tools.utils"></a>

# aea.test`_`tools.utils

Helpful utilities.

<a id="aea.test_tools.utils.wait_for_condition"></a>

#### wait`_`for`_`condition

```python
def wait_for_condition(condition_checker: Callable,
                       timeout: int = 2,
                       error_msg: str = "Timeout",
                       period: float = 0.001) -> None
```

Wait for condition to occur in selected timeout.

