<a id="aea.helpers.io"></a>

# aea.helpers.io

Wrapper over built-in "open" function.

This module contains a wrapper to the built-in 'open'
function, the 'open_file' function, that fixes the
keyword argument 'newline' to be equal to "\n" (the UNIX line separator).
This will force the line separator to be "\n" both
for incoming and outgoing data.

The reason of this is that files written in an AEA package
need to have "\n" as line separator, on all platforms. Otherwise,
the fingerprint of the packages involved would change across platforms
just because the line separators are replaced.

For instance, the 'open' function on Windows, by default (newline=None),
would replace the line separators "\n" with "\r\n".
This has an impact in the computation of the fingerprint.

Hence, any usage of file system functionalities
should either use 'open_file', or set 'newline="\n"' when
calling the 'open' or the 'pathlib.Path.open' functions.

<a id="aea.helpers.io.open_file"></a>

#### open`_`file

```python
def open_file(file: PathNameTypes,
              mode: str = "r",
              buffering: int = -1,
              encoding: Optional[str] = None,
              errors: Optional[str] = None) -> TextIO
```

Open a file.

Behaviour, kwargs and return type are the same for built-in 'open'
and pathlib.Path.open, except for 'newline', which is fixed to '\n'.

For more details on the keyword arguments, please refer
to the documentation for the built-in 'open':

    https://docs.python.org/3/library/functions.html#open

**Arguments**:

- `file`: either a pathlib.Path object or the type accepted by 'open',
i.e. a string, bytes or integer.
- `mode`: the mode in which the file is opened.
- `buffering`: the buffering policy.
- `encoding`: the name of the encoding used to decode or encode the file.
- `errors`: how encoding errors are to be handled

**Returns**:

the IO object.

<a id="aea.helpers.io.to_csv"></a>

#### to`_`csv

```python
def to_csv(data: Dict[str, str], path: Path) -> None
```

Outputs a dictionary to CSV.

<a id="aea.helpers.io.from_csv"></a>

#### from`_`csv

```python
def from_csv(path: Path) -> Dict[str, str]
```

Load a CSV into a dictionary.

