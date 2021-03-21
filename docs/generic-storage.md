The AEA generic storage: description and usage.

## AEA Generic Storage
AEA generic storage allows AEA skill's components to store data permanently and use it any time.
The primary scenario: to save AEA data on shutdown and load back on startup.
Generic storage provides an API for general data manipulation in key-object style.


## Configuration
Storage is enabled by providing in the agent configuration (`aea-config.yaml`) an optional `storage_uri`. The storage URI consists of the backend name and string data provided to selected backend.

The storage URI schema is `<BACKEND_NAME>://[Optional string]`
Example: `storage_uri: sqlite://./some_file.db` tells the AEA to use SQLite backend and store data in `./some_file.db`.

Supported backends:
* SQLite - bundled with python simple SQL engine that uses file or in-memory storage.

## Dialogues and Storage integration

One of the most useful cases is the integration of the dialogues subsystem and storage. It helps maintain dialogues state during agent restarts and reduced memory requirements due to the offloading feature.

### Keep terminal state dialogues

The Dialogues class has the optional boolean argument `keep_terminal_state_dialogues`
which specifies whether a dialogue which has reached its terminal state is kept in memory or not. If `keep_terminal_state_dialogues` is `False`, dialogues that reach a terminal state are removed from memory and can not be used any more. If `keep_terminal_state_dialogues` is `True`, dialogues that reach a terminal state are kept in memory or storage (if configured). If storage is configured, all dialogues in memory are stored on agent stop and restored on agent start.

It useful to save memory with dialogues that are in terminal state and probably will be never used again.

Default behaviour on keep terminals state dialogues is set according to the protocol specification but can be set explicitly with skill configuration section.


Skill configuration to keep terminated dialogues for `DefaultDialogues`.
Example:
### Dialogues dump/restore on agent restart
If storage is enabled then all the dialogues present in memory will be stored on agent's teardown and loaded on agent's start.


### Offload terminal state dialogues

If keep options is set and storage is available dialogues in terminal state will be dumped to generic storage and removed from memory. This option helps to save memory and handle terminated dialogues with the same functionality as when they are kept in memory.

All the active dialogues will be stored and loaded during agent restart. All the terminated offloaded dialogues will stay in storage on agent restart.

To enable dialogues offloading `keep_terminal_state_dialogues` has to be enabled and storage configured.


## Manual usage with skill components
Handlers, Behaviours and Models are able to use storage if enabled.

Storage is available with skill context: `self.context.storage`
if `self.context.storage` is not None, storage is enabled and ready to use.

Generic storage consists of two parts: objects and collections.
Objects consist of the `object_id` (unique string) and object body. The object body is any JSON friendly python data type: `list`, `dict`, `int`, `float`, `string`, `bool`.

Collection is a group of the objects, objects data types can vary in the same collection.
Collection name is name consists of letters, numbers and `_`.


To get/put specific object collection instance should be used.
``` python
my_collection = self.context.storage.get_sync_connection('my_collection')
```

Collection instance provide set of methods to handle data objects.
List of collection methods:
``` python
    def put(self, object_id: str, object_body: JSON_TYPES) -> None:
        """
        Put object into collection.

        :param object_id: str object id
        :param object_body: python dict, json compatible.
        :return: None
        """

    def get(self, object_id: str) -> Optional[JSON_TYPES]:
        """
        Get object from the collection.

        :param object_id: str object id

        :return: dict if object exists in collection otherwise None
        """

    def remove(self, object_id: str) -> None:
        """
        Remove object from the collection.

        :param object_id: str object id

        :return: None
        """

    def find(self, field: str, equals: EQUALS_TYPE) -> List[OBJECT_ID_AND_BODY]:
        """
        Get objects from the collection by filtering by field value.

        :param field: field name to search: example "parent.field"
        :param equals: value field should be equal to

        :return: List of object bodies
        """

    def list(self) -> List[OBJECT_ID_AND_BODY]:
        """
        List all objects with keys from the collection.

        :return: Tuple of objects keys, bodies.
        """
```



Simple behaviour example:

It saves the `datetime` string of the first act and print it to stdout.
``` python
class TestBehaviour(TickerBehaviour):
    """Simple behaviour to count how many acts were called."""

    def setup(self) -> None:
        """Set up behaviour."""

    def act(self) -> None:
        """Make an action."""
        if not (self.context.storage and self.context.storage.is_connected):
        	return
        collection = self.context.storage.get_sync_collection('my_collection')
        first_call_datetime = collection.get("first_call_ts")
        if not first_call_ts:
            # there is no object with "first_call_ts" id.
            first_call_datetime = str(datetime.datetime.now())
	        col.put(first_call_ts, first_call_datetime)
	    print("Act was called for the first time on:", first_call_datetime)
```

Please, pay attention: `datetime` object is not JSON friendly and can not be stored directly. it should be transformed to `timestamp` or string before put into the storage.
