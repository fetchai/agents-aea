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
This module contains an adaptation of click.testing.CliRunner

In particular, it fixes an issue in
CLIRunner.invoke, in the 'finally' clause. More precisely, before reading from
the testing outstream, it checks whether it has been already closed.

Links:

    https://github.com/pallets/click/issues/824

"""
import shlex
import sys

from click._compat import string_types  # type: ignore
from click.testing import CliRunner as ClickCliRunner, Result


class CliRunner(ClickCliRunner):
    """Patch of click.testing.CliRunner"""

    def invoke(
        self,
        cli,
        args=None,
        input=None,  # pylint: disable=redefined-builtin
        env=None,
        catch_exceptions=True,
        color=False,
        **extra
    ):
        """Patch click.testing.CliRunner.invoke()."""
        exc_info = None
        with self.isolation(input=input, env=env, color=color) as outstreams:
            exception = None
            exit_code = 0

            if isinstance(args, string_types):
                args = shlex.split(args)

            try:
                prog_name = extra.pop("prog_name")
            except KeyError:
                prog_name = self.get_default_prog_name(cli)

            try:
                cli.main(args=args or (), prog_name=prog_name, **extra)
            except SystemExit as e:
                exc_info = sys.exc_info()
                exit_code = e.code
                if exit_code is None:
                    exit_code = 0

                if exit_code != 0:
                    exception = e

                if not isinstance(exit_code, int):
                    sys.stdout.write(str(exit_code))
                    sys.stdout.write("\n")
                    exit_code = 1

            except Exception as e:  # pylint: disable=broad-except
                if not catch_exceptions:
                    raise
                exception = e
                exit_code = 1
                exc_info = sys.exc_info()
            finally:
                sys.stdout.flush()
                stdout = outstreams[0].getvalue() if not outstreams[0].closed else b""
                if self.mix_stderr:
                    stderr = None
                else:
                    stderr = (
                        outstreams[1].getvalue() if not outstreams[1].closed else b""
                    )

        return Result(
            runner=self,
            stdout_bytes=stdout,
            stderr_bytes=stderr,
            exit_code=exit_code,
            exception=exception,
            exc_info=exc_info,
        )
