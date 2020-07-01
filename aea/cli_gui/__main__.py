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

"""Main entry point for CLI GUI."""  # pragma: no cover

import argparse  # pragma: no cover

import aea.cli_gui  # pragma: no cover

parser = argparse.ArgumentParser(
    description="Launch the gui through python"
)  # pragma: no cover
parser.add_argument(
    "-p", "--port", help="Port that the web server listens on", type=int, default=8080
)  # pragma: no cover

parser.add_argument(
    "-H",
    "--host",
    help="host that the web server serves from",
    type=str,
    default="127.0.0.1",
)  # pragma: no cover

args, unknown = parser.parse_known_args()  # pragma: no cover

# If we're running in stand alone mode, run the application
if __name__ == "__main__":  # pragma: no cover
    aea.cli_gui.run(args.port, args.host)
