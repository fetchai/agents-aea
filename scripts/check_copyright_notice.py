#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""
This script checks that all the Python files of the repository have:
- (optional) the Python shebang
- the encoding header;
- the copyright notice;

It is assumed the script is run from the repository root.
"""

import itertools
import sys
from pathlib import Path

SHEBANG = "#!/usr/bin/env python3"
ENCODING_HEADER = "# -*- coding: utf-8 -*-"
COPYRIGHT_NOTICE = """# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------
"""


def check_copyright(file: Path) -> bool:
    """
    Given a file, check if the header stuff is in place.

    Return True if the files has the encoding header and the copyright notice,
    optionally prefixed by the shebang. Return False otherwise.

    :param file: the file to check.
    :return True if the file is compliant with the checks, False otherwise.
    """
    content = file.read_text()
    no_shebang = ENCODING_HEADER + "\n" + COPYRIGHT_NOTICE
    with_shebang = SHEBANG + "\n" + no_shebang
    return content.startswith(with_shebang) or content.startswith(no_shebang)


def parse_args():
    """Parse arguments."""
    import argparse

    parser = argparse.ArgumentParser("check_copyright_notice")
    parser.add_argument(
        "--directory", type=str, default=".", help="The path to the repository root."
    )


if __name__ == "__main__":
    python_files = itertools.chain(
        Path("aea").glob("**/*.py"),
        Path("packages").glob("**/*.py"),
        Path("tests").glob("**/*.py"),
        Path("scripts").glob("**/*.py"),
        Path("examples").glob("**/*.py"),
        [Path("setup.py")],
    )

    # filter out protobuf files (*_pb2.py)
    python_files_filtered = filter(
        lambda x: not str(x).endswith("_pb2.py"), python_files
    )

    bad_files = [
        filepath for filepath in python_files_filtered if not check_copyright(filepath)
    ]

    if len(bad_files) > 0:
        print("The following files are not well formatted:")
        print("\n".join(map(str, bad_files)))
        sys.exit(-1)
    else:
        print("OK")
        sys.exit(0)
