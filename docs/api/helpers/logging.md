<a name="aea.helpers.logging"></a>
# aea.helpers.logging

Logging helpers.

<a name="aea.helpers.logging.get_logger"></a>
#### get`_`logger

```python
get_logger(module_path: str, agent_name: str) -> Logger
```

Get the logger based on a module path and agent name.

<a name="aea.helpers.logging.AgentLoggerAdapter"></a>
## AgentLoggerAdapter Objects

```python
class AgentLoggerAdapter(LoggerAdapter)
```

This class is a logger adapter that prepends the agent name to log messages.

<a name="aea.helpers.logging.AgentLoggerAdapter.__init__"></a>
#### `__`init`__`

```python
 | __init__(logger: Logger, agent_name: str) -> None
```

Initialize the logger adapter.

**Arguments**:

- `logger`: the logger.
- `agent_name`: the agent name.

<a name="aea.helpers.logging.AgentLoggerAdapter.process"></a>
#### process

```python
 | process(msg: Any, kwargs: MutableMapping[str, Any]) -> Tuple[Any, MutableMapping[str, Any]]
```

Prepend the agent name to every log message.

<a name="aea.helpers.logging.WithLogger"></a>
## WithLogger Objects

```python
class WithLogger()
```

Interface to endow subclasses with a logger.

<a name="aea.helpers.logging.WithLogger.__init__"></a>
#### `__`init`__`

```python
 | __init__(logger: Optional[Logger] = None, default_logger_name: str = "aea") -> None
```

Initialize the logger.

**Arguments**:

- `logger`: the logger object.
- `default_logger_name`: the default logger name, if a logger is not provided.

<a name="aea.helpers.logging.WithLogger.logger"></a>
#### logger

```python
 | @property
 | logger() -> Logger
```

Get the component logger.

<a name="aea.helpers.logging.WithLogger.logger"></a>
#### logger

```python
 | @logger.setter
 | logger(logger: Optional[Logger]) -> None
```

Set the logger.

