<a name=".aea.helpers.base"></a>
## aea.helpers.base

Miscellaneous helpers.

<a name=".aea.helpers.base.locate"></a>
#### locate

```python
locate(path)
```

Locate an object by name or dotted path, importing as necessary.

<a name=".aea.helpers.base.load_all_modules"></a>
#### load`_`all`_`modules

```python
load_all_modules(directory: Path, glob: str = "*.py", prefix: str = "") -> Dict[str, types.ModuleType]
```

Load all modules of a directory, recursively.

**Arguments**:

- `directory`: the directory where to search for .py modules.
- `glob`: the glob pattern to match. By default *.py
- `prefix`: the prefix to apply in the import path.

**Returns**:

a mapping from import path to module objects.

<a name=".aea.helpers.base._SysModules.load_modules"></a>
#### load`_`modules

```python
 | @staticmethod
 | @contextmanager
 | load_modules(modules: Sequence[Tuple[str, types.ModuleType]])
```

Load modules as a context manager.

**Arguments**:

- `modules`: a list of pairs (import path, module object).

**Returns**:

None.

<a name=".aea.helpers.base.load_module"></a>
#### load`_`module

```python
load_module(dotted_path: str, filepath: Path) -> types.ModuleType
```

Load a module.

**Arguments**:

- `dotted_path`: the dotted path of the package/module.
- `filepath`: the file to the package/module.

**Returns**:

None

**Raises**:

- `ValueError`: if the filepath provided is not a module.
- `Exception`: if the execution of the module raises exception.

<a name=".aea.helpers.base.import_aea_module"></a>
#### import`_`aea`_`module

```python
import_aea_module(dotted_path: str, module_obj) -> None
```

Add an AEA module to sys.modules.

The parameter dotted_path has the form:

packages.<author_name>.<package_type>.<package_name>

If the closed-prefix packages are not present, add them to sys.modules.
This is done in order to emulate the behaviour of the true Python import system,
which in fact imports the packages recursively, for every prefix.

E.g. see https://docs.python.org/3/library/importlib.html#approximating-importlib-import-module
for an explanation on how the 'import' built-in function works.

**Arguments**:

- `dotted_path`: the dotted path to be used in the imports.
- `module_obj`: the module object. It is assumed it has been already executed.

**Returns**:

None

<a name=".aea.helpers.base.load_agent_component_package"></a>
#### load`_`agent`_`component`_`package

```python
load_agent_component_package(item_type: str, item_name: str, author_name: str, directory: os.PathLike)
```

Load a Python package associated to a component..

**Arguments**:

- `item_type`: the type of the item. One of "protocol", "connection", "skill".
- `item_name`: the name of the item to load.
- `author_name`: the name of the author of the item to load.
- `directory`: the component directory.

**Returns**:

the module associated to the Python package of the component.

<a name=".aea.helpers.base.add_modules_to_sys_modules"></a>
#### add`_`modules`_`to`_`sys`_`modules

```python
add_modules_to_sys_modules(modules_by_import_path: Dict[str, types.ModuleType]) -> None
```

Load all modules in sys.modules.

**Arguments**:

- `modules_by_import_path`: a dictionary from import path to module objects.

**Returns**:

None

<a name=".aea.helpers.base.load_env_file"></a>
#### load`_`env`_`file

```python
load_env_file(env_file: str)
```

Load the content of the environment file into the process environment.

**Arguments**:

- `env_file`: path to the env file.

**Returns**:

None.

<a name=".aea.helpers.base.sigint_crossplatform"></a>
#### sigint`_`crossplatform

```python
sigint_crossplatform(process: subprocess.Popen) -> None
```

Send a SIGINT, cross-platform.

The reason is because the subprocess module
doesn't have an API to send a SIGINT-like signal
both on Posix and Windows with a single method.

However, a subprocess.Popen class has the method
'send_signal' that gives more flexibility in this terms.

**Arguments**:

- `process`: the process to send the signal to.

**Returns**:

None

<a name=".aea.helpers.base.RegexConstrainedString"></a>
### RegexConstrainedString

```python
class RegexConstrainedString(UserString):
 |  RegexConstrainedString(seq)
```

A string that is constrained by a regex.

The default behaviour is to match anything.
Subclass this class and change the 'REGEX' class
attribute to implement a different behaviour.

<a name=".aea.helpers.base.cd"></a>
#### cd

```python
@contextlib.contextmanager
cd(path)
```

Change working directory temporarily.

